import asyncio
import logging
import os
import nats
import flask
import functools
import octoprint.plugin
import octoprint.util

from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor
from octoprint.events import Events

from octoprint_nanny.events import try_handle_event

from octoprint_nanny.utils import printnanny_os
from octoprint_nanny.utils.logger import configure_logger

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


PRINTNANNY_WEBAPP_BASE_URL = os.environ.get(
    "PRINTNANNY_WEBAPP_BASE_URL", "https://printnanny.ai"
)
Events.PRINT_PROGRESS = "PrintProgress"

DEFAULT_SETTINGS = dict(
    chatEnabled=True,
    posthogEnabled=False,
)


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

        # create a thread bool for asyncio tasks
        self._thread_pool = ThreadPoolExecutor(max_workers=8)
        self._nc = None

        super().__init__(*args, **kwargs)

    def _init_nats_connection(self):
        if self._nc is None:
            # test nats credential path:
            if os.path.exists(printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS) == False:
                logger.error(
                    "Failed to load PrintNanny Cloud NATS credentials from %s",
                    printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS,
                )
                return
            if printnanny_os.PRINTNANNY_PI is None:
                logger.error("Failed to load PRINTNANNY_PI")
                return
            # get asyncio event loop
            loop = asyncio.new_event_loop()
            # schedule task using ThreadPoolExecutor
            coro = functools.partial(
                nats.connect,
                data={
                    "servers": [printnanny_os.PRINTNANNY_PI.nats_app.nats_server_uri],
                    "user_credentials": printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS,
                },
            )
            future = loop.run_in_executor(self._thread_pool, coro)
            self._nc = future.result()

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
        # drain and shutdown thread pool
        self._thread_pool.shutdown()

    def on_startup(self, *args, **kwargs):
        # configure nats connection
        printnanny_os.load_printnanny_config()
        try:
            self._init_nats_connection()
        except Exception as e:
            logger.error("Error initializing PrintNanny Cloud NATS connection: %s", e)

    def on_after_startup(self, *args, **kwargs):
        # configure logger first
        configure_logger(logger, self._settings.get_plugin_logfile_path())

    def on_event(self, event: str, payload: Dict[Any, Any]):
        if printnanny_os.is_printnanny_os():
            if self._nc is None:
                logger.warning(
                    "PrintNanny Cloud NATS connection is not initialized, skipping event: %s",
                    event,
                )
                return
            try_handle_event(event, payload, self._nc, self._thread_pool)
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
        return DEFAULT_SETTINGS

    ##~~ Template plugin

    def get_template_vars(self):
        printnanny_os.load_printnanny_config()
        custom = {
            "urls": {
                "getting_started_guide": "https://printnanny.ai/docs/category/quick-start/",
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
        return 2

    def get_wizard_version(self):
        return 2

    ## Show OctoPrint setup wizard if PrintNanny Cloud Nats creds aren't present
    def is_wizard_required(self):
        printnanny_os.load_printnanny_config()
        return os.path.exists(printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS) == False

    ##~~ AssetPlugin mixin
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=[
                "js/octo_printnanny.js",
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
