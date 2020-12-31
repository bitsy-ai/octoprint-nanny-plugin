from pathlib import Path
import os
from octoprint_nanny.clients import mqtt
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


def test_client_id_constructor(mocker, private_key_filename, root_ca_filename):
    mock_mqtt = mocker.patch("octoprint_nanny.clients.mqtt.mqtt")
    # mocker.patch('octoprint_nanny.clients.mqtt.open')

    device_id = "device_id_1234"
    client = mqtt.MQTTClient(device_id, private_key_filename, root_ca_filename)

    client_id = f"projects/{mqtt.GCP_PROJECT_ID}/locations/{mqtt.GCP_IOT_DEVICE_REGISTRY_REGION}/registries/{mqtt.GCP_IOT_DEVICE_REGISTRY}/devices/{device_id}"
    
    mock_mqtt.Client.assert_called_once_with(client_id=client_id)
