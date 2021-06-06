import asyncio
import pytest
from asynctest import patch

from unittest.mock import PropertyMock
import PIL
import octoprint_nanny.plugins  # import DEFAULT_SETTINGS, OctoPrintNannyPlugin
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint.events import Events


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
async def test_mqtt_send_queue_valid_octoprint_event(mocker, metadata):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    plugin_settings = mocker.Mock()
    plugin_settings.event_is_tracked.return_value = True
    plugin_settings.metadata = metadata

    mock_on_print_start = mocker.patch.object(WorkerManager, "on_print_start")
    Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES = (
        "plugin_octoprint-nanny_monitoring_frame_bytes"
    )
    manager = WorkerManager(plugin, plugin_settings=plugin_settings)
    event = {"event_type": Events.PRINT_STARTED, "event_data": {}}
    manager.mqtt_send_queue.put_nowait(event)

    mockpublish_octoprint_event_telemetry = mocker.patch.object(
        manager.mqtt_manager.publisher_worker,
        "publish_octoprint_event_telemetry",
        return_value=asyncio.Future(),
    )
    mockpublish_octoprint_event_telemetry.return_value.set_result("foo")

    await manager.mqtt_manager.publisher_worker._loop()

    mockpublish_octoprint_event_telemetry.assert_called_once_with(event)

    mock_on_print_start.assert_called_once_with(
        event_data=event["event_data"], event_type=event["event_type"]
    )


@pytest.mark.asyncio
async def test_mqtt_send_queue_bounding_box_predict(mocker, mock_image, metadata):
    plugin = mocker.Mock()
    plugin.settings.metadata = metadata

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")
    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.mqtt_client")

    plugin_settings = mocker.Mock()
    plugin_settings.event_is_tracked.return_value = True
    plugin_settings.metadata = metadata

    Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES = (
        "plugin_octoprint_nanny_monitoring_frame_bytes"
    )
    Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_B64 = (
        "plugin_octoprint_nanny_monitoring_frame_b64"
    )

    manager = WorkerManager(plugin, plugin_settings=plugin_settings)

    event = {
        "event_type": Events.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES,
        "event_data": {"image": await mock_image.read(), "ts": 1234},
    }
    manager.mqtt_send_queue.put_nowait(event)

    mock_fn = plugin.settings.mqtt_client.publish_monitoring_frame_raw
    mock_fn.return_value = asyncio.Future()
    mock_fn.return_value.set_result("foo")

    await manager.mqtt_manager.publisher_worker._loop()

    mock_fn.assert_called_once()


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
                metadata=metadata.to_dict(),
            ),
            mocker.call(
                command["message"]["remote_control_command_id"],
                success=True,
                metadata=metadata.to_dict(),
            ),
        ]
    )
    mock_start_monitoring.assert_called_once_with(
        event=command["message"], event_type=command["message"]["octoprint_event_type"]
    )
