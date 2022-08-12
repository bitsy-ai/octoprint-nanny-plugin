import logging
import json
from optparse import Option
import subprocess
from typing import Dict, Any, Optional

from octoprint_nanny.utils import printnanny_os

import printnanny_api_client.models
from printnanny_api_client.models import (
    PolymorphicOctoPrintEventRequest,
    OctoPrintServerStatusType,
)


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.events")
# see available events: https://docs.octoprint.org/en/master/events/index.html#id5


PUBLISH_EVENTS = {
    "Startup",  # server
    "Shutdown",  # server
    "PrintProgress",  # printer comms
    "Connecting",  # printer comms
    "Connected",  # printer comms
    "Disconnecting",  # printer comms
    "Disconnected",  # printer comms
    "Error",  # printer comms
    "PrintStarted",  # print job
    "PrintFailed",  # print job
    "PrintDone",  # print job
    "PrintCancelling",  # print job
    "PrintCancelled",  # print job
    "PrintPaused",  # print job
    "PrintResumed",  # print job
    "ClientAuthed",  # client
    "ClientOpened",  # client
    "ClientClosed",  # client
}


def should_publish_event(event: str, payload: Dict[Any, Any]) -> bool:
    return event in PUBLISH_EVENTS


def event_request(
    event: str, payload: Dict[Any, Any]
) -> PolymorphicOctoPrintEventRequest:

    # OctoPrintServerStatus
    if event == "Startup":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.STARTUP,
            payload=payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )
    if event == "Shutdown":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.SHUTDOWN,
            payload=payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )


def try_publish_cmd(
    request: PolymorphicOctoPrintEventRequest,
) -> None:
    payload = json.dumps(request.to_dict())
    cmd = [
        printnanny_os.PRINTNANNY_BIN,
        "nats-publish",
        request.subject_pattern,
        request.event_type,
        "--payload",
        payload,
    ]
    logger.debug("Running command: %s", cmd)
    p = subprocess.run(cmd, capture_output=True)
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.error(
            f"Command exited non-zero code cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None


def try_publish_event(event: str, payload: Dict[Any, Any]):
    """
    Publish event via PrintNanny CLI
    """
    if should_publish_event(event, payload):
        req = event_request(event, payload)
        try_publish_cmd(req)
        return req
    else:
        logger.debug("Ignoring event %s", event)
        return None


def try_handle_event(
    event: str,
    payload: Dict[Any, Any],
):
    try:
        return try_publish_event(event, payload)
    except Exception as e:
        logger.error(
            "Error on publish for event=%s, payload=%s error=%s",
            event,
            payload,
            repr(e),
        )
        return None
