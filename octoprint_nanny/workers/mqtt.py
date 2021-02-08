import aiofiles
import aiohttp
import aioprocessing
import asyncio
import concurrent
import io
import inspect
import logging
import os
import threading
import queue

import logging

import beeline

import print_nanny_client

from octoprint.events import Events

from octoprint_nanny.clients.rest import API_CLIENT_EXCEPTIONS
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.settings import PluginSettingsMemoize

from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint_nanny.predictor import BOUNDING_BOX_PREDICT_EVENT

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.mqtt")


class MQTTManager:
    def __init__(
        self,
        mqtt_send_queue: aioprocessing.Queue,
        mqtt_receive_queue: aioprocessing.Queue,
        plugin_settings: PluginSettingsMemoize,
        plugin,
    ):

        self.plugin_settings = plugin_settings
        self.mqtt_send_queue = mqtt_send_queue
        self.mqtt_receive_queue = mqtt_receive_queue
        halt = threading.Event()
        self.halt = halt
        self.plugin = plugin

        self.publisher_worker = MQTTPublisherWorker(
            self.halt, self.mqtt_send_queue, self.plugin_settings
        )
        self.subscriber_worker = MQTTSubscriberWorker(
            self.halt, self.mqtt_receive_queue, self.plugin_settings, self.plugin
        )
        self.client_worker = MQTTClientWorker(self.halt, self.plugin_settings)
        self._workers = []
        self._worker_threads = []

    @beeline.traced("MQTTManager._drain")
    def _drain(self):
        """
        Halt running workers and wait pending work
        """
        self.halt.set()

        try:
            logger.info("Waiting for MQTTManager.mqtt_client network loop to finish")
            while self.client_worker.plugin_settings.mqtt_client.client.is_connected():
                self.plugin_settings.plugin_settings.mqtt_client.client.disconnect()
            logger.info("Stopping MQTTManager.mqtt_client network loop")
            self.plugin_settings.mqtt_client.client.loop_stop()
        except PluginSettingsRequired:
            pass

        for worker in self._worker_threads:
            logger.info(f"Waiting for worker={worker} thread to drain")
            worker.join()

    @beeline.traced("MQTTManager._reset")
    def _reset(self):
        self.halt = threading.Event()
        self.publisher_worker = MQTTPublisherWorker(
            self.halt, self.mqtt_send_queue, self.plugin_settings
        )
        self.subscriber_worker = MQTTSubscriberWorker(
            self.halt, self.mqtt_receive_queue, self.plugin_settings, self.plugin
        )
        self.client_worker = MQTTClientWorker(
            self.halt, self.plugin_settings.mqtt_client
        )

        self._workers = [
            self.client_worker,
            self.publisher_worker,
            self.subscriber_worker,
        ]
        self._worker_threads = []

    @beeline.traced("MQTTManager.start")
    def start(self):
        """
        (re)initialize and start worker threads
        """
        logger.info("MQTTManager.start was called")
        self._reset()
        for worker in self._workers:
            thread = threading.Thread(target=worker.run)
            thread.daemon = True
            self._worker_threads.append(thread)
            thread.start()

    @beeline.traced("MQTTManager.stop")
    def stop(self):
        logger.info("MQTTManager.stop was called")
        self._drain()


class MQTTClientWorker:
    """
    Manages paho MQTT client's network loop on behalf of Publisher/Subscriber Workers
    https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#network-loop
    """

    def __init__(self, halt, plugin_settings):

        self.plugin_settings = plugin_settings
        self.halt = halt

    @beeline.traced("MQTTClientWorker.run")
    def run(self):
        try:
            return self.plugin_settings.mqtt_client.run(self.halt)
        except PluginSettingsRequired:
            pass
        logger.warning("MQTTClientWorker will exit soon")


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
    # do not warn when the following events are skipped on telemetry update
    MUTED_EVENTS = [Events.Z_CHANGE, "plugin_octoprint_nanny_predict_done"]

    def __init__(self, halt, queue, plugin_settings):

        self.halt = halt
        self.queue = queue
        self.plugin_settings = plugin_settings
        self._callbacks = {}
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    @beeline.traced("MQTTPublisherWorker.register_callbacks")
    def register_callbacks(self, callbacks):
        for k, v in callbacks.items():
            if self._callbacks.get(k) is None:
                self._callbacks[k] = [v]
            else:
                self._callbacks[k].append(v)
        logging.info(f"Registered MQTTSubscribeWorker._callbacks {self._callbacks}")
        return self._callbacks

    @beeline.traced("MQTTPublisherWorker.run")
    def run(self):
        """
        Telemetry worker's event loop is exposed as WorkerManager.loop
        this permits other threads to schedule work in this event loop with asyncio.run_coroutine_threadsafe()
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))

        return loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))

    @beeline.traced("MQTTPublisherWorker._publish_octoprint_event_telemetry")
    async def _publish_octoprint_event_telemetry(self, event):
        event_type = event.get("event_type")
        logger.info(f"_publish_octoprint_event_telemetry {event}")
        event.update(
            dict(
                user_id=self.plugin_settings.user_id,
                device_id=self.plugin_settings.device_id,
                device_cloudiot_name=self.plugin_settings.device_cloudiot_name,
            )
        )
        event.update(self.plugin_settings.get_device_metadata())

        if event_type in self.PRINT_JOB_EVENTS:
            event.update(self.plugin_settings.get_print_job_metadata())
        self.plugin_settings.mqtt_client.publish_octoprint_event(event)

    @beeline.traced("MQTTPublisherWorker._publish_bounding_box_telemetry")
    async def _publish_bounding_box_telemetry(self, event):
        event.update(
            dict(
                user_id=self.plugin_settings.user_id,
                device_id=self.plugin_settings.device_id,
                device_cloudiot_name=self.plugin_settings.device_cloudiot_name,
            )
        )
        self.plugin_settings.mqtt_client.publish_bounding_boxes(event)

    @beeline.traced("MQTTPublisherWorker._loop")
    async def _loop(self):
        try:
            span = self._honeycomb_tracer.start_span(
                {"name": "WorkerManager.queue.coro_get"}
            )

            try:
                event = self.queue.get_nowait()
            except queue.Empty:
                return

            self._honeycomb_tracer.add_context(dict(event=event))
            self._honeycomb_tracer.finish_span(span)

            event_type = event.get("event_type")
            if event_type is None:
                logger.warning(
                    "Ignoring enqueued msg without type declared {event}".format(
                        event=event
                    )
                )
                return

            if event_type == BOUNDING_BOX_PREDICT_EVENT:
                await self._publish_bounding_box_telemetry(event)
                return

            if self.plugin_settings.event_in_tracked_telemetry(event_type):
                await self._publish_octoprint_event_telemetry(event)
            else:
                if event_type not in self.MUTED_EVENTS:
                    logger.warning(f"Discarding {event_type} with payload {event}")
                return

            handler_fns = self._callbacks.get(event_type)
            for handler_fn in handler_fns:
                if handler_fn:
                    if inspect.isawaitable(handler_fn):
                        await handler_fn(**event)
                    else:
                        handler_fn(**event)
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"REST client raised exception {e}", exc_info=True)

    async def loop_forever(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info("Started loop_forever")
        while not self.halt.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired as e:
                pass
        logging.info("Exiting soon loop_forever")


class MQTTSubscriberWorker:
    def __init__(self, halt, queue, plugin_settings, plugin):

        self.halt = halt
        self.queue = queue
        self.plugin_settings = plugin_settings
        self.plugin = plugin
        self._callbacks = {}
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    @beeline.traced("MQTTSubscriberWorker.run")
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )

        return self.loop.run_until_complete(asyncio.ensure_future(self.loop_forever()))

    @beeline.traced("MQTTSubscriberWorker.register_callbacks")
    def register_callbacks(self, callbacks):
        for k, v in callbacks.items():
            if self._callbacks.get(k) is None:
                self._callbacks[k] = [v]
            else:
                self._callbacks[k].append(v)
        logging.info(f"Registered MQTTSubscribeWorker._callbacks {self._callbacks}")
        return self._callbacks

    async def loop_forever(self):
        logger.info("Started loop_forever")
        while not self.halt.is_set():
            try:
                await self._loop()
            except PluginSettingsRequired:
                pass
        logger.info("Exiting soon MQTTSubscribeWorker.loop_forever")

    @beeline.traced("MQTTSubscriberWorker._remote_control_snapshot")
    async def _remote_control_snapshot(self, command_id):
        async with aiohttp.ClientSession() as session:
            res = await session.get(self.plugin_settings.snapshot_url)
            snapshot_io = io.BytesIO(await res.read())

        return await self.plugin_settings.rest_client.create_snapshot(
            image=snapshot_io, command=command_id
        )

    @beeline.traced("MQTTSubscriberWorker._handle_remote_control_command")
    async def _handle_remote_control_command(self, topic, message):
        event_type = message.get("octoprint_event_type")

        if event_type is None:
            logger.warning("Ignoring received message where octoprint_event_type=None")
            return

        command_id = message.get("remote_control_command_id")

        await self._remote_control_snapshot(command_id)

        metadata = self.plugin_settings.get_device_metadata()
        await self.plugin_settings.rest_client.update_remote_control_command(
            command_id, received=True, metadata=metadata
        )

        handler_fns = self._callbacks.get(event_type)

        logger.info(
            f"Got handler_fn={handler_fns} from WorkerManager._callbacks for octoprint_event_type={event_type}"
        )
        if handler_fns is not None:
            for handler_fn in handler_fns:
                try:
                    if inspect.isawaitable(handler_fn):
                        await handler_fn(event=message, event_type=event_type)
                    else:
                        handler_fn(event=message, event_type=event_type)

                    metadata = self.plugin_settings.get_device_metadata()
                    # set success state
                    await self.plugin_settings.rest_client.update_remote_control_command(
                        command_id,
                        success=True,
                        metadata=metadata,
                    )
                except Exception as e:
                    logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                    metadata = self.plugin_settings.get_device_metadata()
                    await self.plugin_settings.rest_client.update_remote_control_command(
                        command_id,
                        success=False,
                        metadata=metadata,
                    )

    @beeline.traced("MQTTSubscriberWorker._loop")
    async def _loop(self):

        trace = self._honeycomb_tracer.start_trace()
        span = self._honeycomb_tracer.start_span(
            {"name": "WorkerManager.queue.coro_get"}
        )

        try:
            event = self.queue.get_nowait()
        except queue.Empty:
            return
        self._honeycomb_tracer.add_context(dict(event=payload))
        self._honeycomb_tracer.finish_span(span)

        topic = payload.get("topic")

        if topic is None:
            logger.warning("Ignoring received message where topic=None")

        elif topic == self.plugin_settings.mqtt_client.remote_control_command_topic:
            await self._handle_remote_control_command(**payload)

        elif topic == self.plugin_settings.mqtt_client.config_topic:
            await self._handle_config_update(**payload)

        else:
            logging.error(f"No handler for topic={topic} in _loop")

        self._honeycomb_tracer.finish_trace(trace)

    @beeline.traced("MQTTSubscriberWorker._handle_config_updat")
    async def _handle_config_update(self, topic, message):
        device_config = print_nanny_client.ExperimentDeviceConfig(**message)

        labels = device_config.artifact.get("labels")
        artifacts = device_config.artifact.get("artifacts")
        version = device_config.artifact.get("version")
        metadata = device_config.artifact.get("metadata")

        async def _download(session, url, filename):
            async with session.get(url) as res:
                async with aiofiles.open(filename, "w+") as f:
                    content = await res.text()
                    return await f.write(content)

        async def _data_file(content, filename):
            async with aiofiles.open(filename, "w+") as f:
                return await f.write(content)

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
            metadata,
            os.path.join(self.plugin.get_plugin_data_folder(), "metadata.json"),
        )
