import concurrent
import asyncio
import pytz
import aiohttp
import logging
import PIL
import backoff
from datetime import datetime
import multiprocessing
import numpy as np
import threading

import beeline

from octoprint.events import Events
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint.events import Events
from octoprint_nanny.types import (
    MonitoringModes,
    MonitoringFrame,
    Image,
)
from websockets.legacy.client import connect as ws_connect


from octoprint_nanny.utils.encoder import NumpyEncoder
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.workers.monitoring")


class MonitoringWorker:
    def __init__(self, queue: multiprocessing.Queue, plugin):
        self.exit = threading.Event()
        self.queue = queue
        self.plugin = plugin
        self.plugin_settings = plugin.settings
        self._snapshot_url = self.plugin_settings.snapshot_url
        self._ws_url = f"{self.plugin_settings.ws_url}{self.plugin_settings.octoprint_device_id}/video/upload/"
        self._fpm = self.plugin_settings.monitoring_frames_per_minute
        self._sleep_interval = 60 / int(self._fpm)

    async def load_url_buffer(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self._snapshot_url) as res:
                # assert res.headers["content-type"] == "image/jpeg"
                b = await res.read()
                await self.ws.send(b)
                return b

    async def _loop(self):
        ts = int(datetime.now(pytz.utc).timestamp())
        image_bytes = await self.load_url_buffer()
        self.queue.put_nowait(
            {
                "event_type": Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES,
                "event_data": {"image": image_bytes, "ts": ts},
            }
        )

    @backoff.on_exception(
        backoff.expo,
        (
            ConnectionResetError,
            aiohttp.client_exceptions.ServerDisconnectedError,
            aiohttp.client_exceptions.ClientOSError,
        ),
        jitter=backoff.random_jitter,
        logger=logger,
        max_time=600,
    )
    async def _producer(self):
        """
        Calculates prediction and publishes result to subscriber queues
        """
        logger.info("Started MonitoringWorker.producer thread")
        async with ws_connect(
            self._ws_url,
            extra_headers=(
                ("Authorization", f"Bearer {self.plugin_settings.auth_token}"),
            ),
        ) as ws:
            logger.info(f"Initialized websocket {ws}")
            self.ws = ws
            logger.info("Initialized ws connection")
            while not self.exit.is_set():
                await asyncio.sleep(self._sleep_interval)
                await self._loop()

        logger.warning("Halt event set, worker will exit soon")

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_debug(True)
        self.loop.set_default_executor(concurrent.futures.ThreadPoolExecutor())
        task = asyncio.ensure_future(self._producer())
        self.loop.run_until_complete(task)
        self.loop.close()

    def shutdown(self):
        logger.warning("MonitoringWorkerV2 shutdown initiated")
        self.exit.set()


class MonitoringManager:
    def __init__(self, mqtt_send_queue, plugin):

        self.mqtt_send_queue = mqtt_send_queue
        self.plugin = plugin
        self._workers = []
        self._worker_threads = []

    @beeline.traced("MonitoringManager._drain")
    def _drain(self):

        for i, worker in enumerate(self._workers):
            logger.info(f"Shutting down worker={worker} process to drain")
            worker.shutdown()
            logger.info(f"Waiting for worker={worker} process to drain")
            self._worker_threads[i].join()

    @beeline.traced("MonitoringManager._reset")
    def _reset(self):
        self._predict_worker = MonitoringWorker(
            self.mqtt_send_queue,
            self.plugin,
        )
        self._workers = [self._predict_worker]
        logger.info(f"Finished resetting MonitoringManager")

    @beeline.traced("MonitoringManager.start")
    async def start(self, print_session=None, **kwargs):
        monitoring_active = self.plugin._settings.get(["monitoring_active"])
        if not monitoring_active:
            self.plugin._settings.set(["monitoring_active"], True)
            self._reset()
            self.plugin.settings.reset_print_session()
            await self.plugin.settings.create_print_session()
            logger.info(
                f"Initializing monitoring workers with print_session={self.plugin.settings.print_session.session}"
            )
            for worker in self._workers:
                thread = threading.Thread(
                    target=worker.run,
                    name=str(worker.__class__),
                )
                thread.daemon = True
                self._worker_threads.append(thread)
                logger.info(f"Starting thread {thread.name}")
                thread.start()
                self._worker_threads.append(thread)

            await self.plugin.settings.rest_client.update_octoprint_device(
                self.plugin.settings.octoprint_device_id,
                monitoring_active=True,
            )
            logger.info("Print Nanny monitoring is now active")
        else:
            logger.warning(
                "Received MONITORING_START command while monitoring is already active, discarding"
            )

    @beeline.traced("MonitoringManager.stop")
    async def stop(self, **kwargs):

        self._drain()
        self.plugin._event_bus.fire(
            Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_RESET,
        )
        self.plugin._settings.set(
            ["monitoring_active"], False
        )  # @todo fix setting iface
        await self.plugin.settings.rest_client.update_octoprint_device(
            self.plugin.settings.octoprint_device_id, monitoring_active=False
        )
        if self.plugin.settings.print_session:
            logger.info(
                f"Closing monitoring session session={self.plugin.settings.print_session.session}"
            )
