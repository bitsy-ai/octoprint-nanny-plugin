import pytest
import concurrent
import asyncio
import threading
from asynctest import CoroutineMock, patch

from octoprint_nanny.workers.monitoring import (
    MonitoringWorker,
    MonitoringManager,
    MonitoringModes,
)


class MockResponse(object):
    headers = {"content-type": "image/jpeg"}

    async def read(self):
        with open("octoprint_nanny/data/images/0.pre.jpg", "rb") as f:
            return f.read()


@pytest.fixture
def mock_response():
    return MockResponse()


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
@patch("octoprint_nanny.workers.monitoring.Events")
async def test_share_lite_webcam_enabled(
    mock_events_enum, mock_get, mock_response, mocker
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

    assert predict_worker._plugin._event_bus.fire.called
    assert predict_worker._pn_ws_queue.put_nowait.called
    assert predict_worker._mqtt_send_queue.put_nowait.called
