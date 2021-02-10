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
        plugin,
    ):

        self.halt = threading.Event()
        self.octo_ws_queue = octo_ws_queue
        self.pn_ws_queue = pn_ws_queue
        self.mqtt_send_queue = mqtt_send_queue
        self.plugin = plugin
        self._worker_threads = []

    @beeline.traced("MonitoringManager._drain")
    def _drain(self):
        self.halt.set()

        for worker in self._worker_threads:
            logger.info(f"Waiting for worker={worker} thread to drain")
            worker.join(10)

    @beeline.traced("MonitoringManager._reset")
    def _reset(self):
        self.halt = threading.Event()
        self._predict_worker = PredictWorker(
            self.plugin.settings.snapshot_url,
            self.plugin.settings.calibration,
            self.octo_ws_queue,
            self.pn_ws_queue,
            self.mqtt_send_queue,
            self.plugin.settings.monitoring_frames_per_minute,
            self.halt,
            self.plugin,
            trace_context=self.plugin.settings.get_device_metadata(),
        )
        self._websocket_worker = WebSocketWorker(
            self.plugin.settings.ws_url,
            self.plugin.settings.auth_token,
            self.pn_ws_queue,
            self.plugin.settings.device_id,
            self.halt,
            trace_context=self.plugin.settings.get_device_metadata(),
        )
        self._workers = [self._predict_worker, self._websocket_worker]
        self._worker_threads = []
        logger.info(f"Finished resetting MonitoringManager")

    @beeline.traced("MonitoringManager.start")
    async def start(self):

        self._reset()

        for worker in self._workers:
            thread = threading.Thread(target=worker.run, name=str(worker.__class__))
            thread.daemon = True
            self._worker_threads.append(thread)
            logger.info(f"Starting thread {thread.name}")
            thread.start()
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, active=True
        )

    @beeline.traced("MonitoringManager.stop")
    async def stop(self):
        self._drain()
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, active=False
        )
