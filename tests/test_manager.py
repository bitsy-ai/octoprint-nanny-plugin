import asyncio
import pytest

from unittest.mock import PropertyMock

import octoprint_nanny.plugins  # import DEFAULT_SETTINGS, OctoPrintNannyPlugin
from octoprint_nanny.manager import WorkerManager
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint.events import Events
from octoprint_nanny.predictor import (
    BOUNDING_BOX_PREDICT_EVENT,
    ANNOTATED_IMAGE_EVENT,
)


def get_default_setting(key):
    return octoprint_nanny.plugins.DEFAULT_SETTINGS[key]


def test_default_settings_client_states(mocker):
    """
    By default, accessing WorkerManger.rest_client and WorkerManger.mqtt_client should raise PluginSettingsRequired
    """
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting
    manager = WorkerManager(plugin)

    assert manager.plugin_settings.auth_token is None
    assert manager.plugin_settings.device_id is None

    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin_settings.mqtt_client)
    with pytest.raises(PluginSettingsRequired):
        dir(manager.plugin_settings.rest_client)


@pytest.mark.asyncio
async def test_mqtt_send_queue_valid_octoprint_event(mocker):
    plugin = mocker.Mock()
    plugin.get_setting = get_default_setting

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.test_mqtt_settings")

    mocker.patch("octoprint_nanny.settings.PluginSettingsMemoize.telemetry_events")
    mocker.patch(
        "octoprint_nanny.settings.PluginSettingsMemoize.event_in_tracked_telemetry",
        return_value=True,
    )
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


# @pytest.mark.asyncio
# async def test_telemetry_queue_send_loop_bounding_box_predict(mocker):
#     plugin = octoprint_nanny.plugins.OctoPrintNannyPlugin()
#     plugin.get_setting = get_default_setting

#     mocker.patch.object(WorkerManager, "test_mqtt_settings")

#     mocker.patch.object(WorkerManager, "telemetry_events")
#     mocker.patch.object(WorkerManager, "event_in_tracked_telemetry", return_value=True)

#     manager = WorkerManager(plugin)

#     event = {"event_type": BOUNDING_BOX_PREDICT_EVENT, "event_data": {}}
#     manager.telemetry_queue.put_nowait(event)

#     mock_fn = mocker.patch.object(
#         manager, "_publish_bounding_box_telemetry", return_value=asyncio.Future()
#     )
#     mock_fn.return_value.set_result("foo")

#     await manager._telemetry_queue_send_loop()

#     mock_fn.assert_called_once_with(event)


# @pytest.mark.asyncio
# async def test_remote_control_receive_loop_valid_octoprint_event(mocker):
#     plugin = octoprint_nanny.plugins.OctoPrintNannyPlugin()
#     plugin.get_setting = get_default_setting

#     mocker.patch.object(WorkerManager, "test_mqtt_settings")

#     mock_remote_control_snapshot = mocker.patch.object(
#         WorkerManager, "_remote_control_snapshot", return_value=asyncio.Future()
#     )
#     mock_remote_control_snapshot.return_value.set_result("foo")

#     mock_rest_client = mocker.patch.object(WorkerManager, "rest_client")
#     mock_rest_client.update_remote_control_command.return_value = asyncio.Future()
#     mock_rest_client.update_remote_control_command.return_value.set_result("foo")

#     mock_mqtt_client = mocker.patch.object(WorkerManager, "mqtt_client")

#     topic = "remote-control-topic"
#     type(mock_mqtt_client).remote_control_command_topic = PropertyMock(
#         return_value=topic
#     )

#     mocker.patch.object(WorkerManager, "get_device_metadata", return_value={})

#     mock_start_monitoring = mocker.patch.object(WorkerManager, "start_monitoring")

#     manager = WorkerManager(plugin)
#     manager._remote_control_event_handlers = {
#         "octoprint_nanny_plugin_monitoring_start": manager.start_monitoring
#     }

#     command = {
#         "message": {
#             "octoprint_event_type": "octoprint_nanny_plugin_monitoring_start",
#             "command": "MonitoringStart",
#             "remote_control_command_id": 1,
#         },
#         "topic": topic,
#     }
#     manager.remote_control_queue.put_nowait(command)

#     await manager._remote_control_receive_loop()

#     mock_remote_control_snapshot.assert_called_once_with(
#         command["message"]["remote_control_command_id"]
#     )

#     mock_rest_client.update_remote_control_command.assert_has_calls(
#         [
#             mocker.call(
#                 command["message"]["remote_control_command_id"],
#                 received=True,
#                 metadata={},
#             ),
#             mocker.call(
#                 command["message"]["remote_control_command_id"],
#                 success=True,
#                 metadata={},
#             ),
#         ]
#     )
#     mock_start_monitoring.assert_called_once_with(
#         event=command["message"], event_type=command["message"]["octoprint_event_type"]
#     )
