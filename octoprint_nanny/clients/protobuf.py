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
    pb = MonitoringImage()
    pb.data = image_bytes
    pb.height = height
    pb.width = width
    pb.metadata.CopyFrom(metadata_pb)
    return pb
