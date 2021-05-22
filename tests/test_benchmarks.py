import concurrent
import pytest
import asyncio
import json
import threading
import io
from octoprint_nanny.workers.monitoring import MonitoringWorker
from octoprint_nanny.predictor import predict_threadsafe
import octoprint_nanny.plugins
from octoprint_nanny.utils.encoder import NumpyEncoder
import sys
import PIL
from print_nanny_client.flatbuffers.monitoring import (
    MonitoringEvent,
)
from datetime import datetime


def get_default_setting(key):
    return octoprint_nanny.plugins.DEFAULT_SETTINGS[key]


@pytest.mark.benchmark(group="active-learning-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_active_learning_json_serialize(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()

    def serialize(buffer):
        ws_msg = worker._create_active_learning_json_msgs(12345, buffer)
        ws_msg = json.dumps(ws_msg, cls=NumpyEncoder)
        return ws_msg

    ws_msg = benchmark(serialize, buffer)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["serializer"] = "json"


@pytest.mark.benchmark(group="active-learning-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_active_learning_flatbuffer_serialize(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()
    (image_width, image_height) = PIL.Image.open(io.BytesIO(buffer)).size

    ts = int(datetime.now().timestamp())

    def serialize(ts, buffer, image_height, image_width):
        ws_msg = worker._create_active_learning_flatbuffer_msg(
            ts, image_height, image_width, buffer
        )
        return ws_msg

    ws_msg = benchmark(serialize, ts, buffer, image_height, image_width)

    deserialized_ws_msg = TelmetryEvent.TelmetryEvent.GetRootAsTelmetryEvent(ws_msg, 0)
    ws_msg_obj = TelmetryEvent.TelmetryEventT.InitFromObj(deserialized_ws_msg)

    assert ws_msg_obj.message.ts == ts
    assert ws_msg_obj.message.image.width == 640
    assert ws_msg_obj.message.image.height == 480

    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["serializer"] = "fb"


@pytest.mark.benchmark(group="lite-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_lite_json_serialize(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()

    (_, _), (viz_buffer, h, w), prediction = predict_threadsafe(
        buffer, calibration=None, min_score_thresh=0.001
    )

    ts = int(datetime.now().timestamp())

    def serialize(ts, buffer, viz_buffer, prediction):
        ws_msg, mqtt_msg = worker._create_lite_json_msgs(
            ts, buffer, viz_buffer, prediction
        )
        ws_msg = json.dumps(ws_msg, cls=NumpyEncoder)
        mqtt_msg = json.dumps(mqtt_msg, cls=NumpyEncoder)
        return ws_msg, mqtt_msg

    ws_msg, mqtt_msg = benchmark(serialize, ts, buffer, viz_buffer, prediction)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(mqtt_msg)
    benchmark.extra_info["serializer"] = "json"


@pytest.mark.benchmark(group="lite-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_lite_flatbuffer_uncalibrated_serialize(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()
    (oh, ow), (viz_buffer, vh, vw), prediction = predict_threadsafe(
        buffer, calibration=None, min_score_thresh=0.001
    )

    ts = int(datetime.now().timestamp())

    def serialize(ts, oh, ow, buffer, vh, vw, viz_buffer, prediction):
        ws_msg, mqtt_msg = worker._create_lite_flatbuffer_msgs(
            ts,
            prediction,
            vh,
            vw,
            viz_buffer,
            # oh, ow, buffer,
        )
        return ws_msg, mqtt_msg

    ws_msg, mqtt_msg = benchmark(
        serialize, ts, oh, ow, buffer, vh, vw, viz_buffer, prediction
    )
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(mqtt_msg)
    benchmark.extra_info["serializer"] = "fb"

    deserialized_ws_msg = TelmetryEvent.TelmetryEvent.GetRootAsTelmetryEvent(ws_msg, 0)
    ws_msg_obj = TelmetryEvent.TelmetryEventT.InitFromObj(deserialized_ws_msg)
    assert ws_msg_obj.message.ts == ts
    assert ws_msg_obj.message.image.width == 640
    assert ws_msg_obj.message.image.height == 480

    deserialized_mqtt_msg = TelmetryEvent.TelmetryEvent.GetRootAsTelmetryEvent(
        mqtt_msg, 0
    )
    mqtt_msg_obj = TelmetryEvent.TelmetryEventT.InitFromObj(deserialized_mqtt_msg)
    assert mqtt_msg_obj.message.ts == ts

    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.scores)
    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.classes)
    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.boxes)


@pytest.mark.benchmark(group="lite-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_lite_flatbuffer_calibrated_serialize(calibration, benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = calibration

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()
    (oh, ow), (viz_buffer, vh, vw), prediction = predict_threadsafe(
        buffer,
        calibration=calibration,
    )

    ts = int(datetime.now().timestamp())

    def serialize(ts, oh, ow, buffer, vh, vw, viz_buffer, prediction):
        ws_msg, mqtt_msg = worker._create_lite_flatbuffer_msgs(
            ts,
            prediction,
            vh,
            vw,
            viz_buffer,
            # oh, ow, buffer,
        )
        return ws_msg, mqtt_msg

    ws_msg, mqtt_msg = benchmark(
        serialize, ts, oh, ow, buffer, vh, vw, viz_buffer, prediction
    )
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(mqtt_msg)
    benchmark.extra_info["serializer"] = "fb"

    deserialized_ws_msg = TelmetryEvent.TelmetryEvent.GetRootAsTelmetryEvent(ws_msg, 0)
    ws_msg_obj = TelmetryEvent.TelmetryEventT.InitFromObj(deserialized_ws_msg)
    assert ws_msg_obj.message.ts == ts
    assert ws_msg_obj.message.image.width == 640
    assert ws_msg_obj.message.image.height == 480

    deserialized_mqtt_msg = TelmetryEvent.TelmetryEvent.GetRootAsTelmetryEvent(
        mqtt_msg, 0
    )
    mqtt_msg_obj = TelmetryEvent.TelmetryEventT.InitFromObj(deserialized_mqtt_msg)
    assert mqtt_msg_obj.message.ts == ts

    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.scores)
    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.classes)
    assert mqtt_msg_obj.message.numDetections == len(mqtt_msg_obj.message.boxes)


@pytest.mark.benchmark(group="predict", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_uncalibrated_predict(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()

    benchmark(predict_threadsafe, buffer, calibration=None, min_score_thresh=0.01)


@pytest.mark.benchmark(group="predict", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_calibrated_predict(benchmark, mocker):

    mock_multiprocess_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    calibration = MonitoringWorker.calc_calibration(
        0.2,
        0.2,
        0.8,
        0.8,
    )
    mock_plugin.settings.calibration = calibration

    worker = MonitoringWorker(
        mock_multiprocess_ws_queue, mock_mqtt_send_queue, halt, mock_plugin
    )
    buffer = await worker.load_url_buffer()

    benchmark(
        predict_threadsafe, buffer, calibration=calibration, min_score_thresh=0.01
    )
