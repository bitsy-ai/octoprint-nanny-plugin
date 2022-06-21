import logging
import json
import subprocess
from typing import Dict, Any, Optional, TypedDict
from octoprint_nanny.utils.printnanny_os import load_printnanny_config, PRINTNANNY_BIN

# TODO descriminator models not getting generated in python?
import printnanny_api_client.models
from octoprint_nanny.exceptions import SetupIncompleteError

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
}


def should_publish_event(event: str, payload: Dict[Any, Any]) -> bool:
    return event in PUBLISH_EVENTS


def event_request(
    event: str, payload: Dict[Any, Any], device: int, octoprint_server: int
) -> printnanny_api_client.models.OctoPrintEventRequest:
    return printnanny_api_client.models.OctoPrintEventRequest(
        model="OctoPrintEvent",
        source=printnanny_api_client.models.EventSource.OCTOPRINT,
        event_name=event,
        payload=payload,
        device=device,
        octoprint_server=octoprint_server,
    )


def try_publish_cmd(
    request: printnanny_api_client.models.OctoPrintEventRequest,
) -> None:
    data = json.dumps(request.to_dict())
    cmd = [PRINTNANNY_BIN, "event", "publish", "--data", data]
    logger.debug("Running command: %s", cmd)
    p = subprocess.run(cmd, capture_output=True)
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.error(
            f"Command exited non-zero code cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None


def try_publish_event(
    event: str, payload: Dict[Any, Any], topic="octoprint_events"
) -> Optional[printnanny_api_client.models.OctoPrintEventRequest]:
    """
    Publish event to MQTT
    """
    if should_publish_event(event, payload):
        config = load_printnanny_config()["config"]
        if config is None:
            raise SetupIncompleteError("PrintNanny conf.d is not set")
        device = config.get("device", {}).get("id")
        octoprint_server = config.get("octoprint", {}).get("server", {}).get("id")
        if device is None:
            raise SetupIncompleteError("PrintNanny conf.d [device] is not set")
        if octoprint_server is None:
            raise SetupIncompleteError(
                "PrintNanny conf.d [octoprint.server] is not set"
            )
        req = event_request(event, payload, device, octoprint_server)
        try_publish_cmd(req)
        return req
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
            "Error on publish for event=%s, payload=%s error=%s",
            event,
            payload,
            repr(e),
        )
        return None
