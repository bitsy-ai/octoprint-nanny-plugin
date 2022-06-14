from os import environ
from typing import Optional, Any, Dict
import logging
import json
import subprocess
import socket

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.utils")

PRINTNANNY_BIN = environ.get("PRINTNANNY_BIN", "/usr/bin/printnanny")
PRINTNANNY_PROFILE = environ.get("PRINTNANNY_PROFILE", "default")


def printnanny_user() -> Optional[Dict[Any, Any]]:
    cmd = [PRINTNANNY_BIN, "config", "get", "user", "-F", "json"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.warning(
            f"Failed to get printnanny user cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None
    logger.info(f"Logged in as printnanny user={stdout}")
    try:
        user = json.loads(stdout)
        return user
    except json.JSONDecodeError as e:
        logger.error(e)
        logger.error(f"Failed to decode printnanny config: {stdout}")
        return None


def printnanny_device() -> Optional[Dict[Any, Any]]:
    cmd = [PRINTNANNY_BIN, "config", "get", "device", "-F", "json"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.warning(
            f"Failed to get printnanny device cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None
    logger.info(f"Authenticated with device={stdout}")
    try:
        user = json.loads(stdout)
        return user
    except json.JSONDecodeError as e:
        logger.error(e)
        logger.error(f"Failed to decode printnanny device={stdout}")
        return None


def printnanny_config() -> Optional[Dict[str, Any]]:
    cmd = [PRINTNANNY_BIN, "config", "show", "-F", "json"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.warning(
            f"Failed to get printnanny config cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None
    try:
        config = json.loads(stdout)
        logger.info(f"Read printnanny config: {config}")
        return config
    except json.JSONDecodeError as e:
        logger.error(e)
        logger.error(f"Failed to decode printnanny config: {stdout}")
        return None


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
    f = open("/etc/os-release", "r").read()
    result = dict(ID="unknown")
    try:
        lines = f.strip().split("\n")
        for line in lines:
            k, v = line.split("=")
            result[k] = v
    except Exception as e:
        logger.error("Error parsing contents of /etc/os-release %s", e)
    return result
