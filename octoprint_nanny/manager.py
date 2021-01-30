from datetime import datetime
from time import sleep
import aiohttp
import aioprocessing
import asyncio
import base64
import concurrent
import inspect
import io
import logging
import multiprocessing
import platform
import pytz
import re
import threading
import uuid

import octoprint.filemanager
from octoprint.events import Events
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

        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
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
        self._auth_token = None
        self._calibration = None
        self._device_cloudiot_name = None
        self._device_id = None
        self._device_info = None
        self._device_serial = None
        self._monitoring_frames_per_minute = None
        self._snapshot_url = None
        self._user_id = None
        self._ws_url = None
        self._monitoring_halt = None
        self.init_worker_threads()

    @beeline.traced("WorkerManager.init_monitoring_threads")
    def init_monitoring_threads(self):
        self._monitoring_halt = threading.Event()

        self.predict_worker = PredictWorker(
            self.snapshot_url,
            self.calibration,
            self.octo_ws_queue,
            self.pn_ws_queue,
            self.telemetry_queue,
            self.monitoring_frames_per_minute,
            self._monitoring_halt,
            self._get_metadata(),
        )

        self.predict_worker_thread = threading.Thread(target=self.predict_worker.run)
        self.predict_worker_thread.daemon = True

        self.websocket_worker = WebSocketWorker(
            self.ws_url,
            self.auth_token,
            self.pn_ws_queue,
            self.shared.print_job_id,
            self.device_serial,
            self._monitoring_halt,
        )
        self.pn_ws_thread = threading.Thread(target=self.websocket_worker.run)
        self.pn_ws_thread.daemon = True

    @beeline.traced("WorkerManager.init_worker_threads")
    def init_worker_threads(self):
        self._thread_halt = threading.Event()

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

    @beeline.traced("WorkerManager.start_monitoring_threads")
    def start_monitoring_threads(self):
        self.predict_worker_thread.start()
        self.pn_ws_thread.start()

    @beeline.traced("WorkerManager.start_worker_threads")
    def start_worker_threads(self):
        self.mqtt_worker_thread.start()
        self.octo_ws_thread.start()
        self.telemetry_worker_thread.start()
        self.remote_control_worker_thread.start()
        while self.loop is None:
            logger.warning("Waiting for event loop to be set and exposed")
            sleep(1)

    @beeline.traced("WorkerManager.stop_monitoring_threads")
    def stop_monitoring_threads(self):
        logger.warning("Setting halt signal for monitoring worker threads")
        if self._monitoring_halt is not None:
            self._monitoring_halt.set()
            logger.info("Waiting for WorkerManager.predict_worker_thread to drain")
            self.predict_worker_thread.join()

            logger.info("Waiting for WorkerManger.pn_ws_thread to drain")
            self.pn_ws_thread.join()

    @beeline.traced("WorkerManager.stop_worker_threads")
    def stop_worker_threads(self):
        logger.warning("Setting halt signal for telemetry worker threads")
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
        self.remote_control_worker_thread.join()
        self.remote_control_loop.close()

        logger.info("Waiting for WorkerManager.octo_ws_thread to drain")
        self.octo_ws_thread.join()

        logger.info("Waiting for WorkerManager.telemetry_worker_thread to drain")
        self.telemetry_worker_thread.join()
        self.loop.close()

        logger.info("Finished halting WorkerManager threads")

    @property
    def device_info(self):
        if self._device_info is None:
            self._device_info = self.plugin._get_device_info()
        return self._device_info

    @property
    def api_url(self):
        return self.plugin._settings.get(["api_url"])

    @property
    def auth_token(self):
        if self._auth_token is None:
            self._auth_token = self.plugin._settings.get(["auth_token"])
        return self._auth_token

    @property
    def ws_url(self):
        if self._ws_url is None:
            self._ws_url = self.plugin._settings.get(["ws_url"])
        return self._ws_url

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
    def monitoring_frames_per_minute(self):
        if self._monitoring_frames_per_minute is None:
            self._monitoring_frames_per_minute = self.plugin._settings.get(
                ["monitoring_frames_per_minute"]
            )
        return self._monitoring_frames_per_minute

    @property
    def rest_client(self):
        logger.info(f"RestAPIClient initialized with api_url={self.api_url}")
        return RestAPIClient(auth_token=self.auth_token, api_url=self.api_url)

    @beeline.traced("WorkerManager._register_plugin_event_handlers")
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
        self._honeycomb_tracer.add_global_context(self._get_metadata())
        # register plugin event handlers
        self._register_plugin_event_handlers()
        self.start_worker_threads()

    @beeline.traced("WorkerManager.on_snapshot")
    def on_snapshot(self, *args, **kwargs):
        logger.info(f"WorkerManager.on_snapshot called with {args} {kwargs}")

    @beeline.traced("WorkerManager.apply_device_registration")
    def apply_device_registration(self):
        self._device_cloudiot_name = None
        self._device_id = None
        logger.info("Halting worker threads to apply new device registration")
        self.stop_worker_threads()
        self.init_worker_threads()
        self.start_worker_threads()

    @beeline.traced("WorkerManager.apply_auth")
    def apply_auth(self):
        self._user_id = None
        self._auth_token = None
        logger.info("Halting worker threads to apply new auth settings")
        self.stop_worker_threads()
        self.init_worker_threads()
        self.start_worker_threads()

    @beeline.traced("WorkerManager._reset_monitoring_settings")
    def _reset_monitoring_settings(self):
        self._calibration = None
        self._monitoring_frames_per_minute = None

    @beeline.traced("WorkerManager.apply_monitoring_settings")
    def apply_monitoring_settings(self):
        self._reset_monitoring_settings()
        logger.info(
            "Stopping any existing monitoring processes to apply new calibration"
        )
        self.stop_monitoring()
        if self.monitoring_active:
            logger.info(
                "Monitoring was active when new calibration was applied. Re-initializing monitoring processes"
            )
            self.start_monitoring()

    @beeline.traced("WorkerManager._on_monitoring_start")
    async def _on_monitoring_start(self, event_type, event_data):
        await self.rest_client.update_octoprint_device(
            self.device_id, monitoring_active=True
        )

    @beeline.traced("WorkerManager._on_monitoring_stop")
    async def _on_monitoring_stop(self, event_type, event_data):
        await self.rest_client.update_octoprint_device(
            self.device_id, monitoring_active=False
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

    @beeline.traced("WorkerManager._publish_bounding_box_telemetry")
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

    @beeline.traced("WorkerManager._publish_octoprint_event_telemetry")
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
            span = self._honeycomb_tracer.start_span(
                {"name": "WorkerManager.remote_control_queue.coro_get"}
            )
            event = await self.remote_control_queue.coro_get()
            self._honeycomb_tracer.add_context(dict(event=event))
            self._honeycomb_tracer.finish_span(span)

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

    @beeline.traced("WorkerManager._remote_control_snapshot")
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
            trace = self._honeycomb_tracer.start_trace()
            span = self._honeycomb_tracer.start_span(
                {"name": "WorkerManager.telemetry_queue.coro_get"}
            )

            event = await self.telemetry_queue.coro_get()
            self._honeycomb_tracer.add_context(dict(event=event))
            self._honeycomb_tracer.finish_span(span)

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
        self.stop_monitoring_threads()

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
        self.init_monitoring_threads()
        self.start_monitoring_threads()

    def _octo_ws_queue_worker(self):
        """
        Child process to -> Octoprint event bus relay
        """
        logger.info("Started _octo_ws_queue_worker")
        while not self._thread_halt.is_set():
            if self.monitoring_active:
                trace = self._honeycomb_tracer.start_trace()
                span = self._honeycomb_tracer.start_span(
                    {"name": "WorkerManager.octo_ws_queue.get"}
                )
                viz_bytes = self.octo_ws_queue.get(block=True)
                self._honeycomb_tracer.finish_span(span)
                self.plugin._event_bus.fire(
                    Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE,
                    payload={"image": base64.b64encode(viz_bytes)},
                )
                self._honeycomb_tracer.finish_trace(trace)

    @beeline.traced("WorkerManager._get_print_job_metadata")
    def _get_print_job_metadata(self):
        return dict(
            printer_data=self.plugin._printer.get_current_data(),
            printer_profile_data=self.plugin._printer_profile_manager.get_current_or_default(),
            temperatures=self.plugin._printer.get_current_temperatures(),
            printer_profile_id=self.shared.printer_profile_id,
            print_job_id=self.shared.print_job_id,
        )

    def _get_metadata(self):
        metadata = dict(
            created_dt=datetime.now(pytz.timezone("America/Los_Angeles")),
            environment=self._environment,
        )
        metadata.update(self.device_info)
        return metadata

    @beeline.traced("WorkerManager._handle_print_start")
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
