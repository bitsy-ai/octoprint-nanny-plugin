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
from octoprint_nanny.predictor import predict_threadsafe

import print_nanny_client
from print_nanny_client.telemetry_event import (
    MonitoringFrame,
    TelemetryEvent,
    TelemetryEventEnum,
)


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_enabled_with_prediction_results_uncalibrated(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker, metadata
):
    mock_get.return_value.__aenter__.return_value = mock_response

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.metadata = metadata
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.min_score_thresh = 0.50
    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.LITE

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    msg = args[0]
    deserialized_msg = TelemetryEvent.TelemetryEvent.GetRootAsTelemetryEvent(msg, 0)
    deserialized_obj = TelemetryEvent.TelemetryEventT.InitFromObj(deserialized_msg)

    assert (
        deserialized_msg.EventType()
        == TelemetryEventEnum.TelemetryEventEnum.monitoring_frame_post
    )

    assert deserialized_msg.Version().decode("utf-8") == print_nanny_client.__version__


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_enabled_with_prediction_results_calibrated(
    mock_base64,
    mock_events_enum,
    mock_get,
    calibration,
    mock_response,
    mocker,
    metadata,
):
    mock_get.return_value.__aenter__.return_value = mock_response

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = calibration
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.min_score_thresh = 0.50
    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.LITE
    plugin.settings.metadata = metadata

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    msg = args[0]
    deserialized_msg = TelemetryEvent.TelemetryEvent.GetRootAsTelemetryEvent(msg, 0)
    assert (
        deserialized_msg.EventType()
        == TelemetryEventEnum.TelemetryEventEnum.monitoring_frame_post
    )
    assert deserialized_msg.Version().decode("utf-8") == print_nanny_client.__version__


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_enabled_zero_prediction_results_uncalibrated(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker, metadata
):
    mock_get.return_value.__aenter__.return_value = mock_response

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.min_score_thresh = 0.999
    plugin.settings.metadata = metadata

    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.LITE

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    assert predict_worker._mqtt_send_queue.put_nowait.called is False


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_enabled_zero_prediction_results_calibrated(
    mock_base64,
    mock_events_enum,
    mock_get,
    calibration,
    mock_response,
    mocker,
    metadata,
):
    mock_get.return_value.__aenter__.return_value = mock_response

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = calibration
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.min_score_thresh = 0.999
    plugin.settings.metadata = metadata

    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.LITE

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    assert predict_worker._mqtt_send_queue.put_nowait.called is False


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_lite_mode_webcam_disabled(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker, metadata
):
    mock_get.return_value.__aenter__.return_value = mock_response

    payload = {}

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.min_score_thresh = 0.50
    plugin.settings.webcam_upload = False
    plugin.settings.monitoring_mode = MonitoringModes.LITE
    plugin.settings.metadata = metadata

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_not_called()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    msg = args[0]
    deserialized_msg = TelemetryEvent.TelemetryEvent.GetRootAsTelemetryEvent(msg, 0)
    assert (
        deserialized_msg.EventType()
        == TelemetryEventEnum.TelemetryEventEnum.monitoring_frame_post
    )
    assert deserialized_msg.Version().decode("utf-8") == print_nanny_client.__version__


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.base64")
async def test_active_learning_mode(
    mock_base64, mock_events_enum, mock_get, mock_response, mocker, metadata
):
    mock_get.return_value.__aenter__.return_value = mock_response

    payload = {}

    plugin = mocker.Mock()

    pn_ws_queue = mocker.Mock()
    mqtt_send_queue = mocker.Mock()

    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30
    plugin.settings.metadata = metadata

    plugin.settings.webcam_upload = True
    plugin.settings.monitoring_mode = MonitoringModes.ACTIVE_LEARNING

    halt = threading.Event()
    predict_worker = MonitoringWorker(pn_ws_queue, mqtt_send_queue, halt, plugin)

    loop = asyncio.get_running_loop()
    predict_worker.loop = loop
    with concurrent.futures.ProcessPoolExecutor() as pool:
        predict_worker.pool = pool
        await predict_worker._loop()

    predict_worker._plugin._event_bus.fire.assert_called_once_with(
        mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64,
        payload=mock_base64.b64encode.return_value,
    )
    predict_worker._pn_ws_queue.put_nowait.assert_called_once()
    predict_worker._mqtt_send_queue.put_nowait.assert_called_once()

    kall = predict_worker._mqtt_send_queue.put_nowait.mock_calls[0]
    _, args, kwargs = kall

    msg = args[0]
    deserialized_msg = TelemetryEvent.TelemetryEvent.GetRootAsTelemetryEvent(msg, 0)

    assert (
        deserialized_msg.EventType()
        == TelemetryEventEnum.TelemetryEventEnum.monitoring_frame_raw
    )
    assert deserialized_msg.Version().decode("utf-8") == print_nanny_client.__version__
