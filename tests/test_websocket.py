import pytest
import multiprocessing
import queue
import urllib
from datetime import datetime
from print_nanny.websocket import WebSocketWorker
from print_nanny.predictor import PredictWorker
import pytz


@pytest.fixture
def ws_client(mocker):
    mocker.patch("print_nanny.websocket.asyncio")

    return WebSocketWorker(
        "http://localhost:8000/ws/predict/",
        "3a833ac48104772a349254690cae747e826886f1",
        multiprocessing.Queue(),
        1,
    )


@pytest.fixture
def predict_worker(mocker):
    mocker.patch("print_nanny.predictor.threading")

    return PredictWorker(
        "http://localhost:8080/?action=snapshot",
        multiprocessing.Queue(),
        multiprocessing.Queue(),
        calibration=None,
    )


def test_wrong_queue_type_raises():
    with pytest.raises(ValueError):
        WebSocketWorker("http://foo.com/ws/", "api_team", queue.Queue(), 1)


def test_ws_url_scheme_parse(mocker):
    mocker.patch("print_nanny.websocket.asyncio")
    ws_client = WebSocketWorker(
        "http://localhost:8000/ws/", "token", multiprocessing.Queue(), 1
    )

    wss_client = WebSocketWorker(
        "https://localhost:8000/ws/", "token", multiprocessing.Queue(), 1
    )

    assert ws_client._url == "ws://localhost:8000/ws/1"
    assert wss_client._url == "wss://localhost:8000/ws/1"
    assert ws_client._extra_headers == (("Authorization", f"Bearer token"),)


@pytest.mark.webapp
@pytest.mark.asyncio
async def test_ws_ping(ws_client):
    assert await ws_client.ping() == "pong"


@pytest.mark.webapp
@pytest.mark.asyncio
async def test_ws_predict_e2e(ws_client, mocker, predict_worker):
    msg = predict_worker._image_msg(datetime.now(pytz.timezone("America/Los_Angeles")))
    predict_msg = predict_worker._predict_msg(msg)

    await ws_client.send(predict_msg)
