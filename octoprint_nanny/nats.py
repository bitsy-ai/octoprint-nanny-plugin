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

NATS_CONNECTION: Optional[nats.aio.client.Client] = None


async def try_publish_nats(event: str, payload: Dict[Any, Any]) -> bool:
    global NATS_CONNECTION
    if NATS_CONNECTION is None:
        NATS_CONNECTION = await nats.connect(
            servers=[PRINTNANNY_OS_NATS_URL],
        )
        logger.info("Connected to NATS server: %s", PRINTNANNY_OS_NATS_URL)

    subject = octoprint_event_to_nats_subject(event)
    if subject is None:
        return False
    try:
        request = await event_request(event, payload)
        request_json = json.dumps(request.to_dict())
        await NATS_CONNECTION.publish(subject, request_json.encode("utf-8"))
        logger.info("Published NATS message on subject=%s message=%s", subject, payload)
        return True
    except Exception as e:
        logger.error(
            "Error publishing NATS message subject=%s error=%s", subject, str(e)
        )
        return False


async def _nats_worker_main(q: multiprocessing.Queue, exit: threading.Event):
    while not exit.is_set():
        try:
            event, payload = q.get(timeout=1)
            await try_publish_nats(event, payload)
        except queue.Empty:
            return
    logger.warning("NatsWorker shutdown complete")


class NatsWorker:
    def __init__(self):
        self._exit = threading.Event()
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="NatsWorker"
        )
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
        self.loop.set_default_executor(self._executor)
        self.loop.run_until_complete(_nats_worker_main(self._queue, self._exit))

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
