import flatbuffers

from print_nanny_message import PrintNannyMessage


def build_monitoring_frame_raw_message(ts, image):
    builder = flatbuffers.Builder(1024)

    # begin message body
    PrintNannyMessage.Telemetry.MonitoringFrameRaw.MonitoringFrameRawStart(builder)
    PrintNannyMessage.Telemetry.MonitoringFrameRaw.MonitoringFrameRawAddTs(builder, ts)
    PrintNannyMessage.Telemetry.MonitoringFrameRaw.MonitoringFrameRawAddImage(
        builder, image
    )
    PrintNannyMessage.Telemetry.MonitoringFrameRaw.MonitoringFrameRawEventType(
        builder,
        PrintNannyMessage.Telemetry.PluginEvent.PluginEvent.monitoring_frame_raw,
    )
    message = PrintNannyMessage.Telemetry.MonitoringFrameRaw.MonitoringFrameRawEnd(
        builder
    )
    # end message body

    # begin message
    PrintNannyMessage.TelemetryMessage.TelemetryMessageStart(builder)
    message_type = (
        PrintNannyMessage.Telemetry.MessageType.MessageType.MonitoringFrameRaw
    )
    PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageAddMessageType(
        builder, message_type
    )
    PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageAddMessage(
        builder, message
    )
    message = PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageEnd(builder)
    # end message
    return message


def build_monitoring_frame_post_message(ts, image_height, image_width, image_bytes):
    builder = flatbuffers.Builder(1024)

    # begin image
    PrintNannyMessage.Telemetry.Image.ImageStart(builder)
    PrintNannyMessage.Telemetry.Image.ImageAddHeight(image_height)
    PrintNannyMessage.Telemetry.Image.ImageAddWidth(image_width)
    PrintNannyMessage.Telemetry.Image.ImageAddData(image_bytes)
    # end image

    # begin message body
    PrintNannyMessage.Telemetry.MonitoringFramePost.MonitoringFramePostStart(builder)
    PrintNannyMessage.Telemetry.MonitoringFramePost.MonitoringFramePostAddTs(
        builder, ts
    )
    PrintNannyMessage.Telemetry.MonitoringFramePost.MonitoringFramePostAddImage(
        builder, image
    )
    PrintNannyMessage.Telemetry.MonitoringFramePost.MonitoringFramePostEventType(
        builder,
        PrintNannyMessage.Telemetry.PluginEvent.PluginEvent.monitoring_frame_post,
    )
    message = PrintNannyMessage.Telemetry.MonitoringFramePost.MonitoringFramePostEnd(
        builder
    )
    # end message body

    # begin message
    PrintNannyMessage.TelemetryMessage.TelemetryMessageStart(builder)
    message_type = (
        PrintNannyMessage.Telemetry.MessageType.MessageType.MonitoringFramePost
    )
    PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageAddMessageType(
        builder, message_type
    )
    PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageAddMessage(
        builder, message
    )
    message = PrintNannyMessage.Telemetry.TelemetryMessage.TelemetryMessageEnd(builder)
    # end message
    return message


def build_bounding_boxes_message(boxes, original_image=None, post_image=None):
    builder = flatbuffers.Builder(1024)

    # begin boxes builder
