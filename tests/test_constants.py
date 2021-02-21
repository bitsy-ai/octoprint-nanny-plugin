import pytest
from octoprint_nanny.constants import PluginEvents, RemoteCommands


def test_octoprint_event_member_in_plugin_events():

    event = "octoprint_nanny_device_register_start"
    assert PluginEvents.member(event) == PluginEvents.DEVICE_REGISTER_START


def test_unprefixed_event_to_octoprint_event():

    event = "device_register_start"
    expected = "octoprint_nanny_device_register_start"

    assert PluginEvents.to_octoprint_event(event) == expected


def test_octoprint_event_to_octoprint_event():

    event = "octoprint_nanny_device_register_start"
    expected = "octoprint_nanny_device_register_start"

    assert PluginEvents.to_octoprint_event(event) == expected


def test_unprefixed_event_from_octoprint_event():

    expected = "device_register_start"
    event = "octoprint_nanny_device_register_start"

    assert PluginEvents.from_octoprint_event(event) == expected


def test_unprefixed_event_from_unprefixed_event():
    """
    it should have no negative side-effects if a non-octoprint prefixed event is passed
    """

    expected = "device_register_start"
    event = "device_register_start"

    assert PluginEvents.from_octoprint_event(event) == expected
