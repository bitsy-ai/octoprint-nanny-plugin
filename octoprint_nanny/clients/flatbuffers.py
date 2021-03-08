import io
import flatbuffers
from typing import Optional

import print_nanny_client
from print_nanny_client.telemetry_event import (
    MonitoringFrame,
    Image,
    Box,
    BoundingBoxes,
    TelemetryEventEnum,
    TelemetryEvent,
    Metadata,
)
import octoprint_nanny.types


def build_bounding_boxes_message(
    builder, monitoring_frame: octoprint_nanny.types.MonitoringFrame
) -> bytes:
    if monitoring_frame.bounding_boxes is None:
        return

    boxes = monitoring_frame.bounding_boxes.detection_boxes
    scores = monitoring_frame.bounding_boxes.detection_scores
    classes = monitoring_frame.bounding_boxes.detection_classes
    num_detections = monitoring_frame.bounding_boxes.num_detections

    # begin boxes builder
    BoundingBoxes.BoundingBoxesStartBoxesVector(builder, len(boxes))
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
    BoundingBoxes.BoundingBoxesAddBoxes(builder, boxes)
    BoundingBoxes.BoundingBoxesAddScores(builder, scores)
    BoundingBoxes.BoundingBoxesAddClasses(builder, classes)
    BoundingBoxes.BoundingBoxesAddNumDetections(builder, num_detections)
    bounding_boxes = BoundingBoxes.BoundingBoxesEnd(builder)
    # end bounding boxes

    return bounding_boxes


def build_telemetry_event_message(
    event_type: int,
    metadata: octoprint_nanny.types.Metadata,
    monitoring_frame: octoprint_nanny.types.MonitoringFrame,
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

    # begin event data
    # prediction is optional; if not provided, inference will run in beam pipeline
    bounding_boxes = build_bounding_boxes_message(builder, monitoring_frame)
    MonitoringFrame.MonitoringFrameStart(builder)
    MonitoringFrame.MonitoringFrameAddImage(builder, image)
    if bounding_boxes:
        MonitoringFrame.MonitoringFrameAddBoundingBoxes(builder, bounding_boxes)
    MonitoringFrame.MonitoringFrameAddTs(builder, monitoring_frame.ts)
    event_data = MonitoringFrame.MonitoringFrameEnd(builder)

    # end event data

    # begin metadata
    Metadata.MetadataStart(builder)
    Metadata.MetadataAddUserId(builder, metadata.user_id)
    Metadata.MetadataAddDeviceCloudiotId(builder, metadata.device_cloudiot_id)
    Metadata.MetadataAddDeviceId(builder, metadata.device_id)
    metadata = Metadata.MetadataEnd(builder)
    # end metadata

    # begin telemetry event
    version = builder.CreateString(print_nanny_client.__version__)
    TelemetryEvent.TelemetryEventStart(builder)
    TelemetryEvent.TelemetryEventAddEventData(builder, event_data)
    TelemetryEvent.TelemetryEventAddEventDataType(
        builder, print_nanny_client.telemetry_event.EventData.EventData.MonitoringFrame
    )
    TelemetryEvent.TelemetryEventAddMetadata(builder, metadata)
    TelemetryEvent.TelemetryEventAddEventType(builder, event_type)
    TelemetryEvent.TelemetryEventAddVersion(builder, version)
    telemetry_event = TelemetryEvent.TelemetryEventEnd(builder)
    builder.Finish(telemetry_event)

    # end tlemetry event
    return builder.Output()
