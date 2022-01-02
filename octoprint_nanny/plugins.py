import asyncio
import logging
import base64
import hashlib
import io
import json
import os
import platform
import uuid
import socket
import requests
import beeline
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
import pytz
from typing import Dict

from pathlib import Path
from datetime import datetime
from octoprint.events import Events

import print_nanny_client  # alpha client
import printnanny_api_client  # beta client
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

import octoprint_nanny.exceptions
from octoprint_nanny.clients.rest import RestAPIClient, API_CLIENT_EXCEPTIONS
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.types import MonitoringModes
from octoprint_nanny.workers.mqtt import build_telemetry_event

from printnanny_api_client import OctoPrintNannyEvent, OctoTelemetryEvent

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


def configure_logger(logger, logfile_path):

    file_logging_handler = CleaningTimedRotatingFileHandler(
        logfile_path,
        when="D",
        backupCount=7,
    )
    file_logging_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(module)s - %(thread)d - %(levelname)s - %(message)s"
        )
    )
    file_logging_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_logging_handler)

    logger.info(f"Logger file handler added {file_logging_handler}")


DEFAULT_API_URL = os.environ.get(
    "OCTOPRINT_NANNY_API_URL", "https://print-nanny.com/api/"
)
DEFAULT_WS_URL = os.environ.get("OCTOPRINT_NANNY_WS_URL", "wss://print-nanny.com/ws/")
DEFAULT_SNAPSHOT_URL = os.environ.get(
    "OCTOPRINT_NANNY_SNAPSHOT_URL", "http://localhost:8080/?action=snapshot"
)

DEFAULT_MQTT_BRIDGE_PORT = os.environ.get("OCTOPRINT_NANNY_MQTT_BRIDGE_PORT", 443)
DEFAULT_MQTT_BRIDGE_HOSTNAME = os.environ.get(
    "OCTOPRINT_NANNY_MQTT_HOSTNAME", "mqtt.2030.ltsapis.goog"
)
DEFAULT_MQTT_ROOT_CERTIFICATE_URL = "https://pki.google.com/roots.pem"
BACKUP_MQTT_ROOT_CERTIFICATE_URL = "https://pki.goog/gsr4/GSR4.crt"

DEFAULT_SETTINGS = dict(
    auth_token=None,
    auth_valid=False,
    device_registered=False,
    user_email=None,
    min_score_thresh=0.50,
    monitoring_frames_per_minute=60,
    mqtt_bridge_hostname=DEFAULT_MQTT_BRIDGE_HOSTNAME,
    mqtt_bridge_port=DEFAULT_MQTT_BRIDGE_PORT,
    mqtt_bridge_primary_root_certificate_url=DEFAULT_MQTT_ROOT_CERTIFICATE_URL,
    mqtt_bridge_backup_root_certificate_url=BACKUP_MQTT_ROOT_CERTIFICATE_URL,
    user_id=None,
    device_manage_url=None,
    device_fingerprint=None,
    device_cloudiot_name=None,
    cloudiot_device_id=None,
    octoprint_device_id=None,
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
    webcam_upload=True,
    monitoring_mode=MonitoringModes.ACTIVE_LEARNING.value,
    monitoring_active=False,
    webcam_to_octoprint_ws=True,
    webcam_to_mqtt=True,
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
    octoprint.plugin.RestartNeedingPlugin,
):

    octoprint_event_prefix = "plugin_octoprint_nanny_"
    plugin_identifier = "octoprint_nanny"
    VERBOSE_EVENTS = [Events.Z_CHANGE, "plugin_octoprint_nanny_monitoring_frame_b64"]

    def __init__(self, *args, **kwargs):
        # User interactive
        self._calibration = None

        self._log_path = None
        self._octoprint_environment = {}

        self.monitoring_active = False
        self.worker_manager = WorkerManager(plugin=self)

    def get_setting(self, key):
        return self._settings.get([key])

    def set_setting(self, key, value):
        return self._settings.set([key], value)

    @beeline.traced("OctoPrintNannyPlugin._test_mqtt_async")
    async def _test_mqtt_async(self):
        try:
            mqtt_client = self.settings.mqtt_client
        except PluginSettingsRequired as e:
            logger.error(f"Initializing mqtt_client failed with error {e}")
            return self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING_FAILED,
                payload=dict(error="Missing device registration"),
            )
        try:
            event = {
                "event_type": Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING,
            }
            payload = build_telemetry_event(event, self).to_dict()
            mqtt_client.publish_octoprint_event(payload)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING_SUCCESS,
                payload=payload,
            )
        except Exception as e:
            logger.error(
                f"Publishing plugin_octoprint_nanny_connect_test_mqtt_ping event failed with error {e}"
            )
            return self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING_FAILED,
                payload=dict(error=str(e)),
            )

    @beeline.traced("OctoPrintNannyPlugin._test_api_auth_async")
    async def _test_api_auth_async(self, auth_token, api_url):
        rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)
        logger.info("Initialized rest_client")
        try:
            user = await rest_client.get_user()
            logger.info(f"Authenticated as PrintNanny user id={user.id}")
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API_SUCCESS,
            )
            return user
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"_test_api_auth API call failed with error{e}")
            self._settings.set(["auth_valid"], False)
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API_FAILED,
                payload=dict(error=str(e)),
            )
            raise e
        except asyncio.TimeoutError as e:
            logger.error(f"Connection to Print Nanny REST API timed out")
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API_FAILED,
                payload=dict(error="Connection timed out"),
            )
            raise e

    def _test_api_auth(self, auth_token: str, api_url: str):
        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth_async(auth_token, api_url), self.worker_manager.loop
        )
        if response.exception():
            return response.exception()
        else:
            return response.result()

    @beeline.traced("OctoPrintNannyPlugin._cpuinfo")
    def _cpuinfo(self) -> dict:
        """
        Dict from /proc/cpu
        Keys lowercased for portability
        {'processor': '3', 'model name': 'ARMv7 Processor rev 3 (v7l)', 'BogoMIPS': '270.00',
        'Features': 'half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32', 'CPU implementer': '0x41',
        'CPU architecture': '7', 'CPU variant': '0x0', 'CPU part': '0xd08', 'CPU revision': '3', 'Hardware': 'BCM2711',
        'Revision': 'c03111', 'Serial': '100000003fa9a39b', 'Model': 'Raspberry Pi 4 Model B Rev 1.1'}
        """
        cpuinfo = {
            x.split(":")[0].strip().lower(): x.split(":")[1].strip().lower()
            for x in open("/proc/cpuinfo").read().split("\n")
            if len(x.split(":")) > 1
        }
        logger.info(f"/proc/cpuinfo:\n {cpuinfo}")
        return cpuinfo

    @beeline.traced("OctoPrintNannyPlugin._meminfo")
    def _meminfo(self) -> dict:
        """
        Dict from /proc/meminfo
        Keys lowercased for portability

            {'MemTotal': '3867172 kB', 'MemFree': '1241596 kB', 'MemAvailable': '3019808 kB', 'Buffers': '131336 kB', 'Cached': '1641988 kB',
            'SwapCached': '1372 kB', 'Active': '1015728 kB', 'Inactive': '1469520 kB', 'Active(anon)': '564560 kB', 'Inactive(anon)': '65344 kB', '
            Active(file)': '451168 kB', 'Inactive(file)': '1404176 kB', 'Unevictable': '16 kB', 'Mlocked': '16 kB', 'HighTotal': '3211264 kB',
            'HighFree': '841456 kB', 'LowTotal': '655908 kB', 'LowFree': '400140 kB', 'SwapTotal': '102396 kB', 'SwapFree': '91388 kB',
            'Dirty': '20 kB', 'Writeback': '0 kB', 'AnonPages': '710936 kB', 'Mapped': '239040 kB', 'Shmem': '3028 kB', 'KReclaimable': '82948 kB',
            'Slab': '105028 kB', 'SReclaimable': '82948 kB', 'SUnreclaim': '22080 kB', 'KernelStack': '2400 kB', 'PageTables': '8696 kB', 'NFS_Unstable': '0 kB',
            'Bounce': '0 kB', 'WritebackTmp': '0 kB', 'CommitLimit': '2035980 kB', 'Committed_AS': '1755048 kB', 'VmallocTotal': '245760 kB', 'VmallocUsed': '5732 kB',
            'VmallocChunk': '0 kB', 'Percpu': '512 kB', 'CmaTotal': '262144 kB', 'CmaFree': '242404 kB'}
        """
        meminfo = {
            x.split(":")[0].strip().lower(): x.split(":")[1].strip().lower()
            for x in open("/proc/meminfo").read().split("\n")
            if len(x.split(":")) > 1
        }
        logger.info(f"/proc/meminfo:\n {meminfo}")
        return meminfo

    @beeline.traced("OctoPrintNannyPlugin.get_device_info")
    def get_device_info(self):
        cpuinfo = self._cpuinfo()

        # @todo warn if neon acceleration is not supported
        cpu_flags = cpuinfo.get("features")
        if isinstance(cpu_flags, str):
            cpu_flags = cpu_flags.split()

        # processors are zero indexed
        cores = int(cpuinfo.get("processor")) + 1
        # covnert kB string like '3867172 kB' to int
        ram = int(self._meminfo().get("memtotal").split()[0])

        logger.info(f"Runtime environment:\n {self._octoprint_environment}")
        python_version = self._octoprint_environment.get("python", {}).get("version")
        pip_version = self._octoprint_environment.get("python", {}).get("pip")
        virtualenv = self._octoprint_environment.get("python", {}).get("virtualenv")

        return {
            "model": cpuinfo.get("model"),
            "platform": platform.platform(),
            "cpu_flags": cpu_flags,
            "hardware": cpuinfo.get("hardware"),
            "revision": cpuinfo.get("revision"),
            "serial": cpuinfo.get("serial", socket.gethostname()),
            "cores": cores,
            "ram": ram,
            "python_version": python_version,
            "pip_version": pip_version,
            "virtualenv": virtualenv,
            "octoprint_version": octoprint.util.version.get_octoprint_version_string(),
            "plugin_version": self._plugin_version,
            "print_nanny_client_version": print_nanny_client.__version__,  # alpha client version
            "print_nanny_beta_client_version": printnanny_api_client.__version__,  # beta client version
        }

    def _reset_octoprint_device(self):
        logger.warning("Resetting local device settings")
        self._settings.set(["device_private_key"], None)
        self._settings.set(["device_public_key"], None)
        self._settings.set(["device_fingerprint"], None)
        self._settings.set(["octoprint_device_id"], None)
        self._settings.set(["device_serial"], None)
        self._settings.set(["device_manage_url"], None)
        self._settings.set(["device_cloudiot_name"], None)
        self._settings.set(["cloudiot_device_id"], None)
        self._settings.set(["device_registered"], False)
        self._settings.save()

    @beeline.traced("OctoPrintNannyPlugin.sync_printer_profiles")
    async def sync_printer_profiles(self, **kwargs) -> bool:
        octoprint_device_id = self.get_setting("octoprint_device_id")
        if octoprint_device_id is None:
            return False
        logger.info(
            f"Syncing printer profiles for octoprint_device_id={octoprint_device_id}"
        )
        printer_profiles = self._printer_profile_manager.get_all()

        # on sync, cache a local map of octoprint id <-> print nanny id mappings for debugging
        id_map: Dict[str, Dict[str, int]] = {"octoprint": {}, "octoprint_nanny": {}}
        for profile_id, profile in printer_profiles.items():
            try:
                created_profile = await self.worker_manager.plugin.settings.rest_client.update_or_create_printer_profile(
                    profile, octoprint_device_id
                )
                id_map["octoprint"][profile_id] = created_profile.id
                id_map["octoprint_nanny"][created_profile.id] = profile_id
            except printnanny_api_client.exceptions.ApiException as e:
                # octoprint device was deleted remotely
                if e.status == 400:
                    try:
                        res = json.loads(e.body)
                        if res.get("octoprint_device") is not None:
                            self._reset_octoprint_device()
                    except ValueError as e2:  # not all responses are JSON serializable right now (e.g. django default responses)
                        pass
                logger.error(f"Error syncing printer profiles {e.body}")
                return False
            except asyncio.TimeoutError as e:
                logger.error(f"Connection to Print Nanny REST API timed out")
                return False

        logger.info(f"Synced {len(printer_profiles)} printer_profile")

        filename = os.path.join(
            self.get_plugin_data_folder(), "printer_profile_id_map.json"
        )
        with io.open(filename, "w+", encoding="utf-8") as f:
            json.dump(id_map, f)
        logger.info(
            f"Wrote id map for {len(printer_profiles)} printer profiles to {filename}"
        )
        return True

    @beeline.traced("OctoPrintNannyPlugin._write_keypair")
    async def _write_keypair(self, device):
        pubkey_filename = os.path.join(self.get_plugin_data_folder(), "public_key.pem")
        privkey_filename = os.path.join(
            self.get_plugin_data_folder(), "private_key.pem"
        )

        with open(pubkey_filename, "w+") as pubkey_f:
            pubkey_f.write(device.public_key)

        with open(pubkey_filename, "rb") as pubkey_fb:
            pubkey_content: bytes = pubkey_fb.read()
            if hashlib.sha256(pubkey_content).hexdigest() != device.public_key_checksum:
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {pubkey_filename} did not match the expected checksum value. Please try again!"
                )

        with open(privkey_filename, "w+") as privkey_f:
            privkey_f.write(device.private_key)
        with open(privkey_filename, "rb") as privkey_fb:
            privkey_content: bytes = privkey_fb.read()
            if (
                hashlib.sha256(privkey_content).hexdigest()
                != device.private_key_checksum
            ):
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {privkey_filename} did not match the expected checksum value. Please try again!"
                )

        logger.info(
            f"Saved keypair {device.fingerprint} to {pubkey_filename} {privkey_filename}"
        )

        self._settings.set(["device_private_key"], privkey_filename)
        self._settings.set(["device_public_key"], pubkey_filename)

    @beeline.traced("OctoPrintNannyPlugin._download_root_certificates")
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

        with open(primary_root_ca_filename, "wb+") as f:
            f.write(root_ca)
        with open(backup_root_ca_filename, "wb+") as f:
            f.write(backup_ca)

        self._settings.set(["ca_cert"], primary_root_ca_filename)
        self._settings.set(["backup_ca_cert"], backup_root_ca_filename)

    @beeline.traced("OctoPrintNannyPlugin._write_ca_certs")
    async def _write_ca_certs(self, device):

        ca_path = os.path.join(
            self.get_plugin_data_folder(),
            "cacerts",
        )
        Path(ca_path).mkdir(parents=True, exist_ok=True)

        primary_ca_filename = os.path.join(ca_path, "primary_ca.pem")

        backup_ca_filename = os.path.join(ca_path, "backup_ca.pem")

        with open(primary_ca_filename, "w+") as primary_f:
            primary_f.write(device.ca_certs["primary"])

        with open(primary_ca_filename, "rb") as primary_fb:
            primary_content = primary_fb.read()

            if (
                hashlib.sha256(primary_content).hexdigest()
                != device.ca_certs["primary_checksum"]
            ):
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {primary_ca_filename} did not match the expected checksum value. Please try again!"
                )

        with open(backup_ca_filename, "w+") as backup_f:
            backup_f.write(device.ca_certs["backup"])

        with open(backup_ca_filename, "rb") as backup_fb:
            backup_content = backup_fb.read()
            if (
                hashlib.sha256(backup_content).hexdigest()
                != device.ca_certs["backup_checksum"]
            ):
                raise octoprint_nanny.exceptions.FileIntegrity(
                    f"The checksum of file {backup_ca_filename} did not match the expected checksum value. Please try again!"
                )

        self._settings.set(["ca_cert"], primary_ca_filename)
        self._settings.set(["backup_ca_cert"], backup_ca_filename)

    @beeline.traced("OctoPrintNannyPlugin.sync_device_metadata")
    async def sync_device_metadata(self):
        octoprint_device_id = self.get_setting("octoprint_device_id")
        if octoprint_device_id is None:
            return
        logger.info(f"Syncing metadata for octoprint_device_id={octoprint_device_id}")

        device_info = self.get_device_info()
        try:
            await self.worker_manager.plugin.settings.rest_client.update_octoprint_device(
                octoprint_device_id, **device_info
            )
        except asyncio.TimeoutError as e:
            logger.error(f"Connection to Print Nanny REST API timed out")

    @beeline.traced("OctoPrintNannyPlugin._register_device")
    async def _register_device(self, device_name):

        logger.info(
            f"OctoPrintNanny._register_device called with device_name={device_name}"
        )
        # device registration

        span = beeline.start_span(context={"name": "get_device_info"})
        device_info = self.get_device_info()

        beeline.add_context(dict(device_info=device_info))
        beeline.finish_span(span)

        span = beeline.start_span(context={"name": "update_or_create_octoprint_device"})
        try:
            logger.info(
                f"update_or_create_octoprint_device from device_info={device_info}"
            )
            device = await self.worker_manager.plugin.settings.rest_client.update_or_create_octoprint_device(
                name=device_name, **device_info
            )
            beeline.add_context(dict(device_upserted=device))
            beeline.finish_span(span)
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
                payload={"msg": str(e)},
            )
            return e

        logger.info(
            f"Registered octoprint device with hardware serial={device.serial} url={device.url} fingerprint={device.fingerprint} id={device.id} cloudiot_num_id={device.cloudiot_device_num_id}"
        )

        await self._write_keypair(device)
        await self._write_ca_certs(device)
        # await self._download_root_certificates()

        self._settings.set(["device_serial"], device.serial)
        self._settings.set(["device_manage_url"], device.manage_url)
        self._settings.set(["octoprint_device_id"], device.id)
        self._settings.set(["device_fingerprint"], device.fingerprint)
        self._settings.set(["device_cloudiot_name"], device.cloudiot_device_name)
        self._settings.set(["cloudiot_device_id"], device.cloudiot_device_num_id)
        self._settings.set(["device_registered"], True)

        self._settings.save()
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_PRINTER_PROFILE_SYNC_START,
            payload={"msg": "Syncing printer profiles..."},
        )
        sync_success = await self.sync_printer_profiles()
        if sync_success:
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_PRINTER_PROFILE_SYNC_DONE,
                payload={
                    "msg": "Success! Printer profiles synced to https://print-nanny.com/dashboard/printer-profiles"
                },
            )
        else:
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_REGISTER_FAILED,
                payload={},
            )

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
    @octoprint.plugin.BlueprintPlugin.route("/startMonitoring", methods=["POST"])
    def start_predict(self):
        # settings test#
        url = self._settings.get(["snapshot_url"])
        res = requests.get(url)
        res.raise_for_status()
        if res.status_code == 200:
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
                payload=base64.b64encode(res.content),
            )
            session = uuid.uuid4().hex
            self._event_bus.fire(
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START, {"session": session}
            )
            return flask.json.jsonify({"ok": 1})
        else:
            return res

    @beeline.traced(name="OctoPrintNannyPlugin.stop_predict")
    @octoprint.plugin.BlueprintPlugin.route("/stopMonitoring", methods=["POST"])
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
        self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_RESET)

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
    @octoprint.plugin.BlueprintPlugin.route("/testConnectionsAsync", methods=["POST"])
    def test_auth_token_async(self):
        """
        Immediately returns a 200 response if auth token is set, 400 if auth not provided
        Connection test results published in async message Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API
        """
        auth_token = flask.request.json.get("auth_token")
        flask.request.json.get("api_url")
        logger.info("Testing REST API connection async")
        if auth_token is None:
            return flask.json.jsonify({"error": "auth_token was not provided"}, 400)

        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API,
            payload=flask.request.json,
        )
        self._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING,
        )
        return flask.json.jsonify({"msg": "Testing Print Nanny connections"}, 200)

    @beeline.traced(name="OctoPrintNannyPlugin.test_auth_token")
    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get("auth_token")
        api_url = flask.request.json.get("api_url")

        logger.info("Testing auth_token in worker thread's event loop")

        try:
            response = self._test_api_auth(auth_token, api_url)
        except Exception as e:
            return (
                flask.json.jsonify(
                    {"msg": "Error communicating with Print Nanny API", "error": str(e)}
                ),
                500,
            )
        if isinstance(response, printnanny_api_client.models.user.User):
            self._settings.set(["auth_token"], auth_token)
            self._settings.set(["auth_valid"], True)
            self._settings.set(["api_url"], api_url)
            self._settings.set(["user_email"], response.email)
            self._settings.set(["user_id"], response.id)

            self._settings.save()
            self.worker_manager.plugin.settings.reset_rest_client_state()
            return flask.json.jsonify(response.to_dict())

    def register_custom_events(self):
        # remove plugin event prefix when registering events (octoprint adds prefix)
        plugin_events = [
            x.replace(self.octoprint_event_prefix, "")
            for x in OctoPrintNannyEvent.allowable_values
        ]
        remote_commands = [
            "remote_command_received",
            "remote_command_failed",
            "remote_command_success",
        ]
        local_only = [
            "monitoring_frame_b64",  # not sent via event telemetry
            "monitoring_frame_bytes",
        ]
        return plugin_events + remote_commands + local_only

    @beeline.traced(name="OctoPrintNannyPlugin.on_after_startup")
    def on_shutdown(self):
        logger.info("Processing shutdown event")
        asyncio.run_coroutine_threadsafe(
            self.worker_manager.shutdown(), self.worker_manager.loop
        ).result()
        self._settings.set(["monitoring_active"], False)

    def on_startup(self, *args, **kwargs):
        logger.info("OctoPrint Nanny starting up")
        self._settings.set(["monitoring_active"], False)

    def on_after_startup(self, *args, **kwargs):
        logger.info("OctoPrint Nanny startup complete, configuring logger")
        configure_logger(logger, self._settings.get_plugin_logfile_path())

    def on_event(self, event_type, event_data):

        tracked = self.settings.event_is_tracked(event_type)

        # shutdown event is handled in .on_shutdown so queue is correctly drained
        # if event_type == Events.SHUTDOWN:
        #     return
        if event_type == Events.PLUGIN_OCTOPRINT_NANNY_DEVICE_RESET:
            self.worker_manager.mqtt_client_reset()

        elif event_type == Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_REST_API:
            # schedule api call on worker_manager's event loop to avoid blocking on_event in OctoPrint's main loop
            asyncio.run_coroutine_threadsafe(
                self._test_api_auth_async(**event_data), self.worker_manager.loop
            )
        elif event_type == Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PING:
            # schedule api call on worker_manager's event loop to avoid blocking on_event in OctoPrint's main loop
            asyncio.run_coroutine_threadsafe(
                self._test_mqtt_async(), self.worker_manager.loop
            )
        elif tracked:
            logger.debug(f"Putting event_type={event_type} into mqtt_send_queue")
            try:
                self.worker_manager.mqtt_send_queue.put_nowait(
                    {"event_type": event_type, "event_data": event_data}
                )
            except BrokenPipeError:
                logger.error(
                    f"BrokenPipeError raised on mqtt_send_queue.put_nowait() call, discarding event_type={event_type}"
                )
        elif event_type in self.VERBOSE_EVENTS:
            pass
        else:
            logger.info(f"Ignoring event_type={event_type} event_data={event_data}")

    def on_environment_detected(self, environment, *args, **kwargs):
        self._octoprint_environment = environment
        self.worker_manager.plugin.settings.on_environment_detected(environment)

    @beeline.traced(name="OctoPrintNannyPlugin.on_settings_initialized")
    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """
        self._log_path = self._settings.get_plugin_logfile_path()
        self.worker_manager.on_settings_initialized()

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        octoprint_job = self._printer.get_current_job()
        payload = {
            "event_type": Events.PRINT_PROGRESS,
            "event_data": {
                "print_progress": progress,
            },
        }
        progress = octoprint_job.get("progress")
        if octoprint_job and progress:
            payload["event_data"].update(
                {
                    "filepos": progress.get("filepos"),
                    "time_elapsed": progress.get("printTime"),
                    "time_remaiing": progress.get("printTimeLeft"),
                }
            )

        self.worker_manager.mqtt_send_queue.put_nowait(payload)

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return DEFAULT_SETTINGS

    ## Template plugin

    def get_template_vars(self):
        return {
            # @ todo is there a covenience method to get all plugin settings?
            # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=settings%20get#octoprint.plugin.PluginSettings.get
            "settings": {
                key: self._settings.get([key])
                for key in self.get_settings_defaults().keys()
            },
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
                self._settings.get(["octoprint_device_id"]) is None,
                self._settings.get(["device_serial"]) is None,
                self._settings.get(["device_registered"]) is False,
                self._settings.get(["device_manage_url"]) is None,
                self._settings.get(["device_cloudiot_name"]) is None,
                self._settings.get(["cloudiot_device_id"]) is None,
                self._settings.get(["user_email"]) is None,
                self._settings.get(["user_id"]) is None,
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
                stable_branch=dict(
                    name="Stable Channel", branch="main", commitish=["main"]
                ),
                prerelease_branches=[
                    dict(
                        name="Prerelease Channel",
                        branch="devel",
                        commitish=["main", "devel"],
                    )
                ],
            ),
        )
