import pytest
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
def mock_response():
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
def metadata():
    return Metadata(
        user_id=1234,
        octoprint_device_id=1234,
        cloudiot_device_id=1234,
        print_session=uuid.uuid4().hex,
        client_version=print_nanny_client.__version__,
        ts=datetime.now().timestamp(),
        environment={},
        octoprint_version=octoprint.util.version.get_octoprint_version_string(),
        plugin_version=__plugin_version__,
    )


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark",
        action="store_true",
        dest="benchmark",
        default=False,
        help="enable benchmark tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--benchmark"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --benchmark option to run")
    for item in items:
        if "benchmark" in item.keywords:
            item.add_marker(skip_slow)
