import octoprint
import printnanny_api_client
from printnanny_api_client.protobuf.common_pb2 import (
    OctoprintEnvironment,
    Metadata,
    PrintSession,
)
from printnanny_api_client.protobuf.monitoring_pb2 import MonitoringImage


def build_monitoring_image(
    image_bytes: bytes, height: int, width: int, metadata_pb: Metadata
) -> MonitoringImage:
    return MonitoringImage(
        data=image_bytes, height=height, width=width, metadata=metadata_pb
    )
