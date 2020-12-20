import aioprocessing
import asyncio
import base64
import re
from datetime import datetime
import platform
import pytz

import logging

import aiohttp

import octoprint.filemanager
from octoprint.events import Events

import threading

from print_nanny.clients.websocket import WebSocketWorker
from print_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from print_nanny.predictor import PredictWorker

import print_nanny_client.exceptions.ApiException

logger = logging.getLogger("octoprint.plugins.print_nanny.manager")

Events.PRINT_PROGRESS = "print_progress"


class WorkerManager:
    """
    Manages PredictWorker, WebsocketWorker, RestWorker processes
    """

    def __init__(self, plugin):

        self.plugin = plugin
        self.manager = aioprocessing.managers.AioManager()
        self.shared = self.manager.Namespace()

        # proxy objects
        self.shared.printer_profile_id = None
        self.shared.print_job_id = None
        self.shared.calibration = None

        self.active = False

        self.tracking_queue = (
            self.manager.Queue()
        )  # holds octoprint events to be uploaded via rest client
        self.octo_ws_queue = (
            self.manager.Queue()
        )  # streamed to octoprint front-end over websocket
        self.pn_ws_queue = (
            self.manager.Queue()
        )  # streamed to print nanny asgi over websocket

        self._tracking_event_handlers = {
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self.stop,
            Events.PRINT_DONE: self.stop,
            Events.PRINT_CANCELLING: self.stop,
            Events.PRINT_CANCELLED: self.stop,
            Events.PRINT_PAUSED: self.stop,
            Events.PRINT_RESUMED: self.stop,
            Events.PRINT_PROGRESS: self._handle_print_progress_upload,
        }

        # daemonized threads for rest api and octoprint websocket relay
        self.rest_api_thread = threading.Thread(target=self._rest_api_worker)
        self.rest_api_thread.daemon = True
        self.rest_api_thread.start()

        self.octo_ws_thread = threading.Thread(target=self._octo_ws_queue_worker)
        self.octo_ws_thread.daemon = True
        self.octo_ws_thread.start()

    async def _handle_print_progress_upload(self, event_type, event_data, **kwargs):
        if self.shared.print_job_id is not None:
            try:
                await self.rest_client.update_print_progress(
                    self.shared.print_job_id, event_data
                )
            except CLIENT_EXCEPTIONS as e:
                logger.error(
                    f"_handle_print_progress_upload() exception {e}", exc_info=True
                )

    async def _handle_octoprint_event(self, event_type, event_data):

        metadata = {"metadata": self._get_metadata()}
        if event_data is not None:
            event_data.update(metadata)
        else:
            event_data = metadata

        try:
            await self.rest_client.create_octoprint_event(event_type, event_data)
        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_octoprint_event() exception {e}", exc_info=True)

    async def _rest_api_worker(self):
        logger.info("Started _rest_client_worker")

        while True:
            event = await self.tracking_queue.get()
            if event.get("event_type") is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event_type=event
                    )
                )
                continue

            handler_fn = self._tracking_event_handlers.get(event["event_type"])

            try:
                if handler_fn:
                    await handler_fn(**event)
                await self._handle_octoprint_event(**event)
            except CLIENT_EXCEPTIONS as e:
                logger.error(e, exc_info=True)

    def stop(self):
        """
        joins and terminates prediction and pn websocket processes
        """
        self.active = False

        self.predict_proc.terminate()
        self.pn_ws_proc.terminate()

    def start(self):
        """
        starts prediction and pn websocket processes
        """
        self.active = True
        webcam_url = self.plugin._settings.global_get(["webcam", "snapshot"])

        self.predict_proc = aioprocessing.AioProcess(
            target=PredictWorker,
            args=(
                webcam_url,
                self.shared.calibration,
                self.octo_ws_queue,
                self.pn_ws_queue,
            ),
            daemon=True,
        )
        self.predict_proc.start()

        auth_token = self.plugin._settings.get(["auth_token"])
        ws_url = self.plugin._settings.get(["ws_url"])
        api_url = self.plugin._settings.get(["api_url"])

        self.rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)

        self.pn_ws_proc = aioprocessing.Process(
            target=WebSocketWorker,
            args=(ws_url, auth_token, self.pn_ws_queue, self.shared.print_job_id),
            daemon=True,
        )
        self.pn_ws_proc.start()

    def _octo_ws_queue_worker(self):
        """
        Child process to -> Octoprint event bus relay
        """
        logger.info("Started _octo_ws_queue_worker")
        while self.active:
            viz_bytes = self.octo_ws_queue.get(block=True)
            self.plugin._event_bus.fire(
                Events.PLUGIN_PRINT_NANNY_PREDICT_DONE,
                payload={"image": base64.b64encode(viz_bytes)},
            )

    def _get_metadata(self):
        metadata = {
            "printer_data": self.plugin._printer.get_current_data(),
            "printer_profile": self.plugin._printer_profile_manager.get_current_or_default(),
            "temperature": self.plugin._printer.get_current_temperatures(),
            "dt": datetime.now(pytz.timezone("America/Los_Angeles")),
            "plugin_version": self.plugin._plugin_version,
            "octoprint_version": octoprint.util.version.get_octoprint_version_string(),
            "platform": platform.platform(),
            "mac_address": ":".join(re.findall("..", "%012x".format(uuid.getnode()))),
            "api_objects": {
                k: None if v is None else v.id for k, v in self._api_objects.items()
            },
            "environment": self._environment,
            "plugin_version": self._plugin_version,
        }
        return metadata

    async def _handle_print_start(self, event_type, event_data):

        event_data.update(self._get_metadata())

        try:
            printer_profile = await self.rest_client.update_or_create_printer_profile(
                event_data
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path
            )

            print_job = await self.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id
            )

            self.shared.print_job_id = print_job.id

        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        self.start()
