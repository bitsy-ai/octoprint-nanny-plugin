import aiohttp
import asyncio
import hashlib
import json
import logging
import queue
import websockets
import urllib
import asyncio
import os
import threading
import aioprocessing
import multiprocessing
import signal
import sys
import os


from octoprint_nanny.utils.encoder import NumpyEncoder

# @ todo configure logger from ~/.octoprint/logging.yaml
logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.websocket")


class WebSocketWorker:
    """
    Relays prediction and image buffers from PredictWorker
    to websocket connection

    Restart proc on api_url and api_token settings change
    """

    def __init__(self, base_url, api_token, producer, print_job_id, device_id):

        if not isinstance(producer, multiprocessing.managers.BaseProxy):
            raise ValueError(
                "producer should be an instance of aioprocessing.managers.AioQueueProxy"
            )

        self._print_job_id = print_job_id
        self._device_id = device_id
        self._base_url = base_url
        self._url = f"{base_url}{device_id}/video/upload/"
        self._api_token = api_token
        self._producer = producer

        self._extra_headers = (("Authorization", f"Bearer {self._api_token}"),)
        self._halt = threading.Event()
        for signame in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
            signal.signal(signame, self._signal_handler)
        asyncio.run(self.run())

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
            msg = self.encode(msg)
            await websocket.send(msg)

    async def run(self, backoff=1):
        try:
            return await self.relay_loop()
        except websockets.exceptions.WebSocketException as e:
            logger.error(
                f"Error connecting to websocket. Retrying in {backoff} seconds. Exception: \n {e}"
            )
            await asyncio.sleep(backoff)
            return await self.run(backoff=backoff * 2)

    async def relay_loop(self):
        logging.info(f"Initializing websocket {self._url}")
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            logger.info(f"Websocket connected {websocket}")
            while not self._halt.is_set():
                msg = await self._producer.coro_get()

                event_type = msg.get("event_type")
                if event_type == "annotated_image":
                    encoded_msg = self.encode(msg=msg)
                    await websocket.send(encoded_msg)
                else:
                    logger.warning(f"Invalid event_type {event_type}, msg ignored")
            logger.warning("Halt event set, process will exit soon")
            sys.exit(0)
