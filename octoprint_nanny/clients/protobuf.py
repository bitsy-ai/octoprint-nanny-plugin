import octoprint
import print_nanny_client
from print_nanny_client.protobuf.common_pb2 import (
    OctoprintEnvironment,
    Metadata,
    PrintSession,
)
from print_nanny_client.protobuf.monitoring_pb2 import MonitoringImage


def build_monitoring_image(
    image_bytes: bytes, height: int, width: int, metadata_pb: Metadata
) -> MonitoringImage:
    return MonitoringImage(
        data=image_bytes, height=height, width=width, metadata=metadata_pb
    )
