import pytest
import concurrent
import asyncio
import threading
from asynctest import CoroutineMock, patch
import unittest.mock
from octoprint_nanny.types import PluginEvents, MonitoringModes
from octoprint_nanny.workers.monitoring import (
    MonitoringWorker,
    MonitoringManager,
    MonitoringModes,
)
from PrintNannyMessage.Telemetry import (
    TelemetryMessage,
    MonitoringFrame,
    MessageType,
    PluginEvent,
)


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_enabled(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker
):
    mock_get.return_value.__aenter__.return_value = mock_response

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30

    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.LITE

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        await predict_worker._loop(loop, pool)

    octoprint_event = PluginEvents.to_octoprint_event(
        PluginEvents.MONITORING_FRAME_POST
    )
    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        octoprint_event,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    mqtt_msg = args[0]
    deserialized_mqtt_msg = TelemetryMessage.TelemetryMessage.GetRootAsTelemetryMessage(
        mqtt_msg, 0
    )
    mqtt_msg_obj = TelemetryMessage.TelemetryMessageT.InitFromObj(deserialized_mqtt_msg)
    assert (
        mqtt_msg_obj.message.eventType == PluginEvent.PluginEvent.bounding_box_predict
    )


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_disabled(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker
):
    mock_get.return_value.__aenter__.return_value = mock_response

    payload = {}

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30

    plugin.settings.webcam_upload = False
    plugin.settings.monitoring_mode = MonitoringModes.LITE

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        await predict_worker._loop(loop, pool)

    octoprint_event = PluginEvents.to_octoprint_event(
        PluginEvents.MONITORING_FRAME_POST
    )
    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        octoprint_event,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_not_called()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    mqtt_msg = args[0]
    deserialized_mqtt_msg = TelemetryMessage.TelemetryMessage.GetRootAsTelemetryMessage(
        mqtt_msg, 0
    )
    mqtt_msg_obj = TelemetryMessage.TelemetryMessageT.InitFromObj(deserialized_mqtt_msg)
    assert (
        mqtt_msg_obj.message.eventType == PluginEvent.PluginEvent.bounding_box_predict
    )


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_active_learning_mode(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker
):
    mock_get.return_value.__aenter__.return_value = mock_response

    payload = {}

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30

    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.ACTIVE_LEARNING

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        await predict_worker._loop(loop, pool)

    octoprint_event = PluginEvents.to_octoprint_event(PluginEvents.MONITORING_FRAME_RAW)
    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        octoprint_event,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    mqtt_msg = args[0]
    deserialized_mqtt_msg = TelemetryMessage.TelemetryMessage.GetRootAsTelemetryMessage(
        mqtt_msg, 0
    )
    mqtt_msg_obj = TelemetryMessage.TelemetryMessageT.InitFromObj(deserialized_mqtt_msg)

    assert (
        mqtt_msg_obj.message.eventType == PluginEvent.PluginEvent.monitoring_frame_raw
    )
