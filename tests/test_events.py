import json
import pytest
from unittest.mock import patch, MagicMock
from printnanny_api_client.models import Pi

from octoprint_nanny.utils.printnanny_os import PrintNannyConfig
from octoprint_nanny.events import should_publish_event, try_handle_event
from octoprint_nanny.utils import printnanny_os


@patch("octoprint_nanny.events.try_publish_nats")
async def test_handle_untracked_event(mock_try_publish_nats):
    await try_handle_event("someuntrackedevent", dict(), MagicMock())
    assert mock_try_publish_nats.called is False


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
        "base_path": "/home/printnanny/.octoprint",
        "venv_path": "/home/printnanny/.octoprint/venv",
        "pip_path": "/home/printnanny/.octoprint/venv/pip",
        "python_path": "/home/printnanny/.octoprint/venv/python"
    },
    "urls": {
        "swupdate": "http://printnanny.local/update/",
        "octoprint": "http://printnanny.local/octoprint/",
        "syncthing": "http://printnanny.local/synchting/",
        "mission_control":  "http://printnanny.local/"
    },
    "mdns_urls": {
        "swupdate": "http://printnanny.local/update/",
        "octoprint": "http://printnanny.local/octoprint/",
        "syncthing": "http://printnanny.local/synchting/",
        "mission_control":  "http://printnanny.local/"
    },
    "shortname_urls": {
        "swupdate": "http://printnanny/update/",
        "octoprint": "http://printnanny/octoprint/",
        "syncthing": "http://printnanny/synchting/",
        "mission_control":  "http://printnanny/"
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


@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_settings")
@patch("octoprint_nanny.events.try_publish_nats")
async def test_handle_events_enabled_true(
    mock_try_publish_nats, mock_printnanny_config
):
    MOCK_PI = await printnanny_os.load_pi_model(json.loads(MOCK_PI_JSON))

    printnanny_os.PRINTNANNY_CLOUD_PI = MOCK_PI
    await try_handle_event("Startup", dict(), MagicMock())
    assert mock_try_publish_nats.called is True


@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_settings")
def test_should_publish_print_progress(mock_printnanny_config):
    mock_printnanny_config.return_value = PrintNannyConfig(
        cmd=["mock", "cmd"],
        stdout="",
        stderr="",
        returncode=0,
        config={
            "alert_settings": {
                "print_progress_percent": 25,
            },
            "octoprint": {"server": {"id": 1}},
        },
    )
    event = "PrintProgress"
    payload = dict(
        progress=25, path="path/to/fake/print", storage="mock_filename.gcode"
    )

    result = should_publish_event(event, payload)

    assert result is True
