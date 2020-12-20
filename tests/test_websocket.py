import pytest
import aioprocessing
import queue
import urllib
from datetime import datetime
from print_nanny.clients.websocket import WebSocketWorker
from print_nanny.predictor import PredictWorker
import pytz


@pytest.fixture
def ws_client(mocker):
    mocker.patch("print_nanny.clients.websocket.asyncio")
    m = aioprocessing.AioManager()
    return WebSocketWorker(
        "ws://localhost:8000/ws/predict/",
        "3a833ac48104772a349254690cae747e826886f1",
        m.Queue(),
        1,
    )


@pytest.fixture
def predict_worker(mocker):
    mocker.patch("print_nanny.predictor.threading")
    m = aioprocessing.AioManager()

    return PredictWorker(
        "http://localhost:8080/?action=snapshot",
        None,
        m.Queue(),
        m.Queue(),
    )

def test_wrong_queue_type_raises():
    with pytest.raises(ValueError):
        WebSocketWorker("http://foo.com/ws/", "api_team", queue.Queue(), 1)


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
