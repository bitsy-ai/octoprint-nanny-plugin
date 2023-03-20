import logging
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler


def configure_logger(logger, logfile_path):

    file_logging_handler = CleaningTimedRotatingFileHandler(
        logfile_path,
        when="D",
        backupCount=7,
    )
    file_logging_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(module)s - %(thread)d - %(levelname)s - %(message)s"
        )
    )
    file_logging_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_logging_handler)

    logger.info(f"Logger file handler added {file_logging_handler}")
