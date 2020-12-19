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

# @ todo configure logger from ~/.octoprint/logging.yaml
logger = logging.getLogger("octoprint.plugins.print_nanny.websocket")


class WorkerManager:
    """
    Manages PredictWorker and WebsocketWorker processes
    """

    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def update_settings(self):
        pass


class WebSocketWorker:
    """
    Relays prediction and image buffers from PredictWorker
    to websocket connection

    Restart proc on api_url and api_token settings change
    """

    def __init__(self, url, api_token, producer, print_job_id=None):

        if not type(producer) is multiprocessing.queues.Queue:
            raise ValueError("producer should be an instance of multiprocessing.Queue")

        self._print_job_id = print_job_id
        self._url = url
        self._api_token = api_token
        self._producer = producer

        self._extra_headers = (("Authorization", f"Bearer {self._api_token}"),)
        asyncio.run(self.run())

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
        except Exception as e:
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
            while True:
                try:
                    msg = self._producer.get_nowait()

                    event_type = msg.get("event_type")

                    if event_type == "predict":
                        if self._print_job_id is None:
                            logger.debug("No print job is active, discarding msg")
                            continue
                        msg["print_job_id"] = self._print_job_id
                        encoded_msg = self.encode(msg)
                        await websocket.send(encoded_msg)
                    elif event_type == "settings":
                        self._update_settings(msg)
                    elif event_type == "print_job":
                        self._print_job_id = msg.get("print_job_id")
                except queue.Empty:
                    pass
