import flatbuffers
import logging

import print_nanny_client
from print_nanny_client.flatbuffers.monitoring import (
    MonitoringEvent,
    Image,
    Box,
    BoundingBoxes,
    Metadata,
)
from octoprint_nanny.types import MonitoringFrame as MonitoringFrameT

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.flatbuffers")


def build_bounding_boxes_message(builder, monitoring_frame: MonitoringFrameT) -> bytes:
    if monitoring_frame.bounding_boxes is None:
        return

    boxes = monitoring_frame.bounding_boxes.detection_boxes
    scores = monitoring_frame.bounding_boxes.detection_scores
    classes = monitoring_frame.bounding_boxes.detection_classes
    num_detections = monitoring_frame.bounding_boxes.num_detections

    # begin boxes builder
    BoundingBoxes.BoundingBoxesStartDetectionBoxesVector(builder, len(boxes))
    for box in boxes:
        Box.CreateBox(builder, *box)
    boxes = builder.EndVector(len(boxes))
    # end boxes

    # begin scores
    scores = builder.CreateNumpyVector(scores)
    # end scores

    # begin classes builder
    classes = builder.CreateNumpyVector(classes)
    # end classes

    # begin bounding boxes
    BoundingBoxes.BoundingBoxesStart(builder)
    BoundingBoxes.BoundingBoxesAddDetectionBoxes(builder, boxes)
    BoundingBoxes.BoundingBoxesAddDetectionScores(builder, scores)
    BoundingBoxes.BoundingBoxesAddDetectionClasses(builder, classes)
    BoundingBoxes.BoundingBoxesAddNumDetections(builder, num_detections)
    bounding_boxes = BoundingBoxes.BoundingBoxesEnd(builder)
    # end bounding boxes

    return bounding_boxes


def build_monitoring_event_flatbuffer(
    event_type: int,
    metadata: Metadata,
    monitoring_frame: MonitoringFrameT,
) -> bytes:

    builder = flatbuffers.Builder(1024)

    # begin image
    Image.ImageStartDataVector(builder, len(monitoring_frame.image.data))

    builder.Bytes[
        builder.head : (builder.head + len(monitoring_frame.image.data))
    ] = monitoring_frame.image.data
    image_data = builder.EndVector(len(monitoring_frame.image.data))
    Image.ImageStart(builder)
    Image.ImageAddHeight(builder, monitoring_frame.image.height)
    Image.ImageAddWidth(builder, monitoring_frame.image.width)
    Image.ImageAddData(builder, image_data)
    image = Image.ImageEnd(builder)
    # end image

    # begin metadata
    client_version = builder.CreateString(print_nanny_client.__version__)
    session = builder.CreateString(metadata.print_session)
    Metadata.MetadataStart(builder)
    Metadata.MetadataAddUserId(builder, metadata.user_id)
    Metadata.MetadataAddCloudiotDeviceId(builder, metadata.cloudiot_device_id)
    Metadata.MetadataAddOctoprintDeviceId(builder, metadata.octoprint_device_id)
    Metadata.MetadataAddTs(builder, monitoring_frame.ts)
    Metadata.MetadataAddClientVersion(builder, client_version)
    Metadata.MetadataAddPrintSession(builder, session)
    metadata = Metadata.MetadataEnd(builder)
    # end metadata

    # begin bounding box and image data
    # prediction is optional; if not provided, inference will run in beam pipeline
    bounding_boxes = build_bounding_boxes_message(builder, monitoring_frame)

    MonitoringEvent.MonitoringEventStart(builder)
    MonitoringEvent.MonitoringEventAddEventType(builder, event_type)
    MonitoringEvent.MonitoringEventAddImage(builder, image)
    MonitoringEvent.MonitoringEventAddMetadata(builder, metadata)

    if bounding_boxes:
        MonitoringEvent.MonitoringEventAddBoundingBoxes(builder, bounding_boxes)

    monitoring_event = MonitoringEvent.MonitoringEventEnd(builder)

    builder.Finish(monitoring_event)

    return builder.Output()
