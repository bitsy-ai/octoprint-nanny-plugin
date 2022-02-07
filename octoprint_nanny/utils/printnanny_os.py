from typing import Optional, Any, Dict
import logging
import json
import subprocess
import socket

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.utils")

def printnanny_cli_version() -> Optional[str]:
    cmd = ["printnanny", "--version"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode('utf-8')
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0:
        logger.warning(f"Failed to get printnanny_cli_version cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}")
        return None
    logger.info(f"Found printnanny_cli_version={stdout}")
    return stdout

def printnanny_image_version() -> Optional[str]:
    cmd = ["cat", "/boot/image_version.txt"]
    p = subprocess.run(cmd, capture_output=True)
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode('utf-8')
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0:
        logger.warning(f"Failed to get printnanny_image_version cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}")
        return None
    logger.info(f"Found printnanny_image_version={stdout}")
    return stdout

def printnanny_config() -> Optional[Dict[str, Any]]:
    hostname = socket.gethostname()
    cmd = ["printnanny", "config", "get"]
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        logger.error(e)
        return None
    stdout = p.stdout.decode('utf-8')
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0:
        logger.warning(f"Failed to get printnanny config cmd={cmd} returncode={p.returncode} stdout={stdout} stderr={stderr}")
        return None
    try:
        config = json.loads(stdout)
        logger.info(f"Read printnanny config: {config}")
        return config
    except json.JSONDecodeError as e:
        logger.error(e)
        logger.error(f"Failed to decode printnanny config: {stdout}")
        return None

def printnanny_dash_url() -> Optional[str]:
    config = printnanny_config()
    hostname = socket.gethostname()
    if config is None:
        logger.warning("Failed to read printnanny config, using defaults for printnanny_dash_url")
        base_path = "/"
    else:
        base_path = config.get("dash", {}).get("base_path", "/")
    return f"//{hostname}{base_path}login"