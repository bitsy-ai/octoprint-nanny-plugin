import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from octoprint_nanny.events import octoprint_event_to_nats_subject, try_publish_nats
from octoprint_nanny.utils import printnanny_os
import socket

MOCK_PI_JSON = """{
    "id": 2,
    "last_boot": null,
    "settings": {
        "id": 2,
        "updated_dt": "2022-08-10T15:42:13.176362Z",
        "cloud_video_enabled": true,
        "telemetry_enabled": false,
        "pi": 2
    },
    "cloudiot_device": null,
    "user": {
        "email": "leigh@print-nanny.com",
        "id": 1,
        "first_name": null,
        "last_name": null,
        "is_beta_tester": true,
        "member_badges": []
    },
    "system_info": null,
    "public_key": null,
    "octoprint_server": {
        "id": 2,
        "settings": null,
        "octoprint_version": "",
        "pip_version": "",
        "python_version": "",
        "printnanny_plugin_version": "",
        "created_dt": "2022-08-10T15:42:13.190818Z",
        "updated_dt": "2022-08-10T15:42:13.190834Z",
        "user": 1,
        "pi": 2,
        "base_url": "/octoprint/",
        "base_path": "/home/printnanny/.octoprint",
        "venv_path": "/home/printnanny/.octoprint/venv",
        "pip_path": "/home/printnanny/.octoprint/venv/pip",
        "python_path": "/home/printnanny/.octoprint/venv/python"
    },
    "urls": {
        "swupdate": "http://printnanny.local/update/",
        "octoprint": "http://printnanny.local/octoprint/",
        "syncthing": "http://printnanny.local/synchting/",
        "mission_control":  "http://printnanny.local/",
        "moonraker_api": "http://printnanny.local/moonraker/"
    },
    "mdns_urls": {
        "swupdate": "http://printnanny.local/update/",
        "octoprint": "http://printnanny.local/octoprint/",
        "syncthing": "http://printnanny.local/synchting/",
        "mission_control":  "http://printnanny.local/",
        "moonraker_api": "http://printnanny.local/moonraker/"
    },
    "shortname_urls": {
        "swupdate": "http://printnanny/update/",
        "octoprint": "http://printnanny/octoprint/",
        "syncthing": "http://printnanny/synchting/",
        "mission_control":  "http://printnanny/",
        "moonraker_api": "http://printnanny/moonraker"
    },
    "sbc": "rpi_4",
    "edition": "octoprint_lite",
    "created_dt": "2022-08-10T15:42:12.088147Z",
    "hostname": "aurora",
    "fqdn": "printnanny.local",
    "favorite": false,
    "setup_finished": false
}
"""

MOCK_STATE_DATA = {
    "state": {
        "text": "Starting",
        "flags": {
            "operational": True,
            "printing": True,
            "cancelling": False,
            "pausing": False,
            "resuming": False,
            "finishing": False,
            "closedOrError": False,
            "error": False,
            "paused": False,
            "ready": False,
            "sdReady": True,
        },
        "error": "",
    },
    "job": {
        "file": {
            "name": "nany 1 v5_0.05mm_PLA_MINI_31s.gcode",
            "path": "nany 1 v5_0.05mm_PLA_MINI_31s.gcode",
            "display": "nany 1 v5_0.05mm_PLA_MINI_31s.gcode",
            "origin": "local",
            "size": 37332,
            "date": 1679069626,
        },
        "estimatedPrintTime": 30.729910721688928,
        "averagePrintTime": 25.556955865001637,
        "lastPrintTime": 26.595943458000022,
        "filament": {
            "tool0": {"length": 22.67491999999998, "volume": 0.05453957410225115}
        },
        "user": "admin",
    },
    "currentZ": None,
    "progress": {
        "completion": 0.0,
        "filepos": 0,
        "printTime": 0,
        "printTimeLeft": None,
        "printTimeLeftOrigin": None,
    },
    "offsets": {},
    "resends": {"count": 0, "transmitted": 9, "ratio": 0},
}


@pytest.mark.asyncio
@patch("nats.connect")
async def test_handle_untracked_event(mock_nats):
    result = await try_publish_nats("someuntrackedevent", dict())
    assert result is False
    assert mock_nats.connect.called is False


@pytest.mark.asyncio
@patch("nats.connect")
async def test_handle_tracked_event(mock_nats):

    MOCK_PI = await printnanny_os.load_pi_model(json.loads(MOCK_PI_JSON))
    printnanny_os.PRINTNANNY_CLOUD_PI = MOCK_PI
    result = await try_publish_nats("Startup", dict())

    assert result is True
    assert mock_nats.called is True
    assert mock_nats.return_value.publish.called is True
    call_args = mock_nats.return_value.publish.call_args[0]
    hostname = socket.gethostname()
    assert call_args[0] == f"pi.{hostname}.octoprint.event.server.startup"
    assert call_args[1] == b'{"status": "Startup"}'
