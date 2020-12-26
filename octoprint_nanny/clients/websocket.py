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
import aioprocessing
import multiprocessing


from octoprint_nanny.utils.encoder import NumpyEncoder

# @ todo configure logger from ~/.octoprint/logging.yaml
logger = logging.getLogger("octoprint.plugins.print_nanny.websocket")


class WebSocketWorker:
    """
    Relays prediction and image buffers from PredictWorker
    to websocket connection

    Restart proc on api_url and api_token settings change
    """

    def __init__(self, url, api_token, producer, print_job_id):

        if not isinstance(producer, multiprocessing.managers.BaseProxy):
            raise ValueError(
                "producer should be an instance of aioprocessing.managers.AioQueueProxy"
            )

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
            while True:
                msg = await self._producer.coro_get()

                event_type = msg.get("event_type")
                if event_type == "predict":
                    if self._print_job_id is not None:
                        msg["print_job_id"] = self._print_job_id
                    encoded_msg = self.encode(msg=msg)
                    await websocket.send(encoded_msg)
                else:
                    logger.warning(f"Invalid event_type {event_type}, msg ignored")
