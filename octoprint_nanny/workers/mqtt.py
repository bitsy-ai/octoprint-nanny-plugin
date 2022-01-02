import aiohttp
import asyncio
import concurrent
import inspect
import json
import logging
import os
import queue
import threading
import sys
from datetime import datetime
import logging
import pytz
import PIL
import io
import beeline
import base64
from typing import List, Callable, Dict, Any, Union

import print_nanny_client # alpha client

import printnanny_api_client # beta client

from octoprint.events import Events
import octoprint
from printnanny_api_client import (
    TelemetryEventPolymorphicRequest,
    OctoprintEnvironmentRequest,
    OctoprintPrinterDataRequest,
)

from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS
from octoprint_nanny.exceptions import PluginSettingsRequired

from octoprint_nanny.clients.honeycomb import beeline
from octoprint_nanny.types import (
    MonitoringModes,
    MonitoringFrame,
    Image,
)
from octoprint_nanny.clients.protobuf import build_monitoring_image
from octoprint_nanny.settings import PluginSettingsMemoize
from octoprint_nanny.clients.mqtt import MQTTClient

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.mqtt")


def build_telemetry_event(event, plugin) -> TelemetryEventPolymorphicRequest:
    environment = plugin.settings.octoprint_environment
    environment = OctoprintEnvironmentRequest(
        os=environment.get("os", {}),
        python=environment.get("python", {}),
        hardware=environment.get("hardware", {}),
        pi_support=environment.get("plugins", {}).get("pi_support", {}),
    )
    printer_data = plugin.settings.current_printer_state
    currentZ = printer_data.pop("currentZ")
    printer_data = OctoprintPrinterDataRequest(current_z=currentZ, **printer_data)
    printer_state = printer_data.state.get("text")
    return TelemetryEventPolymorphicRequest(
        print_session=plugin.settings.print_session_id,
        octoprint_environment=environment,
        octoprint_printer_data=printer_data,
        temperature=plugin.settings.current_temperatures,
        print_nanny_plugin_version=plugin.settings.plugin_version,
        print_nanny_client_version=print_nanny_client.__version__, # alpha client in print_nanny_client namespace
        print_nanny_beta_client_version=printnanny_api_client.__version__, # beta client in printnanny_api_client namespace
        octoprint_version=octoprint.util.version.get_octoprint_version_string(),
        octoprint_device=plugin.settings.octoprint_device_id,
        ts=datetime.now(pytz.timezone("UTC")).timestamp(),
        printer_state=printer_state,
        **event,
    )


class MQTTManager:
    def __init__(
        self,
        mqtt_send_queue: queue.Queue,
        mqtt_receive_queue: queue.Queue,
        plugin_settings: PluginSettingsMemoize,
        plugin,
    ):

        self.mqtt_send_queue = mqtt_send_queue
        self.mqtt_receive_queue = mqtt_receive_queue
        self.exit = threading.Event()

        self.plugin_settings = plugin_settings
        self.plugin = plugin
        self._worker_threads: List[threading.Thread] = []
        self.publisher_worker = MQTTPublisherWorker(
            self.mqtt_send_queue, self.plugin, self.plugin_settings
        )
        self.subscriber_worker = MQTTSubscriberWorker(
            self.mqtt_receive_queue, self.plugin, self.plugin_settings
        )
        self._workers: List[
            Union[MQTTPublisherWorker, MQTTSubscriberWorker, MQTTClient]
        ] = []

    def _reset(self):
        self.exit = threading.Event()
        self._worker_threads = []

    @beeline.traced("MQTTManager.start")
    def start(self, **kwargs):
        """
        (re)initialize and start worker threads
        """
        self._reset()
        # add metadata to honeycomb trace context
        beeline.add_context(self.plugin_settings.metadata.to_dict())

        try:
            mqtt_client = self.plugin_settings.mqtt_client
        except PluginSettingsRequired as e:
            logger.warning(e)
            logger.warning(
                "MQTTManager.start was called without device registration set, ignoring"
            )
            return

        logger.info("MQTTManager.start was called")

        self._workers = [
            self.publisher_worker,
            self.subscriber_worker,
            mqtt_client,
        ]
        for worker in self._workers:
            thread = threading.Thread(
                target=worker.run,
                name=str(worker.__class__),
            )
            thread.daemon = True
            self._worker_threads.append(thread)
            thread.start()
            logger.info(f"Started thread {thread} running {worker.run}")

    def shutdown(self, **kwargs):
        logger.warning("MMQTTManager shutdown initiated")
        for worker in self._workers:
            worker.shutdown()


class MQTTPublisherWorker:
    """
    Run a worker thread dedicated to publishing OctoPrint events to MQTT bridge
    """

    PRINT_JOB_EVENTS = [
        Events.ERROR,
        Events.PRINT_CANCELLING,
        Events.PRINT_CANCELLED,
        Events.PRINT_DONE,
        Events.PRINT_FAILED,
        Events.PRINT_PAUSED,
        Events.PRINT_RESUMED,
        Events.PRINT_STARTED,
    ]

    def __init__(self, queue, plugin, plugin_settings: PluginSettingsMemoize):
        self.exit = threading.Event()
        self.queue = queue
        self.plugin = plugin
        self.plugin_settings = plugin_settings

        # File "/home/pi/octoprint-nanny-plugin/octoprint_nanny/workers/mqtt.py", line 169, in __init__
        # Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_STOP: [plugin_settings.reset_print_session]
        # custom events are not registered at time of class initialization
        self._callbacks: Dict[str, List[Callable]] = {
            Events.PRINT_DONE: [plugin_settings.reset_print_session],
            Events.PRINT_FAILED: [plugin_settings.reset_print_session],
            Events.PRINT_CANCELLED: [plugin_settings.reset_print_session],
            # plugin events are not always registered to octoprint.events.Events object when this class is initialized
            # instead, reference plugin events by string literal
            # Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
            "plugin_octoprint_nanny_monitoring_frame_bytes": [
                self.handle_monitoring_frame_bytes
            ],
        }

    def register_callbacks(self, callbacks) -> Dict[str, List[Callable]]:
        """
        Register callback functions executed during event publish loop
        """
        for k, v in callbacks.items():
            if self._callbacks.get(k) is None:
                self._callbacks[k] = [v]
            else:
                self._callbacks[k].append(v)
        logging.info(f"Registered MQTTSubscribeWorker._callbacks {self._callbacks}")
        return self._callbacks

    def run(self):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )  # TODO Maybe run single-threaded to avoid initializing multiple mqtt clients in backoff/retry situation :thinkface:
        loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))
        loop.close()

    def publish_octoprint_event_telemetry(self, event):
        payload = build_telemetry_event(event, self.plugin)
        return self.plugin_settings.mqtt_client.publish_octoprint_event(
            payload.to_dict()
        )

    @beeline.traced("MQTTPublisherWorker.handle_monitoring_frame_bytes")
    def handle_monitoring_frame_bytes(
        self, event_type: str, event_data: Dict[str, Any], **kwargs
    ):
        assert event_type == Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
        beeline.add_context(self.plugin_settings.metadata.to_dict())
        if self.plugin_settings.monitoring_active:
            image_bytes = event_data["image"]
            byte_size = sys.getsizeof(image_bytes)
            pimage = PIL.Image.open(io.BytesIO(image_bytes))
            (w, h) = pimage.size
            context = dict(image_bytes=byte_size, image_w=w, image_h=h)
            beeline.add_context(context)

            image = Image(height=h, width=w, data=image_bytes)

            monitoring_image = build_monitoring_image(
                image_bytes=image_bytes,
                width=w,
                height=h,
                metadata_pb=self.plugin_settings.metadata_pb,
            )
            b64_image = base64.b64encode(image_bytes)
            if (
                self.plugin_settings.monitoring_active
                and self.plugin_settings.webcam_to_octoprint_ws
            ):
                self.plugin._event_bus.fire(
                    Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
                    payload=b64_image,
                )
            if self.plugin_settings.webcam_to_mqtt:
                return self.plugin_settings.mqtt_client.publish_monitoring_image(
                    monitoring_image.SerializeToString()
                )

    async def _loop(self) -> None:
        try:
            event = self.queue.get(timeout=1)
        except queue.Empty as e:
            return
        event_type = event.get("event_type")
        if event_type is None:
            logger.error(
                "MQTTPublisherWorker ignoring msg without event_type {event}".format(
                    event=event
                )
            )
            return
        logger.debug(f"MQTTPublisherWorker received event_type={event_type}")

        tracked = self.plugin_settings.event_is_tracked(event_type)
        if tracked:
            mqtt_msginfo = self.publish_octoprint_event_telemetry(event)
            logger.debug(f"Published MQTTMessageInfo={mqtt_msginfo}")
        else:
            logger.warning(
                f"MQTTPublisherWorker received untracked event_type={event_type}"
            )

        handler_fns = self._callbacks.get(event_type)
        if handler_fns is None:
            logger.debug(f"No {self.__class__} handler registered for {event_type}")
            return

        for handler_fn in handler_fns:
            logger.debug(f"MQTTPublisherWorker calling handler_fn={handler_fn}")
            if inspect.isawaitable(handler_fn) or inspect.iscoroutinefunction(
                handler_fn
            ):
                await handler_fn(**event)
            else:
                handler_fn(**event)

    async def loop_forever(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info(f"Started {self.__class__}.loop_forever ")
        while not self.exit.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired as e:
                logger.debug(e)
        logger.info(f"Exiting soon {self.__class__}.loop_forever")

    def shutdown(self, **kwargs):
        logger.warning("MQTTPublisherWorker shutdown initiated")
        self.exit.set()


class MQTTSubscriberWorker:
    def __init__(self, queue, plugin, plugin_settings: PluginSettingsMemoize):

        self.exit = threading.Event()
        self.queue = queue
        self.plugin = plugin
        self.plugin_settings = plugin_settings
        self._callbacks = {
            "plugin_octoprint_nanny_connect_test_mqtt_pong": [self.handle_pong]
        }

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )

        self.loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))
        self.loop.close()

    def handle_pong(self, event=None, **kwargs):
        logger.info(f"Received pong event {event}")
        return self.plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_CONNECT_TEST_MQTT_PONG_SUCCESS
        )

    def register_callbacks(self, callbacks):
        for k, v in callbacks.items():
            if self._callbacks.get(k) is None:
                self._callbacks[k] = [v]
            else:
                self._callbacks[k].append(v)
        logging.info(f"Registered MQTTSubscribeWorker._callbacks {self._callbacks}")
        return self._callbacks

    async def loop_forever(self):
        logger.info(f"Started {self.__class__}.loop_forever")
        while not self.exit.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired as e:
                logger.debug(e)
        logger.info(f"Exiting soon {self.__class__}.loop_forever")

    @beeline.traced("MQTTSubscriberWorker._handle_remote_control_command")
    async def _handle_remote_control_command(self, topic, message):
        # add metadata to honeycomb trace context
        beeline.add_context(self.plugin_settings.metadata.to_dict())

        event_type = message.get("octoprint_event_type")

        if event_type is None:
            logger.warning("Ignoring received message where octoprint_event_type=None")
            return

        command_id = message.get("remote_control_command_id")

        await self.plugin_settings.rest_client.update_remote_control_command(
            command_id, received=True, metadata=self.plugin_settings.metadata.to_dict()
        )

        handler_fns = self._callbacks.get(event_type)

        logger.info(
            f"Got handler_fn={handler_fns} from WorkerManager._callbacks for octoprint_event_type={event_type}"
        )

        if handler_fns is not None:
            for handler_fn in handler_fns:
                try:
                    if inspect.isawaitable(handler_fn) or inspect.iscoroutinefunction(
                        handler_fn
                    ):
                        await handler_fn(event=message, event_type=event_type)
                    else:
                        handler_fn(event=message, event_type=event_type)

                    # set success state
                    await self.plugin_settings.rest_client.update_remote_control_command(
                        command_id,
                        success=True,
                        metadata=self.plugin_settings.metadata.to_dict(),
                    )
                except Exception as e:
                    logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                    await self.plugin_settings.rest_client.update_remote_control_command(
                        command_id,
                        success=False,
                        metadata=self.plugin_settings.metadata.to_dict(),
                    )

    async def _loop(self):

        trace = beeline.start_trace()
        span = beeline.start_span({"name": "WorkerManager.queue.coro_get"})

        try:
            payload = self.queue.get(timeout=1)
        except queue.Empty as e:
            return

        # add metadata to honeycomb trace context
        context = dict(event=payload)
        context.update(self.plugin_settings.metadata.to_dict())

        beeline.add_context(context)
        beeline.finish_span(span)

        topic = payload.get("topic")

        if topic is None:
            logger.warning("Ignoring received message where topic=None")

        elif topic == self.plugin_settings.mqtt_client.remote_control_commands_topic:
            await self._handle_remote_control_command(**payload)

        elif topic == self.plugin_settings.mqtt_client.config_topic:
            await self._handle_config_update(**payload)

        else:
            logging.error(f"No handler for topic={topic} in _loop")

        beeline.finish_trace(trace)

    @beeline.traced("MQTTSubscriberWorker._handle_config_update")
    async def _handle_config_update(self, topic, message):
        # add metadata to honeycomb trace context
        beeline.add_context(self.plugin_settings.metadata.to_dict())

        device_config = printnanny_api_client.ExperimentDeviceConfig(**message)

        labels = device_config.artifact.get("labels")
        artifacts = device_config.artifact.get("artifacts")
        version = device_config.artifact.get("version")
        metadata = device_config.artifact.get("metadata")

        async def _download(session, url, filename):
            async with session.get(url) as res:
                with open(filename, "w+") as f:
                    content = await res.text()
                    return f.write(content)

        async def _data_file(content, filename):
            with open(filename, "w+") as f:
                return f.write(content)

        async with aiohttp.ClientSession() as session:
            await _download(
                session,
                labels,
                os.path.join(self.plugin_settings.data_folder, "labels.txt"),
            )
            await _download(
                session,
                artifacts,
                os.path.join(self.plugin_settings.data_folder, "model.tflite"),
            )
        await _data_file(
            version,
            os.path.join(self.plugin_settings.data_folder, "version.txt"),
        )
        await _data_file(
            json.dumps(metadata),
            os.path.join(self.plugin_settings.data_folder, "metadata.json"),
        )

    def shutdown(self):
        logger.warning("MQTTSubscriberWorker shutdown initiated")
        self.exit.set()
