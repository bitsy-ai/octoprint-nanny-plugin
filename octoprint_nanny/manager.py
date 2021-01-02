import aioprocessing
import asyncio
import base64
import re
from datetime import datetime
import platform
import uuid
import pytz
from time import sleep

import logging

import aiohttp

import multiprocessing
import octoprint.filemanager
from octoprint.events import Events

import threading

from octoprint_nanny.clients.websocket import WebSocketWorker
from octoprint_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from octoprint_nanny.clients.mqtt import MQTTClient
from octoprint_nanny.predictor import (
    PredictWorker,
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)

import print_nanny_client

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.manager")

Events.PRINT_PROGRESS = "print_progress"

BACKOFF = 1


class WorkerManager:
    """
    Manages PredictWorker, WebsocketWorker, RestWorker processes
    """

    PRINT_JOB_EVENTS = [
        Events.ERROR,
        Events.PRINT_CANCELLING,
        Events.PRINT_CANCELLED,
        Events.PRINT_DONE,
        Events.PRINT_FAILED,
        Events.PRINT_PAUSED,
        Events.PRINT_RESUMED,
        Events.PRINT_STARTED,
    ]

    def __init__(self, plugin):

        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        # proxy objects
        self.shared.printer_profile_id = None
        self.shared.print_job_id = None
        self.shared.calibration = None

        self.mqtt_client = None
        self.active = False

        # published to GCP MQTT bridge
        self.telemetry_queue = self.manager.AioQueue()
        # images streamed to octoprint front-end over websocket
        self.octo_ws_queue = self.manager.AioQueue()
        # images streamed to webapp asgi over websocket
        self.pn_ws_queue = self.manager.AioQueue()

        self._local_event_handlers = {
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self.stop,
            Events.PRINT_DONE: self.stop,
            Events.PRINT_CANCELLING: self.stop,
            Events.PRINT_CANCELLED: self.stop,
            Events.PRINT_PAUSED: self.stop,
            Events.PRINT_RESUMED: self.stop,
            Events.PRINT_PROGRESS: self._handle_print_progress_upload,
        }

        self._environment = {}

        # daemonized thread for telemetry event handlers
        self.telemetry_worker_thread = threading.Thread(target=self._telemetry_worker)
        self.telemetry_worker_thread.daemon = True

        # daemonized thread for sending annotated image frames to Octoprint's UI
        self.octo_ws_thread = threading.Thread(target=self._octo_ws_queue_worker)
        self.octo_ws_thread.daemon = True

        # daemonized thread for MQTT worker thread
        self.mqtt_worker_thread = threading.Thread(target=self._mqtt_worker)
        self.mqtt_worker_thread.daemon = True

        self.loop = None
        self.telemetry_events = None
        self._user_id = None
        self._device_id = None
        self._calibration = None
        self._snapshot_url = None

    @property
    def snapshot_url(self):
        if self._snapshot_url is None:
            self._snapshot_url = self.plugin._settings.get(["snapshot_url"])
        return self._snapshot_url

    @property
    def device_id(self):
        if self._device_id is None:
            self._device_id = self.plugin._settings.get(["device_id"])
        return self._device_id

    @property
    def user_id(self):
        if self._user_id is None:
            self._user_id = self.plugin._settings.get(["user_id"])
        return self._user_id

    @property
    def calibration(self):
        if self._calibration is None:
            self._calibration = PredictWorker.calc_calibration(
                self.plugin._settings.get(["calibrate_x0"]),
                self.plugin._settings.get(["calibrate_y0"]),
                self.plugin._settings.get(["calibrate_x1"]),
                self.plugin._settings.get(["calibrate_y1"]),
            )
        return self._calibration

    @property
    def rest_client(self):

        api_token = self.plugin._settings.get(["auth_token"])
        api_url = self.plugin._settings.get(["api_url"])

        logger.debug(f"RestAPIClient init with api_token={api_token} api_url={api_url}")
        return RestAPIClient(auth_token=api_token, api_url=api_url)

    def on_settings_initialized(self):

        self.mqtt_worker_thread.start()
        self.octo_ws_thread.start()
        self.telemetry_worker_thread.start()
        while self.loop is None:
            sleep(1)

    def apply_auth(self):
        logger.warning("WorkerManager.apply_auth() not implemented yet")

    def apply_calibration(self):

        logger.info("Applying new calibration")
        self._calibration = None
        self.stop()
        self.start()

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

    def _mqtt_worker(self):
        private_key = self.plugin._settings.get(["device_private_key"])
        device_id = self.plugin._settings.get(["device_cloudiot_name"])
        gcp_root_ca = self.plugin._settings.get(["gcp_root_ca"])
        backoff = 1
        while True:
            if private_key is None or device_id is None or gcp_root_ca is None:
                logger.warning(
                    f"Waiting {backoff }to initialize mqtt client, missing device registration private_key={private_key} device_id={device_id} gcp_root_ca={gcp_root_ca}"
                )
                sleep(backoff)
                backoff = backoff ** 2
                continue
            break
        self.mqtt_client = MQTTClient(
            device_id=device_id, private_key_file=private_key, ca_certs=gcp_root_ca
        )
        logger.info(f"Initialized mqtt client with id {self.mqtt_client.client_id}")
        ###
        # MQTT bridge available
        ###
        return self.mqtt_client.run()

    def _telemetry_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        return self.loop.run_until_complete(
            asyncio.ensure_future(self._telemetry_queue_loop())
        )

    async def _publish_bounding_box_telemetry(self, event):
        logger.debug(f"_publish_bounding_box_telemetry {event}")
        self.mqtt_client.publish_bounding_boxes(event)

    async def _publish_octoprint_event_telemetry(self, event):
        event_type = event.get("event_type")
        logger.debug(f"_publish_octoprint_event_telemetry {event}")
        event.update(dict(user_id=self.user_id, device_id=self.device_id))
        event.update(self._get_metadata())
        if event_type in self.PRINT_JOB_EVENTS:
            event.update(self._get_print_job_metadata)
        self.mqtt_client.publish_octoprint_event(event)

    async def _telemetry_queue_loop(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info("Started _telemetry_queue_loop")

        api_token = self.plugin._settings.get(["auth_token"])
        global BACKOFF

        while True:

            if api_token is None:
                logger.warning(
                    f"auth_token not saved to plugin settings, waiting {BACKOFF} seconds"
                )
                await asyncio.sleep(BACKOFF)
                api_token = self.plugin._settings.get(["auth_token"])
                BACKOFF = BACKOFF ** 2
                continue

            if self.telemetry_events is None:
                self.telemetry_events = await self.rest_client.get_telemetry_events()

            ###
            # Rest API available
            ###
            if self.mqtt_client is None:
                logger.warning(
                    f"Waiting {BACKOFF} seconds for mqtt client to be available"
                )
                await asyncio.sleep(BACKOFF)
                BACKOFF = BACKOFF ** 2
                continue
            ###
            # mqtt client available
            ##

            event = await self.telemetry_queue.coro_get()
            event_type = event.get("event_type")
            if event_type is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event_type=event_type
                    )
                )
                continue

            ##
            # Publish non-octoprint telemetry events
            ##

            # publish to bounding-box telemetry topic
            if event_type == BOUNDING_BOX_PREDICT_EVENT:
                await self._publish_bounding_box_telemetry(event)
                continue

            ##
            # Handle OctoPrint telemetry events
            ##

            # ignore untracked events
            if event_type not in self.telemetry_events:
                # supress warnings about PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE event; this is for octoprint front-end only
                if event_type == Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE:
                    pass
                else:
                    logger.warning(f"Discarding {event_type} with payload {event}")
                continue
            # publish to octoprint-events telemetry topic
            else:
                await self._publish_octoprint_event_telemetry(event)

            # run local handler fn
            handler_fn = self._local_event_handlers.get(event["event_type"])
            try:
                if handler_fn:
                    await handler_fn(**event)
            except CLIENT_EXCEPTIONS as e:
                logger.error(e, exc_info=True)

    def stop(self):
        """
        joins and terminates prediction and pn websocket processes
        """

        self.active = False

        if self.predict_proc:
            logger.info("Terminating predict process")
            self.predict_proc.terminate()
            self.predict_proc.join(3)
            self.predict_proc.close()

        if self.pn_ws_proc:
            logger.info("Terminating websocket process")
            self.pn_ws_proc.terminate()
            self.pn_ws_proc.join()
            self.pn_ws_proc.close()

    def shutdown(self):
        return self.stop()

    def start(self):
        """
        starts prediction and pn websocket processes
        """
        self.active = True

        self.predict_proc = multiprocessing.Process(
            target=PredictWorker,
            args=(
                self.plugin._settings.get(["device_id"]),
                self.plugin._settings.get(["device_cloudiot_name"]),
                self.plugin._settings.get(["user_id"]),
                self.snapshot_url,
                self.calibration,
                self.octo_ws_queue,
                self.pn_ws_queue,
                self.telemetry_queue,
            ),
            daemon=True,
        )
        self.predict_proc.start()

        auth_token = self.plugin._settings.get(["auth_token"])
        ws_url = self.plugin._settings.get(["ws_url"])
        api_url = self.plugin._settings.get(["api_url"])

        self.plugin.rest_client = RestAPIClient(auth_token=auth_token, api_url=api_url)

        self.pn_ws_proc = multiprocessing.Process(
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
        while True:
            if self.active:
                viz_bytes = self.octo_ws_queue.get(block=True)
                self.plugin._event_bus.fire(
                    Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE,
                    payload={"image": base64.b64encode(viz_bytes)},
                )

    def _get_print_job_metadata(self):
        return dict(
            printer_data=self.plugin._printer.get_current_data(),
            printer_profile_data=self.plugin._printer_profile_manager.get_current_or_default(),
            temperatures=self.plugin._printer.get_current_temperatures(),
            printer_profile_id=self.shared.printer_profile_id,
            print_job_id=self.shared.print_job_id,
        )

    def _get_metadata(self):
        return dict(
            created_dt=datetime.now(pytz.timezone("America/Los_Angeles")),
            plugin_version=self.plugin._plugin_version,
            octoprint_version=octoprint.util.version.get_octoprint_version_string(),
            platform=platform.platform(),
            environment=self._environment,
        )

    async def _handle_print_start(self, event_type, event_data):

        try:
            printer_profile = (
                await self.plugin.rest_client.update_or_create_printer_profile(
                    event_data
                )
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.plugin.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path
            )

            print_job = await self.plugin.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id
            )

            self.shared.print_job_id = print_job.id

        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        self.start()
