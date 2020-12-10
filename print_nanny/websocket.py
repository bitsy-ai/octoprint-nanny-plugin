import aiohttp
import asyncio
import hashlib
import json
import multiprocessing
import logging
import queue
import websockets
from urllib import urlparse

import asyncio
import os

from .utils.encoder import NumpyEncoder
logger = logging.getLogger('octoprint.plugins.print_nanny')

class PrintNannyAuthMissing(Exception):
    pass

class WebSocketWorker:
    '''
        Relays prediction and image buffers from PredictWorker
        to websocket connection

        Restart proc on api_url and api_token settings change
    '''

    def __init__(self, api_url, api_token, producer, print_job_id):
        
        parsed_url = urlparse(api_url)
        if parsed_url.scheme == 'http':
            parsed_url.scheme = 'ws'
        elif parsed_url.scheme == 'https':
            parsed_url.scheme = 'wss'
        else:
            raise ValueError(f'Could not parse protocol scheme from {api_url}')
        
        self._print_job_id = print_job_id
        self._url = os.path.join(
            parsed_url.geturl(),
            print_job_id
        )
        self._api_token = api_token
        self._producer = producer


        self._extra_headers = (
            ('Authorization', f'Bearer {self._api_token}')
        )
        asyncio.run(self.relay())

    def encode(self, msg):
        encoded = {}

        for k, v in msg.items():
            if k == 'prediction':
                encoded[k] = json.dumps(v, cls=NumpyEncoder)
            elif k == 'original_image':
                file_hash = hashlib.md5(v.read()).hexdigest()
                v.seek(0)
                encoded[k] = v.read()
                encoded['file_hash'] = file_hash
            elif k == 'annotated_image':
                v.seek(0)
                encoded[k] = v.read()
            else:
                encoded[k] = v
        return json.dumps(encoded)

    async def relay(self):
        logger.info('Started WebSocket.relay loop')
        async with websockets.connect(self._url, extra_headers=self._extra_headers) as websocket:
            logger.info(f'Websocket connected {websocket}')
            while True:
                try:
                    msg = self._producer.get_nowait()
                    encoded_msg = self.encode(msg)
                    await websocket.send(encoded_msg)

                except queue.Empty:
                    logger.warning(f'Websocket relay is dry. If this happens often, try a more frequent sample/predict rate')
            
