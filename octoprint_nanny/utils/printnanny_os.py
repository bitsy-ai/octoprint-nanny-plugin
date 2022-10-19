from os import environ
import concurrent.futures
from typing import Optional, Any, Dict, List, TypedDict
import logging
import json
import asyncio
import subprocess

import printnanny_api_client
from printnanny_api_client.models import Pi

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.utils")

PRINTNANNY_BIN = environ.get("PRINTNANNY_BIN", "/usr/bin/printnanny")
PRINTNANNY_DEBUG = environ.get("PRINTNANNY_DEBUG", False)
PRINTNANNY_DEBUG = PRINTNANNY_DEBUG in ["True", "true", "1", "yes"]

PRINTNANNY_PI: Optional[Pi] = None


class PrintNannyConfig(TypedDict):
    cmd: List[str]
    stdout: str
    stderr: str
    returncode: Optional[int]

    config: Optional[Dict[str, Any]]


def deserialize_pi(pi_dict) -> Pi:
    client = printnanny_api_client.api_client.ApiClient()
    return client._ApiClient__deserialize(pi_dict, Pi)  # type: ignore


def load_pi_model(pi_dict: Dict[str, Any]) -> Pi:
    result = deserialize_pi(pi_dict)

    global PRINTNANNY_PI
    PRINTNANNY_PI = result
    return PRINTNANNY_PI


def load_printnanny_config() -> PrintNannyConfig:
    cmd = [PRINTNANNY_BIN, "config", "show", "--format", "json"]
    returncode = None
    config = None

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
        logger.warning("%s is not installed", PRINTNANNY_BIN)
        return PrintNannyConfig(
            cmd=cmd,
            stdout="",
            stderr="",
            returncode=1,
            config=config,
        )
    try:
        # parse JSON
        config = json.loads(stdout)
        logger.debug("Parsed PrintNanny conf.d, loaded keys: %s", config.keys())

        # try setting global PRINTNANNY_PI var
        pi = config.get("cloud", {}).get("pi")
        if pi is not None:
            load_pi_model(pi)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode printnanny config: %", e)
    return PrintNannyConfig(
        cmd=cmd,
        stdout=stdout,
        stderr=stderr,
        config=config,
        returncode=returncode,
    )


def issue_txt() -> str:
    """
    Captured the contents of /etc/issue as plain text
    """
    try:
        result = open("/etc/issue", "r").read().strip()
    except Exception as e:
        logger.error("Failed to read /etc/issue %s", e)
        result = "Failed to read /etc/issue"
    return result


def etc_os_release() -> Dict[str, str]:
    """
    Captures the contents of /etc/os-release as a dictionary
    """
    config = load_printnanny_config()
    os_release_path = "/etc/os-release"
    if config["config"] is not None:
        os_release_path = (
            config["config"].get("paths", {}).get("os_release", os_release_path)
        )

    f = open(os_release_path, "r").read()
    result = dict(ID="unknown")
    try:
        lines = f.strip().split("\n")
        for line in lines:
            k, v = line.split("=")
            result[k] = v
    except Exception as e:
        logger.error("Error parsing contents of %s %s", os_release_path, e)
    return result


def is_printnanny_os() -> bool:
    osrelease = etc_os_release()
    return osrelease.get("ID") == "printnanny" or PRINTNANNY_DEBUG is True
