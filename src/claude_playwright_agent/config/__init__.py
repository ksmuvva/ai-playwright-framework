"""
Configuration Management Module for Claude Playwright Agent.

This module provides configuration management for the framework including:
- Configuration loading from YAML files
- Configuration validation using Pydantic models
- Profile-based configuration
- Environment variable overrides
- Configuration merging and inheritance
- Environment-specific configuration support
"""

from claude_playwright_agent.config.manager import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    CONFIG_PROFILES_DIR,
    ConfigError,
    ConfigManager,
    ConfigNotFoundError,
    ConfigValidationError,
    DEFAULT_PROFILE,
    ProfileConfig,
    PROFILES,
)
from claude_playwright_agent.config.models import (
    AIConfig,
    AgentConfig,
    BrowserConfig,
    BrowserType,
    EnvironmentConfig,
    EnvironmentType,
    ExecutionConfig,
    FrameworkConfig,
    FrameworkType,
    LoggingConfig,
    RecordingConfig,
    ReportingConfig,
    ReportingFormat,
    SkillConfig,
)

__all__ = [
    # Manager
    "ConfigManager",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "ProfileConfig",
    # Constants
    "CONFIG_DIR_NAME",
    "CONFIG_FILE_NAME",
    "CONFIG_PROFILES_DIR",
    "DEFAULT_PROFILE",
    "PROFILES",
    # Models
    "AgentConfig",
    "FrameworkConfig",
    "BrowserConfig",
    "ExecutionConfig",
    "RecordingConfig",
    "ReportingConfig",
    "SkillConfig",
    "AIConfig",
    "LoggingConfig",
    "EnvironmentConfig",
    # Enums
    "FrameworkType",
    "BrowserType",
    "ReportingFormat",
    "EnvironmentType",
]
