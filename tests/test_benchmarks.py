import concurrent
import pytest
import asyncio
import json
import threading
from octoprint_nanny.workers.monitoring import MonitoringWorker, get_predict_bytes
import octoprint_nanny.plugins
from octoprint_nanny.utils.encoder import NumpyEncoder
import sys
import PIL


def get_default_setting(key):
    return octoprint_nanny.plugins.DEFAULT_SETTINGS[key]


@pytest.mark.benchmark(group="active-learning-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_active_learning_msg_json_serialize(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()

    def predict_and_serialize(buffer):
        ws_msg = worker._create_active_learning_json_msgs(12345, buffer)
        ws_msg = json.dumps(ws_msg, cls=NumpyEncoder)
        return ws_msg

    ws_msg = benchmark(predict_and_serialize, buffer)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(ws_msg)


@pytest.mark.benchmark(group="active-learning-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_active_learning_msg_flatbuffer_serialize(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()
    buffer.seek(0)
    (image_width, image_height) = PIL.Image.open(buffer).size

    def predict_and_serialize(buffer):
        ws_msg = worker._create_active_learning_flatbuffer_msgs(
            12345, image_height, image_width, buffer
        )
        return ws_msg

    ws_msg = benchmark(predict_and_serialize, buffer)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(ws_msg)


@pytest.mark.benchmark(group="lite-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_lite_msg_json_serialize(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()
    (_, _), (viz_buffer, h, w), prediction = get_predict_bytes(
        buffer, calibration=None, min_score_thresh=0.1
    )

    def predict_and_serialize(buffer):
        ws_msg, mqtt_msg = worker._create_lite_json_msgs(12345, viz_buffer, prediction)
        ws_msg = json.dumps(ws_msg, cls=NumpyEncoder)
        mqtt_msg = json.dumps(mqtt_msg, cls=NumpyEncoder)
        return ws_msg, mqtt_msg

    ws_msg, mqtt_msg = benchmark(predict_and_serialize, buffer)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(mqtt_msg)


@pytest.mark.benchmark(group="lite-serializer", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_lite_msg_flatbuffer_serialize(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()
    (_, _), (viz_buffer, h, w), prediction = get_predict_bytes(
        buffer, calibration=None, min_score_thresh=0.1
    )

    def predict_and_serialize(buffer):
        ws_msg, mqtt_msg = worker._create_lite_flatbuffer_msgs(
            12345, viz_buffer, h, w, prediction
        )
        return ws_msg, mqtt_msg

    ws_msg, mqtt_msg = benchmark(predict_and_serialize, buffer)
    benchmark.extra_info["ws_msg_size"] = sys.getsizeof(ws_msg)
    benchmark.extra_info["mqtt_msg_size"] = sys.getsizeof(mqtt_msg)


@pytest.mark.benchmark(group="predict", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_uncalibrated_predict(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
    mock_mqtt_send_queue = mocker.Mock()
    halt = threading.Event()
    mock_plugin = mocker.Mock()
    mock_plugin.get_setting = get_default_setting
    mock_plugin.settings.monitoring_frames_per_minute = 10
    mock_plugin.settings.snapshot_url = get_default_setting("snapshot_url")
    mock_plugin.settings.calibration = None

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()

    benchmark(get_predict_bytes, buffer, calibration=None, min_score_thresh=0.5)


@pytest.mark.benchmark(group="predict", max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_calibrated_predict(benchmark, mocker):

    mock_pn_ws_queue = mocker.Mock()
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

    worker = MonitoringWorker(mock_pn_ws_queue, mock_mqtt_send_queue, halt, mock_plugin)
    buffer = await worker.load_url_buffer()

    benchmark(get_predict_bytes, buffer, calibration=calibration, min_score_thresh=0.5)
