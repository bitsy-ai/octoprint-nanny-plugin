import logging
import os
import flask
import octoprint.plugin
import octoprint.util
import socket
from typing import Any, Dict, List

from octoprint.events import Events

from octoprint_nanny.events import try_handle_event

from octoprint_nanny.utils import printnanny_os
from octoprint_nanny.utils.logger import configure_logger

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


PRINTNANNY_WEBAPP_BASE_URL = os.environ.get(
    "PRINTNANNY_WEBAPP_BASE_URL", "https://printnanny.ai"
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
        self._log_path = None
        super().__init__(*args, **kwargs)

    ##
    ## Octoprint api routes + handlers
    ##
    @octoprint.plugin.BlueprintPlugin.route("/backup", methods=["POST"])
    def create_backup(self):
        helpers = self._plugin_manager.get_helpers("backup", "create_backup")

        if helpers and "create_backup" in helpers:
            backup_file = helpers["create_backup"](exclude=["timelapse"])
            logger.info("Created backup file")
            return flask.json.jsonify({"ok": 1})
        else:
            logger.error("Plugin manager failed to get backup helper")
            raise Exception("Plugin manager failed to get backup helper")

    def register_custom_events(self) -> List[str]:
        return []

    def on_shutdown(self):
        logger.info("Running on_shutdown handler")

    def on_startup(self, *args, **kwargs):
        logger.info("Running on_startup handler args=%s kwargs=%s", args, kwargs)

    def on_after_startup(self, *args, **kwargs):
        logger.info("Running on_after_startup handler args=%s kwargs=%s", args, kwargs)
        configure_logger(logger, self._settings.get_plugin_logfile_path())

    def on_event(self, event: str, payload: Dict[Any, Any]):
        if printnanny_os.is_printnanny_os():
            try_handle_event(event, payload)
        else:
            logger.warning(
                "PrintNanny OS not detected or device is not registered. Ignoring event %s",
                event,
            )

    def on_environment_detected(self, environment, *args, **kwargs):
        logger.info(
            "Running on_environment_detected handler args=%s kwargs=%s", args, kwargs
        )

        self._octoprint_environment = environment

    def on_settings_initialized(self):
        """
        Called after plugin initialization
        """
        logger.info("Running on_settings_initialized handler")

        self._log_path = self._settings.get_plugin_logfile_path()

    ##~~ Progress plugin

    def on_print_progress(self, storage, path, progress):
        octoprint_job = self._printer.get_current_job()
        payload = dict(
            octoprint_job=octoprint_job, storage=storage, path=path, progress=progress
        )
        logger.info("PrintProgress payload%s", payload)
        self.on_event(Events.PRINT_PROGRESS, payload)

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        maybe_config = printnanny_os.load_printnanny_config()
        config = maybe_config.get("config")
        if config is not None:
            janusApiUrl = (
                config.get("device", {}).get("janus_edge", {}).get("api_http_url", "")
            )
            janusApiToken = (
                config.get("device", {}).get("janus_edge", {}).get("api_token", "")
            )

            DEFAULT_SETTINGS = dict(
                janusApiUrl=janusApiUrl,
                janusApiToken=janusApiToken,
                janusBitrateInterval=1000,
                selectedStreamId=None,
                streamWebrtcIceServers="stun:stun.l.google.com:19302",
            )
            return DEFAULT_SETTINGS
        else:
            return dict()

    ##~~ Template plugin

    def get_template_vars(self):
        printnanny_os.load_printnanny_config()
        custom = {
            "urls": {
                "getting_started_guide": "https://docs.printnanny.ai/docs/category/quick-start/",
                "discord_invite": "https://discord.gg/sf23bk2hPr",
                "webapp": PRINTNANNY_WEBAPP_BASE_URL,
            },
            "is_printnanny_os": printnanny_os.is_printnanny_os(),
            "issue_txt": printnanny_os.issue_txt(),
            "etc_os_release": printnanny_os.etc_os_release(),
            "PRINTNANNY_PI": printnanny_os.PRINTNANNY_PI,
        }
        return custom

    ##~~ Wizard plugin mixin
    def get_settings_version(self):
        return 1

    def get_wizard_version(self):
        return 1

    ## Require Wizard if PrintNanny user is not detected
    def is_wizard_required(self):
        printnanny_os.load_printnanny_config()
        return printnanny_os.PRINTNANNY_PI is None

    ##~~ AssetPlugin mixin
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=[
                "js/nanny.js",
                "js/januswebcam_settings.js",
                "js/januswebcam.js",
                "vendor/janus/janus.js",
                "vendor/janus/webrtc-adaptor.js",
            ],
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
