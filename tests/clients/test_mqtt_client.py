from pathlib import Path
import os
from octoprint_nanny.clients import mqtt
import paho.mqtt.client

import pytest


@pytest.fixture
def plugin_data_dir():
    return os.path.join(
        str(Path.home()),
        ".octoprint/data/octoprint_nanny",
    )


@pytest.fixture
def private_key_filename(plugin_data_dir):
    return os.path.join(plugin_data_dir, "private_key.pem")


@pytest.fixture
def root_ca_filename(plugin_data_dir):
    return os.path.join(plugin_data_dir, "gcp_root_ca.pem")


@pytest.fixture
def device_id():
    return "1"


@pytest.fixture
def device_cloudiot_id():
    return "1234"


@pytest.fixture
def client_id(device_cloudiot_id):
    return f"projects/{mqtt.GCP_PROJECT_ID}/locations/{mqtt.IOT_DEVICE_REGISTRY_REGION}/registries/{mqtt.IOT_DEVICE_REGISTRY}/devices/{device_cloudiot_id}"


def test_client_id_constructor(
    mocker,
    private_key_filename,
    root_ca_filename,
    device_id,
    client_id,
    device_cloudiot_id,
):
    mock_mqtt = mocker.patch("octoprint_nanny.clients.mqtt.mqtt")
    client = mqtt.MQTTClient(
        device_id,
        device_cloudiot_id,
        private_key_filename,
        root_ca_filename,
        trace_context={},
    )
    mock_mqtt.Client.assert_called_once_with(client_id=client_id, clean_session=False)
