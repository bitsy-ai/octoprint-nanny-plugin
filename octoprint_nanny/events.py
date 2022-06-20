import logging
import socket
import json
from typing import Dict, Any, Optional
from octoprint_nanny.utils.printnanny_os import PrintNannyConfig

# TODO descriminator models not getting generated in python?
import printnanny_api_client.models
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


def event_request(
    event: str, payload: Dict[Any, Any], device: int
) -> printnanny_api_client.models.OctoPrintEventRequest:
    return printnanny_api_client.models.OctoPrintEventRequest(
        model="OctoPrintEvent",
        source=printnanny_api_client.models.EventSource.OCTOPRINT,
        event_name=event,
        payload=payload,
        device=device,
    )


def try_write_socket(
    request: printnanny_api_client.models.OctoPrintEventRequest, events_socket: str
) -> None:
    data = json.dumps(request.to_dict()).encode("utf-8")
    logger.debug(
        "Publishing data %s to socket %s",
        data,
        events_socket,
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(events_socket)
        client.sendall(data)
        client.close()
        logger.debug("Closed socket %s", events_socket)
    return


def try_publish_event(
    event: str, payload: Dict[Any, Any], topic="octoprint_events"
) -> Optional[printnanny_api_client.models.OctoPrintEventRequest]:
    """
    Publish event to MQTT
    """
    if should_publish_event(event):
        config = PrintNannyConfig
        device = config.get("device", {}).get("id")
        socket = config.get("events_socket")
        if device is None:
            raise SetupIncompleteError("PrintNanny conf.d device is not set")
        if socket is None:
            raise SetupIncompleteError("printnanny_config.events_socket is not set")
        try:
            req = event_request(event, payload, device)
            try_write_socket(req, config["events_socket"])
            return req
        except Exception as e:
            logger.error("Error publishing event=%s error=%s", event, e)
            return None
    else:
        logger.debug("Ignoring event %s", event)
        return None


def try_handle_event(
    event: str,
    payload: Dict[Any, Any],
) -> Optional[printnanny_api_client.models.OctoPrintEventRequest]:
    try:
        return try_publish_event(event, payload)
    except Exception as e:
        logger.error(
            "Error on publish for event=%s, payload=%s error=%s", event, payload, e
        )
