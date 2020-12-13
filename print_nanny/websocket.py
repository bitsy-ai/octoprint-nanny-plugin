import aiohttp
import asyncio
import hashlib
import json
import multiprocessing
import logging
import queue
import websockets
import urllib
import asyncio
import os

from .utils.encoder import NumpyEncoder

logger = logging.getLogger("octoprint.plugins.print_nanny")


class PrintNannyAuthMissing(Exception):
    pass


class WebSocketWorker:
    """
    Relays prediction and image buffers from PredictWorker
    to websocket connection

    Restart proc on api_url and api_token settings change
    """

    def __init__(self, api_url, api_token, producer, print_job_id):

        if not type(producer) is multiprocessing.queues.Queue:
            raise ValueError("producer should be an instance of multiprocessing.Queue")
        parsed_url = urllib.parse.urlparse(api_url)

        if parsed_url.scheme == "http":
            scheme = "ws"
        elif parsed_url.scheme == "https":
            scheme = "wss"
        else:
            raise ValueError(f"Could not parse protocol scheme from {api_url}")

        self._print_job_id = print_job_id

        self._url = f"{scheme}://{parsed_url.netloc}{parsed_url.path}{print_job_id}"
        self._api_token = api_token
        self._producer = producer

        self._extra_headers = (("Authorization", f"Bearer {self._api_token}"),)
        asyncio.run(self.relay())

    def encode(self, msg):
        encoded = {}

        # for k, v in msg.items():
        #     if k == "original_image":
        #         file_hash = hashlib.md5(v.read()).hexdigest()
        #         v.seek(0)
        #         encoded[k] = v.read()
        #         encoded["file_hash"] = file_hash
        #     elif k == "annotated_image":
        #         #v.seek(0)
        #         encoded[k] = v
        #     else:
        #         encoded[k] = v
        return json.dumps(msg, cls=NumpyEncoder)

    async def ping(self, msg=None):
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            if msg is None:
                msg = {"msg": "ping"}
            msg = self.encode(msg)
            await websocket.send(msg)
            return await websocket.recv()

    async def send(self, msg=None):
        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            if msg is None:
                msg = {"msg": "ping"}
            msg = self.encode(msg)
            await websocket.send(msg)

    async def relay(self):
        logging.info(f"Initializing websocket {self._url}")

        async with websockets.connect(
            self._url, extra_headers=self._extra_headers
        ) as websocket:
            logger.info(f"Websocket connected {websocket}")
            while True:
                try:
                    msg = self._producer.get_nowait()
                    encoded_msg = self.encode(msg)
                    await websocket.send(encoded_msg)

                except queue.Empty:
                    logger.warning(
                        f"Websocket relay is dry. If this happens often, try a more frequent sample/predict rate"
                    )
