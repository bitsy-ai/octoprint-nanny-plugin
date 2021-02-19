import asyncio
import pytest
from asynctest import CoroutineMock, patch

from unittest.mock import PropertyMock

import octoprint_nanny.plugins  # import DEFAULT_SETTINGS, OctoPrintNannyPlugin
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint.events import Events
from octoprint_nanny.constants import PluginEvents


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
    assert manager.plugin.settings.device_id is None

    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin.settings.mqtt_client)
    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin.settings.rest_client)


@pytest.mark.asyncio
@patch("octoprint_nanny.settings.PluginSettingsMemoize.get_telemetry_events")
@patch("octoprint_nanny.settings.PluginSettingsMemoize.event_in_tracked_telemetry")
async def test_mqtt_send_queue_valid_octoprint_event(
    mock_event_in_tracked_telemetry, mock_get_telemetry_events, mocker
):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    mock_event_in_tracked_telemetry.return_value = True

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
@patch("octoprint_nanny.settings.PluginSettingsMemoize.get_telemetry_events")
@patch("octoprint_nanny.settings.PluginSettingsMemoize.event_in_tracked_telemetry")
async def test_mqtt_send_queue_bounding_box_predict(
    mock_event_in_tracked_telemetry, mock_get_telemetry_events, mocker
):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    mock_event_in_tracked_telemetry.return_value = False

    manager = WorkerManager(plugin)

    event = {"event_type": PluginEvents.BOUNDING_BOX_PREDICT_DONE, "event_data": {}}
    manager.mqtt_send_queue.put_nowait(event)

    mock_fn = mocker.patch.object(
        manager.mqtt_manager.publisher_worker,
        "_publish_bounding_box_telemetry",
        return_value=asyncio.Future(),
    )
    mock_fn.return_value.set_result("foo")

    await manager.mqtt_manager.publisher_worker._loop()

    mock_fn.assert_called_once_with(event)


@pytest.mark.asyncio
@patch("octoprint_nanny.settings.PluginSettingsMemoize.get_telemetry_events")
@patch("octoprint_nanny.settings.PluginSettingsMemoize.event_in_tracked_telemetry")
async def test_mqtt_receive_queue_valid_octoprint_event(
    mock_event_in_tracked_telemetry, mock_get_telemetry_events, mocker
):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mock_event_in_tracked_telemetry.return_value = True

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    manager = WorkerManager(plugin)

    mock_remote_control_snapshot = mocker.patch(
        "octoprint_nanny.workers.mqtt.MQTTSubscriberWorker._remote_control_snapshot",
        return_value=asyncio.Future(),
    )
    mock_remote_control_snapshot.return_value.set_result("foo")

    mock_rest_client = mocker.patch(
        "octoprint_nanny.settings.PluginSettingsMemoize.rest_client"
    )
    mock_rest_client.create_snapshot.return_value = asyncio.Future()
    mock_rest_client.create_snapshot.return_value.set_result("foo")
    mock_rest_client.update_remote_control_command.return_value = asyncio.Future()
    mock_rest_client.update_remote_control_command.return_value.set_result("foo")

    mock_mqtt_client = mocker.patch(
        "octoprint_nanny.settings.PluginSettingsMemoize.mqtt_client"
    )

    topic = "remote-control-topic"
    type(mock_mqtt_client).commands_topic = PropertyMock(return_value=topic)
    mocker.patch(
        "octoprint_nanny.settings.PluginSettingsMemoize.get_device_metadata",
        return_value={},
    )

    mock_start_monitoring = mocker.patch.object(manager.monitoring_manager, "start")

    manager = WorkerManager(plugin)
    manager.mqtt_manager.subscriber_worker.register_callbacks(
        {"octoprint_nanny_plugin_monitoring_start": mock_start_monitoring}
    )

    command = {
        "message": {
            "octoprint_event_type": "octoprint_nanny_plugin_monitoring_start",
            "command": "MonitoringStart",
            "remote_control_command_id": 1,
        },
        "topic": topic,
    }
    manager.mqtt_manager.mqtt_receive_queue.put_nowait(command)

    await manager.mqtt_manager.subscriber_worker._loop()

    mock_remote_control_snapshot.assert_called_once_with(
        command["message"]["remote_control_command_id"]
    )

    mock_rest_client.update_remote_control_command.assert_has_calls(
        [
            mocker.call(
                command["message"]["remote_control_command_id"],
                received=True,
                metadata={},
            ),
            mocker.call(
                command["message"]["remote_control_command_id"],
                success=True,
                metadata={},
            ),
        ]
    )
    mock_start_monitoring.assert_called_once_with(
        event=command["message"], event_type=command["message"]["octoprint_event_type"]
    )
