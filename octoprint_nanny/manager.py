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
from typing import Optional

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

    def __init__(self, plugin, plugin_settings: Optional[PluginSettingsMemoize] = None):

        self.event_loop_thread = threading.Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()

        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

        self.plugin = plugin
        self.manager = aioprocessing.AioManager()
        self.shared = self.manager.Namespace()

        # images streamed to webapp asgi over websocket
        pn_ws_queue = self.manager.AioQueue()
        self.pn_ws_queue = pn_ws_queue

        # outbound telemetry messages to MQTT bridge
        mqtt_send_queue = self.manager.AioQueue()
        self.mqtt_send_queue = mqtt_send_queue
        # inbound MQTT command and config messages from MQTT bridge
        mqtt_receive_queue = self.manager.AioQueue()
        self.mqtt_receive_queue = mqtt_receive_queue

        if plugin_settings is None:
            plugin_settings = PluginSettingsMemoize(plugin, mqtt_receive_queue)
        self.plugin.settings = plugin_settings

        self.monitoring_manager = MonitoringManager(
            pn_ws_queue,
            mqtt_send_queue,
            plugin,
        )

        self.mqtt_manager = MQTTManager(
            mqtt_send_queue=mqtt_send_queue,
            mqtt_receive_queue=mqtt_receive_queue,
            plugin=plugin,
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
            Events.USER_LOGGED_IN: self.on_user_logged_in,
        }
        self.mqtt_manager.publisher_worker.register_callbacks(
            self._mqtt_send_queue_callbacks
        )

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))
        self.loop = loop
        return loop.run_forever()

    @beeline.traced("WorkerManager._register_plugin_event_handlers")
    def _register_plugin_event_handlers(self):
        """
        Events.PLUGIN_OCTOPRINT_NANNY* events are not available on Events until plugin is fully initialized
        """

        callbacks = {
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_START: self.monitoring_manager.start,
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: self.monitoring_manager.stop,
        }
        self.mqtt_manager.publisher_worker.register_callbacks(callbacks)
        logger.info(f"Registered callbacks {callbacks} on publisher worker")

        self.mqtt_manager.subscriber_worker.register_callbacks(callbacks)
        logger.info(f"Registered callbacks {callbacks} on subscriber worker")

    @beeline.traced("WorkerManager.on_settings_initialized")
    def on_settings_initialized(self):
        self._honeycomb_tracer.add_global_context(
            self.plugin.settings.metadata.to_dict()
        )
        self._register_plugin_event_handlers()
        self.mqtt_manager.start()

    # @beeline.traced("WorkerManager.apply_device_registration")
    # def apply_device_registration(self):
    #     self.mqtt_manager.stop()
    #     logger.info("Resetting WorkerManager device registration state")
    #     self.plugin.settings.reset_device_settings_state()
    #     self.mqtt_manager.start()

    @beeline.traced("WorkerManager.on_settings_save")
    def on_settings_save(self):
        self.mqtt_manager.stop()
        self.plugin.settings.reset_device_settings_state()
        self.plugin.settings.reset_rest_client_state()
        self.mqtt_manager.start()
        logger.info(
            "Stopping any existing monitoring processes to apply new calibration"
        )
        monitoring_was_active = bool(self.plugin.settings.monitoring_active)
        asyncio.run_coroutine_threadsafe(self.monitoring_manager.stop(), self.loop)
        logger.info("Sending latest calibration")
        asyncio.run_coroutine_threadsafe(self.on_calibration_update(), self.loop)
        if monitoring_was_active:
            logger.info(
                "Monitoring was active when new calibration was applied. Re-initializing monitoring processes"
            )
            asyncio.run_coroutine_threadsafe(self.monitoring_manager.start(), self.loop)

    async def on_user_logged_in(self, **kwargs):
        await self.plugin.sync_printer_profiles()
        await self.plugin.sync_device_metadata()

    @beeline.traced("WorkerManager.shutdown")
    async def shutdown(self):
        await self.monitoring_manager.stop()

        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.octoprint_device_id, monitoring_active=False
        )

        self.mqtt_manager.stop()
        self._honeycomb_tracer.on_shutdown()

    ##
    #  Event handlers
    ##
    @beeline.traced("WorkerManager.on_print_start")
    async def on_print_start(self, event_type, event_data, **kwargs):
        logger.info(f"on_print_start called for {event_type} with data {event_data}")
        try:
            current_profile = (
                self.plugin._printer_profile_manager.get_current_or_default()
            )
            printer_profile = (
                await self.plugin.settings.rest_client.update_or_create_printer_profile(
                    current_profile, self.plugin.settings.octoprint_device_id
                )
            )

            self.shared.printer_profile_id = printer_profile.id

            gcode_file_path = self.plugin._file_manager.path_on_disk(
                octoprint.filemanager.FileDestinations.LOCAL, event_data["path"]
            )
            gcode_file = (
                await self.plugin.settings.rest_client.update_or_create_gcode_file(
                    event_data,
                    gcode_file_path,
                    self.plugin.settings.octoprint_device_id,
                )
            )

        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"on_print_start API called failed {e}", exc_info=True)
            return

    async def on_calibration_update(self):
        logger.info(
            f"{self.__class__}.on_calibration_update called for event_type={event_type} event_data={event_data}"
        )
        device_calibration = (
            await self.plugin.settings.rest_client.update_or_create_device_calibration(
                self.plugin.settings.octoprint_device_id,
                {
                    "x0": self.plugin.get_setting("calibrate_x0"),
                    "x1": self.plugin.get_setting("calibrate_x1"),
                    "y0": self.plugin.get_setting("calibrate_y0"),
                    "y1": self.plugin.get_setting("calibrate_y1"),
                },
                self.plugin.settings.calibration,
            )
        )
        logger.info(f"Device calibration upsert succeeded {device_calibration}")
