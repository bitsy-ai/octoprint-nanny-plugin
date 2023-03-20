import multiprocessing
import asyncio
import json
import os
import logging
import socket
import threading
from typing import Dict, Any, Optional
import queue

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


def get_subject(event: str):
    Optional[str]


async def _nats_worker_main(
    q: multiprocessing.Queue, exit: multiprocessing.synchronize.Event
):
    nc = await nats.connect(
        servers=[PRINTNANNY_OS_NATS_URL],
    )
    logger.info("Connected to NATS server: %s", PRINTNANNY_OS_NATS_URL)
    while not exit.is_set():
        try:
            subject, event, payload = q.get(timeout=0.1)
            request = await event_request(event, payload)
            request_json = json.dumps(request)
            await nc.publish(subject, request_json.encode("utf-8"))
            logger.info(
                "Published NATS message on subject=%s message=%s", subject, request
            )
        except queue.Empty:
            return
    logger.warning("NatsWorker shutdown complete")


class NatsWorker:
    def __init__(self):
        self._exit: multiprocessing.synchronize.Event = multiprocessing.Event()
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._process = multiprocessing.Process(
            target=asyncio.run, args=(_nats_worker_main(self._queue, self._exit),)
        )

    def start(self):
        self._process.start()

    def shutdown(self, **kwargs):
        logger.warning("NatsWorker shutdown initiated")
        self._exit.set()

    def add_to_queue(self, subject: str, request: PolymorphicOctoPrintEventRequest):
        try:
            self._queue.put_nowait((subject, request))
        except BrokenPipeError:
            logger.error(
                f"NatsWorker.add_to_queue raised BrokenPipeError, discarding event subject=%s message=%s",
                subject,
                request,
            )

    def handle_event(self, event: str, payload: Dict[Any, Any]):
        if should_publish_event(event, payload):
            subject = octoprint_event_to_nats_subject(event)
            if subject is None:
                return
            try:
                self._queue.put_nowait((subject, event, payload))
            except BrokenPipeError:
                logger.error(
                    f"NatsWorker.add_to_queue raised BrokenPipeError, discarding event subject=%s message=%s",
                    subject,
                    payload,
                )
