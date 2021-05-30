import aiohttp
import asyncio
import concurrent
import inspect
import io
import json
import logging
import os
import queue
import threading

import logging

import beeline

import print_nanny_client

from octoprint.events import Events

from print_nanny_client import TelemetryEvent, OctoprintEnvironment
from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS
from octoprint_nanny.exceptions import PluginSettingsRequired

from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint_nanny.types import MonitoringModes

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.mqtt")


class MQTTManager:
    def __init__(
        self,
        mqtt_send_queue: queue.Queue,
        mqtt_receive_queue: queue.Queue,
        plugin,
    ):

        self.mqtt_send_queue = mqtt_send_queue
        self.mqtt_receive_queue = mqtt_receive_queue
        halt = threading.Event()
        self.halt = halt
        self.plugin = plugin
        self._worker_threads = []
        self.publisher_worker = MQTTPublisherWorker(self.mqtt_send_queue, self.plugin)
        self.subscriber_worker = MQTTSubscriberWorker(
            self.mqtt_receive_queue, self.plugin
        )

    def _drain(self):
        """
        Halt running workers and wait pending work
        """
        self.halt.set()

        for worker in self._worker_threads:
            logger.info(f"Waiting for worker={worker} thread to drain")
            worker.join()

    def _reset(self):
        self.halt = threading.Event()
        self._worker_threads = []

    def start(self, **kwargs):
        """
        (re)initialize and start worker threads
        """
        self._reset()

        try:
            mqtt_client = self.plugin.settings.mqtt_client
        except PluginSettingsRequired as e:
            logger.warning(e)
            logger.warning(
                "MQTTManager.start was called without device registration set, ignoring"
            )

        logger.info("MQTTManager.start was called")

        self._workers = [
            self.publisher_worker,
            self.subscriber_worker,
            mqtt_client,
        ]
        for worker in self._workers:
            thread = threading.Thread(
                target=worker.run, name=str(worker.__class__), args=(self.halt,)
            )
            thread.daemon = True
            self._worker_threads.append(thread)
            thread.start()

    def stop(self):
        logger.info("MQTTManager.stop was called")
        self._drain()


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

    def __init__(self, queue, plugin):

        self.halt = None
        self.queue = queue
        self.plugin = plugin
        self._callbacks = {}
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    def register_callbacks(self, callbacks):
        for k, v in callbacks.items():
            if self._callbacks.get(k) is None:
                self._callbacks[k] = [v]
            else:
                self._callbacks[k].append(v)
        logging.info(f"Registered MQTTSubscribeWorker._callbacks {self._callbacks}")
        return self._callbacks

    def run(self, halt):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        self.halt = halt
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))

        return loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))

    async def publish_octoprint_event_telemetry(self, event):
        # event_type = event.get("event_type")
        # event_data =
        # event.update(
        #     {
        #         "metadata": self.plugin.settings.metadata.to_dict(),
        #         "octoprint_job": self.plugin.settings.get_current_octoprint_job(),
        #     }
        # )
        import pdb

        pdb.set_trace()
        environment = OctoprintEnvironment()
        payload = TelemetryEvent(
            print_session=self.plugin.settings.print_session,
            environment=environment ** event,
        )

        self.plugin.settings.mqtt_client.publish_octoprint_event(event)

    async def _loop(self):
        try:

            try:
                event = self.queue.get(timeout=1)
            except queue.Empty as e:
                return
            span = self._honeycomb_tracer.start_span(
                {"name": "MQTTPublisherWorker._loop"}
            )
            self._honeycomb_tracer.add_context(dict(event=event))
            self._honeycomb_tracer.finish_span(span)

            if isinstance(event, bytearray):
                if self.plugin.settings.monitoring_mode == MonitoringModes.LITE:
                    self.plugin.settings.mqtt_client.publish_monitoring_frame_post(
                        event
                    )
                elif (
                    self.plugin.settings.monitoring_mode
                    == MonitoringModes.ACTIVE_LEARNING
                ):
                    self.plugin.settings.mqtt_client.publish_monitoring_frame_raw(event)
                return
            event_type = event.get("event_type")
            if event_type is None:
                logger.error(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event=event
                    )
                )
                return

            logger.debug(f"MQTTPublisherWorker received event_type={event_type}")
            tracked = self.plugin.settings.event_is_tracked(event_type)
            if tracked:
                await self.publish_octoprint_event_telemetry(event)

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
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"REST client raised exception {e}", exc_info=True)

    async def loop_forever(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info(f"Started {self.__class__}.loop_forever ")
        while not self.halt.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired as e:
                logger.debug(e)
        logger.info(f"Exiting soon {self.__class__}.loop_forever")


class MQTTSubscriberWorker:
    def __init__(self, queue, plugin):

        self.halt = None
        self.queue = queue
        self.plugin = plugin
        self._callbacks = {
            "plugin_octoprint_nanny_connect_test_mqtt_pong": [self.handle_pong]
        }
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    def run(self, halt):
        self.halt = halt
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )

        return self.loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))

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
        while not self.halt.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired as e:
                logger.debug(e)
        logger.info(f"Exiting soon {self.__class__}.loop_forever")

    @beeline.traced("MQTTSubscriberWorker._handle_remote_control_command")
    async def _handle_remote_control_command(self, topic, message):
        event_type = message.get("octoprint_event_type")

        if event_type is None:
            logger.warning("Ignoring received message where octoprint_event_type=None")
            return

        command_id = message.get("remote_control_command_id")

        await self.plugin.settings.rest_client.update_remote_control_command(
            command_id, received=True, metadata=self.plugin.settings.metadata.to_dict()
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
                    await self.plugin.settings.rest_client.update_remote_control_command(
                        command_id,
                        success=True,
                        metadata=self.plugin.settings.metadata.to_dict(),
                    )
                except Exception as e:
                    logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                    await self.plugin.settings.rest_client.update_remote_control_command(
                        command_id,
                        success=False,
                        metadata=self.plugin.settings.metadata.to_dict(),
                    )

    async def _loop(self):

        trace = self._honeycomb_tracer.start_trace()
        span = self._honeycomb_tracer.start_span(
            {"name": "WorkerManager.queue.coro_get"}
        )

        try:
            payload = self.queue.get(timeout=1)
        except queue.Empty as e:
            return

        self._honeycomb_tracer.add_context(dict(event=payload))
        self._honeycomb_tracer.finish_span(span)

        topic = payload.get("topic")

        if topic is None:
            logger.warning("Ignoring received message where topic=None")

        elif topic == self.plugin.settings.mqtt_client.remote_control_commands_topic:
            await self._handle_remote_control_command(**payload)

        elif topic == self.plugin.settings.mqtt_client.config_topic:
            await self._handle_config_update(**payload)

        else:
            logging.error(f"No handler for topic={topic} in _loop")

        self._honeycomb_tracer.finish_trace(trace)

    @beeline.traced("MQTTSubscriberWorker._handle_config_update")
    async def _handle_config_update(self, topic, message):

        device_config = print_nanny_client.ExperimentDeviceConfig(**message)

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
                os.path.join(self.plugin.get_plugin_data_folder(), "labels.txt"),
            )
            await _download(
                session,
                artifacts,
                os.path.join(self.plugin.get_plugin_data_folder(), "model.tflite"),
            )
        await _data_file(
            version,
            os.path.join(self.plugin.get_plugin_data_folder(), "version.txt"),
        )
        await _data_file(
            json.dumps(metadata),
            os.path.join(self.plugin.get_plugin_data_folder(), "metadata.json"),
        )
