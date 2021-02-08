import asyncio
import logging
import threading

import beeline
from octoprint_nanny.workers.websocket import WebSocketWorker
from octoprint_nanny.predictor import (
    PredictWorker,
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")


class MonitoringManager:
    def __init__(
        self,
        octo_ws_queue,
        pn_ws_queue,
        mqtt_send_queue,
        plugin_settings,
        plugin_event_bus,
    ):

        self.halt = threading.Event()
        self.octo_ws_queue = octo_ws_queue
        self.pn_ws_queue = pn_ws_queue
        self.mqtt_send_queue = mqtt_send_queue
        self.plugin_settings = plugin_settings
        self.plugin_event_bus = plugin_event_bus
        self.rest_client = plugin_settings.rest_client

    @beeline.traced
    def _drain(self):
        self.halt.set()

        for worker in self._worker_threads:
            logger.info(f"Waiting for worker={worker} thread to drain")
            worker.join()

    def _reset(self):
        self.halt = threading.Event()
        self._predict_worker = PredictWorker(
            self.plugin_settings.snapshot_url,
            self.plugin_settings.calibration,
            self.octo_ws_queue,
            self.pn_ws_queue,
            self.mqtt_send_queue,
            self.plugin_settings.monitoring_frames_per_minute,
            self.halt,
            self.plugin_event_bus,
            trace_context=self.plugin_settings.get_device_metadata(),
        )
        self._websocket_worker = WebSocketWorker(
            self.plugin_settings.ws_url,
            self.plugin_settings.auth_token,
            self.pn_ws_queue,
            self.plugin_settings.device_id,
            self.halt,
            trace_context=self.plugin_settings.get_device_metadata(),
        )
        self._workers = [self._predict_worker, self._websocket_worker]
        self._worker_threads = []

    @beeline.traced
    async def start(self):
        self._reset()

        for worker in self._workers:
            thread = threading.Thread(target=worker.run)
            thread.daemon = True
            self._worker_threads.append(thread)
            thread.start()
        await self.rest_client.update_octoprint_device(
            self.plugin_settings.device_id, active=True
        )

    @beeline.traced
    async def stop(self):
        self._drain()
        await self.rest_client.update_octoprint_device(
            self.plugin_settings.device_id, active=False
        )
