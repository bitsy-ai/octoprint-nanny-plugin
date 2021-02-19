import base64
import concurrent
import asyncio
import pytz
import aiohttp
import logging
import io
import PIL
from datetime import datetime
import numpy as np

import threading
from enum import Enum

# python >= 3.8
try:
    from typing import TypedDict, Optional, Tuple
# python <= 3.7
except:
    from typing_extensions import TypedDict, Tuple
    from typing import Optional

import beeline
from octoprint.events import Events

from octoprint_nanny.workers.websocket import WebSocketWorker
from octoprint_nanny.predictor import Prediction, ThreadLocalPredictor
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint.events import Events
from octoprint_nanny.constants import PluginEvents, MonitoringModes

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")


class PrintNannyMonitoringFrameMessage(TypedDict):
    ts: datetime
    event_type: str = PluginEvents.MONITORING_FRAME_DONE.value
    image: str


class BoundingBoxMessage(TypedDict):
    prediction: Prediction
    event_type: str = PluginEvents.BOUNDING_BOX_PREDICT_DONE.value
    ts: datetime


PREDICTOR = None


@beeline.traced(name="MonitoringWorker.get_predict_bytes")
@beeline.traced_thread
def _get_predict_bytes(image, calibration):
    global PREDICTOR
    if PREDICTOR is None:
        PREDICTOR = ThreadLocalPredictor(calibration=calibration)
    image = PREDICTOR.load_image(image)
    prediction = PREDICTOR.predict(image)

    prediction, viz_np = PREDICTOR.postprocess(image, prediction)
    viz_image = PIL.Image.fromarray(viz_np, "RGB")
    viz_buffer = io.BytesIO()
    viz_buffer.name = "annotated_image.jpg"
    viz_image.save(viz_buffer, format="JPEG")

    return viz_buffer, prediction


class MonitoringWorker:
    """
    Coordinates frame buffer sampling and prediction work
    Publishes results to websocket and main octoprint event bus
    """

    def __init__(
        self,
        pn_ws_queue,
        mqtt_send_queue,
        halt,
        plugin,
        trace_context={},
    ):
        """
        webcam_url - ./mjpg_streamer -i "./input_raspicam.so -fps 5" -o "./output_http.so"
        octoprint_ws_queue - consumer relay to octoprint's main event bus
        pn_ws_queue - consumer relay to websocket upload proc
        calibration - (x0, y0, x1, y1) normalized by h,w to range [0, 1]
        fpm - approximate frame per minute sample rate, depends on asyncio.sleep()
        halt - threading.Event()
        """
        self._monitoring_mode = plugin.settings.monitoring_mode
        self._plugin = plugin
        self._calibration = plugin.settings.calibration
        self._fpm = plugin.settings.monitoring_frames_per_minute
        self._sleep_interval = 60 / int(self._fpm)
        self._snapshot_url = plugin.settings.snapshot_url

        self._pn_ws_queue = pn_ws_queue
        self._mqtt_send_queue = mqtt_send_queue

        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
        self._honeycomb_tracer.add_global_context(trace_context)

        self._halt = halt

    @beeline.traced(name="MonitoringWorker.load_url_buffer")
    async def load_url_buffer(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self._snapshot_url) as res:
                assert res.headers["content-type"] == "image/jpeg"
                b = await res.read()
                return io.BytesIO(b)

    @staticmethod
    def calc_calibration(x0, y0, x1, y1, height=480, width=640):
        if (
            x0 is None
            or y0 is None
            or x1 is None
            or y1 is None
            or height is None
            or width is None
        ):
            logger.warning(f"Invalid calibration values ({x0}, {y0}) ({x1}, {y1})")
            return None

        mask = np.zeros((height, width))
        for (h, w), _ in np.ndenumerate(np.zeros((height, width))):
            value = (
                1 if (h / height >= y0 and h / height <= y1 and w / width >= x0) else 0
            )
            mask[h][w] = value

        mask = mask.astype(np.uint8)
        logger.info(f"Calibration set")

        return {"mask": mask, "coords": (x0, y0, x1, y1)}

    def _producer_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.ensure_future(self._producer()))
        loop.close()

    @beeline.traced(name="MonitoringWorker._create_active_learning_msgs")
    def _create_active_learning_msgs(
        self, now, image
    ) -> PrintNannyMonitoringFrameMessage:

        # send annotated image bytes to print nanny ui ws and Apache Beam worker
        b64_image = base64.b64encode(image.getvalue())
        ws_msg = PrintNannyMonitoringFrameMessage(
            ts=now,
            event_type=PluginEvents.MONITORING_FRAME_DONE,
            image=b64_image,
        )
        return ws_msg

    async def _active_learning_loop(self, loop, pool):
        now = datetime.now(pytz.utc).timestamp()
        image = await self.load_url_buffer()

        msg = self._create_active_learning_msgs(now, image)

        octoprint_event = PluginEvents.to_octoprint_event(
            PluginEvents.MONITORING_FRAME_DONE
        )
        self._plugin._event_bus.fire(
            octoprint_event,
            payload=msg,
        )
        self._pn_ws_queue.put_nowait(msg)
        self._mqtt_send_queue.put_nowait(msg)

    @beeline.traced(name="MonitoringWorker._create_lite_msgs")
    def _create_lite_msgs(
        self, now, image, viz_buffer, prediction
    ) -> Tuple[PrintNannyMonitoringFrameMessage, BoundingBoxMessage]:

        # send annotated image bytes to print nanny ui ws
        ws_msg = PrintNannyMonitoringFrameMessage(
            ts=now,
            event_type=PluginEvents.MONITORING_FRAME_DONE,
            image=base64.b64encode(viz_buffer.getvalue()),
        )

        # publish bounding box prediction to mqtt telemetry topic
        mqtt_msg = BoundingBoxMessage(
            ts=now, event_type=PluginEvents.BOUNDING_BOX_PREDICT_DONE, data=prediction
        )

        return ws_msg, mqtt_msg

    async def _lite_loop(self, loop, pool):
        now = datetime.now(pytz.utc).timestamp()
        image = await self.load_url_buffer()

        viz_buffer, prediction = await loop.run_in_executor(
            pool, _get_predict_bytes, image, self._calibration
        )

        ws_msg, mqtt_msg = self._create_lite_msgs(now, image, viz_buffer, prediction)

        octoprint_event = PluginEvents.to_octoprint_event(
            PluginEvents.MONITORING_FRAME_DONE
        )
        self._plugin._event_bus.fire(
            octoprint_event,
            payload=ws_msg,
        )
        if self._plugin.settings.webcam_upload:
            self._pn_ws_queue.put_nowait(ws_msg)
        self._mqtt_send_queue.put_nowait(mqtt_msg)

    @beeline.traced(name="MonitoringWorker._loop")
    async def _loop(self, loop, pool):
        if self._monitoring_mode == MonitoringModes.ACTIVE_LEARNING:
            await self._active_learning_loop(loop, pool)
        elif self._monitoring_mode == MonitoringModes.LITE:
            await self._lite_loop(loop, pool)
        else:
            logger.error(f"Unsupported monitoring_mode={self._monitoring_mode}")
            return

    @beeline.traced(name="MonitoringWorker._producer")
    async def _producer(self):
        """
        Calculates prediction and publishes result to subscriber queues
        """
        logger.info("Started MonitoringWorker.consumer thread")
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            while not self._halt.is_set():
                await asyncio.sleep(self._sleep_interval)
                await self._loop(loop, pool)

            logger.warning("Halt event set, worker will exit soon")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._producer())


class MonitoringManager:
    def __init__(
        self,
        pn_ws_queue,
        mqtt_send_queue,
        plugin,
    ):

        self.halt = threading.Event()
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
        self._predict_worker = MonitoringWorker(
            self.pn_ws_queue,
            self.mqtt_send_queue,
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
    async def start(self, **kwargs):
        self._reset()

        for worker in self._workers:
            thread = threading.Thread(target=worker.run, name=str(worker.__class__))
            thread.daemon = True
            self._worker_threads.append(thread)
            logger.info(f"Starting thread {thread.name}")
            thread.start()

        self.plugin._settings.set(["monitoring_active"], True)
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, monitoring_active=True
        )

    @beeline.traced("MonitoringManager.stop")
    async def stop(self, **kwargs):
        self._drain()
        self.plugin._settings.set(["monitoring_active"], False)
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, monitoring_active=False
        )
