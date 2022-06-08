import asyncio
import logging
import io
import json
import os
import flask
import octoprint.plugin
import octoprint.util
from typing import Any, Dict

from octoprint.events import Events

import printnanny_api_client  # beta client
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

from octoprint_nanny.events import try_handle_event
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.utils.printnanny_os import (
    printnanny_version,
    printnanny_config,
)

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
        self._log_path = None
        self.worker_manager = WorkerManager(plugin=self)
        super().__init__(*args, **kwargs)

    def _test_api_auth(self, auth_token: str, api_url: str):
        response = asyncio.run_coroutine_threadsafe(
            self._test_api_auth_async(auth_token, api_url), self.worker_manager.loop
        )
        if response.exception():
            return response.exception()
        else:
            return response.result()

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
        return remote_commands + local_only

    def on_shutdown(self):
        logger.info("Running on_shutdown handler")

    def on_startup(self, *args, **kwargs):
        logger.info("Running on_startup handler args=%s kwargs=%s", args, kwargs)

    def on_after_startup(self, *args, **kwargs):
        logger.info("Running on_after_startup handler args=%s kwargs=%s", args, kwargs)
        configure_logger(logger, self._settings.get_plugin_logfile_path())

    def on_event(self, event: str, payload: Dict[Any, Any]):
        events_enabled = self._settings.get(["events_enabled"])
        config = self._settings.get(["printnanny_config"])
        if config is None:
            logger.warning(
                "PrintNanny OS not detected or device is not registered. Ignoring event %s",
                event,
            )
            return
        try_handle_event(event, payload, config=config, events_enabled=events_enabled)

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
        DEFAULT_SETTINGS = dict(
            backup_auto=False,
            analytics_enabled=False,
            events_enabled=False,
            wizard_complete=-1,
        )
        return DEFAULT_SETTINGS

    ## Template plugin

    def get_template_vars(self):
        custom = {
            "config": printnanny_config(),
            # @ todo is there a covenience method to get all plugin settings?
            # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=settings%20get#octoprint.plugin.PluginSettings.get
            "settings": {
                key: self._settings.get([key])
                for key in self.get_settings_defaults().keys()
            },
            "os_version": printnanny_version(),
            "urls": {
                "getting_started_guide": "https://bitsy-ai.notion.site/Getting-Started-with-Print-Nanny-OS-817bc65297ff44a085120c663dced5f3",
                "discord_invite": "https://discord.gg/sf23bk2hPr",
                "cloud": "https://printnanny.ai",
            },
        }
        return custom

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
            css=["css/printnanny.css"],
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
