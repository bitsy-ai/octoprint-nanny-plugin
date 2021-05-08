import aiohttp
import asyncio
import backoff
import hashlib
import json
import logging
import queue
import websockets
from websockets.exceptions import ConnectionClosedError
import urllib
import asyncio
import os
import threading
import aioprocessing
import multiprocessing
import signal
import sys
import os

import beeline

from octoprint_nanny.utils.encoder import NumpyEncoder
from octoprint_nanny.clients.honeycomb import HoneycombTracer
from octoprint_nanny.types import PluginEvents

# @ todo configure logger from ~/.octoprint/logging.yaml
logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.websocket")


class WebSocketWorker:
    """
    Relays prediction and image buffers from PredictWorker
    to websocket connection

    Restart proc on api_url and auth_token settings change
    """

    def __init__(
        self,
        base_url,
        auth_token,
        producer,
        device_id,
        halt,
        trace_context={},
    ):

        if not isinstance(producer, multiprocessing.managers.BaseProxy):
            raise ValueError(
                "producer should be an instance of aioprocessing.managers.AioQueueProxy"
            )

        self._device_id = device_id
        self._base_url = base_url
        self._url = f"{base_url}{device_id}/video/upload/"
        self._auth_token = auth_token
        self._producer = producer

        self._extra_headers = (("Authorization", f"Bearer {self._auth_token}"),)
        self._halt = halt
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
        self._honeycomb_tracer.add_global_context(trace_context)

    def _signal_handler(self, received_signal, _):
        logger.warning(f"Received signal {received_signal}")
        self._halt.set()
        sys.exit(0)

    def encode(self, msg):
        return json.dumps(msg, cls=NumpyEncoder)

    async def ping(self, msg=None):
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            if msg is None:
                msg = {"event_type": "ping"}
            msg = self.encode(msg)
            await websocket.send(msg)
            return await websocket.recv()

    async def send(self, msg=None):
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            if msg is None:
                msg = {"event_type": "ping"}
            await websocket.send(msg)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.relay_loop())

    async def _loop(self, websocket):
        try:
            msg = await self._producer.coro_get(block=False)
            return await websocket.send(msg)
        except queue.Empty as e:
            return

    @backoff.on_exception(
        backoff.expo,
        ConnectionClosedError,
        jitter=backoff.random_jitter,
        logger=logger,
        max_time=60,
    )
    async def relay_loop(self):
        logging.info(f"Initializing websocket {self._url}")
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            logger.info(f"Websocket connected {websocket}")
            while not self._halt.is_set():
                await self._loop(websocket)
            logger.warning("Halt event set, worker will exit soon")
