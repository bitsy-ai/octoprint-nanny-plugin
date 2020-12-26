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
from print_nanny.predictor import ThreadLocalPredictor

logger = logging.getLogger("octoprint.plugins.print_nanny")


DEFAULT_API_URL = os.environ.get("PRINT_NANNY_API_URL", "https://print-nanny.com/api/")
DEFAULT_WS_URL = os.environ.get(
    "PRINT_NANNY_WS_URL", "wss://print-nanny.com/ws/predict/"
)


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
    def __init__(self, *args, **kwargs):

        # log multiplexing for multiprocessing.Process
        multiprocessing_logging.install_mp_handler()

        # User interactive
        self._calibration = None

        self._log_path = None
        self._environment = {}

        self._worker_manager = WorkerManager(plugin=self)

    # def on_shutdown(self):
    #     self._worker_manager.shutdown()

    async def _test_api_auth(self, auth_token, api_url):
        rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)
        logger.info("Initialized rest_client")
        try:
            user = await rest_client.get_user()
            logger.info(f"Authenticated as user {user}")
            self.rest_client = rest_client
            return user
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_test_api_auth API call failed")
            self._settings.set(["auth_valid"], False)
            return e

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

        if res.status_code == 200:
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

        logger.info("Testing auth_token in event")
        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth(auth_token, api_url), self._worker_manager.loop
        )
        logger.info(f"Created run_coroutine")
        response = response.result()

        if isinstance(response, print_nanny_client.models.user.User):
            self._settings.set(["auth_token"], auth_token)
            self._settings.set(["auth_valid"], True)
            self._settings.set(["api_url"], api_url)
            self._settings.set(["user_email"], response.email)
            self._settings.set(["user_url"], response.url)

            self._settings.save()

            logger.info(f"Authenticated as {response}")
            return flask.json.jsonify(response.to_dict())
        elif isinstance(response, Exception):
            e = str(response)
            logger.error(e)
            return (
                flask.json.jsonify(
                    {"msg": "Error communicating with Print Nanny API", "error": e}
                ),
                500,
            )

    def register_custom_events(self):
        return ["predict_done"]

    def on_event(self, event_type, event_data):
        self._worker_manager.tracking_queue.put_nowait(
            {"event_type": event_type, "event_data": event_data}
        )

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """

        self._log_path = self._settings.get_plugin_logfile_path()
        self._worker_manager.on_settings_initialized()

        if self._settings.get(["auth_token"]) is not None:
            user = asyncio.run_coroutine_threadsafe(
                self._test_api_auth(
                    auth_token=self._settings.get(["auth_token"]),
                    api_url=self._settings.get(["api_url"]),
                ),
                self._worker_manager.loop,
            ).result()

            if user is not None:
                logger.info(f"Authenticated as {user}")
                self._settings.set(["user_email"], user.email)
                self._settings.set(["user_url"], user.url)
                self._settings.set(["auth_valid"], True)

            else:
                logger.warning(f"Invalid auth")

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        self._worker_manager.tracking_queue.put(
            {"event_type": self.PRINT_PROGRESS, "event_data": {"progress": progress}}
        )

    ## EnvironmentDetectionPlugin

    def on_environment_detected(self, environment, *args, **kwargs):
        self._worker_manager._environment = environment

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
            calibrate_h=None,
            calibrate_w=None,
            auto_start=False,
            api_url=DEFAULT_API_URL,
            ws_url=DEFAULT_WS_URL,
        )

    def on_settings_save(self, data):

        prev_calibration = (
            self._settings.get(["calibrate_x0"]),
            self._settings.get(["calibrate_y0"]),
            self._settings.get(["calibrate_x1"]),
            self._settings.get(["calibrate_y1"]),
            self._settings.get(["calibrate_h"]),
            self._settings.get(["calibrate_w"]),
        )
        prev_auth_token = self._settings.get(["auth_token"])
        prev_api_url = self._settings.get(["api_token"])
        super().on_settings_save(data)

        new_calibration = (
            self._settings.get(["calibrate_x0"]),
            self._settings.get(["calibrate_y0"]),
            self._settings.get(["calibrate_x1"]),
            self._settings.get(["calibrate_y1"]),
            self._settings.get(["calibrate_h"]),
            self._settings.get(["calibrate_w"]),
        )
        new_auth_token = self._settings.get(["auth_token"])
        new_api_url = self._settings.get(["api_url"])

        if prev_calibration != new_calibration:

            calibration = ThreadLocalPredictor.get_calibration(
                self._settings.get(["calibrate_x0"]),
                self._settings.get(["calibrate_y0"]),
                self._settings.get(["calibrate_x1"]),
                self._settings.get(["calibrate_y1"]),
                self._settings.get(["calibrate_h"]),
                self._settings.get(["calibrate_w"]),
            )
            self._worker_manager.shared.calibration = calibration

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
