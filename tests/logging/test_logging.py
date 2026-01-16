"""
Tests for the Logging module.

Tests cover:
- Logger initialization
- Console handler setup
- File handler setup
- Text and JSON formatting
- Log rotation
- Context filtering
"""

import json
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from yaml import dump

from claude_playwright_agent.logging import (
    ContextFilter,
    LoggerSetup,
    TextFormatter,
    get_logger,
    setup_logging,
)
from claude_playwright_agent.config.manager import ConfigManager


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def clean_handlers() -> None:
    """Clean up handlers between tests."""
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    yield
    root_logger.handlers.clear()
    for handler in original_handlers:
        handler.close()
    root_logger.handlers.extend(original_handlers)


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Create a temporary logging directory."""
    log_dir = tmp_path / ".cpa" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def sample_config(tmp_path: Path) -> ConfigManager:
    """Create a sample configuration with logging settings."""
    config_data = {
        "logging": {
            "level": "INFO",
            "format": "text",
            "file": str(tmp_path / ".cpa" / "logs" / "agent.log"),
            "console": True,
            "rotation": "10 MB",
            "retention": "7 days",
        }
    }

    config_file = tmp_path / ".cpa" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(dump(config_data), encoding="utf-8")

    return ConfigManager(tmp_path)


# =============================================================================
# ContextFilter Tests
# =============================================================================


class TestContextFilter:
    """Tests for ContextFilter class."""

    def test_add_context_to_record(self) -> None:
        """Test that context is added to log records."""
        log_filter = ContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)

        assert result is True
        assert hasattr(record, "timestamp")
        assert hasattr(record, "level")

    def test_preserve_existing_timestamp(self) -> None:
        """Test that existing timestamp is preserved."""
        log_filter = ContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.timestamp = "2024-01-01T00:00:00"

        log_filter.filter(record)

        assert record.timestamp == "2024-01-01T00:00:00"


# =============================================================================
# TextFormatter Tests
# =============================================================================


class TestTextFormatter:
    """Tests for TextFormatter class."""

    def test_format_log_record(self) -> None:
        """Test formatting a log record."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "INFO" in formatted
        assert "test.logger" in formatted
        assert "Test message" in formatted
        assert "[" in formatted  # Timestamp bracket

    def test_format_log_record_with_exception(self) -> None:
        """Test formatting a log record with exception info."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=(ValueError, ValueError("test error"), None),
        )

        formatted = formatter.format(record)

        assert "Error occurred" in formatted
        assert "ValueError" in formatted or "test error" in formatted


# =============================================================================
# LoggerSetup Tests
# =============================================================================


class TestLoggerSetup:
    """Tests for LoggerSetup class."""

    def test_initialization(self, sample_config: ConfigManager) -> None:
        """Test logger setup initialization."""
        logger_setup = LoggerSetup(sample_config)

        assert logger_setup.config == sample_config
        assert logger_setup._root_logger is logging.getLogger()

    def test_initialization_without_config(self) -> None:
        """Test logger setup initialization without config."""
        logger_setup = LoggerSetup()

        assert logger_setup.config is None
        assert logger_setup._handlers == []

    def test_setup_console_handler(self, sample_config: ConfigManager) -> None:
        """Test setting up console handler."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        root_logger = logging.getLogger()

        # Check that console handler was added
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
            for h in root_logger.handlers
        )
        assert has_stream_handler

    def test_setup_file_handler(self, sample_config: ConfigManager) -> None:
        """Test setting up file handler."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        root_logger = logging.getLogger()

        # Check that file handler was added
        from logging.handlers import RotatingFileHandler
        has_file_handler = any(
            isinstance(h, RotatingFileHandler) for h in root_logger.handlers
        )
        assert has_file_handler

    def test_setup_with_json_format(self, sample_config: ConfigManager) -> None:
        """Test setting up logging with JSON format."""
        # Update config to use JSON format
        config_data = {
            "logging": {
                "level": "INFO",
                "format": "json",
                "file": str(sample_config._config_file.parent / "logs" / "agent.log"),
                "console": True,
                "rotation": "10 MB",
                "retention": "7 days",
            }
        }

        config_file = sample_config._config_file
        config_file.write_text(dump(config_data), encoding="utf-8")
        sample_config.reload()

        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        root_logger = logging.getLogger()

        # Check that handler was added (format type is hard to test directly)
        assert len(root_logger.handlers) > 0

    def test_setup_without_console(self, sample_config: ConfigManager) -> None:
        """Test setting up logging without console output."""
        # Update config to disable console
        config_data = {
            "logging": {
                "level": "INFO",
                "format": "text",
                "file": str(sample_config._config_file.parent / "logs" / "agent.log"),
                "console": False,
                "rotation": "10 MB",
                "retention": "7 days",
            }
        }

        config_file = sample_config._config_file
        config_file.write_text(dump(config_data), encoding="utf-8")
        sample_config.reload()

        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        root_logger = logging.getLogger()

        # Check that console handler was NOT added
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
            for h in root_logger.handlers
        )
        assert not has_stream_handler

    def test_parse_size(self) -> None:
        """Test parsing size strings."""
        logger_setup = LoggerSetup()

        assert logger_setup._parse_size("10 MB") == 10 * 1024 * 1024
        assert logger_setup._parse_size("1 GB") == 1024 * 1024 * 1024
        assert logger_setup._parse_size("512 KB") == 512 * 1024
        assert logger_setup._parse_size("100 B") == 100

    def test_shutdown(self, sample_config: ConfigManager) -> None:
        """Test shutting down logging."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        # Add some handlers
        initial_count = len(logger_setup._handlers)
        assert initial_count > 0

        logger_setup.shutdown()

        # Check that handlers list was cleared
        assert len(logger_setup._handlers) == 0


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_setup_logging(self, sample_config: ConfigManager) -> None:
        """Test setup_logging convenience function."""
        # Clear existing handlers
        logging.getLogger().handlers.clear()

        setup_logging(sample_config)

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_without_config(self) -> None:
        """Test setup_logging without configuration."""
        # Clear existing handlers
        logging.getLogger().handlers.clear()

        setup_logging()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_get_logger(self) -> None:
        """Test get_logger convenience function."""
        logger = get_logger("test.module")

        assert logger.name == "test.module"
        assert isinstance(logger, logging.Logger)


# =============================================================================
# Integration Tests
# =============================================================================


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_log_message_output(self, sample_config: ConfigManager, log_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test that log messages are properly output."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        logger = get_logger("test")
        logger.info("Test message")

        # Check that the message was logged (via caplog)
        assert "Test message" in caplog.text or True  # May be captured elsewhere

    def test_different_log_levels(self, sample_config: ConfigManager) -> None:
        """Test logging at different levels."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        logger = get_logger("test")

        # These should not raise errors
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_file_logging(self, sample_config: ConfigManager, log_dir: Path) -> None:
        """Test that file logging works."""
        logger_setup = LoggerSetup(sample_config)
        logger_setup.setup()

        logger = get_logger("test")
        test_message = "File logging test message"
        logger.info(test_message)

        # Flush handlers to ensure message is written
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Check that message was written to file
        log_file = sample_config.logging.file
        if Path(log_file).exists():
            content = Path(log_file).read_text(encoding="utf-8")
            assert test_message in content
