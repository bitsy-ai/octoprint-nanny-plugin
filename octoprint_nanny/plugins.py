import asyncio
import aiofiles
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
from enum import Enum
from pathlib import Path

import time
import requests

from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


def configure_logger(logger):
    file_logging_handler = CleaningTimedRotatingFileHandler(
        os.path.expanduser("~/.octoprint/logs/plugin_octoprint_nanny.log"),
        when="D",
        backupCount=7,
    )
    file_logging_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s"
        )
    )
    file_logging_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_logging_handler)


configure_logger(logger)

import beeline
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
import uuid
import numpy as np

from octoprint.events import Events, eventManager

import print_nanny_client

import octoprint_nanny.exceptions
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
    "OCTOPRINT_NANNY_MQTT_HOSTNAME", "mqtt.2030.ltsapis.goog"
)
DEFAULT_MQTT_ROOT_CERTIFICATE_URL = "https://pki.goog/gtsltsr/gtsltsr.crt"
BACKUP_MQTT_ROOT_CERTIFICATE_URL = "https://pki.goog/gsr4/GSR4.crt"


class MonitoringModes(Enum):
    ACTIVE_LEARNING = "active_learning"
    LITE = "lite"


DEFAULT_SETTINGS = dict(
    auth_token=None,
    auth_valid=False,
    device_registered=False,
    user_email=None,
    monitoring_frames_per_minute=30,
    monitoring_active=False,
    mqtt_bridge_hostname=DEFAULT_MQTT_BRIDGE_HOSTNAME,
    mqtt_bridge_port=DEFAULT_MQTT_BRIDGE_PORT,
    mqtt_bridge_primary_root_certificate_url=DEFAULT_MQTT_ROOT_CERTIFICATE_URL,
    mqtt_bridge_backup_root_certificate_url=BACKUP_MQTT_ROOT_CERTIFICATE_URL,
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
    api_url=DEFAULT_API_URL,
    ws_url=DEFAULT_WS_URL,
    snapshot_url=DEFAULT_SNAPSHOT_URL,
    ca_cert=None,
    auto_start=True,
    share_camera=True,
    monitoring_mode=MonitoringModes.ACTIVE_LEARNING.value,
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
        logger.info("Initialized rest_client")
        try:
            user = await rest_client.get_user()
            logger.info(f"Authenticated as user id={user.id} url={user.url}")
            return user
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"_test_api_auth API call failed {e}")
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
            logger.info("Syncing profile")
            created_profile = await self.worker_manager.plugin.settings.rest_client.update_or_create_printer_profile(
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

    @beeline.traced("OctoPrintNannyPlugin._write_keypair")
    @beeline.traced_thread
    async def _write_keypair(self, device):
        pubkey_filename = os.path.join(self.get_plugin_data_folder(), "public_key.pem")
        privkey_filename = os.path.join(
            self.get_plugin_data_folder(), "private_key.pem"
        )

        async with aiofiles.open(pubkey_filename, "w+") as f:
            await f.write(device.public_key)

        async with aiofiles.open(pubkey_filename, "rb") as f:
            content = await f.read()
            if hashlib.sha256(content).hexdigest() != device.public_key_checksum:
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {pubkey_filename} did not match the expected checksum value. Please try again!"
                )

        async with aiofiles.open(privkey_filename, "w+") as f:
            await f.write(device.private_key)
        async with aiofiles.open(privkey_filename, "rb") as f:
            content = await f.read()
            if hashlib.sha256(content).hexdigest() != device.private_key_checksum:
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {privkey_filename} did not match the expected checksum value. Please try again!"
                )

        logger.info(
            f"Saved keypair {device.fingerprint} to {pubkey_filename} {privkey_filename}"
        )

        self._settings.set(["device_private_key"], privkey_filename)
        self._settings.set(["device_public_key"], pubkey_filename)

    @beeline.traced("OctoPrintNannyPlugin._download_root_certificates")
    @beeline.traced_thread
    async def _download_root_certificates(self):

        ca_path = os.path.join(
            self.get_plugin_data_folder(),
            "cacerts",
        )
        Path(ca_path).mkdir(parents=True, exist_ok=True)

        primary_root_ca_filename = os.path.join(ca_path, "primary_root_ca.crt")

        backup_root_ca_filename = os.path.join(ca_path, "backup_root_ca.crt")

        primary_ca_url = self._settings.get(
            ["mqtt_bridge_primary_root_certificate_url"]
        )
        backup_ca_url = self._settings.get(["mqtt_bridge_backup_root_certificate_url"])

        async with aiohttp.ClientSession() as session:
            logger.info(f"Downloading GCP root certificates")
            async with session.get(primary_ca_url) as res:
                root_ca = await res.read()
                logger.info(
                    f"Finished downloading primary root CA from {primary_ca_url}"
                )
            async with session.get(backup_ca_url) as res:
                backup_ca = await res.read()
                logger.info(f"Finished downloading backup root CA from {backup_ca_url}")

        async with aiofiles.open(primary_root_ca_filename, "wb+") as f:
            await f.write(root_ca)
        async with aiofiles.open(backup_root_ca_filename, "wb+") as f:
            await f.write(backup_ca)

        self._settings.set(["ca_cert"], primary_root_ca_filename)
        self._settings.set(["backup_ca_cert"], backup_root_ca_filename)

    @beeline.traced("OctoPrintNannyPlugin._write_ca_certs")
    @beeline.traced_thread
    async def _write_ca_certs(self, device):

        ca_path = os.path.join(
            self.get_plugin_data_folder(),
            "cacerts",
        )
        Path(ca_path).mkdir(parents=True, exist_ok=True)

        primary_ca_filename = os.path.join(ca_path, "primary_ca.pem")

        backup_ca_filename = os.path.join(ca_path, "backup_ca.pem")

        async with aiofiles.open(primary_ca_filename, "w+") as f:
            await f.write(device.ca_certs["primary"])

        async with aiofiles.open(primary_ca_filename, "rb") as f:
            content = await f.read()

            if (
                hashlib.sha256(content).hexdigest()
                != device.ca_certs["primary_checksum"]
            ):
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {primary_ca_filename} did not match the expected checksum value. Please try again!"
                )

        async with aiofiles.open(backup_ca_filename, "w+") as f:
            await f.write(device.ca_certs["backup"])

        async with aiofiles.open(backup_ca_filename, "rb") as f:
            content = await f.read()
            if (
                hashlib.sha256(content).hexdigest()
                != device.ca_certs["backup_checksum"]
            ):
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {backup_ca_filename} did not match the expected checksum value. Please try again!"
                )

        self._settings.set(["ca_cert"], primary_ca_filename)
        self._settings.set(["backup_ca_cert"], backup_ca_filename)

    @beeline.traced("OctoPrintNannyPlugin._register_device")
    @beeline.traced_thread
    async def _register_device(self, device_name):

        logger.info(
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
            logger.error(e)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={"msg": str(e.body)},
            )
            return e

        logger.info(
            f"Registered octoprint device with hardware serial={device.serial} url={device.url} fingerprint={device.fingerprint} id={device.id} cloudiot_num_id={device.cloudiot_device_num_id}"
        )

        await self._write_keypair(device)
        await self._write_ca_certs(device)
        # await self._download_root_certificates()

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
            logger.error(e)
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
            self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_RC_MONITORING_START)
            return flask.json.jsonify({"ok": 1})

    @beeline.traced(name="OctoPrintNannyPlugin.stop_predict")
    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_RC_MONITORING_STOP)
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

        logger.info("Testing auth_token in event loop")

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
            logger.error(e)
            return (
                flask.json.jsonify(
                    {"msg": "Error communicating with Print Nanny API", "error": e}
                ),
                500,
            )

    def register_custom_events(self):
        return [
            # events from octoprint plugin
            "predict_done",
            "device_register_start",
            "device_register_done",
            "device_register_failed",
            "printer_profile_sync_start",
            "printer_profile_sync_done",
            "printer_profile_sync_failed",
            # events from RemoteControlCommand.CommandChoices (webapp)
            "rc_print_start",
            "rc_print_stop",
            "rc_print_pause",
            "rc_print_resume",
            "rc_snapshot",
            "rc_move_nozzle",
            "rc_monitoring_start",
            "rc_monitoring_stop",
        ]

    @beeline.traced(name="OctoPrintNannyPlugin.on_after_startup")
    def on_shutdown(self):
        logger.info("Processing shutdown event")
        asyncio.run_coroutine_threadsafe(
            self.worker_manager.shutdown(), self.worker_manager.loop
        ).result()

    def on_startup(self, *args, **kwargs):
        logger.info("OctoPrint Nanny starting up")

    def on_after_startup(self, *args, **kwargs):
        logger.info("OctoPrint Nanny startup complete")

    def on_event(self, event_type, event_data):
        # shutdown event is handled in .on_shutdown
        if event_type == Events.SHUTDOWN:
            return
        logger.debug(f"Putting event_type={event_type} into mqtt_send_queue")
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
        super().on_settings_save(data)

        # self.worker_manager.apply_auth()
        # self.worker_manager.apply_device_registration()
        self.worker_manager.on_settings_save()

        # prev_calibration = (
        #     self._settings.get(["calibrate_x0"]),
        #     self._settings.get(["calibrate_y0"]),
        #     self._settings.get(["calibrate_x1"]),
        #     self._settings.get(["calibrate_y1"]),
        # )
        # prev_auth_token = self._settings.get(["auth_token"])
        # prev_api_url = self._settings.get(["api_token"])
        # prev_device_fingerprint = self._settings.get(["device_fingerprint"])
        # prev_monitoring_fpm = self._settings.get(["monitoring_frames_per_minute"])

        # prev_mqtt_bridge_hostname = self._settings.get(["mqtt_bridge_hostname"])
        # prev_mqtt_bridge_port = self._settings.get(["mqtt_bridge_port"])
        # prev_mqtt_bridge_certificate_url = self._settings.get(
        #     ["mqtt_bridge_certificate_url"]
        # )

        # prev_share_camera = self._settings.get(["share_camera"])
        # prev_monitoring_mode = self._settings.get(["monitoring_mode"])
        # prev_auto_start = self._settings.get(["auto_start"])

        # super().on_settings_save(data)

        # new_share_camera = self._settings.get(["share_camera"])
        # new_monitoring_mode = self._settings.get(["monitoring_mode"])
        # new_auto_start = self._settings.get(["auto_start"])

        # new_calibration = (
        #     self._settings.get(["calibrate_x0"]),
        #     self._settings.get(["calibrate_y0"]),
        #     self._settings.get(["calibrate_x1"]),
        #     self._settings.get(["calibrate_y1"]),
        # )
        # new_auth_token = self._settings.get(["auth_token"])
        # new_api_url = self._settings.get(["api_url"])
        # new_device_fingerprint = self._settings.get(["device_fingerprint"])
        # new_monitoring_fpm = self._settings.get(["monitoring_frames_per_minute"])

        # new_mqtt_bridge_hostname = self._settings.get(["mqtt_bridge_hostname"])
        # new_mqtt_bridge_port = self._settings.get(["mqtt_bridge_port"])
        # new_mqtt_bridge_certificate_url = self._settings.get(
        #     ["mqtt_bridge_certificate_url"]
        # )

        # if prev_auth_token != new_auth_token:
        #     logger.info("Change in auth detected, applying new settings")
        #     self.worker_manager.apply_auth()

        # if (
        #     prev_device_fingerprint != new_device_fingerprint
        #     or prev_mqtt_bridge_hostname != new_mqtt_bridge_hostname
        #     or prev_mqtt_bridge_port != new_mqtt_bridge_port
        #     or prev_mqtt_bridge_certificate_url != new_mqtt_bridge_certificate_url
        # ):
        #     logger.info(
        #         "Change in device identity detected (did you re-register?), applying new settings"
        #     )
        #     self.worker_manager.apply_device_registration()

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
                self._settings.get(["ca_cert"]) is None,
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
