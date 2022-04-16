import pytest
from unittest.mock import patch, MagicMock
from octoprint_nanny.events import try_handle_event
from octoprint_nanny.exceptions import SetupIncompleteError


@patch("octoprint_nanny.events.try_write_socket")
def test_handle_untracked_event(mock_try_write_socket):
    try_handle_event(
        "someuntrackedevent",
        dict(),
        dict(
            octoprint_install=dict(id=1), device=dict(id=1), events_socket="test.sock"
        ),
        events_enabled=True,
    )
    assert not mock_try_write_socket.called


@patch("octoprint_nanny.events.try_write_socket")
def test_handle_events_enabled_true(mock_try_write_socket):
    try_handle_event(
        "Startup",
        dict(),
        dict(
            octoprint_install=dict(id=1), device=dict(id=1), events_socket="test.sock"
        ),
        events_enabled=True,
    )
    assert mock_try_write_socket.called


@patch("octoprint_nanny.events.try_write_socket")
def test_handle_setup_incomplete(mock_try_write_socket):
    with pytest.raises(SetupIncompleteError):
        try_handle_event("Startup", dict(), dict(), events_enabled=True)
    assert not mock_try_write_socket.called
