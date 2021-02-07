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
import os
import re
import threading
import uuid

import octoprint.filemanager
from octoprint.events import Events
from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS
from octoprint_nanny.workers import MultiWorkerMixin
from octoprint_nanny.exceptions import PluginSettingsRequired

from octoprint_nanny.clients.honeycomb import HoneycombTracer
import beeline


Events.PRINT_PROGRESS = "PrintProgress"


class WorkerManager(MultiWorkerMixin):
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
            Events.PRINT_STARTED: self.on_print_start,
            Events.PRINT_FAILED: self.stop_monitoring,
            Events.PRINT_DONE: self.stop_monitoring,
            Events.PRINT_CANCELLING: self.stop_monitoring,
            Events.PRINT_CANCELLED: self.stop_monitoring,
            Events.PRINT_PAUSED: self.stop_monitoring,
            Events.PRINT_RESUMED: self.stop_monitoring,
            Events.SHUTDOWN: self.shutdown,
        }

        self._monitoring_halt = None

        self.event_loop_thread = threading.Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))
        self.loop = loop
        return loop.run_forever()

    @beeline.traced("WorkerManager.init_worker_threads")
    def init_worker_threads(self):
        self._thread_halt = threading.Event()

        self.telemetry_worker_thread = threading.Thread(target=self._telemetry_worker)
        self.telemetry_worker_thread.daemon = True

        # daemonized thread for MQTT worker thread
        self.mqtt_worker_thread = threading.Thread(target=self._mqtt_worker)
        self.mqtt_worker_thread.daemon = True

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

    @beeline.traced("WorkerManager.stop_worker_threads")
    def stop_worker_threads(self):
        logger.warning("Setting halt signal for telemetry worker threads")
        self._thread_halt.set()
        self.plugin._event_bus.fire(Events.PLUGIN_OCTOPRINT_NANNY_WORKER_STOP)
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

        logger.info("Waiting for WorkerManager.remote_control_worker_thread to drain")
        self.remote_control_queue.put_nowait({"event_type": "halt"})
        self.remote_control_worker_thread.join(timeout=10)

        logger.info("Waiting for WorkerManager.telemetry_worker_thread to drain")
        self.telemetry_worker_thread.join(timeout=10)
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
        self.stop_worker_threads()
        self.reset_device_settings_state()
        self.init_worker_threads()
        self.start_worker_threads()

    @beeline.traced("WorkerManager.apply_auth")
    def apply_auth(self):
        logger.info("Resetting WorkerManager user auth state")
        self.reset_rest_client_state()

    @beeline.traced("WorkerManager.apply_monitoring_settings")
    def apply_monitoring_settings(self):
        self.reset_monitoring_settings()
        logger.info(
            "Stopping any existing monitoring processes to apply new calibration"
        )
        self.stop_monitoring()
        if self.monitoring_active:
            logger.info(
                "Monitoring was active when new calibration was applied. Re-initializing monitoring processes"
            )
            self.start_monitoring()

    @beeline.traced("WorkerManager._mqtt_worker")
    def _mqtt_worker(self):
        try:
            return self.mqtt_client.run(self._thread_halt)
        except PluginSettingsRequired:
            pass
        logger.warning("WorkerManager._mqtt_worker exiting")

    @beeline.traced("WorkerManager._telemetry_worker")
    def _telemetry_worker(self):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))

        return loop.run_until_complete(
            asyncio.ensure_future(self._telemetry_queue_send_loop_forever())
        )

    @beeline.traced("WorkerManager._remote_control_worker")
    def _remote_control_worker(self):
        self.remote_control_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.remote_control_loop)
        self.remote_control_loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )

        return self.remote_control_loop.run_until_complete(
            asyncio.ensure_future(self._remote_control_receive_loop_forever())
        )

    @beeline.traced("WorkerManager._publish_bounding_box_telemetry")
    async def _publish_bounding_box_telemetry(self, event):
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

    @beeline.traced("WorkerManager.on_print_start")
    async def on_print_start(self, event_type, event_data, **kwargs):
        logger.info(f"on_print_start called for {event_type} with data {event_data}")
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
            logger.error(f"on_print_start API called failed {e}", exc_info=True)
            return

        if self.plugin.get_setting("auto_start"):
            logger.info("Print Nanny monitoring is set to auto-start")
            self.start_monitoring()
