from unittest.mock import patch
from octoprint_nanny.utils.printnanny_os import (
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