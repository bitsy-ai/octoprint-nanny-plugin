import asyncio
import os
import pytest
from asynctest import CoroutineMock
from asynctest import MagicMock
from datetime import datetime
from octoprint_nanny.workers.mqtt import (
    MQTTManager,
    MQTTSubscriberWorker,
    MQTTPublisherWorker,
)


@pytest.mark.asyncio
async def test_handle_config_update(mocker):
    plugin = mocker.Mock()
    halt = mocker.Mock()
    queue = mocker.Mock()

    data_folder = "/path/to/data"
    plugin.get_plugin_data_folder.return_value = data_folder

    subscriber_worker = MQTTSubscriberWorker(queue=queue, plugin=plugin)

    mock_res = MagicMock()
    mock_res.__aenter__.return_value.get.return_value.__aenter__.return_value.text.return_value = (
        asyncio.Future()
    )
    mock_res.__aenter__.return_value.get.return_value.__aenter__.return_value.text.return_value.set_result(
        MagicMock()
    )
    mocker.patch(
        "octoprint_nanny.workers.mqtt.aiohttp.ClientSession", return_value=mock_res
    )

    writer_mock = MagicMock()
    writer_mock.write.return_value = asyncio.Future()
    writer_mock.write.return_value.set_result(MagicMock())
    open_mock = MagicMock()
    mock_open = mocker.patch("octoprint_nanny.workers.mqtt.open")

    topic = "fake-topic"

    labels_url = "https://labels.com/labels.txt"
    artifacts_url = "https://artifacts.com/artifacts.tflite"
    version = "0.0.0"
    metadata = {"python_version": "3.7.3"}
    message = {
        "id": 1,
        "created_dt": datetime.now(),
        "experiment": {},
        "artifact": {
            "labels": labels_url,
            "artifacts": artifacts_url,
            "version": version,
            "metadata": metadata,
        },
    }
    await subscriber_worker._handle_config_update(topic, message)

    assert mock_open.called
