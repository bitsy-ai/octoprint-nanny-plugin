import pytest
import multiprocessing
import queue
import aiohttp
import urllib
from datetime import datetime
from octoprint_nanny.workers.websocket import WebSocketWorker
from octoprint_nanny.workers.monitoring import MonitoringWorker
import pytz
import threading


@pytest.fixture
def ws_client(mocker):
    mocker.patch("octoprint_nanny.workers.websocket.asyncio")
    q = multiprocessing.Queue()
    return WebSocketWorker(
        "ws://localhost:8000/ws/",
        "3a833ac48104772a349254690cae747e826886f1",
        q,
        1,
        threading.Event(),
        {},
    )


@pytest.fixture
def predict_worker(mocker):
    mocker.patch("octoprint_nanny.predictor.threading")
    q1 = queue.Queue()
    q2 = queue.Queue()

    plugin = mocker.Mock()
    plugin.settings.snapshot_url = "http://localhost:8080/?action=snapshot"
    plugin.settings.calibration = None
    plugin.settings.monitoring_frames_per_minute = 30

    return MonitoringWorker(
        q1,
        q2,
        threading.Event(),
        plugin,
        trace_context={},
    )


def test_wrong_queue_type_raises():
    with pytest.raises(ValueError):
        WebSocketWorker(
            "http://foo.com/ws/", "api_team", queue.Queue(), 1, threading.Event()
        )
