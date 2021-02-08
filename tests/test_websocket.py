import pytest
import aioprocessing
import queue
import aiohttp
import urllib
from datetime import datetime
from octoprint_nanny.workers.websocket import WebSocketWorker
from octoprint_nanny.predictor import PredictWorker
import pytz
import threading


@pytest.fixture
def ws_client(mocker):
    mocker.patch("octoprint_nanny.workers.websocket.asyncio")
    m = aioprocessing.AioManager()
    return WebSocketWorker(
        "ws://localhost:8000/ws/",
        "3a833ac48104772a349254690cae747e826886f1",
        m.Queue(),
        1,
        threading.Event(),
        {},
    )


@pytest.fixture
def predict_worker(mocker):
    mocker.patch("octoprint_nanny.predictor.threading")
    m = aioprocessing.AioManager()

    return PredictWorker(
        "http://localhost:8080/?action=snapshot",
        None,
        m.Queue(),
        m.Queue(),
        m.Queue(),
        5,
        threading.Event(),
        mocker.Mock(),
        trace_context={},
    )


def test_wrong_queue_type_raises():
    with pytest.raises(ValueError):
        WebSocketWorker(
            "http://foo.com/ws/", "api_team", queue.Queue(), 1, threading.Event(), {}
        )


@pytest.mark.webapp
@pytest.mark.asyncio
async def test_ws_ping(ws_client):
    assert await ws_client.ping() == "pong"
