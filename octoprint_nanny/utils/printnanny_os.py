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


def printnanny_version() -> Optional[Dict[str, str]]:
    cmd = [PRINTNANNY_BIN, "version"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    if p.returncode != 0:
        logger.warning(
            f"Failed to get printnanny_version cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}"
        )
        return None
    logger.info(f"Running printnanny_version={stdout}")
    try:
        version = json.loads(stdout)
        return version
    except json.JSONDecodeError as e:
        logger.error(e)
        logger.error(f"Failed to decode printnanny config: {stdout}")
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
