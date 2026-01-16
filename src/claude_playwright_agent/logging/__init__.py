"""
Logging module for Claude Playwright Agent.

This module provides:
- Structured logging configuration
- Context-aware logging
- Multiple log handlers (console, file, rotation)
- JSON and text formatting
- Runtime log level control
"""

import logging
import sys
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger

from claude_playwright_agent.config.manager import ConfigManager


class LogLevel(str, Enum):
    """Standard log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# Custom Log Formatters
# =============================================================================


class ContextFilter(logging.Filter):
    """
    Filter that adds context information to log records.

    Adds:
    - timestamp
    - level name
    - logger name
    - module/function/line info
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to the log record."""
        # Add timestamp if not present
        if not hasattr(record, "timestamp"):
            record.timestamp = datetime.utcnow().isoformat()

        # Add levelname shortcut
        if not hasattr(record, "level"):
            record.level = record.levelname

        return True


class TextFormatter(logging.Formatter):
    """
    Custom text formatter for consistent log output.

    Format: [TIMESTAMP] LEVEL - Logger: Message
    """

    def __init__(self) -> None:
        """Initialize the text formatter."""
        fmt = "[%(asctime)s] %(levelname)-8s - %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        # Add exception info if present
        if record.exc_info:
            # Format exception
            exc_text = self.formatException(record.exc_info)
            if exc_text:
                record.msg = f"{record.msg}\n{exc_text}"

        return super().format(record)


# =============================================================================
# Logger Setup
# =============================================================================


class LoggerSetup:
    """
    Setup and configure logging for the application.

    Features:
    - Console and file logging
    - Text and JSON formats
    - Log rotation
    - Configurable log levels
    - Runtime log level changes
    """

    def __init__(self, config: ConfigManager | None = None) -> None:
        """
        Initialize the logger setup.

        Args:
            config: Optional configuration manager
        """
        self.config = config
        self._root_logger = logging.getLogger()
        self._handlers: list[logging.Handler] = []
        self._current_level: str = "INFO"

    def setup(self) -> None:
        """
        Setup logging based on configuration.

        Configures:
        - Root logger level
        - Console handler
        - File handler with rotation
        - Formatters
        """
        # Get logging configuration
        if self.config:
            log_config = self.config.logging
            log_level = log_config.level
            log_format = log_config.format
            log_file = log_config.file
            console_enabled = log_config.console
        else:
            # Default configuration
            log_level = "INFO"
            log_format = "text"
            log_file = ".cpa/logs/agent.log"
            console_enabled = True

        self._current_level = log_level

        # Set root logger level
        self._root_logger.setLevel(getattr(logging, log_level))

        # Clear existing handlers
        self._root_logger.handlers.clear()

        # Add context filter
        context_filter = ContextFilter()

        # Setup console handler
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level))

            if log_format == "json":
                console_formatter = jsonlogger.JsonFormatter(
                    "%(timestamp)s %(level)s %(name)s %(message)s",
                    timestamp=True,
                )
            else:
                console_formatter = TextFormatter()

            console_handler.setFormatter(console_formatter)
            console_handler.addFilter(context_filter)
            self._root_logger.addHandler(console_handler)
            self._handlers.append(console_handler)

        # Setup file handler
        if log_file:
            file_path = Path(log_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Use RotatingFileHandler for log rotation
            from logging.handlers import RotatingFileHandler

            if self.config:
                max_bytes = self._parse_size(self.config.logging.rotation)
                backup_count = 5  # Keep 5 backup files
            else:
                max_bytes = 10 * 1024 * 1024  # 10 MB
                backup_count = 5

            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, log_level))

            if log_format == "json":
                file_formatter = jsonlogger.JsonFormatter(
                    "%(timestamp)s %(level)s %(name)s %(message)s",
                    timestamp=True,
                )
            else:
                file_formatter = TextFormatter()

            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(context_filter)
            self._root_logger.addHandler(file_handler)
            self._handlers.append(file_handler)

    def set_level(self, level: str | LogLevel) -> None:
        """
        Set the log level at runtime.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if isinstance(level, LogLevel):
            level = level.value

        self._current_level = level.upper()
        log_level = getattr(logging, self._current_level)

        # Update root logger
        self._root_logger.setLevel(log_level)

        # Update all handlers
        for handler in self._handlers:
            handler.setLevel(log_level)

    def get_level(self) -> str:
        """Get the current log level."""
        return self._current_level

    @contextmanager
    def temporary_level(self, level: str | LogLevel):
        """
        Context manager for temporarily changing log level.

        Args:
            level: Temporary log level

        Example:
            with logger_setup.temporary_level("DEBUG"):
                # Debug logging here
                pass
        """
        original_level = self.get_level()
        self.set_level(level)
        try:
            yield
        finally:
            self.set_level(original_level)

    def set_handler_level(self, handler_type: str, level: str | LogLevel) -> None:
        """
        Set log level for a specific handler type.

        Args:
            handler_type: Handler type ("console" or "file")
            level: Log level
        """
        if isinstance(level, LogLevel):
            level = level.value

        log_level = getattr(logging, level.upper())

        for handler in self._handlers:
            is_target = (
                (handler_type == "console" and isinstance(handler, logging.StreamHandler)) or
                (handler_type == "file" and isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)))
            )
            if is_target:
                handler.setLevel(log_level)

    def _parse_size(self, size_str: str) -> int:
        """
        Parse a size string (e.g., "10 MB") into bytes.

        Args:
            size_str: Size string (e.g., "10 MB", "1 GB")

        Returns:
            Size in bytes
        """
        size_str = size_str.strip().upper()

        # Extract number and unit
        import re
        match = re.match(r"([\d.]+)\s*([A-Z]+)", size_str)
        if not match:
            return 10 * 1024 * 1024  # Default to 10 MB

        value = float(match.group(1))
        unit = match.group(2)

        # Convert to bytes
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
        }

        return int(value * multipliers.get(unit, 1))

    def shutdown(self) -> None:
        """Shutdown logging by closing all handlers."""
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()


# =============================================================================
# Convenience Functions
# =============================================================================


_logger_setup: LoggerSetup | None = None


def setup_logging(config: ConfigManager | None = None) -> LoggerSetup:
    """
    Setup logging for the application.

    Args:
        config: Optional configuration manager

    Returns:
        LoggerSetup instance for runtime control
    """
    global _logger_setup
    _logger_setup = LoggerSetup(config)
    _logger_setup.setup()
    return _logger_setup


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str | LogLevel) -> None:
    """
    Set the global log level at runtime.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if _logger_setup:
        _logger_setup.set_level(level)


def get_log_level() -> str:
    """Get the current global log level."""
    if _logger_setup:
        return _logger_setup.get_level()
    return "INFO"


@contextmanager
def temporary_log_level(level: str | LogLevel):
    """
    Context manager for temporarily changing log level.

    Args:
        level: Temporary log level

    Example:
        with temporary_log_level("DEBUG"):
            logger.debug("Detailed info here")
    """
    if _logger_setup:
        with _logger_setup.temporary_level(level):
            yield
    else:
        yield


# =============================================================================
# Module Aliases
# =============================================================================

# For backward compatibility
Logger = logging.Logger


__all__ = [
    "LogLevel",
    "ContextFilter",
    "TextFormatter",
    "LoggerSetup",
    "setup_logging",
    "get_logger",
    "set_log_level",
    "get_log_level",
    "temporary_log_level",
    "Logger",
]
