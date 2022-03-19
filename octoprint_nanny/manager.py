import asyncio
import beeline
import concurrent
import logging
import queue
import threading
from typing import Optional

from octoprint.events import Events
import octoprint.filemanager

from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS
from octoprint_nanny.settings import PluginSettingsMemoize

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
        # outbound telemetry messages to MQTT bridge
        self.mqtt_send_queue: queue.Queue = queue.Queue()
        # inbound MQTT command and config messages from MQTT bridge
        self.mqtt_receive_queue: queue.Queue = queue.Queue()

        if plugin_settings is None:
            plugin_settings = PluginSettingsMemoize(plugin, self.mqtt_receive_queue)

        self.plugin_settings = plugin_settings
        self.plugin = plugin
        self.plugin.settings = plugin_settings

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))
        self.loop = loop
        return loop.run_forever()

    async def on_user_logged_in(self, **kwargs):
        try:
            await self.plugin.sync_printer_profiles()
            await self.plugin.sync_device_metadata()
        except API_CLIENT_EXCEPTIONS:  # rest_client.py contains backoff and giveup logging hanlers
            pass

    async def on_calibration_update(self):
        payload = dict(
            octoprint_device=self.plugin_settings.octoprint_device_id,
            xy=self.plugin_settings.calibration_xy,
        )
        device_calibration = (
            await self.plugin_settings.rest_client.update_or_create_device_calibration(
                **payload
            )
        )
        logger.info(f"Device calibration upsert succeeded {device_calibration}")
