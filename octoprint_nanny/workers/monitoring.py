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
from octoprint_nanny.settings import PluginSettingsMemoizeMixin

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")


class MonitoringWorker(PluginSettingsMemoizeMixin):
    """
    Wrapper for PredictWorker and WebsocketWorker
    """

    def __init__(self, plugin, octo_ws_queue, pn_ws_queue, mqtt_send_queue):

        super().__init__(plugin)
        self.halt = threading.Event()
        self.octo_ws_queue = octo_ws_queue
        self.pn_ws_queue = pn_ws_queue
        self.mqtt_send_queue = mqtt_send_queue

    @beeline.traced()
    def init(self):

        self.predict_worker = PredictWorker(
            self.snapshot_url,
            self.calibration,
            self.octo_ws_queue,
            self.pn_ws_queue,
            self.mqtt_send_queue,
            self.monitoring_frames_per_minute,
            self.halt,
            self.plugin._event_bus,
            trace_context=self.get_device_metadata(),
        )

        self.predict_worker_thread = threading.Thread(target=self.predict_worker.run)
        self.predict_worker_thread.daemon = True

        self.websocket_worker = WebSocketWorker(
            self.ws_url,
            self.auth_token,
            self.pn_ws_queue,
            self.device_id,
            self.halt,
            trace_context=self.get_device_metadata(),
        )
        self.websocket_worker_thread = threading.Thread(
            target=self.websocket_worker.run
        )
        self.websocket_worker_thread.daemon = True

    @beeline.traced()
    async def stop(self, event_type=None, **kwargs):
        """
        joins and terminates dedicated prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.stop_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.active = False

        await self.rest_client.update_octoprint_device(self.device_id, active=False)
        self.halt.set()
        self.predict_worker_thread.join()
        self.websocket_worker_thrad.join()

    @beeline.traced("WorkerManager.start_monitoring")
    async def start(self, event_type=None, **kwargs):
        """
        starts prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.start_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.active = True

        await self.rest_client.update_octoprint_device(self.device_id, active=True)
        self.init()
        self.predict_worker_thread.start()
        self.websocket_worker_thread.start()
