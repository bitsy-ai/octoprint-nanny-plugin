import base64
import concurrent
import asyncio
import pytz
import aiohttp
import logging
import io
import PIL
import functools
from datetime import datetime
import numpy as np
import threading
from enum import Enum
from uuid import uuid4

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
from octoprint_nanny.predictor import (
    ThreadLocalPredictor,
    predict_threadsafe,
    print_is_healthy,
    DETECTION_LABELS,
    explode_prediction_df,
)
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint.events import Events
from octoprint_nanny.types import (
    PluginEvents,
    MonitoringModes,
    MonitoringFrame,
    TelemetryEventEnum,
    Image,
)
from octoprint_nanny.utils.encoder import NumpyEncoder
import octoprint_nanny.clients.flatbuffers

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")
try:
    import pandas as pd
except ImportError:
    logger.warning(
        "Imports for offline inference failed! Only online learning will be available. Please install with [offline] extras to enable offline mode."
    )


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

        self._predictor_kwargs = {
            "calibration": plugin.settings.calibration,
            "min_score_thresh": plugin.settings.min_score_thresh,
        }
        self._fpm = plugin.settings.monitoring_frames_per_minute
        self._sleep_interval = 60 / int(self._fpm)
        self._snapshot_url = plugin.settings.snapshot_url

        self._pn_ws_queue = pn_ws_queue
        self._mqtt_send_queue = mqtt_send_queue

        self._trace_context = trace_context
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
        self._honeycomb_tracer.add_global_context(trace_context)

        self._halt = halt
        self._df = pd.DataFrame()

    @beeline.traced(name="MonitoringWorker.load_url_buffer")
    async def load_url_buffer(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self._snapshot_url) as res:
                assert res.headers["content-type"] == "image/jpeg"
                b = await res.read()
                return b

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

    @beeline.traced(name="MonitoringWorker.update_dataframe")
    def update_dataframe(self, ts, prediction):
        self._df = self._df.append(explode_prediction_df(ts, prediction))
        return self._df

    def _producer_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.ensure_future(self._producer()))
        loop.close()

    @beeline.traced(name="MonitoringWorker._create_active_learning_msg")
    def _create_active_learning_flatbuffer_msg(
        self, monitoring_frame: MonitoringFrame
    ) -> bytes:
        msg = octoprint_nanny.clients.flatbuffers.build_telemetry_event_message(
            event_type=TelemetryEventEnum.monitoring_frame_raw,
            metadata=self._plugin.settings.metadata,
            monitoring_frame=monitoring_frame,
        )
        return msg

    @beeline.traced(name="MonitoringWorker._create_lite_fb_mqtt_msg")
    def _create_lite_fb_msg(
        self, monitoring_frame: MonitoringFrame
    ) -> Tuple[bytes, Optional[bytes]]:
        return octoprint_nanny.clients.flatbuffers.build_telemetry_event_message(
            event_type=TelemetryEventEnum.monitoring_frame_post,
            metadata=self._plugin.settings.metadata,
            monitoring_frame=monitoring_frame,
        )

    @beeline.traced(name="MonitoringWorker._active_learning_loop")
    async def _active_learning_loop(self):
        ts = int(datetime.now(pytz.utc).timestamp())
        image_bytes = await self.load_url_buffer()

        pimage = PIL.Image.open(io.BytesIO(image_bytes))
        (w, h) = pimage.size
        image = Image(height=h, width=w, data=image_bytes)
        monitoring_frame = MonitoringFrame(ts=ts, image=image)

        msg = self._create_active_learning_flatbuffer_msg(monitoring_frame)
        b64_image = base64.b64encode(image_bytes)
        self._plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
            payload=b64_image,
        )
        self._pn_ws_queue.put_nowait(image_bytes)
        self._mqtt_send_queue.put_nowait(msg)

    @beeline.traced(name="MonitoringWorker._lite_predict_and_calc_health")
    async def _lite_predict_and_calc_health(self, ts) -> MonitoringFrame:

        image_bytes = await self.load_url_buffer()
        func = functools.partial(
            predict_threadsafe, ts, image_bytes, **self._predictor_kwargs
        )

        # trace predict latency, including serialization in/out of process pool
        span = self._honeycomb_tracer.start_span(
            context={
                "name": "predict_pooled",
            }
        )

        monitoring_frame = await self.loop.run_in_executor(self.pool, func)
        self._honeycomb_tracer.add_context(
            {"bounding_boxes": monitoring_frame.bounding_boxes}
        )
        self._honeycomb_tracer.finish_span(span)

        # trace metrics calculations in/out of process pool
        if monitoring_frame.bounding_boxes is not None:
            self.update_dataframe(ts, monitoring_frame.bounding_boxes)

        # trace polyfit curve
        span = self._honeycomb_tracer.start_span(
            context={
                "name": "print_is_healthy",
            }
        )

        func = functools.partial(print_is_healthy, self._df)
        healthy = await self.loop.run_in_executor(self.pool, func)
        if healthy is False:
            octoprint_device = self._plugin.settings.device_id
            dataframe = io.BytesIO(name=f"{octoprint_device}_{ts}.parquet")
            self._df.to_parquet(dataframe, engine="pyarrow")
            alert = await self._plugin.settings.rest_client.create_defect_alert(
                octoprint_device=octoprint_device, dataframe=self._df
            )
            logger.warning(f"Created DefectAlert with id={alert.id}")

        return monitoring_frame

    @beeline.traced(name="MonitoringWorker._lite_loop")
    async def _lite_loop(self):
        ts = int(datetime.now(pytz.utc).timestamp())

        monitoring_frame = await self._lite_predict_and_calc_health(ts)

        msg = self._create_lite_fb_msg(monitoring_frame=monitoring_frame)
        self._plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
            payload=base64.b64encode(monitoring_frame.image.data),
        )
        if self._plugin.settings.webcam_upload:
            self._pn_ws_queue.put_nowait(monitoring_frame.image.data)

        if monitoring_frame.bounding_boxes is not None:
            self._mqtt_send_queue.put_nowait(msg)

    @beeline.traced(name="MonitoringWorker._loop")
    async def _loop(self):

        if self._monitoring_mode == MonitoringModes.ACTIVE_LEARNING:
            await self._active_learning_loop()
        elif self._monitoring_mode == MonitoringModes.LITE:
            await self._lite_loop()
        else:
            logger.error(f"Unsupported monitoring_mode={self._monitoring_mode}")
            return

    async def _producer(self):
        """
        Calculates prediction and publishes result to subscriber queues
        """
        logger.info("Started MonitoringWorker.consumer thread")
        loop = asyncio.get_running_loop()
        self.loop = loop
        with concurrent.futures.ProcessPoolExecutor() as pool:
            self.pool = pool
            while not self._halt.is_set():
                await asyncio.sleep(self._sleep_interval)
                await self._loop()

            logger.warning("Halt event set, worker will exit soon")

    def run(self):
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._producer())


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
    async def start(self, session=None, **kwargs):
        self._reset()
        self.plugin.settings.reset_print_session()
        await self.plugin.settings.create_print_session()
        logger.info(
            f"Initializing monitoring workers with session={self.plugin.settings.print_session.session}"
        )
        for worker in self._workers:
            thread = threading.Thread(target=worker.run, name=str(worker.__class__))
            thread.daemon = True
            self._worker_threads.append(thread)
            logger.info(f"Starting thread {thread.name}")
            thread.start()

        self.plugin._settings.set(["monitoring_active"], True)
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id,
            monitoring_active=True,
            last_session=self.plugin.settings.print_session.id,
        )

    @beeline.traced("MonitoringManager.stop")
    async def stop(self, **kwargs):
        self._drain()
        self.plugin._settings.set(
            ["monitoring_active"], False
        )  # @todo fix setting iface
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, monitoring_active=False
        )
        if self.plugin.settings.print_session:
            logger.info(
                f"Closing monitoring session session={self.plugin.settings.print_session.session}"
            )
        self.plugin.settings.reset_print_session()
