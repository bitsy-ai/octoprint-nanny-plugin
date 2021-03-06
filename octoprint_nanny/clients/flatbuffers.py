import io
import flatbuffers
from typing import Optional
from PrintNannyEvent.TelemetrySchema import (
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
    builder, ts: int, prediction: Optional[octoprint_nanny.types.BoundingBoxPrediction] = None
) -> bytes:
    if prediction is None:
        return prediction

    boxes = prediction.detection_boxes
    scores = prediction.detection_scores
    classes = prediction.detection_classes
    num_detections = prediction.num_detections

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
    ts: int,
    metadata: octoprint_nanny.types.Metadata,
    image: octoprint_nanny.types.Image,
    event_type: TelemetryEventEnum.TelemetryEventEnum,
    prediction: Optional[octoprint_nanny.types.BoundingBoxPrediction] = None,
) -> bytes:
    builder = flatbuffers.Builder(1024)

    # begin image
    Image.ImageStartDataVector(builder, len(image.data))
    builder.Bytes[builder.head : (builder.head + len(image.data))] = image.data
    image.data = builder.EndVector(len(image.data))
    Image.ImageStart(builder)
    Image.ImageAddHeight(builder, image.height)
    Image.ImageAddWidth(builder, image.width)
    Image.ImageAddData(builder, image.data)
    image = Image.ImageEnd(builder)
    # end image

    # begin event data
    # prediction is optional; if not provided, inference will run in beam pipeline
    bounding_boxes = build_bounding_boxes_message(builder, ts, prediction)
    MonitoringFrame.MonitoringFrameStart(builder)
    MonitoringFrame.MonitoringFrameAddImage(builder, image)
    if bounding_boxes:
        MonitoringFrame.MonitoringFrameAddBoundingBoxes(builder, bounding_boxes)
    MonitoringFrame.MonitoringFrameAddTs(builder, ts)
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
    TelemetryEvent.TelemetryEventStart(builder)
    TelemetryEvent.TelemetryEventAddEventData(builder, event_data)
    TelemetryEvent.TelemetryEventAddEventType(builder, event_type)
    telemetry_event = TelemetryEvent.TelemetryEventEnd(builder)
    builder.Finish(telemetry_event)

    # end tlemetry event
    return builder.Output()
