import pytest

from octoprint_nanny.plugins import DEFAULT_SETTINGS
from octoprint_nanny.manager import WorkerManager


@pytest.fixture(autouse=True)
def mock_plugin(automock):
    with automock("octoprint_nanny.OctoPrintNannyPlugin"):
        yield


@pytest.fixture
def mock_plugin_default_settings(mock_plugin):
    def get_default_setting(key):
        key = key[0]
        return DEFAULT_SETTINGS[key]

    mock_plugin._settings.get = get_default_setting
    return mock_plugin


def test_invalid_auth_raises(mocker, mock_plugin):
    manager = WorkerManager(mock_plugin)
