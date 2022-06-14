from unittest.mock import patch, mock_open
from octoprint_nanny.utils.printnanny_os import (
    etc_os_release,
    printnanny_config,
)


@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_config_error(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 1
    mock_subprocess.run.return_value = output
    ret = printnanny_config()
    assert ret is None


@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_config_error(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 0
    output.stdout = b'{ "test": "test"}'
    mock_subprocess.run.return_value = output
    ret = printnanny_config()
    assert ret == dict(test="test")


MOCK_OS_RELEASE = """ID=printnanny
ID_LIKE="BitsyLinux"
NAME="PrintNanny Linux"
VERSION="0.1.0 (Amber)"
VERSION_ID=0.1.0
PRETTY_NAME="PrintNanny Linux 0.1.0 (Amber)"
DISTRO_CODENAME="Amber"
"""


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_OS_RELEASE)
def test_known_etc_os_release(mock_file, mocker):
    result = etc_os_release()
    assert result["ID"] == "printnanny"


@patch("builtins.open", new_callable=mock_open, read_data="NONE=NONE")
def test_unknown_etc_os_release(mock_file, mocker):
    result = etc_os_release()
    assert result["ID"] == "unknown"
