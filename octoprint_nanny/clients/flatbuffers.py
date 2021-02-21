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
import octoprint_nanny.types


def build_telemetry_message(builder, message, message_type):
    TelemetryMessage.TelemetryMessageStart(builder)
    TelemetryMessage.TelemetryMessageAddMessageType(builder, message_type)
    TelemetryMessage.TelemetryMessageAddMessage(builder, message)
    message = TelemetryMessage.TelemetryMessageEnd(builder)
    builder.Finish(message)
    # end message
    return builder.Output()


def build_monitoring_frame_raw_message(
    ts: int, image: octoprint_nanny.types.Image
) -> bytes:
    builder = flatbuffers.Builder(1024)

    # begin byte array
    Image.ImageStartDataVector(builder, len(image.data))
    builder.Bytes[builder.head : (builder.head + len(image.data))] = image.data
    image.data = builder.EndVector(len(image.data))
    # end byte array

    # begin image
    Image.ImageStart(builder)
    Image.ImageAddHeight(builder, image.height)
    Image.ImageAddWidth(builder, image.width)
    Image.ImageAddData(builder, image.data)
    image = Image.ImageEnd(builder)
    # end image

    # begin message body
    MonitoringFrame.MonitoringFrameStart(builder)
    MonitoringFrame.MonitoringFrameAddTs(builder, ts)
    MonitoringFrame.MonitoringFrameAddImage(builder, image)
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
    ts: int, image: octoprint_nanny.types.Image
) -> bytes:
    builder = flatbuffers.Builder(1024)

    # begin byte array
    Image.ImageStartDataVector(builder, len(image.data))
    builder.Bytes[builder.head : (builder.head + len(image.data))] = image.data
    image.data = builder.EndVector(len(image.data))
    # end byte array

    # begin image
    Image.ImageStart(builder)
    Image.ImageAddHeight(builder, image.height)
    Image.ImageAddWidth(builder, image.width)
    Image.ImageAddData(builder, image.data)
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
    ts: int, prediction, image: Optional[octoprint_nanny.types.Image] = None
) -> bytes:
    builder = flatbuffers.Builder(1024)
    boxes = prediction.get("detection_boxes")
    scores = prediction.get("detection_scores")
    classes = prediction.get("detection_classes")
    num_detections = prediction.get("num_detections")

    # begin byte array
    if image:
        Image.ImageStartDataVector(builder, len(image.data))
        builder.Bytes[builder.head : (builder.head + len(image.data))] = image.data
        image.data = builder.EndVector(len(image.data))
        # end byte array

        # begin image
        Image.ImageStart(builder)
        Image.ImageAddHeight(builder, image.height)
        Image.ImageAddWidth(builder, image.width)
        Image.ImageAddData(builder, image.data)
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

    if image:
        BoundingBoxes.BoundingBoxesAddImage(builder, image)
    message = BoundingBoxes.BoundingBoxesEnd(builder)
    # end message body

    return build_telemetry_message(
        builder, message, MessageType.MessageType.BoundingBoxes
    )
