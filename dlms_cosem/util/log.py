"""Logging utilities for DLMS/COSEM.

This module provides logging configuration and helper functions
using standard library logging (no external dependencies).

Reference: pdlms/pdlms/util/log.py
"""

import datetime
import logging
import os
import threading
from typing import Optional


class LogConstant:
    """
    Constants for logging configuration.
    """

    LOG_DIR = "logs"
    LOG_REPORT_NAME = "report.log"
    MAX_LOG_SIZE_BYTES = 1024 * 1024 * 20  # 20MB
    MAX_LOG_NUM = 50
    SUMMARY_DIR = "summary"
    LOG_REPORT_FORMAT = (
        "%(asctime)s [%(threadName)-10s] [%(filename)-20s "
        "lineno:%(lineno)-4d] %(levelname)5s : %(message)s"
    )
    LOG_REPORT_PLACEHOLDER = 34


class Log:
    """
    Logger configuration and management.

    Provides a singleton-like logger instance with configurable
    log level and output destination. Thread-safe.
    """

    def __init__(self):
        self.level = logging.INFO
        self._report_logger: Optional[logging.Logger] = None
        self._lock = threading.Lock()
        self._initialized = False
        self._handlers_added = False  # Track if handlers were added
        self.log_report_path = os.path.join(
            LogConstant.LOG_DIR,
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

    @property
    def logger(self) -> logging.Logger:
        """Get or create the logger instance (thread-safe)."""
        # Fast path: if already initialized, return without lock
        if self._initialized and self._report_logger is not None:
            return self._report_logger

        # Slow path: acquire lock and initialize
        with self._lock:
            # Double-check: another thread may have initialized while we waited
            if self._initialized and self._report_logger is not None:
                return self._report_logger

            self._report_logger = logging.getLogger("dlms_cosem.log")
            self._report_logger.propagate = False

            # Only add handlers once
            if not self._handlers_added:
                # Console handler
                h = logging.StreamHandler()
                h.setFormatter(logging.Formatter(LogConstant.LOG_REPORT_FORMAT))
                self._report_logger.addHandler(h)

                # File handler (if log directory exists)
                if os.path.exists(LogConstant.LOG_DIR):
                    fh = logging.FileHandler(
                        os.path.join(LogConstant.LOG_DIR, LogConstant.LOG_REPORT_NAME)
                    )
                    fh.setFormatter(logging.Formatter(LogConstant.LOG_REPORT_FORMAT))
                    self._report_logger.addHandler(fh)

                self._handlers_added = True

            self._report_logger.setLevel(self.level)
            self._initialized = True
            return self._report_logger

    def cleanup(self):
        """Clean up logger resources.

        Call this when shutting down to release file handles.
        """
        with self._lock:
            if self._report_logger and self._handlers_added:
                for handler in self._report_logger.handlers[:]:
                    handler.close()
                    self._report_logger.removeHandler(handler)
                self._handlers_added = False

    def create_logger(self) -> logging.Logger:
        """Create and return the logger instance."""
        return self.logger

    def set_level(self, level: int):
        """Set the logging level."""
        self.level = level
        if self._report_logger:
            self._report_logger.setLevel(level)


# Global logger instance
log = Log()


def _log(level: int, msg: str, *args, **kwargs):
    """
    Internal logging function.

    Args:
        level: Logging level (logging.INFO, etc.)
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    is_print = kwargs.pop("is_print_log", True)
    if is_print and log.logger.isEnabledFor(level):
        log.logger.log(level, msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """
    Log info level message.

    Args:
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    _log(logging.INFO, msg, *args, **kwargs)


def debug(msg: str, *args, **kwargs):
    """
    Log debug level message.

    Args:
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    _log(logging.DEBUG, msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """
    Log error level message.

    Args:
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    _log(logging.ERROR, msg, *args, **kwargs)


def warn(msg: str, *args, **kwargs):
    """
    Log warning level message.

    Args:
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    _log(logging.WARNING, msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """
    Log critical level message.

    Args:
        msg: Message to log
        *args: Additional arguments for message formatting
        **kwargs: Keyword arguments, is_print_log to control output
    """
    _log(logging.CRITICAL, msg, *args, **kwargs)
