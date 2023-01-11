import os
import logging

logger = logging.getLogger(__name__)

MAX_BACKOFF_TIME = int(os.environ.get("OCTOPRINT_NANNY_MAX_BACKOFF_TIME", 120))

logger.info(f"OCTOPRINT_NANNY_MAX_BACKOFF_TIME={MAX_BACKOFF_TIME}")
