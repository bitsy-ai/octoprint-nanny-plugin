import asyncio
import logging
import io
import json
import os
import platform
import socket
import beeline
import aiohttp.client_exceptions
import flask
import octoprint.plugin
import octoprint.util
from typing import Dict
import socket

from octoprint.events import Events

import printnanny_api_client  # beta client
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.utils.printnanny_os import (
    printnanny_version,
    printnanny_config,
)
from printnanny_api_client import OctoPrintNannyEvent

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
    printnanny_version=printnanny_version(),
    printnanny_os=printnanny_config(),
    backup_auto=False,
    wizard_complete=-1,
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
    VERBOSE_EVENTS = [Events.Z_CHANGE]

    def __init__(self, *args, **kwargs):
        # User interactive
        self._calibration = None

        self._log_path = None
        self._octoprint_environment = {}

        self.worker_manager = WorkerManager(plugin=self)

    def get_setting(self, key):
        return self._settings.get([key])

    def set_setting(self, key, value):
        return self._settings.set([key], value)

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

    @beeline.traced("OctoPrintNannyPlugin._test_snapshot_url")
    async def _test_snapshot_url(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                return await res.read()

    ##
    ## Octoprint api routes + handlers
    ##
    @octoprint.plugin.BlueprintPlugin.route("/createBackup", methods=["POST"])
    def create_backup(self):
        helpers = self._plugin_manager.get_helpers("backup", "create_backup")

        if helpers and "create_backup" in helpers:
            backup_file = helpers["create_backup"](exclude=["timelapse"])
            logger.info("Created backup file")
            return flask.json.jsonify({"ok": 1})
        else:
            logger.error("Plugin manager failed to get backup helper")
            raise Exception("Plugin manager failed to get backup helper")

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
            "connect_test_mqtt_pong_success",
        ]
        local_only = [
            "monitoring_frame_b64",  # not sent via event telemetry
            "monitoring_frame_bytes",
        ]
        return plugin_events + remote_commands + local_only

    def on_shutdown(self):
        logger.info("Running on_shutdown handler")

    def on_startup(self, *args, **kwargs):
        logger.info("Running on_startup handler args=%s kwargs=%s", args, kwargs)

    def on_after_startup(self, *args, **kwargs):
        logger.info("Running on_after_startup handler args=%s kwargs=%s", args, kwargs)
        configure_logger(logger, self._settings.get_plugin_logfile_path())

    def on_event(self, event_type, event_data):
        pass

    def on_environment_detected(self, environment, *args, **kwargs):
        logger.info(
            "Running on_environment_detectedp handler args=%s kwargs=%s", args, kwargs
        )

        self._octoprint_environment = environment

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """
        logger.info("Running on_settings_initialized handler")

        self._log_path = self._settings.get_plugin_logfile_path()

    ## Progress plugin

    def on_print_progress(self, storage, path, progress):
        octoprint_job = self._printer.get_current_job()
        pass

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
            "os": json.dumps(self._settings.get(["printnanny_os"]), indent=2),
        }

    ## Wizard plugin mixin

    def get_wizard_version(self):
        return 0

    def is_wizard_required(self):
        return self._settings.get(["wizard_complete"]) < self.get_wizard_version()

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
