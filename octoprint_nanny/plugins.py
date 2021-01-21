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
import platform
from datetime import datetime

import time
import requests

import multiprocessing
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
import uuid
import numpy as np
import multiprocessing_logging

from octoprint.events import Events, eventManager

import print_nanny_client

from .errors import SnapshotHTTPException, WebcamSettingsHTTPException
from octoprint_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.predictor import ThreadLocalPredictor
from octoprint_nanny.clients.honeycomb import HoneycombTracer
import beeline

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


DEFAULT_API_URL = os.environ.get(
    "OCTOPRINT_NANNY_API_URL", "https://print-nanny.com/api/"
)
DEFAULT_WS_URL = os.environ.get(
    "OCTOPRINT_NANNY_WS_URL", "wss://print-nanny.com/ws/images/"
)
DEFAULT_SNAPSHOT_URL = os.environ.get(
    "OCTOPRINT_NANNY_SNAPSHOT_URL", "http://localhost:8080/?action=snapshot"
)
GCP_ROOT_CERTIFICATE_URL = "https://pki.goog/roots.pem"

Events.PRINT_PROGRESS = "PrintProgress"


class OctoPrintNannyPlugin(
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
    octoprint.plugin.ReloadNeedingPlugin,
):
    def __init__(self, *args, **kwargs):

        # log multiplexing for multiprocessing.Process
        multiprocessing_logging.install_mp_handler()

        # User interactive
        self._calibration = None

        self._log_path = None
        self._environment = {}

        self._worker_manager = WorkerManager(plugin=self)

        self._honeycomb_tracer = HoneycombTracer(
            service_name="octoprint-plugin-main",
        )

    def on_shutdown(self):
        self._worker_manager.shutdown()

    @beeline.traced_thread
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

    def _cpuinfo(self) -> dict:
        """
        Dict from /proc/cpu
        {'processor': '3', 'model name': 'ARMv7 Processor rev 3 (v7l)', 'BogoMIPS': '270.00',
        'Features': 'half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32', 'CPU implementer': '0x41',
        'CPU architecture': '7', 'CPU variant': '0x0', 'CPU part': '0xd08', 'CPU revision': '3', 'Hardware': 'BCM2711',
        'Revision': 'c03111', 'Serial': '100000003fa9a39b', 'Model': 'Raspberry Pi 4 Model B Rev 1.1'}
        """
        return {
            x.split(":")[0].strip(): x.split(":")[1].strip()
            for x in open("/proc/cpuinfo").read().split("\n")
            if len(x.split(":")) > 1
        }

    def _meminfo(self) -> dict:
        """
        Dict from /proc/meminfo

            {'MemTotal': '3867172 kB', 'MemFree': '1241596 kB', 'MemAvailable': '3019808 kB', 'Buffers': '131336 kB', 'Cached': '1641988 kB',
            'SwapCached': '1372 kB', 'Active': '1015728 kB', 'Inactive': '1469520 kB', 'Active(anon)': '564560 kB', 'Inactive(anon)': '65344 kB', '
            Active(file)': '451168 kB', 'Inactive(file)': '1404176 kB', 'Unevictable': '16 kB', 'Mlocked': '16 kB', 'HighTotal': '3211264 kB',
            'HighFree': '841456 kB', 'LowTotal': '655908 kB', 'LowFree': '400140 kB', 'SwapTotal': '102396 kB', 'SwapFree': '91388 kB',
            'Dirty': '20 kB', 'Writeback': '0 kB', 'AnonPages': '710936 kB', 'Mapped': '239040 kB', 'Shmem': '3028 kB', 'KReclaimable': '82948 kB',
            'Slab': '105028 kB', 'SReclaimable': '82948 kB', 'SUnreclaim': '22080 kB', 'KernelStack': '2400 kB', 'PageTables': '8696 kB', 'NFS_Unstable': '0 kB',
            'Bounce': '0 kB', 'WritebackTmp': '0 kB', 'CommitLimit': '2035980 kB', 'Committed_AS': '1755048 kB', 'VmallocTotal': '245760 kB', 'VmallocUsed': '5732 kB',
            'VmallocChunk': '0 kB', 'Percpu': '512 kB', 'CmaTotal': '262144 kB', 'CmaFree': '242404 kB'}
        """
        return {
            x.split(":")[0].strip(): x.split(":")[1].strip()
            for x in open("/proc/meminfo").read().split("\n")
            if len(x.split(":")) > 1
        }

    def _get_device_info(self):
        cpuinfo = self._cpuinfo()

        # @todo warn if neon acceleration is not supported
        cpu_flags = cpuinfo.get("Features", "").split()

        # processors are zero indexed
        cores = int(cpuinfo.get("processor")) + 1
        # covnert kB string like '3867172 kB' to int
        ram = int(self._meminfo().get("MemTotal").split()[0])

        python_version = self._environment.get("python", {}).get("version")
        pip_version = self._environment.get("python", {}).get("pip")
        virtualenv = self._environment.get("python", {}).get("virtualenv")

        return {
            "model": cpuinfo.get("Model"),
            "platform": platform.platform(),
            "cpu_flags": cpu_flags,
            "hardware": cpuinfo.get("Hardware"),
            "revision": cpuinfo.get("Revision"),
            "serial": cpuinfo.get("Serial"),
            "cores": cores,
            "ram": ram,
            "python_version": python_version,
            "pip_version": pip_version,
            "virtualenv": virtualenv,
            "octoprint_version": octoprint.util.version.get_octoprint_version_string(),
            "plugin_version": self._plugin_version,
            "print_nanny_client_version": print_nanny_client.__version__,
        }

    async def _sync_printer_profiles(self, device_id):
        printer_profiles = self._printer_profile_manager.get_all()

        # on sync, cache a local map of octoprint id <-> print nanny id mappings for debugging
        id_map = {"octoprint": {}, "octoprint_nanny": {}}
        for profile_id, profile in printer_profiles.items():
            logger.info("Syncing profile")
            created_profile = await self.rest_client.update_or_create_printer_profile(
                profile, device_id
            )
            id_map["octoprint"][profile_id] = created_profile.id
            id_map["octoprint_nanny"][created_profile.id] = profile_id

        logger.info(f"Synced {len(printer_profiles)}")

        filename = os.path.join(
            self.get_plugin_data_folder(), "printer_profile_id_map.json"
        )
        with io.open(filename, "w+", encoding="utf-8") as f:
            json.dump(id_map, f)
        logger.info(
            f"Wrote id map for {len(printer_profiles)} printer profiles to {filename}"
        )

    @beeline.traced_thread
    async def _register_device(self, device_name):

        # device registration
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_START,
            payload={"msg": "Requesting new identity from provision service"},
        )
        device_info = self._get_device_info()
        try:
            device = await self.rest_client.update_or_create_octoprint_device(
                name=device_name, **device_info
            )
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_DONE,
                payload={
                    "msg": f"Success! Device can now be managed remotely: {device.url}"
                },
            )

        except CLIENT_EXCEPTIONS as e:
            logger.error(e)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={"msg": str(e.body)},
            )
            return e

        logger.info(
            f"Registered octoprint device with hardware serial={device.serial} url={device.url} fingerprint={device.fingerprint} device={device}"
        )

        pubkey_filename = os.path.join(self.get_plugin_data_folder(), "public_key.pem")
        privkey_filename = os.path.join(
            self.get_plugin_data_folder(), "private_key.pem"
        )
        root_ca_filename = os.path.join(
            self.get_plugin_data_folder(), "gcp_root_ca.pem"
        )

        async with aiohttp.ClientSession() as session:
            logger.info(f"Downloading newly-provisioned public key {device.public_key}")
            async with session.get(device.public_key) as res:
                pubkey = await res.text()
            logger.info(
                f"Downloading newly-provisioned private key {device.private_key}"
            )
            async with session.get(device.private_key) as res:
                privkey = await res.text()

            logger.info(f"Downloading GCP root certificates")
            async with session.get(GCP_ROOT_CERTIFICATE_URL) as res:
                root_ca = await res.text()

        with io.open(pubkey_filename, "w+", encoding="utf-8") as f:
            f.write(pubkey)
        with io.open(privkey_filename, "w+", encoding="utf-8") as f:
            f.write(privkey)
        with io.open(root_ca_filename, "w+", encoding="utf-8") as f:
            f.write(root_ca)

        logger.info(
            f"Downloaded key pair {device.fingerprint} to {pubkey_filename} {privkey_filename}"
        )
        self._settings.set(["device_private_key"], privkey_filename)
        self._settings.set(["device_public_key"], pubkey_filename)
        self._settings.set(["gcp_root_ca"], root_ca_filename)

        self._settings.set(["device_serial"], device.serial)
        self._settings.set(["device_url"], device.url)
        self._settings.set(["device_id"], device.id)
        self._settings.set(["device_fingerprint"], device.fingerprint)
        self._settings.set(["device_cloudiot_name"], device.cloudiot_device_name)

        self._settings.set(["device_registered"], True)

        self._settings.save()
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_PRINTER_PROFILE_SYNC_START,
            payload={"msg": "Syncing printer profiles..."},
        )
        try:
            printers = await self._sync_printer_profiles(device.id)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_PRINTER_PROFILE_SYNC_DONE,
                payload={
                    "msg": "Success! Printer profiles synced to https://print-nanny.com/dashboard/printer-profiles"
                },
            )
        except CLIENT_EXCEPTIONS as e:
            logger.error(e)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={"msg": str(e.body)},
            )
            return e

        return printers

    async def _test_snapshot_url(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                return await res.read()

    ##
    ## Octoprint api routes + handlers
    ##
    # def register_custom_routes(self):
    @beeline.traced(name="OctoPrintNannyPlugin.start_predict")
    @octoprint.plugin.BlueprintPlugin.route("/startPredict", methods=["POST"])
    def start_predict(self):
        logger.info("Resetting backoff timer in OctoPrintNanny._worker_manager")
        self._worker_manager.reset_backoff()
        # settings test#
        url = self._settings.get(["snapshot_url"])
        res = requests.get(url)
        res.raise_for_status()
        if res.status_code == 200:
            self._worker_manager.start_monitoring()
            return flask.json.jsonify({"ok": 1})

    @beeline.traced(name="OctoPrintNannyPlugin.stop_predict")
    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        logger.info("Resetting backoff timer in OctoPrintNanny._worker_manager")
        self._worker_manager.reset_backoff()
        self._worker_manager.stop_monitoring()
        return flask.json.jsonify({"ok": 1})

    @beeline.traced(name="OctoPrintNannyPlugin.register_device")
    @octoprint.plugin.BlueprintPlugin.route("/registerDevice", methods=["POST"])
    def register_device(self):
        device_name = flask.request.json.get("device_name")
        logger.info("Resetting backoff timer in OctoPrintNanny._worker_manager")
        self._worker_manager.reset_backoff()
        result = asyncio.run_coroutine_threadsafe(
            self._register_device(device_name), self._worker_manager.loop
        ).result()

        if isinstance(result, Exception):
            raise result
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_WORKER_RESTART_START,
            payload={"msg": "Re-initializing worker threads"},
        )
        self._worker_manager.apply_device_registration()
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_WORKER_RESTART_DONE,
            payload={"msg": "Successfully reinitialized workers"},
        )
        self._settings.save()
        return flask.jsonify(result)

    @beeline.traced(name="OctoPrintNannyPlugin.test_snapshot_url")
    @octoprint.plugin.BlueprintPlugin.route("/testSnapshotUrl", methods=["POST"])
    def test_snapshot_url(self):
        snapshot_url = flask.request.json.get("snapshot_url")

        image = asyncio.run_coroutine_threadsafe(
            self._test_snapshot_url(snapshot_url), self._worker_manager.loop
        ).result()

        return flask.jsonify({"image": base64.b64encode(image)})

    @beeline.traced(name="OctoPrintNannyPlugin.test_auth_token")
    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get("auth_token")
        api_url = flask.request.json.get("api_url")

        logger.info("Resetting backoff timer in OctoPrintNanny._worker_manager")
        self._worker_manager.reset_backoff()

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
            self._settings.set(["user_id"], response.id)

            self._settings.save()

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
        return [
            "predict_done",
            "predict_offline",
            "monitoring_start",
            "monitoring_stop",
            "device_register_start",
            "device_register_done",
            "device_register_failed",
            "printer_profile_sync_start",
            "printer_profile_sync_done",
            "printer_profile_sync_failed",
            "worker_restart_start",
            "worker_restart_done",
        ]

    def on_event(self, event_type, event_data):
        self._worker_manager.telemetry_queue.put_nowait(
            {"event_type": event_type, "event_data": event_data}
        )

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """

        self._log_path = self._settings.get_plugin_logfile_path()

        self._honeycomb_tracer.add_global_context(self._get_device_info())

        self._worker_manager.on_settings_initialized()

        if self._settings.get(["auth_token"]) is not None:
            user = asyncio.run_coroutine_threadsafe(
                self._test_api_auth(
                    auth_token=self._settings.get(["auth_token"]),
                    api_url=self._settings.get(["api_url"]),
                ),
                self._worker_manager.loop,
            ).result()

            if isinstance(user, Exception):
                logger.error(user)
                return
            if user is not None:
                self._settings.set(["user_email"], user.email)
                self._settings.set(["user_url"], user.url)
                self._settings.set(["auth_valid"], True)

            else:
                logger.warning(f"Invalid auth")

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        self._worker_manager.telemetry_queue.put(
            {"event_type": Events.PRINT_PROGRESS, "event_data": {"progress": progress}}
        )

    ## EnvironmentDetectionPlugin

    def on_environment_detected(self, environment, *args, **kwargs):
        self._environment = environment
        self._worker_manager._environment = environment

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            auth_token=None,
            auth_valid=False,
            device_registered=False,
            user_email=None,
            user_id=None,
            user_url=None,
            device_url=None,
            device_fingerprint=None,
            device_cloudiot_name=None,
            device_id=None,
            device_name=platform.node(),
            device_private_key=None,
            device_public_key=None,
            device_serial=None,
            user=None,
            calibrated=False,
            calibrate_x0=None,
            calibrate_y0=None,
            calibrate_x1=None,
            calibrate_y1=None,
            auto_start=False,
            api_url=DEFAULT_API_URL,
            ws_url=DEFAULT_WS_URL,
            snapshot_url=DEFAULT_SNAPSHOT_URL,
            gcp_root_ca=None,
        )

    def on_settings_save(self, data):
        prev_calibration = (
            self._settings.get(["calibrate_x0"]),
            self._settings.get(["calibrate_y0"]),
            self._settings.get(["calibrate_x1"]),
            self._settings.get(["calibrate_y1"]),
        )
        prev_auth_token = self._settings.get(["auth_token"])
        prev_api_url = self._settings.get(["api_token"])
        prev_device_fingerprint = self._settings.get(["device_fingerprint"])
        super().on_settings_save(data)

        new_calibration = (
            self._settings.get(["calibrate_x0"]),
            self._settings.get(["calibrate_y0"]),
            self._settings.get(["calibrate_x1"]),
            self._settings.get(["calibrate_y1"]),
        )
        new_auth_token = self._settings.get(["auth_token"])
        new_api_url = self._settings.get(["api_url"])
        new_device_fingerprint = self._settings.get(["device_fingerprint"])

        if prev_calibration != new_calibration:
            logger.info("Change in calibration detected, applying new settings")
            self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_OFFLINE)
            self._worker_manager.apply_calibration()

        if prev_auth_token != new_auth_token:
            logger.info("Change in auth detected, applying new settings")
            self._worker_manager.apply_auth()

        if prev_device_fingerprint != new_device_fingerprint:
            logger.info(
                "Change in device identity detected (did you re-register?), applying new settings"
            )
            self._worker_manager.apply_device_registration()

    ## Template plugin

    def get_template_vars(self):
        return {
            # @ todo is there a covenience method to get all plugin settings?
            # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=settings%20get#octoprint.plugin.PluginSettings.get
            "settings": {
                key: self._settings.get([key])
                for key in self.get_settings_defaults().keys()
            },
            "active": self._worker_manager.monitoring_active,
        }

    ## Wizard plugin mixin

    def get_wizard_version(self):
        return 0

    def is_wizard_required(self):

        return any(
            [
                self._settings.get(["api_url"]) is None,
                self._settings.get(["auth_token"]) is None,
                self._settings.get(["auth_valid"]) is False,
                self._settings.get(["device_private_key"]) is None,
                self._settings.get(["device_public_key"]) is None,
                self._settings.get(["device_fingerprint"]) is None,
                self._settings.get(["device_id"]) is None,
                self._settings.get(["device_serial"]) is None,
                self._settings.get(["device_registered"]) is False,
                self._settings.get(["device_url"]) is None,
                self._settings.get(["device_cloudiot_name"]) is None,
                self._settings.get(["user_email"]) is None,
                self._settings.get(["user_id"]) is None,
                self._settings.get(["user_url"]) is None,
                self._settings.get(["ws_url"]) is None,
                self._settings.get(["gcp_root_ca"]) is None,
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
            octoprint_nanny=dict(
                displayName="OctoPrint Nanny",
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
