from enum import Enum
from dataclasses import dataclass, asdict
from PIL.Image import Image as PillowImage
import numpy as np
from typing import Dict, Optional


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
    ts: float
    print_session: str
    client_version: str
    octoprint_version: str
    plugin_version: str
    octoprint_environment: Dict[str, str]
    model_version: Optional[str] = None

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
    bounding_boxes: Optional[BoundingBoxPrediction] = None

    def to_dict(self):
        return asdict(self)


class MonitoringModes(Enum):
    ACTIVE_LEARNING = "active_learning"
    LITE = "lite"
