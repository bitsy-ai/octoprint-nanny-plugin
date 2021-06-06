import asyncio
import aiohttp
import backoff
import hashlib
import concurrent
import json
import logging
import queue
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


class WebSocketWorkerV2:
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

    def run(self, halt):
        self._halt = halt
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4)
        )
        task = asyncio.ensure_future(self.relay_loop())
        self.loop.run_until_complete(task)
        self.loop.close()

    async def _loop(self, websocket) -> Awaitable:
        try:
            msg = self._queue.get(timeout=1)
            logger.info('Sending websocket msg')
            return await websocket.send_bytes(msg)
        except queue.Empty as e:
            pass

    async def relay_loop(self):
        logging.info(f"Initializing websocket {self._url}")
        async with aiohttp.ClientSession(
            headers=self._extra_headers
        ) as session:
            async with session.ws_connect(self._url, heartbeat=20, timeout=30) as ws:
                logger.info(f"Websocket initialized {ws}")

                while not self._halt.is_set():
                    await self._loop(ws)

                logger.warning("Halt event set, worker will exit soon")
                return True
