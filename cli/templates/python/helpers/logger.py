"""
Structured Logging Configuration using structlog

Provides detailed, structured logging throughout the framework with:
- Colored output for better readability
- Timestamp and log level information
- Context-aware logging (function name, line number, etc.)
- Configurable log levels via environment variable
"""

import os
import sys
import structlog
from structlog.typing import EventDict, WrappedLogger
import logging

# Initialize colorama for Windows compatibility
try:
    from colorama import init as colorama_init
    colorama_init()
except ImportError:
    pass


def add_log_level_color(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add color to log level"""
    colors = {
        "critical": "\033[1;31m",  # Bold Red
        "error": "\033[31m",       # Red
        "warning": "\033[33m",     # Yellow
        "info": "\033[32m",        # Green
        "debug": "\033[36m",       # Cyan
    }
    reset = "\033[0m"

    level = event_dict.get("level", "").lower()
    if level in colors:
        event_dict["level"] = f"{colors[level]}{level.upper()}{reset}"

    return event_dict


def configure_logging(log_level: str = None):
    """
    Configure structured logging for the framework

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, reads from LOG_LEVEL environment variable (default: INFO)
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Convert string to logging level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    numeric_level = level_map.get(log_level, logging.INFO)

    # Configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_log_level_color,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


# Default logger for the framework
logger = get_logger("ai-playwright-framework")


def log_framework_info():
    """Log framework initialization information"""
    logger.info(
        "framework_initialized",
        version="2.0.0",
        python_version=sys.version.split()[0],
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def log_phoenix_status(enabled: bool, endpoint: str = None, ui_launched: bool = False):
    """Log Phoenix tracing status"""
    if enabled:
        logger.info(
            "phoenix_enabled",
            endpoint=endpoint,
            ui_launched=ui_launched,
            message="Phoenix tracing is active - all LLM calls will be traced",
        )
    else:
        logger.warning(
            "phoenix_disabled",
            message="Phoenix tracing is disabled - LLM observability unavailable",
        )


def log_ai_config(provider: str, model: str, features: dict):
    """Log AI configuration"""
    logger.info(
        "ai_configured",
        provider=provider,
        model=model,
        **features,
    )


def log_browser_config(browser: str, headless: bool, viewport: dict):
    """Log browser configuration"""
    logger.info(
        "browser_configured",
        browser=browser,
        headless=headless,
        viewport=viewport,
    )


def log_scenario_start(scenario_name: str, tags: list):
    """Log scenario start"""
    logger.info(
        "scenario_started",
        scenario=scenario_name,
        tags=tags,
    )


def log_scenario_end(scenario_name: str, status: str, duration: float = None):
    """Log scenario completion"""
    if status == "passed":
        logger.info(
            "scenario_passed",
            scenario=scenario_name,
            duration_ms=duration,
        )
    else:
        logger.error(
            "scenario_failed",
            scenario=scenario_name,
            status=status,
            duration_ms=duration,
        )


def log_step_execution(step_name: str, status: str, duration: float = None):
    """Log step execution"""
    if status == "passed":
        logger.debug(
            "step_passed",
            step=step_name,
            duration_ms=duration,
        )
    else:
        logger.error(
            "step_failed",
            step=step_name,
            duration_ms=duration,
        )


def log_healing_attempt(locator: str, success: bool, new_locator: str = None):
    """Log self-healing attempt"""
    if success:
        logger.info(
            "healing_success",
            original_locator=locator,
            healed_locator=new_locator,
            message="Locator successfully healed",
        )
    else:
        logger.warning(
            "healing_failed",
            locator=locator,
            message="Failed to heal locator",
        )


def log_ai_request(operation: str, provider: str, model: str, prompt_length: int):
    """Log AI request"""
    logger.debug(
        "ai_request",
        operation=operation,
        provider=provider,
        model=model,
        prompt_length=prompt_length,
    )


def log_ai_response(operation: str, success: bool, tokens: dict = None, duration: float = None):
    """Log AI response"""
    if success:
        logger.info(
            "ai_response_success",
            operation=operation,
            duration_ms=duration,
            **(tokens or {}),
        )
    else:
        logger.error(
            "ai_response_failed",
            operation=operation,
            duration_ms=duration,
        )


def log_error(context: str, error: Exception, details: dict = None):
    """Log error with context"""
    logger.error(
        "error_occurred",
        context=context,
        error_type=type(error).__name__,
        error_message=str(error),
        **(details or {}),
        exc_info=True,
    )
