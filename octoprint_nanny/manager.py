import asyncio
import beeline
import concurrent
import logging
import queue
import threading

from octoprint.events import Events

from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS

Events.PRINT_PROGRESS = "PrintProgress"
logger = logging.getLogger("octoprint.plugins.octoprint_nanny.manager")


class WorkerManager:
    """
    Manages an asynio event loop running in a separate ThreadPool
    """

    def __init__(self, plugin):

        self.event_loop_thread = threading.Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()
        # outbound telemetry messages to MQTT bridge
        self.mqtt_send_queue: queue.Queue = queue.Queue()
        # inbound MQTT command and config messages from MQTT bridge
        self.mqtt_receive_queue: queue.Queue = queue.Queue()

        self.plugin = plugin

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
