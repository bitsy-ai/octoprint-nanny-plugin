import aiofiles
import aiohttp
import io
import inspect
import logging
import os
import threading


import beeline

import print_nanny_client

from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint_nanny.clients.rest import RestAPIClient, API_CLIENT_EXCEPTIONS
from octoprint_nanny.predictor import (
    PredictWorker,
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)
from octoprint_nanny.settings import PluginSettingsMemoizeMixin

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.")


class ReceiveWorkerMixin(PluginSettingsMemoizeMixin):
    async def _remote_control_receive_loop_forever(self):
        logger.info("Started _remote_control_receive_loop_forever")
        while not self._thread_halt.is_set():
            try:
                await self._remote_control_receive_loop()
            except PluginSettingsRequired:
                pass
        logger.info("Exiting soon _remote_control_receive_loop_forever")

    @beeline.traced("WorkerManager._remote_control_snapshot")
    async def _remote_control_snapshot(self, command_id):
        async with aiohttp.ClientSession() as session:
            res = await session.get(self.snapshot_url)
            snapshot_io = io.BytesIO(await res.read())

        return await self.rest_client.create_snapshot(
            image=snapshot_io, command=command_id
        )

    @beeline.traced("WorkerManager._handle_remote_control_command")
    async def _handle_remote_control_command(self, topic, message):
        event_type = message.get("octoprint_event_type")

        if event_type is None:
            logger.warning("Ignoring received message where octoprint_event_type=None")
            return

        command_id = message.get("remote_control_command_id")

        await self._remote_control_snapshot(command_id)

        metadata = self.get_device_metadata()
        await self.rest_client.update_remote_control_command(
            command_id, received=True, metadata=metadata
        )

        handler_fn = self._remote_control_event_handlers.get(event_type)

        logger.info(
            f"Got handler_fn={handler_fn} from WorkerManager._remote_control_event_handlers for octoprint_event_type={event_type}"
        )
        if handler_fn:
            try:
                if inspect.isawaitable(handler_fn):
                    await handler_fn(event=message, event_type=event_type)
                else:
                    handler_fn(event=message, event_type=event_type)

                metadata = self.get_device_metadata()
                # set success state
                await self.rest_client.update_remote_control_command(
                    command_id,
                    success=True,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Error calling handler_fn {handler_fn} \n {e}")
                metadata = self.get_device_metadata()
                await self.rest_client.update_remote_control_command(
                    command_id,
                    success=False,
                    metadata=metadata,
                )

    @beeline.traced("WorkerManager._remote_control_receive_loop")
    async def _remote_control_receive_loop(self):

        trace = self._honeycomb_tracer.start_trace()
        span = self._honeycomb_tracer.start_span(
            {"name": "WorkerManager.remote_control_queue.coro_get"}
        )
        payload = await self.remote_control_queue.coro_get()
        self._honeycomb_tracer.add_context(dict(event=payload))
        self._honeycomb_tracer.finish_span(span)

        topic = payload.get("topic")

        if topic is None:
            logger.warning("Ignoring received message where topic=None")

        elif topic == self.mqtt_client.remote_control_command_topic:
            await self._handle_remote_control_command(**payload)

        elif topic == self.mqtt_client.mqtt_config_topic:
            await self.get_device_config(**payload)

        else:
            logging.error(
                f"No handler for topic={topic} in _remote_control_receive_loop"
            )

        self._honeycomb_tracer.finish_trace(trace)

    @beeline.traced("WorkerManager.get_device_config")
    async def get_device_config(self, topic, message):
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


class TelemetryWorkerMixin:
    @beeline.traced("WorkerManager._publish_octoprint_event_telemetry")
    async def _publish_octoprint_event_telemetry(self, event):
        event_type = event.get("event_type")
        logger.info(f"_publish_octoprint_event_telemetry {event}")
        event.update(
            dict(
                user_id=self.user_id,
                device_id=self.device_id,
                device_cloudiot_name=self.device_cloudiot_name,
            )
        )
        event.update(self.get_device_metadata())

        if event_type in self.PRINT_JOB_EVENTS:
            event.update(self.get_print_job_metadata())
        self.mqtt_client.publish_octoprint_event(event)

    @beeline.traced("WorkerManager._telemetry_queue_send_loop")
    async def _telemetry_queue_send_loop(self):
        try:
            span = self._honeycomb_tracer.start_span(
                {"name": "WorkerManager.telemetry_queue.coro_get"}
            )

            event = await self.telemetry_queue.coro_get()

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

            if self.event_in_tracked_telemetry(event_type):
                await self._publish_octoprint_event_telemetry(event)
            else:
                if event_type not in self.MUTED_EVENTS:
                    logger.warning(f"Discarding {event_type} with payload {event}")
                return

            # run local handler fn
            handler_fn = self._local_event_handlers.get(event_type)
            if handler_fn:

                if inspect.isawaitable(handler_fn):
                    await handler_fn(**event)
                else:
                    handler_fn(**event)
        except API_CLIENT_EXCEPTIONS as e:
            logger.error(f"REST client raised exception {e}", exc_info=True)

    async def _telemetry_queue_send_loop_forever(self):
        """
        Publishes telemetry events via HTTP
        """
        logger.info("Started _telemetry_queue_send_loop_forever")
        while not self._thread_halt.is_set():
            try:
                await self._telemetry_queue_send_loop()
            except PluginSettingsRequired as e:
                pass
        logging.info("Exiting soon _telemetry_queue_send_loop_forever")


class MonitoringWorkerMixin:
    @beeline.traced("WorkerManager.init_monitoring_threads")
    def init_monitoring_threads(self):
        self._monitoring_halt = threading.Event()

        self.predict_worker = PredictWorker(
            self.snapshot_url,
            self.calibration,
            self.octo_ws_queue,
            self.pn_ws_queue,
            self.telemetry_queue,
            self.monitoring_frames_per_minute,
            self._monitoring_halt,
            self.plugin._event_bus,
            trace_context=self.get_device_metadata(),
        )

        self.predict_worker_thread = threading.Thread(target=self.predict_worker.run)
        self.predict_worker_thread.daemon = True

        self.websocket_worker = WebSocketWorker(
            self.ws_url,
            self.auth_token,
            self.pn_ws_queue,
            self.shared.print_job_id,
            self.device_id,
            self._monitoring_halt,
            trace_context=self.get_device_metadata(),
        )
        self.pn_ws_thread = threading.Thread(target=self.websocket_worker.run)
        self.pn_ws_thread.daemon = True

    @beeline.traced("WorkerManager.stop_monitoring")
    def stop_monitoring(self, event_type=None, **kwargs):
        """
        joins and terminates dedicated prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.stop_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.monitoring_active = False

        asyncio.run_coroutine_threadsafe(
            self.rest_client.update_octoprint_device(
                self.device_id, monitoring_active=False
            ),
            self.loop,
        ).result()

        self.stop_monitoring_threads()

    @beeline.traced("WorkerManager.start_monitoring")
    def start_monitoring(self, event_type=None, **kwargs):
        """
        starts prediction and pn websocket processes
        """
        logging.info(
            f"WorkerManager.start_monitoring called by event_type={event_type} event={kwargs}"
        )
        self.monitoring_active = True

        asyncio.run_coroutine_threadsafe(
            self.rest_client.update_octoprint_device(
                self.device_id, monitoring_active=True
            ),
            self.loop,
        ).result()

        self.init_monitoring_threads()
        self.start_monitoring_threads()


class MultiWorkerMixin(
    TelemetryWorkerMixin,
    ReceiveWorkerMixin,
    MonitoringWorkerMixin,
):
    pass
