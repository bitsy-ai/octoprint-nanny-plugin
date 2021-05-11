from enum import Enum
from dataclasses import dataclass, asdict
from PIL.Image import Image as PillowImage
import numpy as np
from typing import Optional, Dict

from print_nanny_client import (
    OctoPrintPluginEventEventTypeEnum as OctoPrintPluginEventTypes,
)
from print_nanny_client import (
    OctoPrintEventEventTypeEnum as OctoPrintEventTypes,
)
from print_nanny_client.models.command_enum import CommandEnum
from print_nanny_client.flatbuffers.monitoring.MonitoringEventTypeEnum import (
    MonitoringEventTypeEnum,
)


PLUGIN_PREFIX = "octoprint_nanny_"


@dataclass
class Image:
    height: int
    width: int
    data: bytes
    # ndarray: np.ndarray
    def to_dict(self):
        return asdict(self)


@dataclass
class Metadata:
    user_id: int
    octoprint_device_id: int
    cloudiot_device_id: int
    ts: int
    print_session: str
    client_version: str
    octoprint_version: str
    plugin_version: str
    environment: Dict[str, str]
    model_version: str = None

    def to_dict(self):
        return asdict(self)


@dataclass
class BoundingBoxPrediction:
    num_detections: int
    detection_scores: np.ndarray
    detection_boxes: np.ndarray
    detection_classes: np.ndarray

    def to_dict(self):
        return asdict(self)


@dataclass
class MonitoringFrame:
    ts: int
    image: Image
    bounding_boxes: BoundingBoxPrediction = None

    def to_dict(self):
        return asdict(self)


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
    "OctoPrintPluginEvents",
    {
        attr: getattr(OctoPrintPluginEventTypes, attr)
        for attr in dir(OctoPrintPluginEventTypes)
        if getattr(OctoPrintPluginEventTypes, attr)
        in OctoPrintPluginEventTypes.allowable_values
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
