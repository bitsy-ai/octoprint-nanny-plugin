import logging
import socket
import json
from typing import Dict, Any, Optional

# TODO descriminator models not getting generated in python?
import printnanny_api_client.models
from octoprint_nanny.exceptions import SetupIncompleteError
from octoprint_nanny.utils.printnanny_os import printnanny_config

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
    event: str, payload: Dict[Any, Any], device: int, octoprint_install: int
) -> printnanny_api_client.models.OctoPrintEventRequest:
    return printnanny_api_client.models.OctoPrintEventRequest(
        model="OctoPrintEvent",
        source=printnanny_api_client.models.EventSource.OCTOPRINT,
        event_name=event,
        payload=payload,
        device=device,
        octoprint_install=octoprint_install,
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
    event: str, payload: Dict[Any, Any], config: Dict[Any, Any]
) -> Optional[printnanny_api_client.models.OctoPrintEventRequest]:
    if should_publish_event(event):
        device = config.get("device", {}).get("id")
        octoprint_install = config.get("octoprint_install", {}).get("id")
        socket = config.get("events_socket")
        if device is None:
            raise SetupIncompleteError("printnanny_config.device is not set")
        if octoprint_install is None:
            raise SetupIncompleteError("printnanny_config.octoprint_install is not set")
        if socket is None:
            raise SetupIncompleteError("printnanny_config.events_socket is not set")
        try:
            req = event_request(event, payload, device, octoprint_install)
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
    config: Dict[Any, Any],
    events_enabled: bool = True,
) -> Optional[printnanny_api_client.models.OctoPrintEventRequest]:
    if events_enabled:
        return try_publish_event(event, payload, config)
    logger.debug(
        "Skipping publish for event=%s, events_enabled=%s", event, events_enabled
    )
    return None
