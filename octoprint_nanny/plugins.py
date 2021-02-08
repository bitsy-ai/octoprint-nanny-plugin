import asyncio
import logging
import base64
import concurrent
import glob
import hashlib
import io
import json
import os
import platform
import platform
import queue
import re
import threading
from datetime import datetime

import time
import requests

import beeline
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
import uuid
import numpy as np

from octoprint.events import Events, eventManager
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

import print_nanny_client

from octoprint_nanny.clients.rest import RestAPIClient, API_CLIENT_EXCEPTIONS
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.clients.honeycomb import HoneycombTracer

DEFAULT_API_URL = os.environ.get(
    "OCTOPRINT_NANNY_API_URL", "https://print-nanny.com/api/"
)
DEFAULT_WS_URL = os.environ.get(
    "OCTOPRINT_NANNY_WS_URL", "wss://print-nanny.com/ws/images/"
)
DEFAULT_SNAPSHOT_URL = os.environ.get(
    "OCTOPRINT_NANNY_SNAPSHOT_URL", "http://localhost:8080/?action=snapshot"
)

DEFAULT_MQTT_BRIDGE_PORT = os.environ.get("OCTOPRINT_NANNY_MQTT_BRIDGE_PORT", 8883)
DEFAULT_MQTT_BRIDGE_HOSTNAME = os.environ.get(
    "OCTOPRINT_NANNY_MQTT_HOSTNAME", "mqtt.googleapis.com"
)
DEFAULT_MQTT_ROOT_CERTIFICATE_URL = "https://pki.goog/roots.pem"

DEFAULT_SETTINGS = dict(
    auth_token=None,
    auth_valid=False,
    device_registered=False,
    user_email=None,
    monitoring_frames_per_minute=30,
    monitoring_active=False,
    mqtt_bridge_hostname=DEFAULT_MQTT_BRIDGE_HOSTNAME,
    mqtt_bridge_port=DEFAULT_MQTT_BRIDGE_PORT,
    mqtt_bridge_root_certificate_url=DEFAULT_MQTT_ROOT_CERTIFICATE_URL,
    user_id=None,
    user_url=None,
    device_url=None,
    device_fingerprint=None,
    device_cloudiot_name=None,
    device_cloudiot_id=None,
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
        # User interactive
        self._calibration = None

        self._log_path = None
        self._environment = {}

        self.worker_manager = WorkerManager(plugin=self)
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    def get_setting(self, key):
        return self._settings.get([key])

    @beeline.traced("OctoPrintNannyPlugin._test_api_auth")
    @beeline.traced_thread
    async def _test_api_auth(self, auth_token, api_url):
        rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)
        self._logger.info("Initialized rest_client")
        try:
            user = await rest_client.get_user()
            self._logger.info(f"Authenticated as user id={user.id} url={user.url}")
            return user
        except API_CLIENT_EXCEPTIONS as e:
            self._logger.error(f"_test_api_auth API call failed {e}")
            self._settings.set(["auth_valid"], False)

    @beeline.traced("OctoPrintNannyPlugin._cpuinfo")
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

    @beeline.traced("OctoPrintNannyPlugin._meminfo")
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

    @beeline.traced("OctoPrintNannyPlugin.get_device_info")
    @beeline.traced_thread
    def get_device_info(self):
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

    @beeline.traced("OctoPrintNannyPlugin._sync_printer_profiles")
    @beeline.traced_thread
    async def _sync_printer_profiles(self, device_id):
        printer_profiles = self._printer_profile_manager.get_all()

        # on sync, cache a local map of octoprint id <-> print nanny id mappings for debugging
        id_map = {"octoprint": {}, "octoprint_nanny": {}}
        for profile_id, profile in printer_profiles.items():
            self._logger.info("Syncing profile")
            created_profile = (
                await self.worker_manager.rest_client.update_or_create_printer_profile(
                    profile, device_id
                )
            )
            id_map["octoprint"][profile_id] = created_profile.id
            id_map["octoprint_nanny"][created_profile.id] = profile_id

        self._logger.info(f"Synced {len(printer_profiles)}")

        filename = os.path.join(
            self.get_plugin_data_folder(), "printer_profile_id_map.json"
        )
        with io.open(filename, "w+", encoding="utf-8") as f:
            json.dump(id_map, f)
        self._logger.info(
            f"Wrote id map for {len(printer_profiles)} printer profiles to {filename}"
        )

    @beeline.traced("OctoPrintNannyPlugin._write_keypair")
    @beeline.traced_thread
    async def _write_keypair(self, device):
        pubkey_filename = os.path.join(self.get_plugin_data_folder(), "public_key.pem")
        privkey_filename = os.path.join(
            self.get_plugin_data_folder(), "private_key.pem"
        )

        with io.open(pubkey_filename, "w+", encoding="utf-8") as f:
            f.write(device.public_key)
        with io.open(privkey_filename, "w+", encoding="utf-8") as f:
            f.write(device.private_key)

        self._logger.info(
            f"Saved keypair {device.fingerprint} to {pubkey_filename} {privkey_filename}"
        )

        self._settings.set(["device_private_key"], privkey_filename)
        self._settings.set(["device_public_key"], pubkey_filename)

    @beeline.traced("OctoPrintNannyPlugin._download_root_certificates")
    @beeline.traced_thread
    async def _download_root_certificates(self):
        root_ca_filename = os.path.join(
            self.get_plugin_data_folder(), "gcp_root_ca.pem"
        )

        root_ca_url = self._settings.get(["mqtt_bridge_root_certificate_url"])

        async with aiohttp.ClientSession() as session:
            self._logger.info(f"Downloading GCP root certificates")
            async with session.get(root_ca_url) as res:
                root_ca = await res.text()
        with io.open(root_ca_filename, "w+", encoding="utf-8") as f:
            f.write(root_ca)
        self._settings.set(["gcp_root_ca"], root_ca_filename)

    @beeline.traced("OctoPrintNannyPlugin._register_device")
    @beeline.traced_thread
    async def _register_device(self, device_name):

        self._logger.info(
            f"OctoPrintNanny._register_device called with device_name={device_name}"
        )
        # device registration

        span = self._honeycomb_tracer.start_span(context={"name": "get_device_info"})
        device_info = self.get_device_info()

        self._honeycomb_tracer.add_context(dict(device_info=device_info))
        self._honeycomb_tracer.finish_span(span)

        span = self._honeycomb_tracer.start_span(
            context={"name": "update_or_create_octoprint_device"}
        )
        try:
            device = await self.worker_manager.plugin.settings.rest_client.update_or_create_octoprint_device(
                name=device_name, **device_info
            )
            self._honeycomb_tracer.add_context(dict(device_upserted=device))
            self._honeycomb_tracer.finish_span(span)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_DONE,
                payload={
                    "msg": f"Success! Device can now be managed remotely: {device.url}"
                },
            )

        except API_CLIENT_EXCEPTIONS as e:
            self._logger.error(e)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={"msg": str(e.body)},
            )
            return e

        self._logger.info(
            f"Registered octoprint device with hardware serial={device.serial} url={device.url} fingerprint={device.fingerprint} id={device.id} cloudiot_num_id={device.cloudiot_device_num_id}"
        )

        await self._write_keypair(device)
        await self._download_root_certificates()

        self._settings.set(["device_serial"], device.serial)
        self._settings.set(["device_url"], device.url)
        self._settings.set(["device_id"], device.id)
        self._settings.set(["device_fingerprint"], device.fingerprint)
        self._settings.set(["device_cloudiot_name"], device.cloudiot_device_name)
        self._settings.set(["device_cloudiot_id"], device.cloudiot_device_num_id)
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
        except API_CLIENT_EXCEPTIONS as e:
            self._logger.error(e)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={"msg": str(e.body)},
            )
            return e

        return printers

    @beeline.traced("OctoPrintNannyPlugin._test_snapshot_url")
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
        # settings test#
        url = self._settings.get(["snapshot_url"])
        res = requests.get(url)
        res.raise_for_status()
        if res.status_code == 200:
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE,
                payload={"image": base64.b64encode(res.content)},
            )
            self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START)
            return flask.json.jsonify({"ok": 1})

    @beeline.traced(name="OctoPrintNannyPlugin.stop_predict")
    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP)
        return flask.json.jsonify({"ok": 1})

    @beeline.traced(name="OctoPrintNannyPlugin.register_device")
    @octoprint.plugin.BlueprintPlugin.route("/registerDevice", methods=["POST"])
    def register_device(self):
        device_name = flask.request.json.get("device_name")

        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_START,
            payload={"msg": "Requesting new identity from provision service"},
        )

        future = asyncio.run_coroutine_threadsafe(
            self._register_device(device_name), self.worker_manager.loop
        )
        result = future.result()
        if isinstance(result, Exception):
            raise result
        self._settings.save()
        self.worker_manager.apply_device_registration()
        return flask.jsonify(result)

    @beeline.traced(name="OctoPrintNannyPlugin.test_snapshot_url")
    @octoprint.plugin.BlueprintPlugin.route("/testSnapshotUrl", methods=["POST"])
    def test_snapshot_url(self):
        snapshot_url = flask.request.json.get("snapshot_url")

        image = asyncio.run_coroutine_threadsafe(
            self._test_snapshot_url(snapshot_url), self.worker_manager.loop
        ).result()

        return flask.jsonify({"image": base64.b64encode(image)})

    @beeline.traced(name="OctoPrintNannyPlugin.test_auth_token")
    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get("auth_token")
        api_url = flask.request.json.get("api_url")

        self._logger.info("Testing auth_token in event loop")

        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth(auth_token, api_url), self.worker_manager.loop
        )
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
            self._logger.error(e)
            return (
                flask.json.jsonify(
                    {"msg": "Error communicating with Print Nanny API", "error": e}
                ),
                500,
            )

    def register_custom_events(self):
        return [
            "predict_done",
            "monitoring_start",
            "monitoring_stop",
            "snapshot",
            "device_register_start",
            "device_register_done",
            "device_register_failed",
            "printer_profile_sync_start",
            "printer_profile_sync_done",
            "printer_profile_sync_failed",
            "worker_stop",
            "worker_start",
        ]

    @beeline.traced(name="OctoPrintNannyPlugin.on_after_startup")
    def on_shutdown(self):
        self._logger.info("Processing shutdown event")
        self.worker_manager.shutdown()

    @beeline.traced(name="OctoPrintNannyPlugin.on_after_startup")
    def on_after_startup(self):
        file_logging_handler = CleaningTimedRotatingFileHandler(
            self._settings.get_plugin_logfile_path(),
            when="D",
            backupCount=7,
        )
        file_logging_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        self._logger.addHandler(file_logging_handler)

    def on_event(self, event_type, event_data):
        # shutdown event is handled in .on_shutdown
        if event_type == Events.SHUTDOWN:
            return
        self.worker_manager.mqtt_send_queue.put_nowait(
            {"event_type": event_type, "event_data": event_data}
        )

    @beeline.traced(name="OctoPrintNannyPlugin.on_settings_initialized")
    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """
        self._honeycomb_tracer.add_global_context(self.get_device_info())
        self._log_path = self._settings.get_plugin_logfile_path()
        self.worker_manager.on_settings_initialized()

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        self.worker_manager.mqtt_send_queue.put_nowait(
            {"event_type": Events.PRINT_PROGRESS, "event_data": {"progress": progress}}
        )

    ## EnvironmentDetectionPlugin
    @beeline.traced(name="OctoPrintNannyPlugin.on_environment_detected")
    def on_environment_detected(self, environment, *args, **kwargs):
        self._environment = environment
        self.worker_manager.plugin.settings.on_environment_detected(environment)

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return DEFAULT_SETTINGS

    @beeline.traced(name="OctoPrintNannyPlugin.on_settings_save")
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
        prev_monitoring_fpm = self._settings.get(["monitoring_frames_per_minute"])

        prev_mqtt_bridge_hostname = self._settings.get(["mqtt_bridge_hostname"])
        prev_mqtt_bridge_port = self._settings.get(["mqtt_bridge_port"])
        prev_mqtt_bridge_certificate_url = self._settings.get(
            ["mqtt_bridge_certificate_url"]
        )

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
        new_monitoring_fpm = self._settings.get(["monitoring_frames_per_minute"])

        new_mqtt_bridge_hostname = self._settings.get(["mqtt_bridge_hostname"])
        new_mqtt_bridge_port = self._settings.get(["mqtt_bridge_port"])
        new_mqtt_bridge_certificate_url = self._settings.get(
            ["mqtt_bridge_certificate_url"]
        )

        if prev_mqtt_bridge_certificate_url != new_mqtt_bridge_certificate_url:
            asyncio.run_coroutine_threadsafe(
                self._download_root_certificates(), self.worker_manager.loop
            )
        if (
            prev_monitoring_fpm != new_monitoring_fpm
            or prev_calibration != new_calibration
        ):
            self._logger.info(
                "Change in frames per minute or calibration detected, applying new settings"
            )
            self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_OFFLINE)
            self.worker_manager.apply_monitoring_settings()

        if prev_auth_token != new_auth_token:
            self._logger.info("Change in auth detected, applying new settings")
            self.worker_manager.apply_auth()

        if (
            prev_device_fingerprint != new_device_fingerprint
            or prev_mqtt_bridge_hostname != new_mqtt_bridge_hostname
            or prev_mqtt_bridge_port != new_mqtt_bridge_port
            or prev_mqtt_bridge_certificate_url != new_mqtt_bridge_certificate_url
        ):
            self._logger.info(
                "Change in device identity detected (did you re-register?), applying new settings"
            )
            self.worker_manager.apply_device_registration()

    ## Template plugin

    def get_template_vars(self):
        return {
            # @ todo is there a covenience method to get all plugin settings?
            # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=settings%20get#octoprint.plugin.PluginSettings.get
            "settings": {
                key: self._settings.get([key])
                for key in self.get_settings_defaults().keys()
            },
            "active": self.worker_manager.monitoring_active,
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
                self._settings.get(["device_cloudiot_id"]) is None,
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
    @beeline.traced(name="OctoPrintNannyPlugin.get_update_information")
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            octoprint_nanny=dict(
                displayName=self._plugin_name,
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
