import logging
from typing import Dict, Any, Optional

from printnanny_api_client.models.polymorphic_event_request import (
    PolymorphicEventRequest,
)
from octoprint_nanny.exceptions import SetupIncompleteError

logger = logging.getLogger(__name__)
# see available events: https://docs.octoprint.org/en/master/events/index.html#id5
PUBLISH_EVENTS = [
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
]


def should_publish_event(event: str) -> bool:
    return event in PUBLISH_EVENTS

def event_request(event, payload: Dict[Any, Any]) -> PolymorphicEventRequest:



def try_publish_event(
    event: str, payload: Dict[Any, Any], socket: str
) -> Optional[PolymorphicEventRequest]:
    if should_publish_event(event):
        logger.debug("Publishing event %s payload %s to socket %s")
    else:
        logger.debug("Ignoring event %s", event)
        return None


def try_handle_event(
    event: str,
    payload: Dict[Any, Any],
    socket: Optional[str] = None,
    events_enabled: bool = True,
) -> Optional[PolymorphicEventRequest]:
    if events_enabled:
        if socket is None:
            raise SetupIncompleteError()
        return try_publish_event(event, payload, socket)
    logger.debug(
        "Skipping publish for event=%s, events_enabled=%s", event, events_enabled
    )
