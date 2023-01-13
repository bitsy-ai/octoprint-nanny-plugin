import asyncio
import logging
import os

import nats
import backoff
import functools
import octoprint.plugin
import octoprint.util

from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from octoprint.events import Events

from octoprint_nanny.clients.rest import PrintNannyCloudAPIClient
from octoprint_nanny.events import try_handle_event
from octoprint_nanny.env import MAX_BACKOFF_TIME
from octoprint_nanny.utils import printnanny_os
from octoprint_nanny.utils.logger import configure_logger

logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


PRINTNANNY_WEBAPP_BASE_URL = os.environ.get(
    "PRINTNANNY_WEBAPP_BASE_URL", "https://printnanny.ai"
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
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._nc = None

        # get/set a new asyncio event loop context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._loop.set_default_executor(self._thread_pool)

        super().__init__(*args, **kwargs)

    @backoff.on_exception(
        backoff.expo,
        ValueError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    def _init_cloud_nats_connection(self):
        if self._nc is None:
            if printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS is None:
                logger.warning(
                    "_init_cloud_nats_connection called before printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS was set"
                )
                raise ValueError(
                    "printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS is None, expected path to PrintNanny Cloud NATS credentials"
                )
            # test nats credential path:
            if os.path.exists(printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS) == False:
                logger.error(
                    "Failed to load PrintNanny Cloud NATS credentials from %s",
                    printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS,
                )
                return
            if printnanny_os.PRINTNANNY_CLOUD_PI is None:
                logger.error("Failed to load PRINTNANNY_CLOUD_PI")
                return
            self._nc = self._loop.run_until_complete(
                nats.connect(
                    servers=[
                        printnanny_os.PRINTNANNY_CLOUD_PI.nats_app.nats_server_uri
                    ],
                    user_credentials=printnanny_os.PRINTNANNY_CLOUD_NATS_CREDS,
                )
            )

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

    def _save_octoprint_api_key(self):
        if printnanny_os.PRINTNANNY_CLOUD_PI is None:
            logger.warn(
                "Failed to set Octoprint API key, printnanny_os.PRINTNANNY_CLOUD_PIis None"
            )
            return
        if printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server is None:
            logger.warn(
                "Failed to set Octoprint API key, printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server is None"
            )
            return

        if self._printnanny_api_client is None:
            logger.warn(
                "Failed to set Octoprint API key, PrintNannyCloudAPIClient is not initialized"
            )
            return

        api_key = self._settings.generateApiKey()
        octoprint_server_id = printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id
        logger.info(
            "Setting OctoprintServer.api_key where id=%s",
            octoprint_server_id,
        )
        result = self._loop.run_until_complete(
            self._printnanny_api_client.update_octoprint_server_api_key(
                octoprint_server_id=octoprint_server_id,
                api_key=api_key,
            ),
        )
        logger.info("Updated OctoPrint API key for server id=%s", result.id)

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
        logger.info("load_printnanny_cloud_data result %s", cloud_result)
        # run blocking i/o in a thread, pre-allocated using ThreadPoolExecutor
        settings_result = await self._loop.run_in_executor(
            self._thread_pool, printnanny_os.load_printnanny_settings
        )
        logger.info("load_printnanny_settings result %s", settings_result)

    def on_after_startup(self, *args, **kwargs):
        # configure logger first
        configure_logger(logger, self._settings.get_plugin_logfile_path())

        # then load PrintNanny Cloud data models
        self._loop.run_until_complete(self.load_printnanny())
        # configure PrintNanny Cloud NATS connection
        try:
            self._init_cloud_nats_connection()
        except Exception as e:
            logger.error("Error initializing PrintNanny Cloud NATS connection: %s", e)
        # configure PrintNanny Cloud REST api credentials
        try:
            self._init_cloud_api_client()
        except Exception as e:
            logger.error("Error initializing PrintNanny Cloud API client: %s", e)
        # configure octoprint REST api credentials
        try:
            self._save_octoprint_api_key()
        except Exception as e:
            logger.error(
                "Error sending OctoPrint API key to PrintNanny Cloud: %s",
                e,
                exc_info=True,
            )

    def on_event(self, event: str, payload: Dict[Any, Any]):
        if printnanny_os.is_printnanny_os():
            if self._nc is None:
                logger.warning(
                    "PrintNanny Cloud NATS connection is not initialized, skipping event: %s",
                    event,
                )
                return
            coro = functools.partial(
                try_handle_event, event=event, payload=payload, nc=self._nc
            )
            future = asyncio.run_coroutine_threadsafe(coro(), self._loop)
            result = future.result()
            logger.info("%s try_handle_event result ok: %s", event, result)
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
        custom = {
            "urls": {
                "getting_started_guide": "https://printnanny.ai/docs/category/quick-start/",
                "discord_invite": "https://discord.gg/sf23bk2hPr",
                "webapp": PRINTNANNY_WEBAPP_BASE_URL,
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
