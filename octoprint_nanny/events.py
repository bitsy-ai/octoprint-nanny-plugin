import logging
import nats
from typing import Dict, Any, Optional, TypedDict, Callable
import socket
import os
from octoprint_nanny.utils import printnanny_os

import printnanny_api_client.models

import printnanny_octoprint_models


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.events")

PRINTNANNY_OS_NATS_URL = os.environ.get(
    "PRINTNANNY_OS_NATS_URL", f"nats://{socket.gethostname()}:4223"
)

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.nats")

NATS_CONNECTION: Optional[nats.aio.client.Client] = None

# begin NATS message builders
def printnanny_nats_gcode_event_msg(
    event: str, *args
) -> printnanny_octoprint_models.OctoPrintGcode:
    if event == "Alert":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.ALERT_M300
        )

    elif event == "Cooling":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.COOLING_M245
        )

    elif event == "Dwell":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.DWELL_G4
        )

    elif event == "Estop":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.ESTOP_M112
        )
    # note: M600 is hard-coded here because OctoPrint doesn't pass along underlying gocde
    # FilamentChange event can be triggered by M600, M701, M702 https://github.com/bitsy-ai/printnanny-os/issues/131#issuecomment-1314855952
    # This will result in M701 and M702 events being ingested into PrintNanny's event system as M600 codes
    elif event == "FilamentChange":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.FILAMENT_CHANGE_M600
        )

    elif event == "Home":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.HOME_G28
        )

    elif event == "PowerOn":
        return printnanny_octoprint_models.OctoPrintGcode(
            gcode=printnanny_octoprint_models.GcodeEvent.POWER_ON_M80
        )

    elif event == "PowerOff":
        return printnanny_octoprint_models.OctoPrintGcode(
            printnanny_octoprint_models.GcodeEvent.POWER_ON_M81
        )
    raise ValueError(f"printnanny_nats_gcode_event_msg not support event={event}")


def printnanny_nats_octoprint_server_status_msg(
    event: str, _payload: Dict[Any, Any]
) -> printnanny_octoprint_models.OctoPrintServerStatusChanged:
    if event == "Startup":
        return printnanny_octoprint_models.OctoPrintServerStatusChanged(
            status=printnanny_octoprint_models.OctoPrintServerStatus.STARTUP
        )
    elif event == "Shutdown":
        return printnanny_octoprint_models.OctoPrintServerStatusChanged(
            status=printnanny_octoprint_models.OctoPrintServerStatus.SHUTDOWN
        )
    raise ValueError(f"build_gcode_event_msg does not support event={event}")


def printnanny_nats_printer_status_msg(
    event: str, payload: Dict[Any, Any]
) -> printnanny_octoprint_models.PrinterStatusChanged:
    status_str = payload.get("state_id")
    if status_str is None:
        raise ValueError(
            "Failed to get state_id field from event=%s payload=%s", event, payload
        )
    status = getattr(printnanny_octoprint_models.PrinterStatus, status_str)
    return printnanny_octoprint_models.PrinterStatusChanged(status=status)


def printnanny_nats_print_progress_msg(
    _event: str, payload: Dict[Any, Any]
) -> printnanny_octoprint_models.JobProgress:
    return printnanny_octoprint_models.JobProgress(**payload)


def printnanny_nats_print_job_status_msg(
    event: str, payload: Dict[Any, Any]
) -> printnanny_octoprint_models.JobStatusChanged:
    if event == printnanny_octoprint_models.JobStatus.PRINT_STARTED.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_STARTED
    elif event == printnanny_octoprint_models.JobStatus.PRINT_FAILED.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_FAILED
    elif event == printnanny_octoprint_models.JobStatus.PRINT_DONE.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_DONE
    elif event == printnanny_octoprint_models.JobStatus.PRINT_CANCELLING.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_CANCELLING
    elif event == printnanny_octoprint_models.JobStatus.PRINT_CANELLED.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_CANELLED
    elif event == printnanny_octoprint_models.JobStatus.PRINT_PAUSED.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_PAUSED
    elif event == printnanny_octoprint_models.JobStatus.PRINT_RESUMED.value:
        status = printnanny_octoprint_models.JobStatus.PRINT_RESUMED
    else:
        raise ValueError(
            "printnanny_nats_print_job_status_msg not configured to handle event=%s",
            event,
        )

    return printnanny_octoprint_models.JobStatus(status=status)


# end NATS message builders


class EventMapping(TypedDict):
    nats_subject: str
    msg_builder: Callable


# EVENT_MAPPING follows format:
# "OctoPrintEventName" : { "nats_subject": "str", msg_builder: function }
EVENT_MAPPINGS: Dict[str, EventMapping] = {
    # begin octoprint server status
    "Startup": {
        "nats_subject": "pi.{pi_id}.octoprint.event.server.startup",
        "msg_builder": printnanny_nats_octoprint_server_status_msg,
    },  # server
    "Shutdown": {
        "nats_subject": "pi.{pi_id}.octoprint.event.server.shutdown",
        "msg_builder": printnanny_nats_octoprint_server_status_msg,
    },  # server
    # begin printer status
    "PrinterStateChanged": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.status",
        "msg_builder": printnanny_nats_printer_status_msg,
    },  # printer status
    # begin print job
    "PrintProgress": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_progress",
        "msg_builder": printnanny_nats_print_progress_msg,
    },  # print job
    "PrintStarted": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintFailed": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintDone": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintCancelling": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintCancelled": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintPaused": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    "PrintResumed": {
        "nats_subject": "pi.{pi_id}.octoprint.event.printer.job_status",
        "msg_builder": printnanny_nats_print_job_status_msg,
    },  # print job
    ### begin gcode processing
    "Alert": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "Cooling": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "Dwell": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "Estop": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "FilamentChange": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "Home": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "PowerOff": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
    "PowerOn": {
        "nats_subject": "pi.{pi_id}.octoprint.event.gcode",
        "msg_builder": printnanny_nats_gcode_event_msg,
    },  # gcode processing
}


def should_publish_event(event: str, payload: Dict[Any, Any]) -> bool:
    return event in EVENT_MAPPINGS.keys()


def octoprint_event_to_nats_subject(event: str, pi_id: str) -> Optional[str]:
    mapping: Optional[EventMapping] = EVENT_MAPPINGS.get(event)
    if mapping is None:
        raise ValueError("No NATS msg subject configured for OctoPrint event=%s", event)
    return mapping["nats_subject"].format(pi_id=pi_id)


async def sanitize_payload(data: Dict[Any, Any]) -> Dict[Any, Any]:
    async with printnanny_api_client.ApiClient() as client:
        return client.sanitize_for_serialization(data)


def build_nats_msg(event: str, payload: Dict[Any, Any]) -> str:
    mapping: Optional[EventMapping] = EVENT_MAPPINGS.get(event)
    if mapping is None:
        raise ValueError("No NATS msg handler configured for OctoPrint event=%s", event)
    builder_fn = mapping["msg_builder"]
    if builder_fn is None:
        raise ValueError(f"No msg_builder fn configured for event={event}")

    msg = builder_fn(event, payload)
    if msg is None:
        raise ValueError(
            "Failed to build NATS message event=%s payload=%s", event, payload
        )
    msg_json = msg.json()
    return msg_json


async def try_publish_nats(event: str, payload: Dict[Any, Any]) -> bool:
    if should_publish_event(event, payload):

        global NATS_CONNECTION
        if NATS_CONNECTION is None:
            NATS_CONNECTION = await nats.connect(
                servers=[PRINTNANNY_OS_NATS_URL],
            )
            logger.info("Connected to NATS server: %s", PRINTNANNY_OS_NATS_URL)

        hostname = socket.gethostname()
        subject = octoprint_event_to_nats_subject(event, hostname)
        if subject is None:
            return False
        msg = build_nats_msg(event, payload)
        try:
            if msg:
                await NATS_CONNECTION.publish(subject, msg.encode("utf-8"))
                logger.info(
                    "Published NATS message: subject=%s message=%s", subject, msg
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Error publishing NATS message subject=%s error=%s", subject, str(e)
            )
            return False
    else:
        logger.info(
            "NATS subject not configured for event=%s, refusing to publish payload=%s",
            event,
            payload,
        )
        return False
