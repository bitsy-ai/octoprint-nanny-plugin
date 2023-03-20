import multiprocessing
import asyncio
import json
import os
import functools
import logging
import concurrent
import socket
from multiprocessing.synchronize import Event as EventClass
from typing import Dict, Any, Optional
import queue
import threading

import nats
from printnanny_api_client.models import PolymorphicOctoPrintEventRequest

from octoprint_nanny.events import (
    should_publish_event,
    octoprint_event_to_nats_subject,
    event_request,
)

PRINTNANNY_OS_NATS_URL = os.environ.get(
    "PRINTNANNY_OS_NATS_URL", f"nats://{socket.gethostname()}:4223"
)

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.nats")


async def try_publish_nats(
    nc: nats.aio.client.Client, event: str, payload: Dict[Any, Any]
) -> bool:
    subject = octoprint_event_to_nats_subject(event)
    if subject is None:
        return False
    try:
        request = await event_request(event, payload)
        request_json = json.dumps(request)
        await nc.publish(subject, request_json.encode("utf-8"))
        logger.info("Published NATS message on subject=%s message=%s", subject, payload)
        return True
    except Exception as e:
        logger.error(
            "Error publishing NATS message subject=%s error=%s", subject, str(e)
        )
        return False


async def _nats_worker_main(q: multiprocessing.Queue, exit: threading.Event):
    nc = await nats.connect(
        servers=[PRINTNANNY_OS_NATS_URL],
    )

    logger.info("Connected to NATS server: %s", PRINTNANNY_OS_NATS_URL)
    while not exit.is_set():
        try:
            event, payload = q.get(timeout=1)
            await try_publish_nats(nc, event, payload)
        except queue.Empty:
            return
    logger.warning("NatsWorker shutdown complete")


class NatsWorker:
    def __init__(self):
        self._exit = threading.Event()
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._thread = threading.Thread(
            target=self.run,
            name=str(self.__class__),
        )
        self._thread.daemon = True
        logger.info(f"Starting thread {self._thread.name}")
        self._thread.start()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_debug(True)
        self.loop.set_default_executor(concurrent.futures.ProcessPoolExecutor())

        self.loop.call_soon_threadsafe(
            functools.partial(_nats_worker_main, self._queue, self._exit)
        )
        try:
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def shutdown(self, **kwargs):
        logger.warning("NatsWorker shutdown initiated")
        self._exit.set()
        self._thread.join()

    def handle_event(self, event: str, payload: Dict[Any, Any]):
        if should_publish_event(event, payload):
            try:
                self._queue.put_nowait((event, payload))
            except BrokenPipeError:
                logger.error(
                    f"NatsWorker.add_to_queue raised BrokenPipeError, discarding event event=%s message=%s",
                    event,
                    payload,
                )
