import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from octoprint_nanny.nats import NatsWorker, try_publish_nats
from octoprint_nanny.events import (
    octoprint_event_to_nats_subject,
)


@patch("nats.connect")
def test_handle_untracked_event(mock_nats):
    worker = NatsWorker()
    worker.handle_event("someuntrackedevent", dict())
    worker._queue = MagicMock()
    assert worker._queue.put_nowait.called is False


@patch("nats.connect")
def test_handle_tracked_event(mock_nats):
    worker = NatsWorker()
    worker._queue = MagicMock()
    worker.handle_event("Startup", dict())
    assert worker._queue.put_nowait.called is True


def test_handle_untracked_subject():
    subject = octoprint_event_to_nats_subject("foo")
    assert subject is None


def test_handle_tracked_subject():
    subject = octoprint_event_to_nats_subject("Startup")
    assert subject == "octoprint.event.server.startup"


@pytest.mark.asyncio
async def test_handle_tracked_event_publish():
    mock_nc = AsyncMock()
    event = "Startup"
    payload = dict()
    result = await try_publish_nats(mock_nc, event, payload)
    assert result is True
    assert mock_nc.publish.called is True
