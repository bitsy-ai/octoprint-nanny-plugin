import asyncio
import backoff
import hashlib
import json
import logging
import queue
import websockets
import websockets.exceptions
import urllib
import asyncio
import os
import threading
import multiprocessing
import signal
import sys
import os
from typing import Awaitable

import beeline

from octoprint_nanny.utils.encoder import NumpyEncoder
from octoprint_nanny.clients.honeycomb import HoneycombTracer

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
        queue,
        device_id,
        trace_context={},
    ):

        if not isinstance(queue, multiprocessing.queues.Queue):
            raise ValueError("queue should be an instance of multiprocessing.Queue")

        self._device_id = device_id
        self._base_url = base_url
        self._url = f"{base_url}{device_id}/video/upload/"
        self._auth_token = auth_token
        self._queue = queue

        self._extra_headers = (("Authorization", f"Bearer {self._auth_token}"),)
        self._halt = None
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")
        self._honeycomb_tracer.add_global_context(trace_context)

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

    def run(self, halt):
        self._halt = halt
        loop = asyncio.new_event_loop()
        loop.set_debug(True)
        asyncio.set_event_loop(loop)
        task = asyncio.ensure_future(self.relay_loop())
        result = loop.run_until_complete(task)
        loop.close()

    async def _loop(self, websocket) -> Awaitable:
        try:
            msg = self._queue.get(timeout=1)
            await websocket.send(msg)
        except queue.Empty as e:
            pass
        except websockets.exceptions.InvalidMessage as e:
            logger.warning("An invalid ")

    @backoff.on_exception(
        backoff.expo,
        (websockets.exceptions.WebSocketException,),
        jitter=backoff.random_jitter,
        logger=logger,
        max_time=600,
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
            return True
