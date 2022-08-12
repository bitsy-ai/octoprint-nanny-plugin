import logging
import asyncio
import json
import subprocess
from typing import Dict, Any, Optional
from caseconverter import kebabcase

from octoprint_nanny.utils import printnanny_os

import printnanny_api_client.models
from printnanny_api_client.models import (
    PolymorphicOctoPrintEventRequest,
    OctoPrintServerStatusType,
    OctoPrintPrintJobStatusType,
    OctoPrintClientStatusType,
    OctoPrintPrinterStatusType,
)


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.events")
# see available events: https://docs.octoprint.org/en/master/events/index.html#id5


PUBLISH_EVENTS = {
    "Startup",  # server
    "Shutdown",  # server
    "PrinterStateChanged",  # printer status
    "PrintProgress",  # print job
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


async def sanitize_payload(data: Dict[Any, Any]) -> Dict[Any, Any]:
    async with printnanny_api_client.ApiClient() as client:
        return client.sanitize_for_serialization(data)


def event_request(
    event: str, payload: Dict[Any, Any]
) -> Optional[PolymorphicOctoPrintEventRequest]:

    # bail if PRINTNANNY_PI is not set
    if printnanny_os.PRINTNANNY_PI is None:
        logger.warning(
            "printnanny_os.PRINTNANNY_PI is not set, refusing to publish event=%s payload %s",
            event,
            payload,
        )
        return None

    # sanitize OctoPrint payloads
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coroutine = sanitize_payload(payload)
    sanitized_payload = loop.run_until_complete(coroutine)

    # OctoPrintServerStatus
    if event == "Startup":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.STARTUP,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )
    elif event == "Shutdown":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.SHUTDOWN,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )

    # OctoPrintPrintJob
    elif event == "PrintProgress":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTPROGRESS,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintStarted":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTSTARTED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintFailed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTFAILED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintDone":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTDONE,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintCancelling":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTCANCELLING,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )

    elif event == "PrintCancelled":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTCANCELLED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintPaused":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTPAUSED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintResumed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTRESUMED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )

    # client events
    elif event == "ClientOpened":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintClientStatusType.CLIENTOPENED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintClientStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_CLIENT,
        )
    elif event == "ClientAuthed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintClientStatusType.CLIENTAUTHED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintClientStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_CLIENT,
        )
    elif event == "ClientClosed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
            event_type=OctoPrintClientStatusType.CLIENTCLOSED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintClientStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_CLIENT,
        )

    # printer status events
    elif event == "PrinterStateChanged":
        state_id = payload.get("state_id", "OFFLINE")
        if state_id == "OPEN_SERIAL":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROPENSERIAL,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CONNECTING":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERCONNECTING,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "OPERATIONAL":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROPERATIONAL,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "PRINTING":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERINPROGRESS,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "PAUSED":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERPAUSED,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CLOSED":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROFFLINE,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "ERROR":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERERROR,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "UNKNOWN":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROFFLINE,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CLOSED_WITH_ERROR":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERERROR,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
    logger.warning(
        "No PolymorphicOctoPrintEventRequest serializer configured for event=%s payload=%s",
        event,
        payload,
    )
    return None


def try_publish_cmd(
    request: PolymorphicOctoPrintEventRequest,
) -> Optional[subprocess.CompletedProcess]:
    payload = json.dumps(request.to_dict())
    cmd = [
        printnanny_os.PRINTNANNY_BIN,
        "nats-publisher",
        request.subject_pattern,
        "--event-type",
        kebabcase(request.event_type),
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
    return p


def try_handle_event(
    event: str,
    payload: Dict[Any, Any],
) -> Optional[subprocess.CompletedProcess]:
    try:
        if should_publish_event(event, payload):
            req = event_request(event, payload)
            if req is not None:
                return try_publish_cmd(req)
        return None
    except Exception as e:
        logger.error(
            "Error on publish for event=%s, payload=%s error=%s",
            event,
            payload,
            repr(e),
        )
        return None
