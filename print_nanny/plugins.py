import asyncio
import base64
import glob
import hashlib
import io
import json
import logging
import os
import platform
import queue
import re
import threading
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ProcessPoolExecutor
import time

import multiprocessing
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
import pytz
import uuid
import requests
import numpy as np
from octoprint.events import Events, eventManager
from PIL import Image
import multiprocessing_logging

import print_nanny_client

from .errors import SnapshotHTTPException, WebcamSettingsHTTPException
from .predictor import PredictWorker
from .websocket import WebSocketWorker, RestAPIClient, WorkerManager
from .utils.encoder import NumpyEncoder

logger = logging.getLogger("octoprint.plugins.print_nanny")


CLIENT_EXCEPTIONS = (
    print_nanny_client.exceptions.ApiException,
    aiohttp.client_exceptions.ClientError,
)

DEFAULT_API_URL = os.environ.get("PRINT_NANNY_API_URL", "https://print-nanny.com/api")
DEFAULT_WS_URL = os.environ.get("PRINT_NANNY_WS_URL", "ws://localhost:8000/ws/predict/")


class BitsyNannyPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.WizardPlugin,
    octoprint.plugin.BlueprintPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.EnvironmentDetectionPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.ShutdownPlugin,
):

    PREDICT_START = "predict_start"
    PREDICT_DONE = "predict_done"
    PREDICT_FAILED = "predict_failed"

    UPLOAD_START = "upload_start"
    UPLOAD_FAILED = "upload_failed"
    UPLOAD_DONE = "upload_done"

    PRINT_PROGRESS = "print_progress"

    def __init__(self, *args, **kwargs):

        # log multiplexing for multiprocessing.Process
        multiprocessing_logging.install_mp_handler()

        # wraps auto-generated swagger api
        self.rest_client = RestAPIClient()

        # manages worker processes and relay queues
        self._worker_manager = WorkerManager()

        # Dedicated processes for predictor and websocket stream
        self._predict_ui_results = None
        self._predict_ws_results = None
        self._predict_proc = None
        self._ws_proc = None
        self._relay_thread = None

        # REST API calls (async event loop)
        self._api_objects = {}
        self._api_thread = threading.Thread(target=self._start_api_loop)
        self._api_thread.daemon = True
        self._api_thread.start()

        # User interactive
        self._tracking_events = None
        self._calibration = None

        # octoprint event handlers
        self._queue_event_handlers = {
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self._stop,
            Events.PRINT_DONE: self._stop,
            Events.PRINT_CANCELLING: self._stop,
            Events.PRINT_CANCELLED: self._stop,
            Events.PRINT_PAUSED: self._stop,
            Events.PRINT_RESUMED: self._stop,
            Events.UPLOAD: self._handle_file_upload,
            self.PRINT_PROGRESS: self._handle_print_progress_upload,
        }

        self._log_path = None
        self._environment = {}
        self._workers = []
        self._active = False

    def _relay_worker(self):
        """
        Child process to -> Octoprint event bus relay
        """
        logger.info("Started event relay worker")
        while self._active:
            viz_bytes = self._predict_ui_results.get(block=True)
            logger.info(f"Sending {Events.PLUGIN_PRINT_NANNY_PREDICT_DONE}")
            self._event_bus.fire(
                Events.PLUGIN_PRINT_NANNY_PREDICT_DONE,
                payload={"image": base64.b64encode(viz_bytes)},
            )

    def _start_api_loop(self):
        self._event_loop = asyncio.new_event_loop()
        self._upload_queue = asyncio.Queue(loop=self._event_loop)
        self._event_loop.run_until_complete(self._upload_worker())

    def on_shutdown(self):
        for worker in self._workers:
            logging.warning(f"Shutting down {worker}")
            worker.join(timeout=10)

    async def _start_workers(self, retries=3):

        self._active = True

        if self._predict_ui_results is None:
            self._predict_ui_results = multiprocessing.Queue()

        if self._predict_ws_results is None:
            self._predict_ws_results = multiprocessing.Queue()
        # UI streaming loop
        if self._relay_thread is None:
            self._relay_thread = threading.Thread(target=self._relay_worker)
            self._relay_thread.daemon = True
            self._relay_thread.start()
            self._workers.append(self._relay_thread)

        if self._predict_proc is None:
            webcam_url = self._settings.global_get(["webcam", "snapshot"])
            self._predict_proc = multiprocessing.Process(
                target=PredictWorker,
                args=(
                    webcam_url,
                    self._predict_ui_results,
                    self._predict_ws_results,
                    self._calibration,
                ),
            )
            self._predict_proc.daemon = True
            logger.info("Starting PredictWorker process")
            self._workers.append(self._predict_proc)
            self._predict_proc.start()

        if self._ws_proc is None:
            api_token = self._settings.get(["auth_token"])
            ws_url = self._settings.get(["ws_url"])
            print_job_id = self._api_objects.get("print_job", {}).get("id")

            self._ws_proc = multiprocessing.Process(
                target=WebSocketWorker,
                args=(ws_url, api_token, self._predict_ws_results, print_job_id),
            )
            self._ws_proc.daemon = True
            self._workers.append(self._ws_proc)
            self._ws_proc.start()

    def _get_metadata(self):
        metadata = {
            "printer_data": self._printer.get_current_data(),
            "printer_profile": self._printer_profile_manager.get_current_or_default(),
            "temperature": self._printer.get_current_temperatures(),
            "dt": datetime.now(pytz.timezone("America/Los_Angeles")),
            "plugin_version": self._plugin_version,
            "octoprint_version": octoprint.util.version.get_octoprint_version_string(),
            "platform": platform.platform(),
            "mac_address": ":".join(re.findall("..", "%012x".format(uuid.getnode()))),
            "api_objects": {
                k: None if v is None else v.id for k, v in self._api_objects.items()
            },
            "environment": self._environment,
            "plugin_version": self._plugin_version,
        }
        return metadata

    def _queue_upload(self, data):
        self._event_loop.call_soon_threadsafe(self._upload_queue.put_nowait, data)

    def _resume(self, *args, **kwargs):
        self._active = True

    def _pause(self, *args, **kwargs):
        self._active = False

    def _stop(self, *args, **kwargs):
        self._active = False
        for worker in self._workers:
            logging.warning(f"Shutting down {worker}")
            worker.join(timeout=1)
            if isinstance(worker, multiprocessing.Process):
                worker.close()

        self._workers = []
        self._predict_proc = None
        self._ws_proc = None
        self._relay_thread = None
        self._predict_ui_results = None
        self._predict_ws_results = None

    def _reset(self, *args, **kwargs):
        self._api_objects = {}

    async def _test_api_auth(self, auth_token, api_url):
        rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)
        try:
            user = rest_client.get_user()
            self.rest_client = rest_client
            return user
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_test_api_auth API call failed {e}", exc_info=True)
            return

    async def _handle_file_upload(self, event_type, event_data):
        try:

            await self.rest_client.create_gcode_file(event_data, gcode_file_path)
            return gcode_file
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_file_upload API call failed {e}", exc_info=True)

    async def _handle_print_start(self, event_type, event_data):

        event_data.update(self._get_metadata())

        try:
            printer_profile = await self.rest_client.update_or_create_printer_profile(
                event_data
            )

            self._api_objects["printer_profile"] = printer_profile

            gcode_file_path = self._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path
            )

            # self._api_objects["gcode_file"] = gcode_file

            print_job = await self.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id
            )

            self._api_objects["print_job"] = printer_profile

        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        await self._start_workers()

    async def _get_tracking_events(self):
        """
        @todo make tracking events opt-in
        https://github.com/bitsy-ai/octoprint-nanny-plugin/issues/10
        """
        if not self._tracking_events:
            self._tracking_events = self.rest_client.get_tracking_events()
        return self._tracking_events

    async def _handle_octoprint_event(self, event_type, event_data, **kwargs):
        logger.debug(f"_handle_octoprint_event processing {event_type}")

        # handled by _handle_predict_event
        if event_type == self.PREDICT_DONE:
            return
        # handled by _handle_print_progress_update
        if event_type == self.PRINT_PROGRESS:
            return

        elif event_type not in await self._get_tracking_events():
            return

        metadata = {"metadata": self._get_metadata()}
        if event_data is not None:
            event_data.update(metadata)
        else:
            event_data = metadata

        try:
            event = await self.rest_client.create_octoprint_event(
                event_type, event_data
            )
            return event
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_octoprint_event() exception {e}", exc_info=True)

    async def _handle_print_progress_upload(self, event_type, event_data, **kwargs):
        print_job = self._api_objects.get("print_job")
        if print_job is not None:
            try:
                await self.rest_client.update_print_progress(print_job.id, event_data)
            except CLIENT_EXCEPTIONS as e:
                logger.error(
                    f"_handle_print_progress_upload() exception {e}", exc_info=True
                )

    async def _upload_worker(self):
        """
        async
        """
        logger.info("Started _upload_worker thread")
        while True:
            event = await self._upload_queue.get()
            event_type = event.get("event_type")
            if event.get("event_type") is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event_type=event
                    )
                )
                continue
            handler_fn = self._queue_event_handlers.get(event["event_type"])

            try:
                if handler_fn:
                    logger.debug(
                        f"Calling handler_fn {handler_fn} in _upload_worker for {event_type}"
                    )

                    if asyncio.iscoroutinefunction(handler_fn):
                        await handler_fn(**event)
                    else:
                        handler_fn(**event)
                    await self._handle_octoprint_event(**event)

                else:
                    await self._handle_octoprint_event(**event)
            except Exception as e:
                logger.error(e, exc_info=True)
            self._upload_queue.task_done()

    ##
    ## Octoprint api routes + handlers
    ##
    # def register_custom_routes(self):
    @octoprint.plugin.BlueprintPlugin.route("/startPredict", methods=["POST"])
    def start_predict(self):

        # settings test#
        if self._settings.global_get(["webcam", "snapshot"]) is None:
            raise WebcamSettingsHTTPException()
        url = self._settings.global_get(["webcam", "snapshot"])
        res = requests.get(url)
        res.raise_for_status()

        if not self._active:
            logger.info("POST /startPredict is starting predict worker")
            response = asyncio.run_coroutine_threadsafe(
                self._start_workers(), self._event_loop
            ).result()
            self._active = True
        return flask.json.jsonify({"ok": 1})

    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        self._stop()
        return flask.json.jsonify({"ok": 1})

    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get("auth_token")
        api_url = flask.request.json.get("api_url")

        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth(auth_token, api_url), self._event_loop
        ).result()

        if isinstance(response, print_nanny_client.models.user.User):
            self._settings.set(["auth_token"], auth_token)
            self._settings.set(["auth_valid"], True)
            self._settings.set(["api_url"], api_url)
            self._settings.set(["user_email"], response.email)
            self._settings.set(["user_url"], response.url)

            self._settings.save()

            logger.info(f"Authenticated as {response}")
            return flask.json.jsonify(response.to_dict())

        return flask.json.jsonify(response.body)

    def register_custom_events(self):
        return ["predict_done", "predict_failed", "upload_done", "upload_failed"]

    def on_event(self, event_type, event_data):
        IGNORED = [Events.PLUGIN_PRINT_NANNY_PREDICT_DONE]

        if self._tracking_events is None or event_type in self._tracking_events:
            self._queue_upload({"event_type": event_type, "event_data": event_data})
            logger.info(f"{event_type} added to upload queue")

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """

        self._log_path = self._settings.get_plugin_logfile_path()

        if self._settings.get(["auth_token"]) is not None:

            user = self.rest_client.get_user(self._settings.get(["auth_token"]))

            # user = asyncio.run_coroutine_threadsafe(
            #     self._test_api_auth(
            #         auth_token=self._settings.get(["auth_token"]),
            #         api_url=self._settings.get(["api_url"]),
            #     ),
            #     self._event_loop,
            # ).result()

            if user is not None:
                logger.info(f"Authenticated as {user}")
                self._settings.set(["user_email"], user.email)
                self._settings.set(["user_url"], user.url)
            else:
                logger.warning(f"Invalid auth")

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        self._queue_upload(
            {"event_type": self.PRINT_PROGRESS, "event_data": {"progress": progress}}
        )

    ## EnvironmentDetectionPlugin

    def on_environment_detected(self, environment, *args, **kwargs):
        self._environment = environment

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            auth_token=None,
            auth_valid=False,
            user_email=None,
            user_url=None,
            user=None,
            calibrated=False,
            calibrate_x0=None,
            calibrate_y0=None,
            calibrate_x1=None,
            calibrate_y1=None,
            auto_start=False,
            api_url=DEFAULT_API_URL,
            ws_url=DEFAULT_WS_URL,
        )

    ## Wizard plugin mixin

    def get_wizard_version(self):
        return 0

    def is_wizard_required(self):

        return any(
            [
                self._settings.get(["auth_token"]) is None,
                self._settings.get(["api_url"]) is None,
                self._settings.get(["user_email"]) is None,
                self._settings.get(["user_url"]) is None,
            ]
        )

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/nanny.js"],
            css=["css/nanny.css"],
            less=["less/nanny.less"],
            img=["img/wizard_example.jpg"],
            vendor=["vendor/swagger-client@3.12.0.browser.min.js"],
        )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            nanny=dict(
                displayName="Print Nanny",
                displayVersion=self._plugin_version,
                # version check: github repository
                type="github_release",
                user="bitsy-ai",
                repo="octoprint-nanny-plugin",
                current=self._plugin_version,
                # update method: pip
                pip="https://github.com/bitsy-ai/octoprint-nanny-plugin/archive/{target_version}.zip",
            )
        )
