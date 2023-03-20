import multiprocessing
import threading
import asyncio
import os
import logging
import concurrent
import queue
from typing import Tuple

import nats

from printnanny_api_client.models import PolymorphicOctoPrintEventRequest

PRINTNANNY_OS_NATS_URL = os.environ.get(
    "PRINTNANNY_OS_NATS_URL", f"nats://{os.hostname}:4223"
)

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.nats")

async def _nats_worker_main(queue: multiprocessing.Queue, exit: multiprocessing.Event):
    nc = await nats.connect(
        servers=[
            PRINTNANNY_OS_NATS_URL          
        ],
    )
    logger.info(
        "Connected to NATS server: %s",
        PRINTNANNY_OS_NATS_URL
    )
    while not exit.is_set():
        try:
            subject, request: Tuple[str, PolymorphicOctoPrintEventRequest] = queue.get(timeout=0.1)
            await nc.publish(subject, request.encode("utf-8"))
            logger.info("Published NATS message on subject=%s message=%s", subject, request)
        except queue.Empty:
            return
    logger.warning("NatsWorker shutdown complete")

class NatsWorker:
    def __init__(self):
        self._exit = multiprocessing.Event()
        self._queue = multiprocessing.Queue()
        self._process = multiprocessing.Process(target=asyncio.run, args=(_nats_worker_main(self._queue, self._exit)))

    def start(self):
        self._process.start()

    def shutdown(self, **kwargs):
        logger.warning("NatsWorker shutdown initiated")
        self.exit.set()

    def add_to_queue(self, subject: str, request: PolymorphicOctoPrintEventRequest):
        try:
            self._queue.put_nowait(
            (subject, request)
            )
        except BrokenPipeError:
            logger.error(
                f"NatsWorker.add_to_queue raised BrokenPipeError, discarding event subject=%s message=%s",
                subject,
                request
            )