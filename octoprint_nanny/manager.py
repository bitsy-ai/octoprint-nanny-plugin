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
from octoprint_nanny.clients.rest import RestAPIClient, API_CLIENT_EXCEPTIONS
from octoprint_nanny.clients.mqtt import MQTTClient
from octoprint_nanny.predictor import (
    PredictWorker,
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)
from octoprint_nanny.exceptions import PluginSettingsRequired

from octoprint_nanny.clients.honeycomb import HoneycombTracer
import print_nanny_client
import beeline

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.manager")

Events.PRINT_PROGRESS = "PrintProgress"


class PluginSettingsMemoizeMixin:
    """
    Convenience methods/properties for accessing OctoPrint plugin settings and computed metadata
    """

    def __init__(self, plugin):
        self.plugin = plugin

        # stateful clients and computed settings that require re-initialization when settings change
        self._calibration = None
        self._mqtt_client = None
        self._telemetry_events = None
        self._device_info = None
        self._rest_client = None

        self.environment = {}

    @beeline.traced("PluginSettingsMemoize._reset_device_settings_state")
    @beeline.traced_thread
    def reset_device_settings_state(self):
        self._mqtt_client = None
        self._device_info = None

    @beeline.traced(name="PluginSettingsMemoize.get_device_metadata")
    @beeline.traced_thread
    def get_device_metadata(self):
        metadata = dict(
            created_dt=datetime.now(pytz.timezone("America/Los_Angeles")),
            environment=self.environment,
        )
        metadata.update(self.device_info)
        return metadata

    @beeline.traced(name="PluginSettingsMemoize.get_print_job_metadata")
    @beeline.traced_thread
    def get_print_job_metadata(self):
        return dict(
            printer_data=self.plugin._printer.get_current_data(),
            printer_profile_data=self.plugin._printer_profile_manager.get_current_or_default(),
            temperatures=self.plugin._printer.get_current_temperatures(),
            printer_profile_id=self.shared.printer_profile_id,
            print_job_id=self.shared.print_job_id,
        )

    @beeline.traced(name="PluginSettingsMemoize.on_environment_detected")
    @beeline.traced_thread
    def on_environment_detected(self, environment):
        self.environment = environment

    @property
    def device_cloudiot_name(self):
        return self.plugin.get_setting("device_cloudiot_name")

    @property
    def device_id(self):
        return self.plugin.get_setting("device_id")

    @property
    def device_info(self):
        if self._device_info is None:
            self._device_info = self.plugin.get_device_info()
        return self._device_info

    @property
    def device_serial(self):
        return self.plugin.get_setting("device_serial")

    @property
    def device_private_key(self):
        return self.plugin.get_setting("device_private_key")

    @property
    def device_public_key(self):
        return self.plugin.get_setting("device_public_key")

    @property
    def gcp_root_ca(self):
        return self.plugin.get_setting("gcp_root_ca")

    @property
    def api_url(self):
        return self.plugin.get_setting("api_url")

    @property
    def auth_token(self):
        return self.plugin.get_setting("auth_token")

    @property
    def ws_url(self):
        return self.plugin.get_setting("ws_url")

    @property
    def snapshot_url(self):
        return self.plugin.get_setting("snapshot_url")

    @property
    def user_id(self):
        return self.plugin.get_setting("user_id")

    @property
    def calibration(self):
        if self._calibration is None:
            self._calibration = PredictWorker.calc_calibration(
                self.plugin.get_setting("calibrate_x0"),
                self.plugin.get_setting("calibrate_y0"),
                self.plugin.get_setting("calibrate_x1"),
                self.plugin.get_setting("calibrate_y1"),
            )
        return self._calibration

    @property
    def monitoring_frames_per_minute(self):
        return self.plugin.get_setting("monitoring_frames_per_minute")

    @property
    def rest_client(self):
        if self.auth_token is None:
            raise PluginSettingsRequired(f"auth_token is not set")
        if self._rest_client is None:
            self._rest_client = RestAPIClient(
                auth_token=self.auth_token, api_url=self.api_url
            )
            logger.info(f"RestAPIClient initialized with api_url={self.api_url}")
        return self._rest_client

    def test_mqtt_settings(self):
        if self.device_id is None or self.device_private_key is None:
            raise PluginSettingsRequired(
                f"Received None for device_id={self.device_id} or private_key_file={self.device_private_key}"
            )
        return True

    @property
    def mqtt_client(self):
        self.test_mqtt_settings()
        if self._mqtt_client is None:
            self._mqtt_client = MQTTClient(
                device_id=self.device_id,
                private_key_file=self.device_private_key,
                ca_certs=self.gcp_root_ca,
                remote_control_queue=self.remote_control_queue,
                trace_context=self.get_device_metadata(),
            )
        return self._mqtt_client

    @property
    def telemetry_events(self):
        if self.auth_token is None:
            raise PluginSettingsRequired(f"auth_token is not set")
        if self._telemetry_events is None:
            loop = asyncio.get_event_loop()
            self.telemetry_events = asyncio.run_coroutine_threadsafe(
                self.rest_client.get_telemetry_events(), loop
            ).result()
        return self._telemetry_events

    def event_in_tracked_telemetry(self, event_type):
        return event_type in self.telemetry_events


class WorkerManager(PluginSettingsMemoizeMixin):
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
    MUTED_EVENTS = [Events.Z_CHANGE, "plugin_octoprint_nanny_predict_done"]

    EVENT_PREFIX = "plugin_octoprint_nanny_"

    def __init__(self, plugin):

        super().__init__(plugin)
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        # proxy objects
        self.shared.printer_profile_id = None
        self.shared.print_job_id = None
        self.shared.calibration = None

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
            Events.SHUTDOWN: self.shutdown,
        }

        self._remote_control_event_handlers = {}
        self._monitoring_halt = None

        self.event_loop_thread = threading.Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()

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
            self.plugin._event_bus,
            trace_context=self.get_device_metadata(),
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
            trace_context=self.get_device_metadata(),
        )
        self.pn_ws_thread = threading.Thread(target=self.websocket_worker.run)
        self.pn_ws_thread.daemon = True

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))

        self.loop = loop
        return loop.run_forever()

    @beeline.traced("WorkerManager.init_mqtt_worker_thread")
    def init_mqtt_worker_thread(self):
        # daemonized thread for MQTT worker thread
        self.mqtt_worker_thread = threading.Thread(target=self._mqtt_worker)
        self.mqtt_worker_thread.daemon = True

    @beeline.traced("WorkerManager.init_worker_threads")
    def init_worker_threads(self):
        self._thread_halt = threading.Event()

        self.init_mqtt_worker_thread()

        self.telemetry_worker_thread = threading.Thread(target=self._telemetry_worker)
        self.telemetry_worker_thread.daemon = True

        # daemonized thread for handling inbound commands received via MQTT
        self.remote_control_worker_thread = threading.Thread(
            target=self._remote_control_worker
        )
        self.remote_control_worker_thread.daemon = True

    @beeline.traced("WorkerManager.start_monitoring_threads")
    def start_monitoring_threads(self):
        self.predict_worker_thread.start()
        self.pn_ws_thread.start()

    @beeline.traced("WorkerManager.start_worker_threads")
    def start_worker_threads(self):
        self.mqtt_worker_thread.start()
        self.telemetry_worker_thread.start()
        self.remote_control_worker_thread.start()

    @beeline.traced("WorkerManager.stop_monitoring_threads")
    def stop_monitoring_threads(self):
        logger.warning("Setting halt signal for monitoring worker threads")
        if self._monitoring_halt is not None:
            self._monitoring_halt.set()
            logger.info("Waiting for WorkerManager.predict_worker_thread to drain")
            self.predict_worker_thread.join()

            logger.info("Waiting for WorkerManger.pn_ws_thread to drain")
            self.pn_ws_thread.join()

    @beeline.traced("WorkerManager.stop_mqtt_worker_thread")
    def stop_mqtt_worker_thread(self):
        logger.info(
            "Waiting for WorkerMangager.mqtt_client network connection to close"
        )

        try:
            while self.mqtt_client.client.is_connected():
                self.mqtt_client.client.disconnect()
            logger.info("Waiting for WorkerManager.mqtt_worker_thread to drain")
            self.mqtt_client.client.disconnect()
            self.mqtt_client.client.loop_stop()
        except PluginSettingsRequired:
            pass
        self.mqtt_worker_thread.join()

    @beeline.traced("WorkerManager.stop_worker_threads")
    def stop_worker_threads(self):
        logger.warning("Setting halt signal for telemetry worker threads")
        self._thread_halt.set()
        self.plugin._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_WORKER_STOP)

        self.stop_mqtt_worker_thread()

        logger.info("Waiting for WorkerManager.remote_control_worker_thread to drain")
        self.remote_control_queue.put_nowait({"event_type": "halt"})
        self.remote_control_worker_thread.join()

        logger.info("Waiting for WorkerManager.telemetry_worker_thread to drain")
        self.telemetry_worker_thread.join()
        logger.info("Finished halting WorkerManager threads")

    @beeline.traced("WorkerManager._register_plugin_event_handlers")
    def _register_plugin_event_handlers(self):
        """
        Events.PLUGIN_OCTOPRINT_NANNY* events are not available on Events until plugin is fully initialized
        """
        self._local_event_handlers.update(
            {
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self.start_monitoring,
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self.stop_monitoring,
            }
        )
        self._remote_control_event_handlers.update(
            {
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self.start_monitoring,
                Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self.stop_monitoring,
                Events.PLUGIN_OCTOPRINT_NANNY_SNAPSHOT: self.on_snapshot,
            }
        )

    @beeline.traced("WorkerManager.on_settings_initialized")
    def on_settings_initialized(self):
        self._honeycomb_tracer.add_global_context(self.get_device_metadata())
        self.init_worker_threads()

        # register plugin event handlers
        self._register_plugin_event_handlers()
        self.start_worker_threads()

    @beeline.traced("WorkerManager.on_snapshot")
    def on_snapshot(self, *args, **kwargs):
        logger.info(f"WorkerManager.on_snapshot called with {args} {kwargs}")

    @beeline.traced("WorkerManager.apply_device_registration")
    def apply_device_registration(self):
        logger.info("Resetting WorkerManager device registration state")
        self.reset_device_settings_state()
        self.stop_mqtt_worker_thread()
        self.init_mqtt_worker_thread()
        self.mqtt_worker_thread.start()

    @beeline.traced("WorkerManager.apply_auth")
    def apply_auth(self):
        logger.info("Resetting WorkerManager user auth state")
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
        try:
            return self.mqtt_client.run(self._thread_halt)
        except PluginSettingsRequired:
            pass

    def _telemetry_worker(self):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            asyncio.ensure_future(self._telemetry_queue_send_loop_forever())
        )

    def _remote_control_worker(self):
        self.remote_control_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.remote_control_loop)

        return self.remote_control_loop.run_until_complete(
            asyncio.ensure_future(self._remote_control_receive_loop_forever())
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
        event.update(self.get_device_metadata())

        if event_type in self.PRINT_JOB_EVENTS:
            event.update(self.get_print_job_metadata())
        self.mqtt_client.publish_octoprint_event(event)

    async def _remote_control_receive_loop_forever(self):
        logger.info("Started _remote_control_receive_loop_forever")
        while not self._thread_halt.is_set():
            try:
                await self._remote_control_receive_loop()
            except PluginSettingsRequired:
                pass
        logger.info("Exiting soon _remote_control_receive_loop_forever")

    @beeline.traced("WorkerManager._remote_control_receive_loop")
    async def _remote_control_receive_loop(self):

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
            return

        command_id = event.get("remote_control_command_id")

        await self._remote_control_snapshot(command_id)

        metadata = self.get_device_metadata()
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

                metadata = self.get_device_metadata()
                # set success state
                await self.rest_client.update_remote_control_command(
                    command_id,
                    success=True,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                metadata = self.get_device_metadata()
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

    @beeline.traced("WorkerManager._telemetry_queue_send_loop")
    async def _telemetry_queue_send_loop(self):
        try:
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
                return

            if event_type == BOUNDING_BOX_PREDICT_EVENT:
                await self._publish_bounding_box_telemetry(event)
                return

            if self.event_in_tracked_telemetry(event_type):
                await self._publish_octoprint_event_telemetry(event)
            else:
                if event_type not in self.MUTED_EVENTS:
                    logger.warning(f"Discarding {event_type} with payload {event}")
                return

            # run local handler fn
            handler_fn = self._local_event_handlers.get(event_type)
            if handler_fn:

                if inspect.isawaitable(handler_fn):
                    await handler_fn(**event)
                else:
                    handler_fn(**event)
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"REST client raised exception {e}", exc_info=True)

    async def _telemetry_queue_send_loop_forever(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info("Started _telemetry_queue_send_loop_forever")
        while not self._thread_halt.is_set():
            try:
                await self._telemetry_queue_send_loop()
            except PluginSettingsRequired as e:
                logger.error(e)
        logging.info("Exiting soon _telemetry_queue_send_loop_forever")

    @beeline.traced("WorkerManager.stop_monitoring")
    def stop_monitoring(self, event_type=None, **kwargs):
        """
        joins and terminates dedicated prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.stop_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.monitoring_active = False

        asyncio.run_coroutine_threadsafe(
            self.rest_client.update_octoprint_device(
                self.device_id, monitoring_active=False
            ),
            self.loop,
        ).result()

        self.stop_monitoring_threads()

    @beeline.traced("WorkerManager.shutdown")
    def shutdown(self):
        self.stop_monitoring()

        asyncio.run_coroutine_threadsafe(
            self.rest_client.update_octoprint_device(
                self.device_id, monitoring_active=False
            ),
            self.loop,
        ).result()

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

        asyncio.run_coroutine_threadsafe(
            self.rest_client.update_octoprint_device(
                self.device_id, monitoring_active=True
            ),
            self.loop,
        ).result()

        self.init_monitoring_threads()
        self.start_monitoring_threads()

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

        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"_handle_print_start API called failed {e}", exc_info=True)
            return

        if self.plugin.get_setting("auto_start"):
            logger.info("Print Nanny monitoring is set to auto-start")
            self.start_monitoring()
