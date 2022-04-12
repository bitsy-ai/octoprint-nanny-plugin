import pytest
from unittest.mock import patch, MagicMock
from octoprint_nanny.events import try_handle_event
from octoprint_nanny.exceptions import SetupIncompleteError


@patch("octoprint_nanny.events.try_publish_event")
def test_handle_events_enabled_true(mock_try_publish_event):
    try_handle_event("test", dict(), socket="test.sock", events_enabled=True)
    assert mock_try_publish_event.called


@patch("octoprint_nanny.events.try_publish_event")
def test_handle_setup_incomplete(mock_try_publish_event):
    with pytest.raises(SetupIncompleteError):
        try_handle_event("test", dict(), socket=None, events_enabled=True)
    assert not mock_try_publish_event.called
