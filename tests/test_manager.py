import asyncio
import pytest
from asynctest import CoroutineMock, patch

from unittest.mock import PropertyMock

import octoprint_nanny.plugins  # import DEFAULT_SETTINGS, OctoPrintNannyPlugin
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint.events import Events
from octoprint_nanny.types import PluginEvents


def get_default_setting(key):
    return octoprint_nanny.plugins.DEFAULT_SETTINGS[key]


def test_default_settings_client_states(mocker):
    """
    By default, accessing WorkerManger.rest_client and WorkerManger.mqtt_client should raise PluginSettingsRequired
    """
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting
    manager = WorkerManager(plugin)

    assert manager.plugin.settings.auth_token is None
    assert manager.plugin.settings.octoprint_device_id is None

    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin.settings.mqtt_client)
    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin.settings.rest_client)


@pytest.mark.asyncio
@patch("octoprint_nanny.settings.PluginSettingsMemoize.event_is_tracked")
async def test_mqtt_send_queue_valid_octoprint_event(mock_event_is_tracked, mocker):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    mock_event_is_tracked.return_value = True

    mock_on_print_start = mocker.patch.object(WorkerManager, "on_print_start")

    manager = WorkerManager(plugin)
    event = {"event_type": Events.PRINT_STARTED, "event_data": {}}
    manager.mqtt_send_queue.put_nowait(event)

    mock_publish_octoprint_event_telemetry = mocker.patch.object(
        manager.mqtt_manager.publisher_worker,
        "_publish_octoprint_event_telemetry",
        return_value=asyncio.Future(),
    )
    mock_publish_octoprint_event_telemetry.return_value.set_result("foo")

    await manager.mqtt_manager.publisher_worker._loop()

    mock_publish_octoprint_event_telemetry.assert_called_once_with(event)

    mock_on_print_start.assert_called_once_with(
        event_data=event["event_data"], event_type=event["event_type"]
    )


@pytest.mark.asyncio
@patch("octoprint_nanny.settings.PluginSettingsMemoize.event_is_tracked")
async def test_mqtt_send_queue_bounding_box_predict(mock_event_is_tracked, mocker):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")
    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.mqtt_client")

    mock_event_is_tracked.return_value = False

    manager = WorkerManager(plugin)

    event = bytearray("testing".encode())
    manager.mqtt_send_queue.put_nowait(event)

    mock_fn = plugin.settings.mqtt_client.publish_monitoring_frame_raw
    mock_fn.return_value = asyncio.Future()
    mock_fn.return_value.set_result("foo")

    await manager.mqtt_manager.publisher_worker._loop()

    mock_fn.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_mqtt_receive_queue_valid_octoprint_event(mocker, metadata):
    plugin = mocker.Mock()
    plugin_settings = mocker.Mock()
    plugin_settings.event_is_tracked.return_value = True
    plugin_settings.metadata = metadata

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    plugin_settings.rest_client.update_remote_control_command.return_value = (
        asyncio.Future()
    )
    plugin_settings.rest_client.update_remote_control_command.return_value.set_result(
        "foo"
    )

    mock_topic = "mock_command_topic"
    plugin_settings.mqtt_client.remote_control_commands_topic = mock_topic
    plugin_settings.mqtt_client.commands_topic = mock_topic

    manager = WorkerManager(plugin, plugin_settings=plugin_settings)
    mock_start_monitoring = mocker.patch.object(manager.monitoring_manager, "start")

    manager.plugin.settings.metadata = metadata
    manager.mqtt_manager.subscriber_worker.register_callbacks(
        {"octoprint_nanny_plugin_monitoring_start": mock_start_monitoring}
    )

    command = {
        "message": {
            "octoprint_event_type": "octoprint_nanny_plugin_monitoring_start",
            "command": "MonitoringStart",
            "remote_control_command_id": 1,
        },
        "topic": mock_topic,
    }
    manager.mqtt_manager.mqtt_receive_queue.put_nowait(command)

    await manager.mqtt_manager.subscriber_worker._loop()

    plugin_settings.rest_client.update_remote_control_command.assert_has_calls(
        [
            mocker.call(
                command["message"]["remote_control_command_id"],
                received=True,
                metadata=metadata,
            ),
            mocker.call(
                command["message"]["remote_control_command_id"],
                success=True,
                metadata=metadata,
            ),
        ]
    )
    mock_start_monitoring.assert_called_once_with(
        event=command["message"], event_type=command["message"]["octoprint_event_type"]
    )
