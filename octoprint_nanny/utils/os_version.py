from typing import Optional
import logging
import subprocess

logger = logging.getLogger(__name__)

def printnanny_cli_version() -> Optional[str]:
    cmd = ["printnanny", "--version"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        logger.warning(f"Failed to get printnanny_cli_version cmd={f} returncode={returncode} stdout={p.stdout} stderr={p.stderr}")
        return
    logger.info(f"Found printnanny_cli_version={p.stdout}")
    return p.stdout

def printnanny_image_version() -> Optional[str]:
    cmd = ["cat", "/boot/image_version.txt"]
    if p.returncode != 0:
        logger.warning(f"Failed to get printnanny_image_version cmd={f} returncode={returncode} stdout={p.stdout} stderr={p.stderr}")
        return
    logger.info(f"Found printnanny_image_version={p.stdout}")
    return p.stdout

def printnanny_login_url() -> str:
    pass