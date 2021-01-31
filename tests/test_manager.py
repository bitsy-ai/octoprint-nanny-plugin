import pytest

import octoprint_nanny.plugins  # import DEFAULT_SETTINGS, OctoPrintNannyPlugin
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired


@pytest.fixture(autouse=True)
def mock_plugin(automock):
    with automock((octoprint_nanny.plugins, "OctoPrintNannyPlugin"), unlocked=True):
        yield


def get_default_setting(key):
    return octoprint_nanny.plugins.DEFAULT_SETTINGS[key]


def test_default_settings_client_states(mocker):
    """
    By default, accessing WorkerManger.rest_client and WorkerManger.mqtt_client should raise PluginSettingsRequired
    """
    plugin = octoprint_nanny.plugins.OctoPrintNannyPlugin()
    plugin.get_setting = get_default_setting
    manager = WorkerManager(plugin)

    assert manager.auth_token is None
    assert manager.device_id is None

    with pytest.raises(PluginSettingsRequired):
        dir(manager.mqtt_client)
    with pytest.raises(PluginSettingsRequired):
        dir(manager.rest_client)
