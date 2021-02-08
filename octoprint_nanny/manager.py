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

from octoprint.events import Events
import octoprint.filemanager

from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS


from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.settings import PluginSettingsMemoize
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint_nanny.workers.mqtt import MQTTManager
from octoprint_nanny.workers.monitoring import MonitoringManager
import beeline


Events.PRINT_PROGRESS = "PrintProgress"
logger = logging.getLogger("octoprint.plugins.octoprint_nanny.manager")


class WorkerManager:
    """
    Coordinates MQTTManager and MonitoringManager classes
    """

    def __init__(self, plugin):

        self.event_loop_thread = threading.Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()

        plugin_settings = PluginSettingsMemoize(plugin)
        self.plugin_settings = plugin_settings
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        self.monitoring_active = False

        # images streamed to octoprint front-end over websocket
        octo_ws_queue = self.manager.AioQueue()
        self.octo_ws_queue = octo_ws_queue
        # images streamed to webapp asgi over websocket
        pn_ws_queue = self.manager.AioQueue()
        self.pn_ws_queue = pn_ws_queue

        # outbound telemetry messages to MQTT bridge
        mqtt_send_queue = self.manager.AioQueue()
        self.mqtt_send_queue = mqtt_send_queue
        # inbound MQTT command and config messages from MQTT bridge
        mqtt_receive_queue = self.manager.AioQueue()
        self.mqtt_receive_queue = mqtt_receive_queue

        self.mqtt_manager = MQTTManager(
            mqtt_send_queue, mqtt_receive_queue, plugin_settings, plugin
        )
        self.monitoring_manager = MonitoringManager(
            octo_ws_queue,
            pn_ws_queue,
            mqtt_send_queue,
            plugin_settings,
            self.plugin._event_bus,
        )

        # local callback/handler functions for events published via telemetry queue
        self._mqtt_send_queue_callbacks = {
            Events.PRINT_STARTED: self.on_print_start,
            Events.PRINT_FAILED: self.monitoring_manager.stop,
            Events.PRINT_DONE: self.monitoring_manager.stop,
            Events.PRINT_CANCELLING: self.monitoring_manager.stop,
            Events.PRINT_CANCELLED: self.monitoring_manager.stop,
            Events.PRINT_PAUSED: self.monitoring_manager.stop,
            Events.PRINT_RESUMED: self.monitoring_manager.start,
            Events.SHUTDOWN: self.shutdown,
        }

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))
        self.loop = loop
        return loop.run_forever()

    @beeline.traced()
    def _register_plugin_event_handlers(self):
        """
        Events.PLUGIN_OCTOPRINT_NANNY* events are not available on Events until plugin is fully initialized
        """
        pass
        # self._local_event_handlers.update(
        #     {
        #         Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self.start_monitoring,
        #         Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self.stop_monitoring,
        #     }
        # )
        # self._remote_control_event_handlers.update(
        #     {
        #         Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self.start_monitoring,
        #         Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self.stop_monitoring,
        #     }
        # )

    @beeline.traced()
    def on_settings_initialized(self):
        self._honeycomb_tracer.add_global_context(self.get_device_metadata())
        # self._register_plugin_event_handlers()
        self.mqtt_manager.start()

    @beeline.traced()
    def apply_device_registration(self):
        self.mqtt_manager.stop()
        logger.info("Resetting WorkerManager device registration state")
        self.plugin_settings.reset_device_settings_state()
        self.mqtt_manager.start()

    @beeline.traced()
    def apply_auth(self):
        logger.info("Resetting WorkerManager user auth state")
        self.mqtt_manager.stop()
        self.plugin_settings.reset_rest_client_state()
        self.mqtt_manager.start()

    @beeline.traced()
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

    @beeline.traced()
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

    @beeline.traced()
    async def on_print_start(self, event_type, event_data, **kwargs):
        logger.info(f"on_print_start called for {event_type} with data {event_data}")
        try:
            current_profile = (
                self.plugin._printer_profile_manager.get_current_or_default()
            )
            printer_profile = await self.rest_client.update_or_create_printer_profile(
                current_profile, self.device_id
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = await self.rest_client.update_or_create_gcode_file(
                event_data, gcode_file_path, self.device_id
            )

            print_job = await self.rest_client.create_print_job(
                event_data, gcode_file.id, printer_profile.id, self.device_id
            )

            self.shared.print_job_id = print_job.id

        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"on_print_start API called failed {e}", exc_info=True)
            return

        if self.plugin.get_setting("auto_start"):
            logger.info("Print Nanny monitoring is set to auto-start")
            self.start_monitoring()
