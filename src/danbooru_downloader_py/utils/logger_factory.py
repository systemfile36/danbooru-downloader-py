# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py

from __future__ import annotations

import datetime
import logging
import sys
from pathlib import Path


APP_NAME = "danbooru-downloader-py"
APP_LOGGER_NAME = "danbooru_downloader_py"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_FILE_LEVEL = logging.DEBUG
DEFAULT_STREAM_LEVEL = logging.INFO
DEFAULT_LOGGER_LEVEL = logging.DEBUG


def get_default_log_dir() -> Path:
    """
    Return the default application log directory.

    Example:
        ~/.danbooru-downloader-py/logs
    """
    log_dir = Path.home() / f".{APP_NAME}" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_default_log_file_path(
    log_dir: Path | None = None,
    filename_prefix: str = APP_LOGGER_NAME,
) -> Path:
    """
    Return the daily log file path for the whole application.

    Example:
        ~/.danbooru-downloader-py/logs/danbooru_downloader_py_2026-03-11.log
    """
    actual_log_dir = log_dir or get_default_log_dir()
    actual_log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    return actual_log_dir / f"{filename_prefix}_{today}.log"


def get_file_handler(
    log_format: str = LOG_FORMAT,
    log_dir: Path | None = None,
    level: int = DEFAULT_FILE_LEVEL,
) -> logging.FileHandler:
    """
    Create a file handler for the whole application log file.
    """
    log_path = get_default_log_file_path(log_dir=log_dir)

    formatter = logging.Formatter(log_format)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler


def get_stream_handler(
    log_format: str = LOG_FORMAT,
    level: int = DEFAULT_STREAM_LEVEL,
) -> logging.StreamHandler:
    """
    Create a stream handler for stdout.
    """
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler


def _has_equivalent_handler(
    logger: logging.Logger,
    handler: logging.Handler,
) -> bool:
    """
    Check whether an equivalent handler is already attached to the logger.

    For FileHandler:
        compare by concrete log file path.

    For StreamHandler:
        compare by stream object.

    For other handler types:
        compare by handler class.
    """
    for existing in logger.handlers:
        if type(existing) is not type(handler):
            continue

        if isinstance(existing, logging.FileHandler) and isinstance(handler, logging.FileHandler):
            if Path(existing.baseFilename) == Path(handler.baseFilename):
                return True

        elif isinstance(existing, logging.StreamHandler) and isinstance(handler, logging.StreamHandler):
            if existing.stream is handler.stream:
                return True

        else:
            return True

    return False


def _configure_logger(
    logger: logging.Logger,
    handlers: list[logging.Handler],
    level: int = DEFAULT_LOGGER_LEVEL,
) -> logging.Logger:
    """
    Configure logger safely without adding duplicate handlers.
    """
    logger.setLevel(level)
    logger.propagate = False

    for handler in handlers:
        if not _has_equivalent_handler(logger, handler):
            logger.addHandler(handler)

    return logger


def get_app_logger(
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Return the root application logger.

    This logger writes to:
      - one shared daily log file for the whole app
      - stdout
    """
    logger = logging.getLogger(APP_LOGGER_NAME)

    handlers = [
        get_file_handler(log_dir=log_dir),
        get_stream_handler(),
    ]

    return _configure_logger(logger, handlers)


def get_module_logger(
    module_name: str,
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Return a logger for a module.

    Recommended usage in each module:
        logger = get_module_logger(__name__)

    Examples of logger names:
        danbooru_downloader_py.commands.dump
        danbooru_downloader_py.concurrent.db_manager
    """
    logger_name = module_name or APP_LOGGER_NAME
    logger = logging.getLogger(logger_name)

    handlers = [
        get_file_handler(log_dir=log_dir),
        get_stream_handler(),
    ]

    return _configure_logger(logger, handlers)

def get_default_logger(
    name: str | None = None,
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Backward-compatible helper.

    If name is None, return the application logger.
    Otherwise, return a module-style logger with the given name.
    """
    if name is None:
        return get_app_logger(log_dir=log_dir)
    return get_module_logger(name, log_dir=log_dir)