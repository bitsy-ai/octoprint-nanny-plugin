import logging
import socket
import json
from typing import Dict, Any, Optional
from octoprint_nanny.utils.printnanny_os import (
    load_printnanny_config,
    load_printnanny_config,
)

# TODO descriminator models not getting generated in python?
import printnanny_api_client.models
from octoprint_nanny.exceptions import SetupIncompleteError

logger = logging.getLogger(__name__)
# see available events: https://docs.octoprint.org/en/master/events/index.html#id5


def should_publish_print_progress(event: str, payload: Dict[Any, Any]):
    config = load_printnanny_config()
    alert_settings = config["config"].get("alert_settings", {})
    threshold = alert_settings.get("print_progress_percent")
    if threshold is None:
        logger.warning(
            "Discarding event=%s using alert_settings=%s because print_progress_percent is not set.",
            event,
            alert_settings,
        )
        return False
    progress = payload.get("progress")
    if progress is None:
        logger.warning(
            "%s event handler expected key 'progress' to be set in payload=%s but got None",
            event,
            payload,
        )
    return progress % threshold == 0


PUBLISH_EVENTS = {
    "Startup": lambda event, payload: True,  # server
    "Shutdown": lambda event, payload: True,  # server
    "PrintProgress": should_publish_print_progress,  # printer comms
    "Connecting": lambda event, payload: True,  # printer comms
    "Connected": lambda event, payload: True,  # printer comms
    "Disconnecting": lambda event, payload: True,  # printer comms
    "Disconnected": lambda event, payload: True,  # printer comms
    "Error": lambda event, payload: True,  # printer comms
    "PrintStarted": lambda event, payload: True,  # print job
    "PrintFailed": lambda event, payload: True,  # print job
    "PrintDone": lambda event, payload: True,  # print job
    "PrintCancelling": lambda event, payload: True,  # print job
    "PrintCancelled": lambda event, payload: True,  # print job
    "PrintPaused": lambda event, payload: True,  # print job
    "PrintResumed": lambda event, payload: True,  # print job
}


def should_publish_event(event: str, payload: Dict[Any, Any]) -> bool:
    if event in PUBLISH_EVENTS.keys():
        handler = PUBLISH_EVENTS[event]
        return handler.__call__(event, payload)
    return False


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
    if should_publish_event(event, payload):
        config = load_printnanny_config()["config"]

        import pdb

        pdb.set_trace()
        if config is None:
            raise SetupIncompleteError("PrintNanny conf.d is not set")
        device = config.get("device", {}).get("id")
        socket = config.get("paths", {}).get("events_socket")
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
