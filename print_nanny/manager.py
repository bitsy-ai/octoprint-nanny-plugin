import aioprocessing
import asyncio
import base64
import re
from datetime import datetime
import platform
import uuid
import pytz
from time import sleep

import logging

import aiohttp

import multiprocessing
import octoprint.filemanager
from octoprint.events import Events

import threading

from print_nanny.clients.websocket import WebSocketWorker
from print_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from print_nanny.predictor import PredictWorker

import print_nanny_client

logger = logging.getLogger("octoprint.plugins.print_nanny.manager")

Events.PRINT_PROGRESS = "print_progress"


class WorkerManager:
    """
    Manages PredictWorker, WebsocketWorker, RestWorker processes
    """

    def __init__(self, plugin):

        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        # proxy objects
        self.shared.printer_profile_id = None
        self.shared.print_job_id = None
        self.shared.calibration = None

        self.active = False

        # holds octoprint events to be uploaded via rest client

        self.tracking_queue = self.manager.AioQueue()
        # streamed to octoprint front-end over websocket
        self.octo_ws_queue = self.manager.AioQueue()
        # streamed to print nanny asgi over websocket
        self.pn_ws_queue = self.manager.AioQueue()

        self._tracking_event_handlers = {
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self.stop,
            Events.PRINT_DONE: self.stop,
            Events.PRINT_CANCELLING: self.stop,
            Events.PRINT_CANCELLED: self.stop,
            Events.PRINT_PAUSED: self.stop,
            Events.PRINT_RESUMED: self.stop,
            Events.PRINT_PROGRESS: self._handle_print_progress_upload,
        }

        self._environment = {}

        # daemonized threads for rest api and octoprint websocket relay
        self.rest_api_thread = threading.Thread(target=self._rest_api_worker)
        self.rest_api_thread.daemon = True

        self.octo_ws_thread = threading.Thread(target=self._octo_ws_queue_worker)
        self.octo_ws_thread.daemon = True

        self.loop = None
        self.tracking_events = None

    @property
    def rest_client(self):

        api_token = self.plugin._settings.get(["auth_token"])
        api_url = self.plugin._settings.get(["api_url"])

        logger.debug(f"RestAPIClient init with api_token={api_token} api_url={api_url}")
        return RestAPIClient(auth_token=api_token, api_url=api_url)

    def on_settings_initialized(self):

        self.rest_api_thread.start()
        self.octo_ws_thread.start()
        while self.loop is None:
            sleep(1)

    async def _handle_print_progress_upload(self, event_type, event_data, **kwargs):
        if self.shared.print_job_id is not None:
            try:
                await self.rest_client.update_print_progress(
                    self.shared.print_job_id, event_data
                )
            except CLIENT_EXCEPTIONS as e:
                logger.error(
                    f"_handle_print_progress_upload() exception {e}", exc_info=True
                )

    async def _handle_octoprint_event(self, event_type, event_data):

        metadata = {"metadata": self._get_metadata()}
        if event_data is not None:
            event_data.update(metadata)
        else:
            event_data = metadata

        try:
            await self.rest_client.create_octoprint_event(event_type, event_data)
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_octoprint_event() exception {e}", exc_info=True)

    def _rest_api_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        return self.loop.run_until_complete(
            asyncio.ensure_future(self._tracking_queue_loop())
        )

    async def _tracking_queue_loop(self):
        logger.info("Started _rest_client_worker")

        api_token = None

        while True:

            if api_token is None:
                api_token = self.plugin._settings.get(["auth_token"])
                await asyncio.sleep(30)
                continue

            if self.tracking_events is None:
                try:
                    self.tracking_events = await self.rest_client.get_tracking_events()
                except CLIENT_EXCEPTIONS as e:
                    logger.error(e)
                    await asyncio.sleep(30)
                continue

            event = await self.tracking_queue.coro_get()
            event_type = event.get("event_type")
            if event_type is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event_type=event
                    )
                )
                continue

            # ignore events originating from print_nanny plugin
            if event_type == Events.PLUGIN_PRINT_NANNY_PREDICT_DONE:
                continue

            # ignore untracked events
            if event_type not in self.tracking_events:
                logger.warning(f"Discarding {event_type}")
                continue

            handler_fn = self._tracking_event_handlers.get(event["event_type"])

            try:
                if handler_fn:
                    await handler_fn(**event)
                await self._handle_octoprint_event(**event)
            except CLIENT_EXCEPTIONS as e:
                logger.error(e, exc_info=True)

    def stop(self):
        """
        joins and terminates prediction and pn websocket processes
        """

        self.active = False

        logger.info("Terminating predict process")
        self.predict_proc.terminate()
        logger.info("Terminating websocket process")
        self.pn_ws_proc.terminate()

    def start(self):
        """
        starts prediction and pn websocket processes
        """
        self.active = True
        webcam_url = self.plugin._settings.global_get(["webcam", "snapshot"])

        self.predict_proc = multiprocessing.Process(
            target=PredictWorker,
            args=(
                webcam_url,
                self.shared.calibration,
                self.octo_ws_queue,
                self.pn_ws_queue,
            ),
            daemon=True,
        )
        self.predict_proc.start()

        auth_token = self.plugin._settings.get(["auth_token"])
        ws_url = self.plugin._settings.get(["ws_url"])
        api_url = self.plugin._settings.get(["api_url"])

        self.plugin.rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)

        self.pn_ws_proc = multiprocessing.Process(
            target=WebSocketWorker,
            args=(ws_url, auth_token, self.pn_ws_queue, self.shared.print_job_id),
            daemon=True,
        )
        self.pn_ws_proc.start()

    def _octo_ws_queue_worker(self):
        """
        Child process to -> Octoprint event bus relay
        """
        logger.info("Started _octo_ws_queue_worker")
        while True:
            if self.active:
                viz_bytes = self.octo_ws_queue.get(block=True)
                self.plugin._event_bus.fire(
                    Events.PLUGIN_PRINT_NANNY_PREDICT_DONE,
                    payload={"image": base64.b64encode(viz_bytes)},
                )

    def _get_metadata(self):
        metadata = {
            "printer_data": self.plugin._printer.get_current_data(),
            "printer_profile": self.plugin._printer_profile_manager.get_current_or_default(),
            "temperature": self.plugin._printer.get_current_temperatures(),
            "dt": datetime.now(pytz.timezone("America/Los_Angeles")),
            "plugin_version": self.plugin._plugin_version,
            "octoprint_version": octoprint.util.version.get_octoprint_version_string(),
            "platform": platform.platform(),
            "mac_address": ":".join(re.findall("..", "%012x".format(uuid.getnode()))),
            "api_objects": {
                "printer_profile_id": self.shared.printer_profile_id,
                "print_job_id": self.shared.print_job_id,
            },
            "environment": self._environment,
        }
        return metadata

    async def _handle_print_start(self, event_type, event_data):

        event_data.update(self._get_metadata())

        try:
            printer_profile = (
                await self.plugin.rest_client.update_or_create_printer_profile(
                    event_data
                )
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.plugin.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path
            )

            print_job = await self.plugin.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id
            )

            self.shared.print_job_id = print_job.id

        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        self.start()
