from unittest.mock import patch
from octoprint_nanny.utils.printnanny_os import (
    printnanny_config,
    printnanny_image_version,
    printnanny_cli_version
)

@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_cli_returns_error(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 1
    mock_subprocess.run.return_value = output
    ret = printnanny_cli_version()
    assert ret is None

@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_cli_returns_version(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 0
    output.stdout = b"0.0.0"
    mock_subprocess.run.return_value = output
    ret = printnanny_cli_version()
    assert ret == "0.0.0"

@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_image_version_error(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 1
    mock_subprocess.run.return_value = output
    ret = printnanny_image_version()
    assert ret is None

@patch("octoprint_nanny.utils.printnanny_os.subprocess")
def test_printnanny_image_version(mock_subprocess, mocker):
    output = mocker.Mock()
    output.returncode = 0
    output.stdout = b"test"
    mock_subprocess.run.return_value = output
    ret = printnanny_image_version()
    assert ret == "test"

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