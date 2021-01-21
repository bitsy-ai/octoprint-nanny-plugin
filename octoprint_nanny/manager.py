import aioprocessing
import asyncio
import base64
import re
from datetime import datetime
import platform
import uuid
import pytz
from time import sleep
import io
import aiohttp

import logging

import aiohttp

import multiprocessing
import octoprint.filemanager
from octoprint.events import Events
import inspect
import threading

from octoprint_nanny.clients.websocket import WebSocketWorker
from octoprint_nanny.clients.rest import RestAPIClient, CLIENT_EXCEPTIONS
from octoprint_nanny.clients.mqtt import MQTTClient
from octoprint_nanny.predictor import (
    PredictWorker,
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)
from octoprint_nanny.clients.honeycomb import HoneycombTracer
import print_nanny_client
import beeline

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.manager")

Events.PRINT_PROGRESS = "PrintProgress"


class WorkerManager:
    """
    Manages PredictWorker, WebsocketWorker, RestWorker processes
    """

    MAX_BACKOFF = 256
    BACKOFF = 2

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

    # do not warn when the following events are skipped on telemetry update
    MUTED_EVENTS = [Events.Z_CHANGE]

    def __init__(self, plugin):

        self._honeycomb_tracer = HoneycombTracer(service_name="worker_manager_main")
        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        # proxy objects
        self.shared.printer_profile_id = None
        self.shared.print_job_id = None
        self.shared.calibration = None

        self.mqtt_client = None
        self.monitoring_active = False

        # outbound telemetry to GCP MQTT bridge
        self.telemetry_queue = self.manager.AioQueue()
        # images streamed to octoprint front-end over websocket
        self.octo_ws_queue = self.manager.AioQueue()
        # images streamed to webapp asgi over websocket
        self.pn_ws_queue = self.manager.AioQueue()
        # inbound commands from MQTT
        self.remote_control_queue = self.manager.AioQueue()

        self._local_event_handlers = {
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self.stop_monitoring,
            Events.PRINT_DONE: self.stop_monitoring,
            Events.PRINT_CANCELLING: self.stop_monitoring,
            Events.PRINT_CANCELLED: self.stop_monitoring,
            Events.PRINT_PAUSED: self.stop_monitoring,
            Events.PRINT_RESUMED: self.stop_monitoring,
        }

        self._remote_control_event_handlers = {
            "StartMonitoring": self.start_monitoring,
            "StopMonitoring": self.stop_monitoring,
            "Snapshot": self.on_snapshot,
        }

        self._environment = {}

        self.telemetry_events = None
        self._user_id = None
        self._device_id = None
        self._calibration = None
        self._snapshot_url = None
        self._device_cloudiot_name = None
        self._device_serial = None
        self._auth_token = None

        self.predict_proc = None
        self.pn_ws_proc = None

        self.init_worker_threads()

    def init_worker_threads(self):
        self._thread_halt = threading.Event()
        # daemonized thread for outbount telemetry event handlers

        self.telemetry_worker_thread = threading.Thread(target=self._telemetry_worker)
        self.telemetry_worker_thread.daemon = True

        # daemonized thread for sending annotated image frames to Octoprint's UI
        self.octo_ws_thread = threading.Thread(target=self._octo_ws_queue_worker)
        self.octo_ws_thread.daemon = True

        # daemonized thread for MQTT worker thread
        self.mqtt_worker_thread = threading.Thread(target=self._mqtt_worker)
        self.mqtt_worker_thread.daemon = True

        # daemonized thread for handling inbound commands received via MQTT
        self.remote_control_worker_thread = threading.Thread(
            target=self._remote_control_worker
        )
        self.remote_control_worker_thread.daemon = True

        self.loop = None

    def start_worker_threads(self):
        self.mqtt_worker_thread.start()
        self.octo_ws_thread.start()
        self.telemetry_worker_thread.start()
        self.remote_control_worker_thread.start()
        while self.loop is None:
            logger.warning("Waiting for event loop to be set and exposed")
            sleep(1)

    def stop_worker_threads(self):
        logger.warning("Setting halt signal for worker threads")
        self._thread_halt.set()

        logger.info(
            "Waiting for WorkerMangager.mqtt_client network connection to close"
        )

        if self.mqtt_client is not None:
            while self.mqtt_client.client.is_connected():
                self.mqtt_client.client.disconnect()
            logger.info("Waiting for WorkerManager.mqtt_worker_thread to drain")
            self.mqtt_client.client.disconnect()
            self.mqtt_client.client.loop_stop()
        self.mqtt_worker_thread.join()

        logger.info("Waiting for WorkerManager.remote_control_worker_thread to drain")
        self.remote_control_queue.put({"msg": "halt"})
        self.remote_control_worker_thread.join()
        self.remote_control_loop.close()

        logger.info("Waiting for WorkerManager.octo_ws_thread to drain")
        self.octo_ws_thread.join()

        logger.info("Waiting for WorkerManager.telemetry_worker_thread to drain")
        self.telemetry_queue.put({"msg": "halt"})
        self.telemetry_worker_thread.join()
        self.loop.close()

        logger.info("Finished halting WorkerManager threads")

    @property
    def api_url(self):
        return self.plugin._settings.get(["api_url"])

    @property
    def auth_token(self):
        if self._auth_token is None:
            self._auth_token = self.plugin._settings.get(["auth_token"])
        return self._auth_token

    @property
    def snapshot_url(self):
        if self._snapshot_url is None:
            self._snapshot_url = self.plugin._settings.get(["snapshot_url"])
        return self._snapshot_url

    @property
    def device_cloudiot_name(self):
        if self._device_cloudiot_name is None:
            self._device_cloudiot_name = self.plugin._settings.get(
                ["device_cloudiot_name"]
            )
        return self._device_cloudiot_name

    @property
    def device_id(self):
        if self._device_id is None:
            self._device_id = self.plugin._settings.get(["device_id"])
        return self._device_id

    @property
    def device_serial(self):
        if self._device_id is None:
            self._device_id = self.plugin._settings.get(["device_serial"])
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
        logger.info(f"RestAPIClient initialized with api_url={self.api_url}")
        return RestAPIClient(auth_token=self.auth_token, api_url=self.api_url)

    def _register_plugin_event_handlers(self):
        """
        Events.PLUGIN_OCTOPRINT_NANNY* events are not available on Events until plugin is fully initialized
        """
        self._local_event_handlers.update(
            {
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self._on_monitoring_start,
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self._on_monitoring_stop,
            }
        )

    def reset_backoff(self):
        self.BACKOFF = 2

    @beeline.traced("WorkerManager.on_settings_initialized")
    def on_settings_initialized(self):
        # register plugin event handlers
        self._register_plugin_event_handlers()
        self.start_worker_threads()

    def on_snapshot(self, *args, **kwargs):
        logger.info(f"WorkerManager.on_snapshot called with {args} {kwargs}")

    def apply_device_registration(self):
        self._device_cloudiot_name = None
        self._device_id = None
        logger.info("Halting worker threads to apply new device registration")
        self.stop_worker_threads()
        self.init_worker_threads()
        self.start_worker_threads()

    def apply_auth(self):
        self._user_id = None
        self._auth_token = None
        logger.info("Halting worker threads to apply new auth settings")
        self.stop_worker_threads()
        self.init_worker_threads()
        self.start_worker_threads()

    @beeline.traced("WorkerManager.apply_calibration")
    def apply_calibration(self):
        self._calibration = None
        logger.info(
            "Stopping any existing monitoring processes to apply new calibration"
        )
        self.stop_monitoring()
        if self.monitoring_active:
            logger.info(
                "Monitoring was active when new calibration was applied. Re-initializing monitoring processes"
            )
            self.start_monitoring()

    async def _on_monitoring_start(self, event_type, event_data):
        await self.rest_client.update_octoprint_device(
            self.device_id, monitoring_acitve=True
        )

    async def _on_monitoring_stop(self, event_type, event_data):
        await self.rest_client.update_octoprint_device(
            self.device_id, monitoring_acitve=False
        )

    def _mqtt_worker(self):
        private_key = self.plugin._settings.get(["device_private_key"])
        device_id = self.plugin._settings.get(["device_cloudiot_name"])
        gcp_root_ca = self.plugin._settings.get(["gcp_root_ca"])
        while not self._thread_halt.is_set():
            if private_key is None or device_id is None or gcp_root_ca is None:
                logger.warning(
                    f"Waiting {self.BACKOFF} seconds to initialize mqtt client, missing device registration private_key={private_key} device_id={device_id} gcp_root_ca={gcp_root_ca}"
                )
                sleep(self.BACKOFF)
                if self.BACKOFF < self.MAX_BACKOFF:
                    self.BACKOFF = self.BACKOFF ** 2
                continue
            break
        self.mqtt_client = MQTTClient(
            device_id=device_id,
            private_key_file=private_key,
            ca_certs=gcp_root_ca,
            remote_control_queue=self.remote_control_queue,
        )
        logger.info(f"Initialized mqtt client with id {self.mqtt_client.client_id}")
        ###
        # MQTT bridge available
        ###
        return self.mqtt_client.run(self._thread_halt)

    def _telemetry_worker(self):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        return self.loop.run_until_complete(
            asyncio.ensure_future(self._telemetry_queue_send_loop())
        )

    def _remote_control_worker(self):
        self.remote_control_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.remote_control_loop)
        return self.remote_control_loop.run_until_complete(
            asyncio.ensure_future(self._remote_control_receive_loop())
        )

    async def _publish_bounding_box_telemetry(self, event):
        logger.debug(f"_publish_bounding_box_telemetry {event}")
        event.update(
            dict(
                user_id=self.user_id,
                device_id=self.device_id,
                device_cloudiot_name=self.device_cloudiot_name,
            )
        )
        self.mqtt_client.publish_bounding_boxes(event)

    async def _publish_octoprint_event_telemetry(self, event):
        event_type = event.get("event_type")
        logger.info(f"_publish_octoprint_event_telemetry {event}")
        event.update(
            dict(
                user_id=self.user_id,
                device_id=self.device_id,
                device_cloudiot_name=self.device_cloudiot_name,
            )
        )
        event.update(self._get_metadata())

        if event_type in self.PRINT_JOB_EVENTS:
            event.update(self._get_print_job_metadata())
        self.mqtt_client.publish_octoprint_event(event)

    async def _remote_control_receive_loop(self):
        logger.info("Started _remote_control_receive_loop")
        while not self._thread_halt.is_set():

            if self.auth_token is None:
                logger.warning(
                    f"auth_token not saved to plugin settings, waiting {self.BACKOFF} seconds"
                )
                await asyncio.sleep(self.BACKOFF)
                if self.BACKOFF < self.MAX_BACKOFF:
                    self.BACKOFF = self.BACKOFF ** 2
                continue

            trace = self._honeycomb_tracer.start_trace()

            event = await self.remote_control_queue.coro_get()
            logging.info(f"Received event in _remote_control_receive_loop {event}")

            command = event.get("command")
            if command is None:
                logger.warning("Ignoring received message where command=None")
                continue

            command_id = event.get("remote_control_command_id")

            await self._remote_control_snapshot(command_id)

            metadata = self._get_metadata()
            await self.rest_client.update_remote_control_command(
                command_id, received=True, metadata=metadata
            )

            handler_fn = self._remote_control_event_handlers.get(command)

            logger.info(
                f"Got handler_fn={handler_fn} from WorkerManager._remote_control_event_handlers for command={command}"
            )

            if handler_fn:
                try:
                    if inspect.isawaitable(handler_fn):
                        await handler_fn(event=event, event_type=command)
                    else:
                        handler_fn(event=event, event_type=command)

                    metadata = self._get_metadata()
                    # set success state
                    await self.rest_client.update_remote_control_command(
                        command_id,
                        success=True,
                        metadata=metadata,
                    )
                except Exception as e:
                    logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                    metadata = self._get_metadata()
                    await self.rest_client.update_remote_control_command(
                        command_id,
                        success=False,
                        metadata=metadata,
                    )

            self._honeycomb_tracer.finish_trace(trace)

    async def _remote_control_snapshot(self, command_id):
        async with aiohttp.ClientSession() as session:
            res = await session.get(self.snapshot_url)
            snapshot_io = io.BytesIO(await res.read())

        return await self.rest_client.create_snapshot(
            image=snapshot_io, command=command_id
        )

    async def _telemetry_queue_send_loop(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info("Started _telemetry_queue_send_loop")

        self.BACKOFF

        while not self._thread_halt.is_set():

            if self.auth_token is None:
                logger.warning(
                    f"auth_token not saved to plugin settings, waiting {self.BACKOFF} seconds"
                )
                await asyncio.sleep(self.BACKOFF)
                if self.BACKOFF < self.MAX_BACKOFF:
                    self.BACKOFF = self.BACKOFF ** 2
                continue

            if self.telemetry_events is None:
                try:
                    self.telemetry_events = (
                        await self.rest_client.get_telemetry_events()
                    )
                except CLIENT_EXCEPTIONS as e:
                    await asyncio.sleep(self.BACKOFF)
                    if self.BACKOFF < self.MAX_BACKOFF:
                        self.BACKOFF = self.BACKOFF ** 2

            ###
            # Rest API available
            ###
            if self.mqtt_client is None:
                logger.warning(
                    f"Waiting {self.BACKOFF} seconds for mqtt client to be available"
                )
                await asyncio.sleep(self.BACKOFF)
                if self.BACKOFF < self.MAX_BACKOFF:
                    self.BACKOFF = self.BACKOFF ** 2
                continue
            ###
            # mqtt client available
            ##

            event = await self.telemetry_queue.coro_get()
            event_type = event.get("event_type")
            if event_type is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event=event
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
            if self.telemetry_events is None or event_type not in self.telemetry_events:
                # supress warnings about PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE event; this is for octoprint front-end only
                if event_type == Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE:
                    pass
                elif event_type not in self.MUTED_EVENTS:
                    logger.warning(f"Discarding {event_type} with payload {event}")
                continue
            # publish to octoprint-events telemetry topic
            else:
                await self._publish_octoprint_event_telemetry(event)

            trace = self._honeycomb_tracer.start_trace()

            # run local handler fn
            handler_fn = self._local_event_handlers.get(event["event_type"])

            if handler_fn:
                try:
                    if inspect.isawaitable(handler_fn):
                        await handler_fn(**event)
                    else:
                        handler_fn(**event)
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f"Error running {handler_fn } \n {e}", exc_info=True)

            self._honeycomb_tracer.finish_trace(trace)

    @beeline.traced("WorkerManager.stop_monitoring")
    def stop_monitoring(self, event_type=None, **kwargs):
        """
        joins and terminates dedicated prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.stop_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.monitoring_active = False
        self.plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP,
        )
        if self.predict_proc:
            logger.info("Terminating predict process")
            self.predict_proc.terminate()
            self.predict_proc.join(30)
            if self.predict_proc.is_alive():
                self.predict_proc.kill()
            self.predict_proc.close()
            self.predict_proc = None

        if self.pn_ws_proc:
            logger.info("Terminating websocket process")
            self.pn_ws_proc.terminate()
            self.pn_ws_proc.join(30)
            if self.pn_ws_proc.is_alive():
                self.pn_ws_proc.kill()
            self.pn_ws_proc.close()
            self.pn_ws_proc = None

    @beeline.traced("WorkerManager.shutdown")
    def shutdown(self):
        self.stop_monitoring()
        self.stop_worker_threads()
        self._honeycomb_tracer.on_shutdown()

    @beeline.traced("WorkerManager.start_monitoring")
    def start_monitoring(self, event_type=None, **kwargs):
        """
        starts prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.start_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.monitoring_active = True
        self.plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START,
        )

        if self.predict_proc is None:
            self.predict_proc = multiprocessing.Process(
                target=PredictWorker,
                args=(
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

        if self.pn_ws_proc is None:
            self.pn_ws_proc = multiprocessing.Process(
                target=WebSocketWorker,
                args=(
                    ws_url,
                    auth_token,
                    self.pn_ws_queue,
                    self.shared.print_job_id,
                    self.device_serial,
                ),
                daemon=True,
            )
            self.pn_ws_proc.start()

    def _octo_ws_queue_worker(self):
        """
        Child process to -> Octoprint event bus relay
        """
        logger.info("Started _octo_ws_queue_worker")
        while not self._thread_halt.is_set():
            if self.monitoring_active:
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

    async def _handle_print_start(self, event_type, event_data, **kwargs):
        logger.info(
            f"_handle_print_start called for {event_type} with data {event_data}"
        )
        try:
            current_profile = (
                self.plugin._printer_profile_manager.get_current_or_default()
            )
            printer_profile = (
                await self.plugin.rest_client.update_or_create_printer_profile(
                    current_profile, self.device_id
                )
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.plugin.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path, self.device_id
            )

            print_job = await self.plugin.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id, self.device_id
            )

            self.shared.print_job_id = print_job.id

        except CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        if self.plugin._settings.get(["auto_start"]):
            logger.info("Print Nanny monitoring is set to auto-start")
            self.start_monitoring()
