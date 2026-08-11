"""
HHMS Logging Configuration
==========================

Centralized logging configuration for HHMS.

Features
--------
- Console logging
- Rotating file logging
- Automatic log directory creation
- Configurable log level
- Duplicate handler prevention

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config.settings import get_settings


def configure_logging() -> logging.Logger:
    """
    Configure and return the application logger.

    This function is idempotent. Calling it multiple times will
    not create duplicate handlers.

    Returns
    -------
    logging.Logger
        Configured HHMS application logger.
    """

    settings = get_settings()

    logger = logging.getLogger(settings.APP_SHORT_NAME)

    if logger.handlers:
        return logger

    log_level = getattr(
        logging,
        settings.LOG_LEVEL.upper(),
        logging.INFO,
    )

    logger.setLevel(log_level)
    logger.propagate = False

    log_directory = settings.log_path.parent
    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = settings.log_path

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(module)s | "
            "%(funcName)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger