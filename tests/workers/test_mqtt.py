import asyncio
import os
import pytest
from asynctest import CoroutineMock
from asynctest import MagicMock
from datetime import datetime
from octoprint_nanny.workers.mqtt import (
    MQTTClientWorker,
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

    subscriber_worker = MQTTSubscriberWorker(halt=halt, queue=queue, plugin=plugin)

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
    open_mock.__aenter__.return_value = writer_mock
    mock_aiofiles = mocker.patch(
        "octoprint_nanny.workers.mqtt.aiofiles.open", return_value=open_mock
    )

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

    mock_aiofiles.assert_has_calls(
        [
            mocker.call(os.path.join(data_folder, "labels.txt"), "w+"),
            mocker.call(os.path.join(data_folder, "model.tflite"), "w+"),
            mocker.call(os.path.join(data_folder, "version.txt"), "w+"),
            mocker.call(os.path.join(data_folder, "metadata.json"), "w+"),
        ]
    )
