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
import multiprocessing_logging

import print_nanny_client

from .errors import SnapshotHTTPException, WebcamSettingsHTTPException
from print_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from print_nanny.manager import WorkerManager

logger = logging.getLogger("octoprint.plugins.print_nanny")
multiprocessing_logging.install_mp_handler()


DEFAULT_API_URL = os.environ.get("PRINT_NANNY_API_URL", "https://print-nanny.com/api")
DEFAULT_WS_URL = os.environ.get("PRINT_NANNY_WS_URL", "ws://print-nanny.com/ws/predict/")


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

    PRINT_PROGRESS = "print_progress"

    def __init__(self, *args, **kwargs):

        # log multiplexing for multiprocessing.Process

        # wraps auto-generated swagger api
        self.rest_client = RestAPIClient()

        # User interactive
        self._tracking_events = None
        self._calibration = None

        self._log_path = None
        self._environment = {}

        self._worker_manager = WorkerManager(plugin=self)

    # def on_shutdown(self):
    #     self._worker_manager.shutdown()

    async def _test_api_auth(self, auth_token, api_url):
        rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)
        try:
            user = await rest_client.get_user()
            self.rest_client = rest_client
            return user
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_test_api_auth API call failed {e}", exc_info=True)
            return

    async def _get_tracking_events(self):
        """
        @todo make tracking events opt-in
        https://github.com/bitsy-ai/octoprint-nanny-plugin/issues/10
        """
        if not self._tracking_events:
            self._tracking_events = self.rest_client.get_tracking_events()
        return self._tracking_events

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

        self._worker_manager.start()

        return flask.json.jsonify({"ok": 1})

    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        self._worker_manager.stop()
        return flask.json.jsonify({"ok": 1})

    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get("auth_token")
        api_url = flask.request.json.get("api_url")

        
        loop = asyncio.get_running_loop()
        logger.info('Testing auth_token in event')
        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth(auth_token, api_url), loop
        ).result(3)

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
        return ["predict_done"]

    def on_event(self, event_type, event_data):
        if self._tracking_events is None or event_type in self._tracking_events:
            self._worker_manager.tracking_queue.put_nowait(
                {"event_type": event_type, "event_data": event_data}
            )

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """

        self._log_path = self._settings.get_plugin_logfile_path()
        if self._settings.get(["auth_token"]) is not None:
            loop = asyncio.get_event_loop()
            user = asyncio.run_coroutine_threadsafe(
                self._test_api_auth(
                    auth_token=self._settings.get(["auth_token"]),
                    api_url=self._settings.get(["api_url"]),
                ),
                loop,
            ).result()

            if user is not None:
                logger.info(f"Authenticated as {user}")
                self._settings.set(["user_email"], user.email)
                self._settings.set(["user_url"], user.url)
            else:
                logger.warning(f"Invalid auth")

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        self._worker_manager.tracking_queue.put(
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
