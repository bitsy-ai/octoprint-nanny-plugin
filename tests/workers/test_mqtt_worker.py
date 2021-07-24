import asyncio
import pytest
from asynctest import CoroutineMock
from asynctest import MagicMock
from datetime import datetime
from octoprint_nanny.workers.mqtt import (
    MQTTManager,
    MQTTSubscriberWorker,
    MQTTPublisherWorker,
)


def test_frame_sent_monitoring_active(
    mocker, mock_plugin, EVENT_PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
):
    queue = mocker.Mock()
    worker = MQTTPublisherWorker(
        queue=queue, plugin=mock_plugin, plugin_settings=mock_plugin.settings
    )
    mock_plugin.settings.monitoring_active = True

    res = worker.handle_monitoring_frame_bytes(
        **EVENT_PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
    )

    assert mock_plugin.settings.mqtt_client.called_once()
    assert mock_plugin._event_bus.fire().called_once()


def test_frame_skipped_monitoring_inactive(
    mocker, mock_plugin, EVENT_PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
):
    queue = mocker.Mock()
    worker = MQTTPublisherWorker(
        queue=queue, plugin=mock_plugin, plugin_settings=mock_plugin.settings
    )

    mock_plugin.settings.monitoring_active = False
    res = worker.handle_monitoring_frame_bytes(
        **EVENT_PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES
    )

    assert mock_plugin.settings.mqtt_client.called is False
    assert mock_plugin._event_bus.fire().called is False


@pytest.mark.asyncio
async def test_handle_config_update(mocker, plugin_settings):
    plugin = mocker.Mock()
    mocker.Mock()
    queue = mocker.Mock()

    plugin_settings.data_folder = "/path/to/data"
    subscriber_worker = MQTTSubscriberWorker(
        queue=queue, plugin=plugin, plugin_settings=plugin_settings
    )

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
    MagicMock()
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
