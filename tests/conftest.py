import pytest

from print_nanny_client.protobuf.common_pb2 import PrintSession
from octoprint_nanny.types import Metadata
from octoprint_nanny.workers.monitoring import MonitoringWorker
from octoprint_nanny import __plugin_version__
import uuid
import print_nanny_client
from datetime import datetime
import octoprint


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
        event_type="plugin_octoprint_nanny_monitoring_frame_b64",
        event_data=dict(image=image),
    )


@pytest.fixture
def mock_image():
    return MockResponse()


@pytest.fixture
def calibration():
    return MonitoringWorker.calc_calibration(
        0.2,
        0.2,
        0.8,
        0.8,
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
        client_version=print_nanny_client.__version__,
        ts=datetime.now().timestamp(),
        octoprint_environment=octoprint_environment,
        octoprint_version="0.0.0",
        plugin_version=__plugin_version__,
    )


@pytest.fixture
def metadata_pb():
    pb = print_nanny_client.protobuf.monitoring_pb2.Metadata()
    pb.user_id = 1234
    pb.octoprint_device_id = 1234
    pb.cloudiot_device_id = 1234
    pb.ts = datetime.now().timestamp()
    return pb


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark",
        action="store_true",
        dest="benchmark",
        default=False,
        help="enable benchmark tests",
    )


@pytest.fixture
def plugin_settings(
    mocker, metadata, metadata_pb, current_printer_state, current_temperatures
):
    plugin_settings = mocker.Mock()
    plugin_settings.metadata = metadata

    pb = PrintSession()
    pb.id = 1
    pb.session = uuid.uuid4().hex
    pb.created_ts = datetime.now().timestamp()
    pb.datesegment = "2021/01/01"
    plugin_settings.print_session_pb = pb

    plugin_settings.metadata_pb = metadata_pb
    plugin_settings.current_printer_state = current_printer_state
    plugin_settings.plugin_version = __plugin_version__
    plugin_settings.current_temperatures = current_temperatures

    return plugin_settings


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
