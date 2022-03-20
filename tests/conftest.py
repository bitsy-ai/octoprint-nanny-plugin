import pytest

from octoprint_nanny import __plugin_version__
import printnanny_api_client
from datetime import datetime


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
def metadata(octoprint_environment):
    return Metadata(
        user_id=1234,
        octoprint_device_id=1234,
        cloudiot_device_id=1234,
        client_version=printnanny_api_client.__version__,
        ts=datetime.now().timestamp(),
        octoprint_environment=octoprint_environment,
        octoprint_version="0.0.0",
        plugin_version=__plugin_version__,
    )


@pytest.fixture
def metadata_pb():
    return print_nanny_client.protobuf.monitoring_pb2.Metadata(
        user_id=1234,
        octoprint_device_id=1234,
        cloudiot_device_id=1234,
        ts=datetime.now().timestamp(),
    )


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark",
        action="store_true",
        dest="benchmark",
        default=False,
        help="enable benchmark tests",
    )


@pytest.fixture
def mock_plugin(mocker, plugin_settings):
    plugin = mocker.Mock()
    plugin.settings = plugin_settings
    return plugin


def pytest_collection_modifyitems(config, items):
    if config.getoption("--benchmark"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --benchmark option to run")
    for item in items:
        if "benchmark" in item.keywords:
            item.add_marker(skip_slow)
