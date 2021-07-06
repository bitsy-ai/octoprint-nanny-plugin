import pytest
from asynctest import patch, CoroutineMock, MagicMock
from octoprint_nanny.types import MonitoringModes
from octoprint_nanny.workers.monitoring import (
    MonitoringWorker,
    MonitoringManager,
    MonitoringModes,
)

import print_nanny_client

@pytest.mark.asyncio
@patch("octoprint_nanny.workers.monitoring.Events")
@patch("octoprint_nanny.workers.monitoring.MonitoringWorker.load_url_buffer")
@patch("octoprint_nanny.workers.monitoring.datetime")
async def test_monitoring_worker_loop(
   mock_events_enum, mock_load_url_buffer, mock_datetime,  mock_plugin, mocker
):

    plugin = mocker.Mock()
    mock_load_url_buffer.return_value = b''

    mock_queue = mocker.Mock()
    plugin.settings.snapshot_url = "http://localhost:8080"
    plugin.settings.calibration = None


    monitoring_worker = MonitoringWorker(mock_queue, mock_plugin)
    mock_datetime.now.timestamp.return_value = 1234 

    await monitoring_worker._loop()
    
    assert mock_load_url_buffer.called_once
    assert mock_queue.called_with(dict(
        event_type=mock_events_enum.PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES,
        event_data=dict(ts=1234, image_bytes=b'')
    ))