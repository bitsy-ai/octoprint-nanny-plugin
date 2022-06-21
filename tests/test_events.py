from octoprint_nanny.utils.printnanny_os import PrintNannyConfig
import pytest
from unittest.mock import patch
from octoprint_nanny.events import should_publish_event, try_handle_event


@patch("octoprint_nanny.events.try_publish_cmd")
def test_handle_untracked_event(mock_try_publish_cmd):
    try_handle_event(
        "someuntrackedevent",
        dict(),
    )
    assert mock_try_publish_cmd.called is False


@patch("octoprint_nanny.events.load_printnanny_config")
@patch("octoprint_nanny.events.try_publish_cmd")
def test_handle_events_enabled_true(mock_try_publish_cmd, mock_printnanny_config):
    mock_printnanny_config.return_value = PrintNannyConfig(
        cmd=["mock", "cmd"],
        stdout="",
        stderr="",
        returncode=0,
        config={
            "device": {"id": 1},
            "paths": {"events_socket": "test.sock"},
            "octoprint": {"server": {"id": 1}},
        },
    )
    try_handle_event(
        "Startup",
        dict(),
    )
    assert mock_try_publish_cmd.called is True


@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_config")
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
