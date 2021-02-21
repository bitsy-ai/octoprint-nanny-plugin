import io
import flatbuffers
from typing import Optional
from PrintNannyMessage.Telemetry import (
    MonitoringFrame,
    Image,
    Box,
    BoundingBoxes,
    PluginEvent,
    TelemetryMessage,
    MessageType,
)


def build_telemetry_message(builder, message, message_type):
    TelemetryMessage.TelemetryMessageStart(builder)
    TelemetryMessage.TelemetryMessageAddMessageType(builder, message_type)
    TelemetryMessage.TelemetryMessageAddMessage(builder, message)
    message = TelemetryMessage.TelemetryMessageEnd(builder)
    builder.Finish(message)
    # end message
    return builder.Output()


def build_monitoring_frame_raw_message(
    ts: int,
    image_height: int,
    image_width: int,
    image_bytes: bytes,
) -> bytes:
    builder = flatbuffers.Builder(1024)

    # begin byte array
    Image.ImageStartDataVector(builder, len(image_bytes))
    builder.Bytes[builder.head : (builder.head + len(image_bytes))] = image_bytes
    image_bytes = builder.EndVector(len(image_bytes))
    # end byte array

    # begin message body
    MonitoringFrame.MonitoringFrameStart(builder)
    MonitoringFrame.MonitoringFrameAddTs(builder, ts)
    MonitoringFrame.MonitoringFrameAddImage(builder, image_bytes)
    MonitoringFrame.MonitoringFrameAddEventType(
        builder,
        PluginEvent.PluginEvent.monitoring_frame_raw,
    )
    message = MonitoringFrame.MonitoringFrameEnd(builder)
    # end message body

    return build_telemetry_message(
        builder, message, MessageType.MessageType.MonitoringFrame
    )


def build_monitoring_frame_post_message(
    ts: int, image_height: int, image_width: int, image_bytes: bytes
) -> bytes:
    builder = flatbuffers.Builder(1024)

    # begin byte array
    Image.ImageStartDataVector(builder, len(image_bytes))
    builder.Bytes[builder.head : (builder.head + len(image_bytes))] = image_bytes
    image_bytes = builder.EndVector(len(image_bytes))
    # end byte array

    # begin image
    Image.ImageStart(builder)
    Image.ImageAddHeight(builder, image_height)
    Image.ImageAddWidth(builder, image_width)
    Image.ImageAddData(builder, image_bytes)
    image = Image.ImageEnd(builder)
    # end image

    # begin message body
    MonitoringFrame.MonitoringFrameStart(builder)
    MonitoringFrame.MonitoringFrameAddTs(builder, ts)
    MonitoringFrame.MonitoringFrameAddImage(builder, image)
    MonitoringFrame.MonitoringFrameAddEventType(
        builder,
        PluginEvent.PluginEvent.monitoring_frame_post,
    )
    message = MonitoringFrame.MonitoringFrameEnd(builder)
    # end message body
    return build_telemetry_message(
        builder, message, MessageType.MessageType.MonitoringFrame
    )


def build_bounding_boxes_message(
    ts: int,
    prediction,
    image_height: Optional[int] = None,
    image_width: Optional[int] = None,
    image_bytes: Optional[bytes] = None,
) -> bytes:
    builder = flatbuffers.Builder(1024)
    boxes = prediction.get("detection_boxes")
    scores = prediction.get("detection_scores")
    classes = prediction.get("detection_classes")
    num_detections = prediction.get("num_detections")

    # begin byte array
    image = None
    if image_height is not None and image_width is not None and image_bytes is not None:
        Image.ImageStartDataVector(builder, len(image_bytes))
        builder.Bytes[builder.head : (builder.head + len(image_bytes))] = image_bytes
        image_bytes = builder.EndVector(len(image_bytes))
        # end byte array

        # begin image
        Image.ImageStart(builder)
        Image.ImageAddHeight(builder, image_height)
        Image.ImageAddWidth(builder, image_width)
        Image.ImageAddData(builder, image_bytes)
        image = Image.ImageEnd(builder)
        # end image

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

    # begin message body
    BoundingBoxes.BoundingBoxesStart(builder)
    BoundingBoxes.BoundingBoxesAddTs(builder, ts)
    BoundingBoxes.BoundingBoxesAddBoxes(builder, boxes)
    BoundingBoxes.BoundingBoxesAddScores(builder, scores)
    BoundingBoxes.BoundingBoxesAddClasses(builder, classes)
    BoundingBoxes.BoundingBoxesAddNumDetections(builder, num_detections)
    BoundingBoxes.BoundingBoxesAddEventType(
        builder, PluginEvent.PluginEvent.bounding_box_predict
    )

    if image is not None:
        BoundingBoxes.BoundingBoxesAddImage(builder, image)
    message = BoundingBoxes.BoundingBoxesEnd(builder)
    # end message body

    return build_telemetry_message(
        builder, message, MessageType.MessageType.BoundingBoxes
    )
