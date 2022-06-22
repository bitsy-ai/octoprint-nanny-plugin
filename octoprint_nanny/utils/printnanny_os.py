from os import environ
from typing import Optional, Any, Dict, List, TypedDict
import logging
import json
import subprocess

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.utils")

PRINTNANNY_BIN = environ.get("PRINTNANNY_BIN", "/usr/bin/printnanny")


class PrintNannyConfig(TypedDict):
    cmd: List[str]
    stdout: str
    stderr: str
    returncode: Optional[int]

    config: Dict[str, Any]


def load_printnanny_config() -> PrintNannyConfig:
    cmd = [PRINTNANNY_BIN, "config", "show", "-F", "json"]
    returncode = None
    config: Dict[str, Any] = dict()

    # run /usr/bin/printnanny config show -F json
    try:
        p = subprocess.run(cmd, capture_output=True)
        stdout = p.stdout.decode("utf-8")
        stderr = p.stderr.decode("utf-8")
        returncode = p.returncode
        if p.returncode != 0:
            logger.error(
                f"Failed to get printnanny config cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
            )
            return PrintNannyConfig(
                cmd=cmd,
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                config=config,
            )
    # FileNotFoundError thrown when PRINTNANNY_BIN is not found
    except FileNotFoundError as e:
        logger.error(e)
        stdout = ""
        stderr = str(e)

    # parse JSON
    try:
        config = json.loads(stdout)
        logger.debug("Parsed PrintNanny conf.d, loaded keys: %s", config.keys())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode printnanny config: %", e)
    return PrintNannyConfig(
        cmd=cmd,
        stdout=stdout,
        stderr=stderr,
        config=config,
        returncode=returncode,
    )


def janus_edge_hostname() -> str:
    return environ.get("JANUS_EDGE_HOSTNAME", "localhost")


def janus_edge_api_token() -> str:
    return environ.get("JANUS_EDGE_API_TOKEN", "janustoken")


def issue_txt() -> str:
    """
    Captured the contents of /boot/issue.txt as plain text
    """
    try:
        result = open("/boot/issue.txt", "r").read().strip()
    except Exception as e:
        logger.error("Failed to read /boot/issue.txt %s", e)
        result = "Failed to read /boot/issue.txt"
    return result


def etc_os_release() -> Dict[str, str]:
    """
    Captures the contents of /etc/os-release as a dictionary
    """
    config = load_printnanny_config()
    os_release = config["config"].get("paths", {}).get("os_release", "/etc/os-release")
    f = open(os_release, "r").read()
    result = dict(ID="unknown")
    try:
        lines = f.strip().split("\n")
        for line in lines:
            k, v = line.split("=")
            result[k] = v
    except Exception as e:
        logger.error("Error parsing contents of %s %s", os_release, e)
    return result


def is_printnanny_os() -> bool:
    osrelease = etc_os_release()
    return osrelease.get("ID") == "printnanny"
