from unittest.mock import patch, mock_open

from octoprint_nanny.utils import printnanny_os

MOCK_PRINTNANNY_OS_RELEASE = """ID=printnanny
ID_LIKE="BitsyLinux"
NAME="PrintNanny Linux"
VERSION="0.1.0 (Amber)"
VERSION_ID=0.1.0
PRETTY_NAME="PrintNanny Linux 0.1.0 (Amber)"
DISTRO_CODENAME="Amber"
"""

MOCK_OTHER_OS_RELEASE = """
PRETTY_NAME="Ubuntu 22.04 LTS"
TESTING="newfield"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=jammy
"""


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_PRINTNANNY_OS_RELEASE)
@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_config")
def test_known_etc_os_release(mock_printnanny_config, mock_file):
    result = printnanny_os.etc_os_release()
    assert result["ID"] == "printnanny"
    assert mock_file.called is True
    assert mock_printnanny_config.called is True


@patch("builtins.open", new_callable=mock_open, read_data="NONE=NONE")
@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_config")
def test_unknown_etc_os_release(mock_printnanny_config, mock_file):
    result = printnanny_os.etc_os_release()
    assert result["ID"] == "unknown"
    assert mock_file.called
    assert mock_printnanny_config.called is True


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_PRINTNANNY_OS_RELEASE)
@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_config")
def test_is_printnanny_os(mock_printnanny_config, mock_file):
    assert printnanny_os.is_printnanny_os() is True
    assert mock_file.called
    assert mock_printnanny_config.called is True


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_OTHER_OS_RELEASE)
@patch("octoprint_nanny.utils.printnanny_os.load_printnanny_config")
def test_is_printnanny_os(mock_printnanny_config, mock_file):
    assert printnanny_os.is_printnanny_os() is False
    assert mock_file.called
    assert mock_printnanny_config.called is True
