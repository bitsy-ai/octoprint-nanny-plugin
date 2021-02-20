from enum import Enum
from print_nanny_client.models import command_enum

PLUGIN_PREFIX = "octoprint_nanny_"


class MonitoringModes(Enum):
    ACTIVE_LEARNING = "active_learning"
    LITE = "lite"


class ClassMemberMixin(object):
    """
    Utility for checking Enum membership on strings
    For sanity, membership is checked using the value and OctoPrint's generated event value
    e.g. "octoprint_nanny_value"
    """

    @classmethod
    def to_octoprint_event(cls, value: str):
        if isinstance(value, Enum):
            if PLUGIN_PREFIX not in value.value:
                value = f"{PLUGIN_PREFIX}{value.value}"
        elif isinstance(value, str):
            if PLUGIN_PREFIX not in value:
                value = f"{PLUGIN_PREFIX}{value}"
        return value

    @classmethod
    def from_octoprint_event(cls, value: str):
        return value.replace(PLUGIN_PREFIX, "")

    @classmethod
    def _octoprint_event_member(cls, value: str):
        value = cls.from_octoprint_event(value)
        return cls(value)

    @classmethod
    def member(cls, value: str):
        """
        Returns Member if event string matches value (with or without plugin prefix)
        """
        if PLUGIN_PREFIX in value:
            return cls._octoprint_event_member(value)

        return cls(value)


class PluginEvents(ClassMemberMixin, Enum):
    """
    Events originating from OctoPrint Nanny plugin code
    """

    BOUNDING_BOX_PREDICT_DONE = "bounding_box_predict_done"
    MONITORING_FRAME_DONE = "monitoring_frame_done"

    DEVICE_REGISTER_START = "device_register_start"
    DEVICE_REGISTER_DONE = "device_register_done"
    DEVICE_REGISTER_FAILED = "device_register_failed"

    PRINTER_PROFILE_SYNC_START = "printer_profile_sync_start"
    PRINTER_PROFILE_SYNC_DONE = "printer_profile_sync_done"
    PRINTER_PROFILE_SYNC_FAILED = "printer_profile_sync_failed"


class RemoteCommands(ClassMemberMixin, Enum):
    """
    Events originating from MQTT command topic
    """

    PRINT_START = "print_start"
    PRINT_STOP = "print_stop"
    PRINT_PAUSE = "print_pause"
    PRINT_RESUME = "print_resume"

    SNAPSHOT = "snapshot"

    MOVE_NOZZLE = "move_nozzle"

    MONITORING_START = "monitoring_start"
    MONITORING_STOP = "monitoring_stop"
