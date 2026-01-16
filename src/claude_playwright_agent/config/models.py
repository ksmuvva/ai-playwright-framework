"""
Configuration data models for Claude Playwright Agent.

This module defines Pydantic models for configuration validation
following the configuration schema defined in the documentation.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EnvironmentType(str, Enum):
    """Environment types for configuration."""
    DEVELOPMENT = "development"
    DEV = "dev"
    TESTING = "testing"
    TEST = "test"
    STAGING = "staging"
    STAGE = "stage"
    PRODUCTION = "production"
    PROD = "prod"


class FrameworkType(str, Enum):
    """Supported BDD frameworks."""
    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"


class BrowserType(str, Enum):
    """Supported browsers."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class ReportingFormat(str, Enum):
    """Report output formats."""
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"
    XML = "xml"


# =============================================================================
# Framework Configuration
# =============================================================================


class FrameworkConfig(BaseModel):
    """BDD framework settings."""

    bdd_framework: FrameworkType = Field(
        default=FrameworkType.BEHAVE,
        description="BDD framework to use"
    )
    language: str = Field(
        default="python",
        description="Programming language"
    )
    template: str = Field(
        default="basic",
        description="Project template (basic, advanced, ecommerce)"
    )
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for tests"
    )
    default_timeout: int = Field(
        default=30000,
        description="Default timeout in milliseconds",
        ge=1000,
        le=300000,
    )

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        """Validate template is one of the allowed values."""
        allowed = {"basic", "advanced", "ecommerce"}
        if v not in allowed:
            raise ValueError(f"Template must be one of {allowed}")
        return v


# =============================================================================
# Browser Configuration
# =============================================================================


class BrowserConfig(BaseModel):
    """Browser execution settings."""

    browser: BrowserType = Field(
        default=BrowserType.CHROMIUM,
        description="Default browser"
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    viewport_width: int = Field(
        default=1280,
        description="Browser viewport width",
        ge=320,
        le=3840,
    )
    viewport_height: int = Field(
        default=720,
        description="Browser viewport height",
        ge=240,
        le=2160,
    )
    slow_mo: int = Field(
        default=0,
        description="Slow down actions by N milliseconds",
        ge=0,
        le=5000,
    )
    devtools: bool = Field(
        default=False,
        description="Open browser DevTools"
    )


# =============================================================================
# Execution Configuration
# =============================================================================


class ExecutionConfig(BaseModel):
    """Test execution settings."""

    parallel_workers: int = Field(
        default=1,
        description="Number of parallel test workers",
        ge=1,
        le=16,
    )
    retry_failed: int = Field(
        default=0,
        description="Number of times to retry failed tests",
        ge=0,
        le=5,
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop on first failure"
    )
    randomize: bool = Field(
        default=False,
        description="Randomize test execution order"
    )
    self_healing: bool = Field(
        default=True,
        description="Enable self-healing locators"
    )
    video: bool = Field(
        default=False,
        description="Record video of test execution"
    )
    screenshots: str = Field(
        default="on-failure",
        description="When to take screenshots (always, on-failure, never)",
    )
    trace: str = Field(
        default="retain-on-failure",
        description="When to keep trace (retain-on-failure, on, off)",
    )


# =============================================================================
# Recording Configuration
# =============================================================================


class RecordingConfig(BaseModel):
    """Recording ingestion settings."""

    auto_parse: bool = Field(
        default=True,
        description="Automatically parse recordings on ingest"
    )
    generate_page_objects: bool = Field(
        default=True,
        description="Generate page object classes"
    )
    deduplicate_elements: bool = Field(
        default=True,
        description="Deduplicate similar elements across recordings"
    )
    extract_components: bool = Field(
        default=True,
        description="Extract reusable UI components"
    )
    scenario_naming: str = Field(
        default="descriptive",
        description="Scenario naming style (descriptive, concise)",
    )
    step_organization: str = Field(
        default="feature-based",
        description="Step file organization (feature-based, flat)",
    )


# =============================================================================
# Reporting Configuration
# =============================================================================


class ReportingConfig(BaseModel):
    """Test reporting settings."""

    formats: list[ReportingFormat] = Field(
        default_factory=lambda: [ReportingFormat.HTML],
        description="Report output formats"
    )
    output_dir: str = Field(
        default="reports",
        description="Report output directory"
    )
    include_ai_analysis: bool = Field(
        default=True,
        description="Include AI-powered failure analysis"
    )
    include_screenshots: bool = Field(
        default=True,
        description="Include screenshots in reports"
    )
    include_trace: bool = Field(
        default=False,
        description="Include trace logs in reports"
    )
    generate_executive_summary: bool = Field(
        default=True,
        description="Generate executive summary for stakeholders"
    )
    history_size: int = Field(
        default=50,
        description="Number of historical runs to keep",
        ge=0,
        le=1000,
    )


# =============================================================================
# Skills Configuration
# =============================================================================


class SkillConfig(BaseModel):
    """Claude Skills configuration."""

    enabled: list[str] = Field(
        default_factory=list,
        description="List of enabled skill names"
    )
    disabled: list[str] = Field(
        default_factory=list,
        description="List of disabled skill names"
    )
    auto_invoke: list[str] = Field(
        default_factory=lambda: ["self-healing"],
        description="Skills to auto-invoke on matching events"
    )
    custom_skills_dir: str = Field(
        default=".cpa/skills/custom",
        description="Directory for custom skills"
    )


# =============================================================================
# AI Configuration
# =============================================================================


class AIConfig(BaseModel):
    """AI model configuration with multi-provider support."""

    # NEW: Provider selection
    provider: str = Field(
        default="anthropic",
        description="LLM provider to use (anthropic, openai, glm)"
    )

    # NEW: Fallback providers
    fallback_providers: list[str] = Field(
        default_factory=list,
        description="Fallback providers in priority order"
    )

    # NEW: Provider-specific settings
    provider_settings: dict[str, dict] = Field(
        default_factory=dict,
        description="Provider-specific configuration overrides"
    )

    # NEW: Model aliases for cross-provider compatibility
    model_aliases: dict[str, str] = Field(
        default_factory=dict,
        description="Model name aliases for different providers"
    )

    # Existing fields (maintained for backward compatibility)
    model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default model to use (provider-specific)"
    )
    max_tokens: int = Field(
        default=8192,
        description="Maximum tokens for AI responses",
        ge=1024,
        le=200000,
    )
    temperature: float = Field(
        default=0.3,
        description="AI response temperature (0-1)",
        ge=0.0,
        le=1.0,
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching"
    )
    timeout: int = Field(
        default=120,
        description="AI request timeout in seconds",
        ge=10,
        le=600,
    )

    def get_provider_config(self, provider_name: str | None = None) -> dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider_name: Provider name (anthropic, openai, glm)
                          Uses self.provider if None

        Returns:
            Provider-specific configuration merged with base settings
        """
        provider = provider_name or self.provider

        base_config = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
        }

        # Apply provider-specific overrides
        provider_overrides = self.provider_settings.get(provider, {})
        base_config.update(provider_overrides)

        return base_config


# =============================================================================
# Logging Configuration
# =============================================================================


class LoggingConfig(BaseModel):
    """Logging settings."""

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="text",
        description="Log format (text, json)",
    )
    file: str = Field(
        default=".cpa/logs/agent.log",
        description="Log file path"
    )
    console: bool = Field(
        default=True,
        description="Enable console logging"
    )
    rotation: str = Field(
        default="10 MB",
        description="Log rotation size"
    )
    retention: str = Field(
        default="7 days",
        description="Log retention period"
    )

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()


# =============================================================================
# Environment Configuration
# =============================================================================


class EnvironmentConfig(BaseModel):
    """
    Environment-specific configuration overrides.

    This model allows overriding base configuration settings
    for specific environments (dev, test, staging, prod).
    """

    name: EnvironmentType = Field(
        description="Environment name"
    )
    base_url: str | None = Field(
        default=None,
        description="Override base URL for this environment"
    )
    browser: BrowserType | None = Field(
        default=None,
        description="Override browser for this environment"
    )
    headless: bool | None = Field(
        default=None,
        description="Override headless mode for this environment"
    )
    parallel_workers: int | None = Field(
        default=None,
        description="Override parallel workers for this environment",
        ge=1,
        le=16,
    )
    timeout: int | None = Field(
        default=None,
        description="Override default timeout for this environment (ms)",
        ge=1000,
        le=300000,
    )
    screenshots: str | None = Field(
        default=None,
        description="Override screenshot setting for this environment"
    )
    video: bool | None = Field(
        default=None,
        description="Override video recording for this environment"
    )
    log_level: str | None = Field(
        default=None,
        description="Override log level for this environment"
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set for this environment"
    )

    def apply_to_config(self, config: "AgentConfig") -> "AgentConfig":
        """
        Apply environment overrides to a base configuration.

        Args:
            config: Base configuration to override

        Returns:
            New configuration with environment overrides applied
        """
        config_dict = config.model_dump()

        # Apply overrides
        if self.base_url is not None:
            config_dict["framework"]["base_url"] = self.base_url
        if self.browser is not None:
            config_dict["browser"]["browser"] = self.browser.value
        if self.headless is not None:
            config_dict["browser"]["headless"] = self.headless
        if self.parallel_workers is not None:
            config_dict["execution"]["parallel_workers"] = self.parallel_workers
        if self.timeout is not None:
            config_dict["framework"]["default_timeout"] = self.timeout
        if self.screenshots is not None:
            config_dict["execution"]["screenshots"] = self.screenshots
        if self.video is not None:
            config_dict["execution"]["video"] = self.video
        if self.log_level is not None:
            config_dict["logging"]["level"] = self.log_level

        # Apply environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value

        return AgentConfig(**config_dict)


# =============================================================================
# Main Configuration Model
# =============================================================================


class AgentConfig(BaseModel):
    """
    Complete agent configuration.

    This model represents the full .cpa/config.yaml structure
    with validation for all configuration sections.
    """

    framework: FrameworkConfig = Field(
        default_factory=FrameworkConfig,
        description="BDD framework settings"
    )
    browser: BrowserConfig = Field(
        default_factory=BrowserConfig,
        description="Browser execution settings"
    )
    execution: ExecutionConfig = Field(
        default_factory=ExecutionConfig,
        description="Test execution settings"
    )
    recording: RecordingConfig = Field(
        default_factory=RecordingConfig,
        description="Recording ingestion settings"
    )
    reporting: ReportingConfig = Field(
        default_factory=ReportingConfig,
        description="Test reporting settings"
    )
    skills: SkillConfig = Field(
        default_factory=SkillConfig,
        description="Claude Skills configuration"
    )
    ai: AIConfig = Field(
        default_factory=AIConfig,
        description="AI model configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging settings"
    )
    environments: dict[str, EnvironmentConfig] = Field(
        default_factory=dict,
        description="Environment-specific configuration overrides"
    )
    active_environment: str | None = Field(
        default=None,
        description="Currently active environment name"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "framework": {
                    "bdd_framework": "behave",
                    "language": "python",
                    "template": "basic",
                    "base_url": "http://localhost:8000",
                    "default_timeout": 30000,
                },
                "browser": {
                    "browser": "chromium",
                    "headless": True,
                    "viewport_width": 1280,
                    "viewport_height": 720,
                },
                "execution": {
                    "parallel_workers": 1,
                    "retry_failed": 0,
                    "self_healing": True,
                },
                "environments": {
                    "dev": {
                        "name": "dev",
                        "base_url": "http://localhost:3000",
                    },
                    "prod": {
                        "name": "prod",
                        "base_url": "https://example.com",
                        "headless": True,
                        "video": True,
                    },
                },
            }
        }

    def get_environment(self, env_name: str) -> EnvironmentConfig | None:
        """
        Get an environment configuration by name.

        Args:
            env_name: Environment name (e.g., 'dev', 'prod')

        Returns:
            EnvironmentConfig if found, None otherwise
        """
        return self.environments.get(env_name)

    def list_environments(self) -> list[str]:
        """
        List all available environment names.

        Returns:
            List of environment names
        """
        return list(self.environments.keys())

    def with_environment(self, env_name: str) -> "AgentConfig":
        """
        Apply environment overrides to create a new configuration.

        Args:
            env_name: Name of the environment to apply

        Returns:
            New AgentConfig with environment overrides applied

        Raises:
            ValueError: If environment not found
        """
        env = self.get_environment(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found. Available: {self.list_environments()}")

        config = env.apply_to_config(self)
        config.active_environment = env_name
        return config

    def model_dump_yaml(self) -> str:
        """Export to YAML format."""
        import io

        import yaml

        # Convert to dict for YAML serialization with mode='json' to handle enums
        data = self.model_dump(mode='json')

        with io.StringIO() as output:
            yaml.dump(data, output, default_flow_style=False, sort_keys=False)
            return output.getvalue()

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "AgentConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            AgentConfig instance

        Raises:
            ValueError: If file cannot be read or parsed
        """
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Configuration file not found: {path}")

        import yaml

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to read configuration file: {e}") from e

        if data is None:
            return cls()

        return cls(**data)
