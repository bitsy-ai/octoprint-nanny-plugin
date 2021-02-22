from enum import Enum
from dataclasses import dataclass
from PIL.Image import Image as PillowImage
import numpy as np
from typing import Optional

from print_nanny_client.models.plugin_event_event_type_enum import (
    PluginEventEventTypeEnum as PluginEventTypes,
)
from print_nanny_client.models.octo_print_event_event_type_enum import (
    OctoPrintEventEventTypeEnum as OctoPrintEventTypes,
)
from print_nanny_client.models.command_enum import CommandEnum

PLUGIN_PREFIX = "octoprint_nanny_"


@dataclass
class Image:
    height: int
    width: int
    data: bytes


@dataclass
class Metadata:
    user_id: int
    device_id: int
    device_cloudiot_id: int


@dataclass
class BoundingBoxPrediction:
    num_detections: int
    detection_scores: np.ndarray
    detection_boxes: np.ndarray
    detection_classes: np.ndarray
    image: Image = None


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
    def is_member(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def member(cls, value: str):
        """
        Returns Member if event string matches value (with or without plugin prefix)
        """
        if PLUGIN_PREFIX in value:
            return cls._octoprint_event_member(value)

        return cls(value)


class EnumBase(ClassMemberMixin, Enum):
    pass


PluginEvents = EnumBase(
    "PluginEvents",
    {
        attr: getattr(PluginEventTypes, attr)
        for attr in dir(PluginEventTypes)
        if getattr(PluginEventTypes, attr) in PluginEventTypes.allowable_values
    },
)

RemoteCommands = EnumBase(
    "RemoteCommands",
    {
        attr: getattr(CommandEnum, attr)
        for attr in dir(CommandEnum)
        if getattr(CommandEnum, attr) in CommandEnum.allowable_values
    },
)

TrackedOctoPrintEvents = EnumBase(
    "TrackedOctoPrintEvents",
    {
        attr: getattr(OctoPrintEventTypes, attr)
        for attr in dir(OctoPrintEventTypes)
        if getattr(OctoPrintEventTypes, attr) in OctoPrintEventTypes.allowable_values
    },
)
