import logging
from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
from multiprocessing_logging import install_mp_handler


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
    install_mp_handler()
    logger.info("Installed multiprocessing_logging.install_mp_handler")
