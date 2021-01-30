import pytest
import aioprocessing
import queue
import aiohttp
import urllib
from datetime import datetime
from octoprint_nanny.clients.websocket import WebSocketWorker
from octoprint_nanny.predictor import PredictWorker
import pytz
import threading


@pytest.fixture
def ws_client(mocker):
    mocker.patch("octoprint_nanny.clients.websocket.asyncio")
    m = aioprocessing.AioManager()
    return WebSocketWorker(
        "ws://localhost:8000/ws/",
        "3a833ac48104772a349254690cae747e826886f1",
        m.Queue(),
        1,
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
        threading.Event(),
        mocker.mock(),
        {},
    )


def test_wrong_queue_type_raises():
    with pytest.raises(ValueError):
        WebSocketWorker(
            "http://foo.com/ws/", "api_team", queue.Queue(), 1, 1, threading.Event(), {}
        )


@pytest.mark.webapp
@pytest.mark.asyncio
async def test_ws_ping(ws_client):
    assert await ws_client.ping() == "pong"


@pytest.mark.webapp
@pytest.mark.asyncio
async def test_ws_predict_e2e(ws_client, mocker, predict_worker):
    async with aiohttp.ClientSession() as session:
        msg = await predict_worker._image_msg(
            datetime.now(pytz.timezone("America/Los_Angeles")), session
        )

        predict_msg = predict_worker._predict_msg(msg)

    res = await ws_client.send(predict_msg)
