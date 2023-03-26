import asyncio
import logging
import os

import functools
import octoprint.plugin
import octoprint.util

from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from octoprint.events import Events

from octoprint_nanny.clients.rest import PrintNannyCloudAPIClient
from octoprint_nanny.events import try_publish_nats
from octoprint_nanny.utils import printnanny_os
from octoprint_nanny.worker import AsyncTaskWorker

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


PRINTNANNY_API_BASE_URL = os.environ.get(
    "PRINTNANNY_API_BASE_URL", "https://printnanny.ai"
)


Events.PRINT_PROGRESS = "PrintProgress"

DEFAULT_SETTINGS = dict(chatEnabled=True, posthogEnabled=False, apiToken=None)


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
        self._printnanny_api_client: Optional[PrintNannyCloudAPIClient] = None

        # create a thread pool for asyncio tasks
        self.worker = AsyncTaskWorker()

        super().__init__(*args, **kwargs)

    def _init_cloud_api_client(self):
        if printnanny_os.PRINTNANNY_CLOUD_API is None:
            logger.info(
                "_init_cloud_api_client failed, printnanny_os.PRINTNANNY_CLOUD_API is None"
            )
            return
        if self._printnanny_api_client is None:
            self._printnanny_api_client = PrintNannyCloudAPIClient(
                base_path=printnanny_os.PRINTNANNY_CLOUD_API.get(
                    "base_path", "https://printnanny.ai"
                ),
                bearer_access_token=printnanny_os.PRINTNANNY_CLOUD_API.get(
                    "bearer_access_token"
                ),
            )
            logger.info(
                "Initialized PrintNannyCloudAPIClient: %s",
                printnanny_os.PRINTNANNY_CLOUD_API.get("base_path"),
            )

    ##
    ## Octoprint api routes + handlers
    ##
    @octoprint.plugin.BlueprintPlugin.route("/printnanny/test", methods=["POST"])
    def test_printnanny_cloud_nats(self):
        # reload config
        self._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_SERVER_TEST)
        return dict(ok=True)

    def register_custom_events(self) -> List[str]:
        return ["server_test"]

    def on_shutdown(self):
        # drain and shutdown thread pool
        self._thread_pool.shutdown()

    def on_startup(self, *args, **kwargs):
        pass

    async def load_printnanny(self):
        cloud_result = await printnanny_os.load_printnanny_cloud_data()
        logger.debug("load_printnanny_cloud_data result %s", cloud_result)
        # run blocking i/o in a thread, pre-allocated using ThreadPoolExecutor
        settings_result = self.worker.run_coroutine_threadsafe(
            printnanny_os.load_printnanny_settings()
        )
        logger.debug("load_printnanny_settings result %s", settings_result)

    def on_after_startup(self, *args, **kwargs):
        # load PrintNanny Cloud data models
        self.worker.run_coroutine_threadsafe(self.load_printnanny())

        # configure PrintNanny Cloud REST api credentials
        try:
            self._init_cloud_api_client()
        except Exception as e:
            logger.error("Error initializing PrintNanny Cloud API client: %s", e)

    def on_event(self, event: str, payload: Dict[Any, Any]):
        future = self.worker.run_coroutine_threadsafe(try_publish_nats(event, payload))
        future.result()

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
        self.on_event(Events.PRINT_PROGRESS, payload)

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return DEFAULT_SETTINGS

    ##~~ Template plugin

    def get_template_vars(self):
        custom = {
            "urls": {
                "getting_started_guide": "https://printnanny.ai/docs/category/quick-start/",
                "discord_invite": "https://discord.gg/sf23bk2hPr",
                "webapp": PRINTNANNY_API_BASE_URL,
            },
            "is_printnanny_os": printnanny_os.is_printnanny_os(),
            "issue_txt": printnanny_os.issue_txt(),
            "etc_os_release": printnanny_os.etc_os_release(),
            "PRINTNANNY_CLOUD_PI": printnanny_os.PRINTNANNY_CLOUD_PI,
        }
        return custom

    ##~~ Wizard plugin mixin
    def get_settings_version(self):
        return 2

    def get_wizard_version(self):
        return 2

    def is_wizard_required(self):
        return False

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
