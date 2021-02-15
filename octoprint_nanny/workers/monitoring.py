import asyncio
import logging
import threading
from enum import Enum

import beeline
from octoprint_nanny.workers.websocket import WebSocketWorker
from octoprint_nanny.predictor import Prediction, ThreadLocalPredictor

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")

BOUNDING_BOX_PREDICT_EVENT = "bounding_box_predict"
ANNOTATED_IMAGE_EVENT = "annotated_image"


class MonitoringModes(Enum):
    ACTIVE_LEARNING = "active_learning"
    LITE = "lite"


PREDICTOR = None


@beeline.traced(name="PredictWorker.get_predict_bytes")
@beeline.traced_thread
def _get_predict_bytes(msg):
    global PREDICTOR
    image = PREDICTOR.load_image(msg["original_image"])
    prediction = PREDICTOR.predict(image)

    viz_np = PREDICTOR.postprocess(image, prediction)
    viz_image = PIL.Image.fromarray(viz_np, "RGB")
    viz_buffer = io.BytesIO()
    viz_buffer.name = "annotated_image.jpg"
    viz_image.save(viz_buffer, format="JPEG")
    return viz_buffer, prediction


class PredictWorker:
    """
    Coordinates frame buffer sampling and prediction work
    Publishes results to websocket and main octoprint event bus
    """

    def __init__(
        self,
        webcam_url: str,
        calibration: dict,
        octoprint_ws_queue,
        pn_ws_queue,
        mqtt_send_queue,
        fpm,
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
        self._plugin = plugin
        self._calibration = calibration
        self._fpm = fpm
        self._sleep_interval = 60 / int(fpm)
        self._webcam_url = webcam_url

        self._octoprint_ws_queue = octoprint_ws_queue
        self._pn_ws_queue = pn_ws_queue
        self._mqtt_send_queue = mqtt_send_queue

        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
        self._honeycomb_tracer.add_global_context(trace_context)

        self._halt = halt

    @beeline.traced(name="PredictWorker.load_url_buffer")
    async def load_url_buffer(self, session):
        res = await session.get(self._webcam_url)
        assert res.headers["content-type"] == "image/jpeg"
        return io.BytesIO(await res.read())

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
                1
                if (
                    h / height >= y0
                    and h / height <= y1
                    and w / width >= x0
                    and w / width <= x1
                )
                else 0
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

    @beeline.traced(name="PredictWorker._image_msg")
    async def _image_msg(self, ts):
        async with aiohttp.ClientSession() as session:
            original_image = await self.load_url_buffer(session)
            return dict(
                ts=ts,
                original_image=original_image,
            )

    @beeline.traced(name="PredictWorker._create_msgs")
    def _create_msgs(self, msg, viz_buffer, prediction):
        # send annotated image bytes to octoprint ui ws
        # viz_bytes = viz_buffer.getvalue()
        # self._octoprint_ws_queue.put_nowait(viz_bytes)

        # send annotated image bytes to print nanny ui ws
        ws_msg = msg.copy()
        # send only annotated image data
        # del ws_msg["original_image"]
        ws_msg.update(
            {
                "event_type": "annotated_image",
                "annotated_image": viz_buffer,
            }
        )

        mqtt_msg = msg.copy()
        # publish bounding box prediction to mqtt telemetry topic
        # del mqtt_msg["original_image"]
        mqtt_msg.update(
            {
                "event_type": "bounding_box_predict",
            }
        )
        mqtt_msg.update(prediction)

        return ws_msg, mqtt_msg

    @beeline.traced(name="PredictWorker._producer")
    async def _producer(self):
        """
        Calculates prediction and publishes result to subscriber queues
        """
        logger.info("Started PredictWorker.consumer thread")
        loop = asyncio.get_running_loop()
        global predictor
        predictor = ThreadLocalPredictor(calibration=self._calibration)
        logger.info(f"Initialized predictor {predictor}")
        with concurrent.futures.ProcessPoolExecutor() as pool:
            while not self._halt.is_set():
                await asyncio.sleep(self._sleep_interval)
                trace = self._honeycomb_tracer.start_trace()

                now = datetime.now(pytz.timezone("America/Los_Angeles")).timestamp()
                msg = await self._image_msg(now)
                viz_buffer, prediction = await loop.run_in_executor(
                    pool, _get_predict_bytes, msg
                )
                ws_msg, mqtt_msg = self._create_msgs(msg, viz_buffer, prediction)
                logger.info(f"Firing {Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE}")
                self._plugin._event_bus.fire(
                    Events.PLUGIN_OCTOPRINT_NANNY_PREDICT_DONE,
                    payload={"image": base64.b64encode(viz_buffer.getvalue())},
                )
                self._pn_ws_queue.put_nowait(ws_msg)
                self._mqtt_send_queue.put_nowait(mqtt_msg)

                self._honeycomb_tracer.finish_trace(trace)

            logger.warning("Halt event set, worker will exit soon")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._producer())


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
    async def start(self, **kwargs):

        self._reset()

        for worker in self._workers:
            thread = threading.Thread(target=worker.run, name=str(worker.__class__))
            thread.daemon = True
            self._worker_threads.append(thread)
            logger.info(f"Starting thread {thread.name}")
            thread.start()
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, monitoring_active=True
        )

    @beeline.traced("MonitoringManager.stop")
    async def stop(self, **kwargs):
        self._drain()
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.device_id, monitoring_active=False
        )
