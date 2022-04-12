import pytest
import os
from octoprint_nanny import __plugin_version__
from octoprint.plugin import plugin_manager as plugin_manager_factory
from octoprint.plugin.core import PluginManager
from datetime import datetime

from octoprint_nanny.plugins import OctoPrintNannyPlugin


class MockResponse(object):
    headers = {"content-type": "image/jpeg"}

    async def read(self):
        with open("octoprint_nanny/data/images/0.pre.jpg", "rb") as f:
            return f.read()


@pytest.fixture
def current_temperatures():
    # TODO get payload structure https://docs.octoprint.org/en/master/modules/printer.html#octoprint.printer.PrinterInterface.get_current_temperatures
    return dict()


@pytest.fixture
def current_printer_state():
    return {
        "state": {
            "text": "Offline",
            "flags": {
                "operational": False,
                "printing": False,
                "cancelling": False,
                "pausing": False,
                "resuming": False,
                "finishing": False,
                "closedOrError": True,
                "error": False,
                "paused": False,
                "ready": False,
                "sdReady": False,
            },
            "error": "",
        },
        "job": {
            "file": {
                "name": None,
                "path": None,
                "size": None,
                "origin": None,
                "date": None,
            },
            "estimatedPrintTime": None,
            "lastPrintTime": None,
            "filament": {"length": None, "volume": None},
            "user": None,
        },
        "currentZ": None,
        "progress": {
            "completion": None,
            "filepos": None,
            "printTime": None,
            "printTimeLeft": None,
            "printTimeOrigin": None,
        },
        "offsets": {},
        "resends": {"count": 0, "ratio": 0},
    }


@pytest.fixture
def EVENT_PLUGIN_OCTOPRINT_NANNY_MONITORING_FRAME_BYTES():
    with open("octoprint_nanny/data/images/0.pre.jpg", "rb") as f:
        image = f.read()
    return dict(
        event_type="plugin_octoprint_nanny_monitoring_frame_bytes",
        event_data=dict(image=image, ts=datetime.now().timestamp()),
    )


@pytest.fixture
def octoprint_environment():
    return {
        "os": {"id": "linux", "platform": "linux", "bits": 32},
        "python": {
            "version": "3.7.3",
            "pip": "21.1.2",
            "virtualenv": "/home/pi/oprint",
        },
        "hardware": {"cores": 4, "freq": 1500.0, "ram": 3959304192},
        "plugins": {
            "pi_support": {
                "model": "Raspberry Pi 4 Model B Rev 1.1",
                "throttle_state": "0x0",
                "octopi_version": "0.18.0",
            }
        },
    }


@pytest.fixture
def plugin_manager() -> PluginManager:
    plugin_folders = [os.getcwd()]
    m = plugin_manager_factory(init=True, plugin_folders=plugin_folders)
    # m.reload_plugins(startup=True)
    return m


@pytest.fixture
def plugin(plugin_manager) -> OctoPrintNannyPlugin:
    return plugin_manager.plugins.get("octoprint_nanny").implementation
