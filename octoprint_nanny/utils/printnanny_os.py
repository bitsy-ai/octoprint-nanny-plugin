import os
from typing import Optional, Any, Dict, List, TypedDict
import logging
import json
import subprocess

import printnanny_api_client
from printnanny_api_client.models import Pi

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.utils")

PRINTNANNY_BIN = os.environ.get("PRINTNANNY_BIN", "/usr/bin/printnanny")
PRINTNANNY_DEBUG = os.environ.get("PRINTNANNY_DEBUG", False)
PRINTNANNY_DEBUG = PRINTNANNY_DEBUG in ["True", "true", "1", "yes"]


PRINTNANNY_CLOUD_PI: Optional[Pi] = None
PRINTNANNY_CLOUD_NATS_CREDS: Optional[str] = None


class PrintNannyApiConfig(TypedDict):
    base_path: str
    bearer_access_token: Optional[str]


PRINTNANNY_CLOUD_API: Optional[PrintNannyApiConfig] = None


class PrintNannyConfig(TypedDict):
    cmd: List[str]
    stdout: str
    stderr: str
    returncode: Optional[int]

    config: Optional[Dict[str, Any]]


async def deserialize_pi(pi_dict) -> Pi:
    async with printnanny_api_client.api_client.ApiClient() as client:
        return client._ApiClient__deserialize(pi_dict, Pi)  # type: ignore


async def load_pi_model(pi_dict: Dict[str, Any]) -> Pi:
    result = await deserialize_pi(pi_dict)
    global PRINTNANNY_CLOUD_PI
    PRINTNANNY_CLOUD_PI = result
    return PRINTNANNY_CLOUD_PI


def load_api_config(api_config_dict: Dict[str, str]) -> PrintNannyApiConfig:
    global PRINTNANNY_CLOUD_API

    PRINTNANNY_CLOUD_API = PrintNannyApiConfig(
        base_path=api_config_dict.get("api_base_path", "https://printnanny.ai/"),
        bearer_access_token=api_config_dict.get("api_bearer_access_token"),
    )
    return PRINTNANNY_CLOUD_API


async def load_printnanny_cloud_data():
    cmd = [PRINTNANNY_BIN, "cloud", "show", "--format", "json"]
    # run /usr/bin/printnanny cloud show --format json
    try:
        p = subprocess.run(cmd, capture_output=True)
        stdout = p.stdout.decode("utf-8")
        stderr = p.stderr.decode("utf-8")
        if p.returncode != 0:
            logger.error(
                f"Failed to get printnanny settings cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
            )
            return

        cloud_data = json.loads(stdout)
        pi = cloud_data.get("pi")
        if pi is None:
            logger.error("Failed to parse pi from data=%s", cloud_data)
        # try setting global PRINTNANNY_CLOUD_PI var
        await load_pi_model(pi)
    except Exception as e:
        logger.error("Error running cmd %s %s", cmd, e)


def load_printnanny_settings() -> PrintNannyConfig:
    cmd = [PRINTNANNY_BIN, "settings", "show", "--format", "json"]
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
                f"Failed to get printnanny settings cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
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

        api_config = config.get("cloud")

        # try setting PRINTNANNY_CLOUD_API var
        if api_config is not None:
            load_api_config(api_config)

        nats_creds = config.get("paths", {}).get("state_dir")
        if nats_creds is not None:
            nats_creds = os.path.join(
                config.get("paths", {}).get("state_dir"),
                "creds/printnanny-cloud-nats.creds",
            )
            global PRINTNANNY_CLOUD_NATS_CREDS
            PRINTNANNY_CLOUD_NATS_CREDS = nats_creds

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
    config = load_printnanny_settings()
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
