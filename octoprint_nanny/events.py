import logging
import nats
from typing import Dict, Any, Optional

from octoprint_nanny.utils import printnanny_os

import printnanny_api_client.models
from printnanny_api_client.models import (
    PolymorphicOctoPrintEventRequest,
    OctoPrintServerStatusType,
    OctoPrintPrintJobStatusType,
    GcodeEventType,
    OctoPrintPrinterStatusType,
)


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.events")
# see available events: https://docs.octoprint.org/en/master/events/index.html#id5


PUBLISH_EVENTS = {
    "Startup": "octoprint.event.server.startup",  # server
    "Shutdown": "octoprint.event.server.shutdown",  # server
    "PrinterStateChanged": "octoprint.event.printer.status",  # printer status
    "PrintProgress": "octoprint.event.printer.progress",  # print job
    "PrintStarted": "octoprint.event.print_job.started",  # print job
    "PrintFailed": "octoprint.event.print_job.failed",  # print job
    "PrintDone": "octoprint.event.print_job.done",  # print job
    "PrintCancelling": "octoprint.event.print_job.cancelling",  # print job
    "PrintCancelled": "octoprint.event.print_job.cancelled",  # print job
    "PrintPaused": "octoprint.event.print_job.paused",  # print job
    "PrintResumed": "octoprint.event.print_job.resumed",  # print job
    "Alert": "octoprint.event.gcode.alert",  # gcode processing
    "Cooling": "octoprint.event.gcode.cooling",  # gcode processing
    "Dwell": "octoprint.event.gcode.dwell",  # gcode processing
    "Estop": "octoprint.event.gcode.estop",  # gcode processing
    "FilamentChange": "octoprint.event.gcode.filament_change",  # gcode processing
    "Home": "octoprint.event.gcode.home",  # gcode processing
    "PowerOff": "octoprint.event.gcode.poweroff",  # gcode processing
    "PowerOn": "octoprint.event.gcode.poweron",  # gcode processing
}


def should_publish_event(event: str, payload: Dict[Any, Any]) -> bool:
    return event in PUBLISH_EVENTS.keys()


def octoprint_event_to_nats_subject(event: str) -> Optional[str]:
    result = PUBLISH_EVENTS.get(event)
    if result is None:
        logger.warning("No NATS subject configured for OctoPrint event=%s", event)
    return result


async def sanitize_payload(data: Dict[Any, Any]) -> Dict[Any, Any]:
    async with printnanny_api_client.ApiClient() as client:
        return client.sanitize_for_serialization(data)


async def event_request(
    event: str, payload: Dict[Any, Any]
) -> Optional[PolymorphicOctoPrintEventRequest]:
    # bail if PRINTNANNY_CLOUD_PI is not set
    if printnanny_os.PRINTNANNY_CLOUD_PI is None:
        logger.warning(
            "printnanny_os.PRINTNANNY_CLOUD_PI is not set, attempting to load",
        )
        await printnanny_os.load_printnanny_cloud_data()
        if printnanny_os.PRINTNANNY_CLOUD_PI is None:
            logger.warning(
                "printnanny_os.PRINTNANNY_CLOUD_PI is not set, ignoring %s",
                event,
            )
            return None

    # sanitize OctoPrint payloads
    sanitized_payload = await sanitize_payload(payload)

    # OctoPrintGcodeEvent
    if event == "Alert":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M300,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "Cooling":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M245,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "Dwell":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.G4,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "Estop":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M112,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )

    elif event == "FilamentChange":
        # note: M600 is hard-coded here because OctoPrint doesn't pass along underlying gocde
        # FilamentChange event can be triggered by M600, M701, M702 https://github.com/bitsy-ai/printnanny-os/issues/131#issuecomment-1314855952
        # This will result in M701 and M702 events being ingested into PrintNanny's event system as M600 codes
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M600,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "Home":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.G28,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "PowerOn":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M80,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )
    elif event == "PowerOff":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=GcodeEventType.M81,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintGcodeEventSubjectPatternEnum.PI_PI_ID_OCTOPRINT_GCODE,
        )

    # OctoPrintServerStatus
    elif event == "Startup":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.STARTUP,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )
    elif event == "Shutdown":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.SHUTDOWN,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )

    elif event == "plugin_octoprint_nanny_test_server":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintServerStatusType.TEST,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintServerStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_SERVER,
        )

    # OctoPrintPrintJob
    elif event == "PrintProgress":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTPROGRESS,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintStarted":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTSTARTED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintFailed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTFAILED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintDone":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTDONE,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintCancelling":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTCANCELLING,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )

    elif event == "PrintCancelled":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTCANCELLED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintPaused":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTPAUSED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )
    elif event == "PrintResumed":
        return PolymorphicOctoPrintEventRequest(
            pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
            octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
            event_type=OctoPrintPrintJobStatusType.PRINTRESUMED,
            payload=sanitized_payload,
            subject_pattern=printnanny_api_client.models.OctoPrintPrintJobStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINT_JOB,
        )

    # printer status events
    elif event == "PrinterStateChanged":
        state_id = payload.get("state_id", "OFFLINE")
        if state_id == "OPEN_SERIAL":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROPENSERIAL,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CONNECTING":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERCONNECTING,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "OPERATIONAL":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROPERATIONAL,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "PRINTING":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERINPROGRESS,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "PAUSED":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERPAUSED,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CLOSED":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROFFLINE,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "ERROR":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTERERROR,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "UNKNOWN":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
                event_type=OctoPrintPrinterStatusType.PRINTEROFFLINE,
                payload=sanitized_payload,
                subject_pattern=printnanny_api_client.models.OctoPrintPrinterStatusSubjectPatternEnum.PI_PI_ID_OCTOPRINT_PRINTER,
            )
        elif state_id == "CLOSED_WITH_ERROR":
            return PolymorphicOctoPrintEventRequest(
                pi=printnanny_os.PRINTNANNY_CLOUD_PI.id,
                octoprint_server=printnanny_os.PRINTNANNY_CLOUD_PI.octoprint_server.id,
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
