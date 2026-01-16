"""
Configuration Manager - Core configuration management for Claude Playwright Agent.

This module implements the ConfigManager class which handles:
- Loading configuration from YAML files
- Configuration validation
- Profile-based configuration (dev, test, prod)
- Configuration merging and overrides
- Environment variable overrides
- Configuration inheritance
"""

import os
from pathlib import Path
from typing import Any, Final

from pydantic import ValidationError

from claude_playwright_agent.config.models import (
    AIConfig,
    AgentConfig,
    BrowserConfig,
    ExecutionConfig,
    FrameworkConfig,
    LoggingConfig,
    RecordingConfig,
    ReportingConfig,
    SkillConfig,
)

# =============================================================================
# Constants
# =============================================================================

CONFIG_DIR_NAME: Final = ".cpa"
CONFIG_FILE_NAME: Final = "config.yaml"
CONFIG_PROFILES_DIR: Final = "profiles"
DEFAULT_PROFILE: Final = "default"

# Available profiles
PROFILES: Final = ["default", "dev", "test", "prod", "ci"]


# =============================================================================
# Exceptions
# =============================================================================


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Exception raised when configuration file is not found."""

    pass


class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails."""

    pass


# =============================================================================
# Configuration Profiles
# =============================================================================


class ProfileConfig:
    """Configuration profile definitions."""

    @staticmethod
    def get_profile_config(profile: str) -> dict[str, Any]:
        """
        Get configuration for a specific profile.

        Args:
            profile: Profile name (dev, test, prod, ci)

        Returns:
            Configuration dictionary for the profile
        """
        profiles = {
            "default": {
                "framework": {
                    "bdd_framework": "behave",
                    "template": "basic",
                    "default_timeout": 30000,
                },
                "browser": {
                    "browser": "chromium",
                    "headless": True,
                },
                "execution": {
                    "parallel_workers": 1,
                    "retry_failed": 0,
                },
                "logging": {
                    "level": "INFO",
                },
            },
            "dev": {
                "framework": {
                    "bdd_framework": "behave",
                    "template": "advanced",
                },
                "browser": {
                    "browser": "chromium",
                    "headless": False,
                    "devtools": True,
                    "slow_mo": 100,
                },
                "execution": {
                    "parallel_workers": 1,
                    "fail_fast": True,
                },
                "logging": {
                    "level": "DEBUG",
                    "console": True,
                },
                "reporting": {
                    "include_ai_analysis": True,
                },
            },
            "test": {
                "framework": {
                    "bdd_framework": "pytest-bdd",
                    "template": "basic",
                },
                "browser": {
                    "browser": "chromium",
                    "headless": True,
                },
                "execution": {
                    "parallel_workers": 4,
                    "retry_failed": 2,
                    "self_healing": True,
                },
                "logging": {
                    "level": "INFO",
                    "console": False,
                },
                "recording": {
                    "generate_page_objects": True,
                    "deduplicate_elements": True,
                },
            },
            "prod": {
                "framework": {
                    "bdd_framework": "behave",
                    "template": "advanced",
                },
                "browser": {
                    "browser": "chromium",
                    "headless": True,
                },
                "execution": {
                    "parallel_workers": 8,
                    "retry_failed": 1,
                    "fail_fast": False,
                },
                "logging": {
                    "level": "WARNING",
                    "console": False,
                },
                "reporting": {
                    "formats": ["html", "json"],
                    "include_ai_analysis": True,
                },
            },
            "ci": {
                "framework": {
                    "bdd_framework": "pytest-bdd",
                },
                "browser": {
                    "browser": "chromium",
                    "headless": True,
                },
                "execution": {
                    "parallel_workers": 4,
                    "retry_failed": 2,
                    "fail_fast": False,
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "console": True,
                },
                "reporting": {
                    "formats": ["json", "xml"],
                    "include_ai_analysis": False,
                },
                "recording": {
                    "video": True,
                    "screenshots": "always",
                },
            },
        }

        return profiles.get(profile, profiles["default"])


# =============================================================================
# Configuration Manager
# =============================================================================


class ConfigManager:
    """
    Manages framework configuration with validation and profiles.

    Features:
    - Load configuration from YAML files
    - Profile-based configuration
    - Environment variable overrides
    - Configuration validation
    - Configuration merging
    - Configuration inheritance
    """

    def __init__(
        self,
        project_path: str | Path | None = None,
        profile: str = DEFAULT_PROFILE,
        env_prefix: str = "CPA_",
    ) -> None:
        """
        Initialize the ConfigManager.

        Args:
            project_path: Path to project root. Defaults to current directory.
            profile: Configuration profile to use.
            env_prefix: Prefix for environment variable overrides.

        Raises:
            ConfigError: If profile is not valid
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._config_dir = self._project_path / "config" / "default"
        self._config_file = self._config_dir / "config.yaml"
        self._profiles_dir = self._project_path / "config" / "profiles"

        # Validate profile (allow custom profiles)
        custom_profiles = self._get_custom_profiles()
        valid_profiles = PROFILES + custom_profiles

        if profile not in valid_profiles:
            raise ConfigError(
                f"Invalid profile: {profile}. "
                f"Valid profiles: {PROFILES} + custom: {custom_profiles}"
            )

        self._profile = profile
        self._env_prefix = env_prefix

        # Load configuration
        self._config: AgentConfig = self._load_config()

    def _load_config(self) -> AgentConfig:
        """
        Load configuration from file, profile, and environment.

        Returns:
            AgentConfig instance
        """
        # Start with profile defaults
        profile_config = self._load_profile_config(self._profile)
        config_dict = profile_config.copy()

        # Resolve profile inheritance
        config_dict = self._resolve_profile_inheritance(config_dict)

        # Load from file if exists
        if self._config_file.exists():
            try:
                file_config = AgentConfig.from_yaml_file(self._config_file)
                # Deep merge file config over profile defaults
                config_dict = self._deep_merge(config_dict, file_config.model_dump())
            except (ValidationError, ValueError) as e:
                raise ConfigValidationError(f"Invalid configuration file: {e}") from e

        # Apply environment variable overrides
        config_dict = self._apply_env_overrides(config_dict)

        # Validate and create config
        try:
            return AgentConfig(**config_dict)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e

    def _load_profile_config(self, profile: str) -> dict[str, Any]:
        """
        Load configuration for a specific profile.

        Args:
            profile: Profile name

        Returns:
            Profile configuration dictionary
        """
        # First try built-in profiles
        if profile in PROFILES:
            return ProfileConfig.get_profile_config(profile)

        # Try custom profiles from project directory
        profile_file = self._profiles_dir / f"{profile}.yaml"
        if profile_file.exists():
            try:
                import yaml
                with open(profile_file, encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                raise ConfigError(f"Failed to load custom profile '{profile}': {e}") from e

        # Fall back to default
        return ProfileConfig.get_profile_config(DEFAULT_PROFILE)

    def _resolve_profile_inheritance(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve profile inheritance by merging base profile.

        Args:
            config: Profile configuration with optional 'extends' key

        Returns:
            Resolved configuration dictionary
        """
        # Check for inheritance
        extends = config.get("extends")
        if not extends or extends not in PROFILES + self._get_custom_profiles():
            return config

        # Load base profile
        base_config = self._load_profile_config(extends)

        # Resolve nested inheritance first
        base_config = self._resolve_profile_inheritance(base_config)

        # Merge: base -> child (child values override base)
        return self._deep_merge(base_config, config)

    def _get_custom_profiles(self) -> list[str]:
        """
        Get list of custom profile names.

        Returns:
            List of custom profile names
        """
        if not self._profiles_dir.exists():
            return []

        custom_profiles = []
        for profile_file in self._profiles_dir.glob("*.yaml"):
            custom_profiles.append(profile_file.stem)

        return sorted(custom_profiles)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Environment variables should be in the format:
        CPA_SECTION__KEY=value

        Examples:
            CPA_BROWSER__HEADLESS=false
            CPA_EXECUTION__PARALLEL_WORKERS=4

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with overrides applied
        """
        result = config.copy()

        for env_var, env_value in os.environ.items():
            if not env_var.startswith(self._env_prefix):
                continue

            # Remove prefix and parse
            var_parts = env_var[len(self._env_prefix):].split("__")

            if len(var_parts) != 2:
                continue

            section, key = var_parts
            section = section.lower()
            key = key.lower()

            # Convert value to appropriate type
            converted_value = self._convert_env_value(env_value)

            # Apply override
            if section not in result:
                result[section] = {}
            result[section][key] = converted_value

        return result

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.

        Args:
            value: Environment variable value

        Returns:
            Converted value
        """
        # Boolean
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String
        return value

    # =========================================================================
    # Configuration Access
    # =========================================================================

    @property
    def framework(self) -> FrameworkConfig:
        """Get framework configuration."""
        return self._config.framework

    @property
    def browser(self) -> BrowserConfig:
        """Get browser configuration."""
        return self._config.browser

    @property
    def execution(self) -> ExecutionConfig:
        """Get execution configuration."""
        return self._config.execution

    @property
    def recording(self) -> RecordingConfig:
        """Get recording configuration."""
        return self._config.recording

    @property
    def reporting(self) -> ReportingConfig:
        """Get reporting configuration."""
        return self._config.reporting

    @property
    def skills(self) -> SkillConfig:
        """Get skills configuration."""
        return self._config.skills

    @property
    def ai(self) -> AIConfig:
        """Get AI configuration."""
        return self._config.ai

    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        return self._config.logging

    @property
    def config(self) -> AgentConfig:
        """Get complete configuration."""
        return self._config

    # =========================================================================
    # Configuration Operations
    # =========================================================================

    def save(self, path: str | Path | None = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save to. Defaults to .cpa/config.yaml
        """
        if path is None:
            path = self._config_file
        else:
            path = Path(path)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._config.model_dump_yaml())

    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = self._load_config()

    def update(self, **kwargs: Any) -> None:
        """
        Update configuration values.

        Args:
            **kwargs: Configuration values to update

        Example:
            config_manager.update(browser_headless=False, execution_parallel_workers=4)
        """
        config_dict = self._config.model_dump()

        for key, value in kwargs.items():
            parts = key.split("_")
            if len(parts) < 2:
                continue

            section = parts[0]
            setting = "_".join(parts[1:])

            if section not in config_dict:
                config_dict[section] = {}
            config_dict[section][setting] = value

        try:
            self._config = AgentConfig(**config_dict)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration update failed: {e}") from e

    def get_profile(self) -> str:
        """Get current profile name."""
        return self._profile

    def set_profile(self, profile: str) -> None:
        """
        Set configuration profile.

        Args:
            profile: Profile name (dev, test, prod, ci, or custom profile)

        Raises:
            ConfigError: If profile is not valid
        """
        # Get all valid profiles (built-in + custom)
        valid_profiles = PROFILES + self._get_custom_profiles()

        if profile not in valid_profiles:
            raise ConfigError(
                f"Invalid profile: {profile}. "
                f"Valid profiles: {valid_profiles}"
            )

        self._profile = profile
        self.reload()

    def list_profiles(self) -> dict[str, list[str]]:
        """
        List all available profiles.

        Returns:
            Dictionary with 'built_in' and 'custom' profile lists
        """
        return {
            "built_in": PROFILES,
            "custom": self._get_custom_profiles(),
        }

    # =========================================================================
    # Environment Management
    # =========================================================================

    def get_active_environment(self) -> str | None:
        """
        Get the currently active environment name.

        Returns:
            Environment name if active, None otherwise
        """
        return self._config.active_environment

    def list_environments(self) -> list[str]:
        """
        List all available environments in the configuration.

        Returns:
            List of environment names
        """
        return self._config.list_environments()

    def use_environment(self, env_name: str) -> AgentConfig:
        """
        Switch to a specific environment configuration.

        Args:
            env_name: Name of the environment to use (e.g., 'dev', 'prod')

        Returns:
            New AgentConfig with environment overrides applied

        Raises:
            ConfigError: If environment not found
        """
        try:
            return self._config.with_environment(env_name)
        except ValueError as e:
            raise ConfigError(str(e)) from e

    def add_environment(
        self,
        env_name: str,
        base_url: str | None = None,
        browser: str | None = None,
        headless: bool | None = None,
        parallel_workers: int | None = None,
        timeout: int | None = None,
        screenshots: str | None = None,
        video: bool | None = None,
        log_level: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """
        Add or update an environment configuration.

        Args:
            env_name: Name of the environment
            base_url: Override base URL
            browser: Override browser
            headless: Override headless mode
            parallel_workers: Override parallel workers
            timeout: Override timeout (ms)
            screenshots: Override screenshot setting
            video: Override video recording
            log_level: Override log level
            env_vars: Environment variables to set
        """
        from claude_playwright_agent.config.models import EnvironmentConfig, EnvironmentType

        # Map string to enum
        try:
            env_type = EnvironmentType(env_name)
        except ValueError:
            # Use custom value
            env_type = EnvironmentType.DEVELOPMENT  # Default, will be overridden

        # Create environment config
        env_config = EnvironmentConfig(
            name=env_type,
            base_url=base_url,
            browser=browser,
            headless=headless,
            parallel_workers=parallel_workers,
            timeout=timeout,
            screenshots=screenshots,
            video=video,
            log_level=log_level,
            env_vars=env_vars or {},
        )

        # Add to configuration
        config_dict = self._config.model_dump()
        if "environments" not in config_dict:
            config_dict["environments"] = {}
        config_dict["environments"][env_name] = env_config.model_dump()

        # Recreate config
        self._config = AgentConfig(**config_dict)

    def remove_environment(self, env_name: str) -> None:
        """
        Remove an environment configuration.

        Args:
            env_name: Name of the environment to remove

        Raises:
            ConfigError: If environment not found
        """
        if env_name not in self._config.environments:
            raise ConfigError(f"Environment '{env_name}' not found")

        config_dict = self._config.model_dump()
        del config_dict["environments"][env_name]

        self._config = AgentConfig(**config_dict)

    # =========================================================================
    # Configuration Export
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config.model_dump()

    def to_yaml(self) -> str:
        """Export configuration as YAML string."""
        return self._config.model_dump_yaml()

    # =========================================================================
    # Class Methods
    # =========================================================================

    @classmethod
    def create_default_config(cls, project_path: str | Path) -> "ConfigManager":
        """
        Create a ConfigManager with default configuration.

        Args:
            project_path: Path to project root

        Returns:
            ConfigManager instance with default configuration
        """
        manager = cls(project_path, profile="default")
        manager.save()
        return manager

    @classmethod
    def from_file(cls, path: str | Path) -> "ConfigManager":
        """
        Create a ConfigManager from a configuration file.

        Args:
            path: Path to configuration file

        Returns:
            ConfigManager instance
        """
        path = Path(path)
        project_path = path.parent.parent
        return cls(project_path)
