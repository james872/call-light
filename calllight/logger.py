"""
Logging configuration.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .constants import LOG_DIRECTORY, LOG_NAME


def configure_logger(debug: bool = False) -> logging.Logger:
    """
    Configure the application logger.

    Parameters
    ----------
    debug
        Enable DEBUG logging.

    Returns
    -------
    logging.Logger
    """

    logger = logging.getLogger(LOG_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    #
    # Console output
    #

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger.addHandler(console)

    #
    # Log file
    #

    try:

        LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

        logfile = RotatingFileHandler(
            LOG_DIRECTORY / "call-light.log",
            maxBytes=1_000_000,
            backupCount=5,
        )

        logfile.setFormatter(formatter)

        logger.addHandler(logfile)

    except PermissionError:

        logger.warning(
            "Unable to create log directory %s. "
            "File logging disabled.",
            LOG_DIRECTORY,
        )

    return logger
