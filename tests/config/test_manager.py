"""
Comprehensive tests for ConfigManager and configuration models.

Tests cover:
- Configuration model validation
- ConfigManager operations
- Profile loading
- Environment variable overrides
- Configuration merging
- Configuration export/import
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from claude_playwright_agent.config import (
    AIConfig,
    AgentConfig,
    BrowserConfig,
    BrowserType,
    ConfigError,
    ConfigManager,
    ConfigValidationError,
    ExecutionConfig,
    FrameworkConfig,
    FrameworkType,
    LoggingConfig,
    PROFILES,
    RecordingConfig,
    ReportingConfig,
    ReportingFormat,
    SkillConfig,
)
from claude_playwright_agent.config.manager import ProfileConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def config_manager(temp_project_dir: Path) -> ConfigManager:
    """Create a ConfigManager instance for testing."""
    return ConfigManager(temp_project_dir, profile="default")


@pytest.fixture
def config_file_content() -> str:
    """Sample configuration file content."""
    return """
framework:
  bdd_framework: behave
  language: python
  template: advanced
  base_url: https://example.com
  default_timeout: 60000

browser:
  browser: chromium
  headless: true
  viewport_width: 1920
  viewport_height: 1080
  slow_mo: 50

execution:
  parallel_workers: 4
  retry_failed: 2
  fail_fast: false
  self_healing: true

recording:
  auto_parse: true
  generate_page_objects: true
  deduplicate_elements: true

reporting:
  formats:
    - html
    - json
  output_dir: reports
  include_ai_analysis: true

ai:
  model: claude-3-5-sonnet-20241022
  max_tokens: 16000
  temperature: 0.5
  enable_caching: true

logging:
  level: DEBUG
  format: text
  console: true
"""


# =============================================================================
# Configuration Model Tests
# =============================================================================


class TestFrameworkConfig:
    """Tests for FrameworkConfig model."""

    def test_default_values(self) -> None:
        """Test default framework configuration."""
        config = FrameworkConfig()

        assert config.bdd_framework == FrameworkType.BEHAVE
        assert config.language == "python"
        assert config.template == "basic"
        assert config.base_url == "http://localhost:8000"
        assert config.default_timeout == 30000

    def test_custom_values(self) -> None:
        """Test custom framework configuration."""
        config = FrameworkConfig(
            bdd_framework=FrameworkType.PYTEST_BDD,
            template="advanced",
            base_url="https://example.com",
            default_timeout=60000,
        )

        assert config.bdd_framework == FrameworkType.PYTEST_BDD
        assert config.template == "advanced"
        assert config.base_url == "https://example.com"
        assert config.default_timeout == 60000

    def test_invalid_template_raises_error(self) -> None:
        """Test that invalid template raises validation error."""
        with pytest.raises(ValidationError):
            FrameworkConfig(template="invalid_template")

    def test_timeout_bounds(self) -> None:
        """Test timeout bounds validation."""
        # Valid bounds
        FrameworkConfig(default_timeout=1000)
        FrameworkConfig(default_timeout=300000)

        # Invalid bounds
        with pytest.raises(ValidationError):
            FrameworkConfig(default_timeout=500)

        with pytest.raises(ValidationError):
            FrameworkConfig(default_timeout=500000)


class TestBrowserConfig:
    """Tests for BrowserConfig model."""

    def test_default_values(self) -> None:
        """Test default browser configuration."""
        config = BrowserConfig()

        assert config.browser == BrowserType.CHROMIUM
        assert config.headless is True
        assert config.viewport_width == 1280
        assert config.viewport_height == 720

    def test_all_browsers(self) -> None:
        """Test all browser types."""
        for browser_type in BrowserType:
            config = BrowserConfig(browser=browser_type)
            assert config.browser == browser_type

    def test_invalid_timeout_raises_error(self) -> None:
        """Test that invalid slow_mo raises validation error."""
        with pytest.raises(ValidationError):
            BrowserConfig(slow_mo=-1)

        with pytest.raises(ValidationError):
            BrowserConfig(slow_mo=10000)


class TestExecutionConfig:
    """Tests for ExecutionConfig model."""

    def test_default_values(self) -> None:
        """Test default execution configuration."""
        config = ExecutionConfig()

        assert config.parallel_workers == 1
        assert config.retry_failed == 0
        assert config.fail_fast is False
        assert config.self_healing is True

    def test_parallel_workers_bounds(self) -> None:
        """Test parallel workers bounds validation."""
        ExecutionConfig(parallel_workers=1)
        ExecutionConfig(parallel_workers=16)

        with pytest.raises(ValidationError):
            ExecutionConfig(parallel_workers=0)

        with pytest.raises(ValidationError):
            ExecutionConfig(parallel_workers=20)


class TestRecordingConfig:
    """Tests for RecordingConfig model."""

    def test_default_values(self) -> None:
        """Test default recording configuration."""
        config = RecordingConfig()

        assert config.auto_parse is True
        assert config.generate_page_objects is True
        assert config.deduplicate_elements is True


class TestReportingConfig:
    """Tests for ReportingConfig model."""

    def test_default_values(self) -> None:
        """Test default reporting configuration."""
        config = ReportingConfig()

        assert config.formats == [ReportingFormat.HTML]
        assert config.output_dir == "reports"
        assert config.include_ai_analysis is True

    def test_multiple_formats(self) -> None:
        """Test multiple reporting formats."""
        config = ReportingConfig(
            formats=[ReportingFormat.HTML, ReportingFormat.JSON, ReportingFormat.XML]
        )

        assert len(config.formats) == 3
        assert ReportingFormat.HTML in config.formats


class TestAIConfig:
    """Tests for AIConfig model."""

    def test_default_values(self) -> None:
        """Test default AI configuration."""
        config = AIConfig()

        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.enable_caching is True

    def test_temperature_bounds(self) -> None:
        """Test temperature bounds validation."""
        AIConfig(temperature=0.0)
        AIConfig(temperature=1.0)

        with pytest.raises(ValidationError):
            AIConfig(temperature=-0.1)

        with pytest.raises(ValidationError):
            AIConfig(temperature=1.1)


class TestLoggingConfig:
    """Tests for LoggingConfig model."""

    def test_default_values(self) -> None:
        """Test default logging configuration."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "text"
        assert config.console is True


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_default_values(self) -> None:
        """Test default agent configuration."""
        config = AgentConfig()

        assert isinstance(config.framework, FrameworkConfig)
        assert isinstance(config.browser, BrowserConfig)
        assert isinstance(config.execution, ExecutionConfig)

    def test_all_sections(self) -> None:
        """Test that all configuration sections are present."""
        config = AgentConfig()

        assert hasattr(config, "framework")
        assert hasattr(config, "browser")
        assert hasattr(config, "execution")
        assert hasattr(config, "recording")
        assert hasattr(config, "reporting")
        assert hasattr(config, "skills")
        assert hasattr(config, "ai")
        assert hasattr(config, "logging")

    def test_export_to_yaml(self) -> None:
        """Test exporting configuration to YAML."""
        config = AgentConfig(
            framework=FrameworkConfig(template="advanced"),
            browser=BrowserConfig(headless=False),
        )

        yaml_str = config.model_dump_yaml()

        assert "framework:" in yaml_str
        assert "browser:" in yaml_str
        assert "advanced" in yaml_str

    def test_invalid_log_level_raises_error(self) -> None:
        """Test that invalid log level raises validation error."""
        with pytest.raises(ValidationError):
            AgentConfig(
                logging=LoggingConfig(level="INVALID")
            )


# =============================================================================
# ConfigManager Tests
# =============================================================================


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_initialization(self, temp_project_dir: Path) -> None:
        """Test ConfigManager initialization."""
        manager = ConfigManager(temp_project_dir)

        assert manager.framework.bdd_framework == FrameworkType.BEHAVE
        assert manager.browser.browser == BrowserType.CHROMIUM

    def test_profile_loading(self, temp_project_dir: Path) -> None:
        """Test loading different profiles."""
        # Dev profile
        dev_manager = ConfigManager(temp_project_dir, profile="dev")
        assert dev_manager.browser.headless is False
        assert dev_manager.logging.level == "DEBUG"

        # Test profile
        test_manager = ConfigManager(temp_project_dir, profile="test")
        assert test_manager.execution.parallel_workers == 4
        assert test_manager.framework.bdd_framework == FrameworkType.PYTEST_BDD

        # Prod profile
        prod_manager = ConfigManager(temp_project_dir, profile="prod")
        assert prod_manager.execution.parallel_workers == 8
        assert prod_manager.logging.level == "WARNING"

    def test_all_profiles(self, temp_project_dir: Path) -> None:
        """Test that all defined profiles can be loaded."""
        for profile in PROFILES:
            manager = ConfigManager(temp_project_dir, profile=profile)
            assert manager.get_profile() == profile

    def test_invalid_profile_raises_error(self, temp_project_dir: Path) -> None:
        """Test that invalid profile raises error."""
        with pytest.raises(ConfigError, match="Invalid profile"):
            ConfigManager(temp_project_dir, profile="invalid_profile")

    def test_get_config_sections(self, config_manager: ConfigManager) -> None:
        """Test getting configuration sections."""
        assert isinstance(config_manager.framework, FrameworkConfig)
        assert isinstance(config_manager.browser, BrowserConfig)
        assert isinstance(config_manager.execution, ExecutionConfig)
        assert isinstance(config_manager.recording, RecordingConfig)
        assert isinstance(config_manager.reporting, ReportingConfig)
        assert isinstance(config_manager.skills, SkillConfig)
        assert isinstance(config_manager.ai, AIConfig)
        assert isinstance(config_manager.logging, LoggingConfig)

    def test_get_full_config(self, config_manager: ConfigManager) -> None:
        """Test getting full configuration."""
        config = config_manager.config

        assert isinstance(config, AgentConfig)
        assert config.framework.bdd_framework == FrameworkType.BEHAVE


# =============================================================================
# Configuration File Tests
# =============================================================================


class TestConfigurationFile:
    """Tests for configuration file operations."""

    def test_save_config(self, temp_project_dir: Path) -> None:
        """Test saving configuration to file."""
        manager = ConfigManager(temp_project_dir)
        manager.save()

        config_file = temp_project_dir / ".cpa" / "config.yaml"
        assert config_file.exists()

        # Verify content
        content = config_file.read_text()
        assert "framework:" in content
        assert "browser:" in content

    def test_load_from_file(self, temp_project_dir: Path, config_file_content: str) -> None:
        """Test loading configuration from file."""
        # Write configuration file
        config_dir = temp_project_dir / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(config_file_content)

        # Load and verify
        manager = ConfigManager(temp_project_dir)

        assert manager.framework.template == "advanced"
        assert manager.framework.base_url == "https://example.com"
        assert manager.framework.default_timeout == 60000
        assert manager.browser.viewport_width == 1920
        assert manager.execution.parallel_workers == 4

    def test_invalid_config_raises_error(self, temp_project_dir: Path) -> None:
        """Test that invalid configuration raises error."""
        # Write invalid configuration
        config_dir = temp_project_dir / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
framework:
  bdd_framework: invalid_framework
  template: invalid_template
""")

        with pytest.raises(ConfigValidationError, match="validation"):
            ConfigManager(temp_project_dir)

    def test_reload_config(self, temp_project_dir: Path, config_file_content: str) -> None:
        """Test reloading configuration."""
        manager = ConfigManager(temp_project_dir)
        original_timeout = manager.framework.default_timeout

        # Write new config file
        config_dir = temp_project_dir / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(config_file_content)

        # Reload and verify
        manager.reload()
        assert manager.framework.default_timeout == 60000
        assert manager.framework.default_timeout != original_timeout


# =============================================================================
# Configuration Update Tests
# =============================================================================


class TestConfigurationUpdate:
    """Tests for configuration updates."""

    def test_update_single_value(self, config_manager: ConfigManager) -> None:
        """Test updating a single configuration value."""
        original_headless = config_manager.browser.headless

        config_manager.update(browser_headless=False)

        assert config_manager.browser.headless != original_headless
        assert config_manager.browser.headless is False

    def test_update_multiple_values(self, config_manager: ConfigManager) -> None:
        """Test updating multiple configuration values."""
        config_manager.update(
            browser_headless=False,
            execution_parallel_workers=8,
            logging_level="DEBUG"
        )

        assert config_manager.browser.headless is False
        assert config_manager.execution.parallel_workers == 8
        assert config_manager.logging.level == "DEBUG"

    def test_update_with_invalid_value_raises_error(self, config_manager: ConfigManager) -> None:
        """Test that updating with invalid value raises error."""
        with pytest.raises(ConfigValidationError):
            config_manager.update(execution_parallel_workers=50)  # Exceeds max


# =============================================================================
# Environment Variable Override Tests
# =============================================================================


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_env_override_headless(self, temp_project_dir: Path) -> None:
        """Test environment override for browser headless."""
        with patch.dict(os.environ, {"CPA_BROWSER__HEADLESS": "false"}):
            manager = ConfigManager(temp_project_dir)
            assert manager.browser.headless is False

    def test_env_override_parallel_workers(self, temp_project_dir: Path) -> None:
        """Test environment override for parallel workers."""
        with patch.dict(os.environ, {"CPA_EXECUTION__PARALLEL_WORKERS": "8"}):
            manager = ConfigManager(temp_project_dir)
            assert manager.execution.parallel_workers == 8

    def test_env_override_log_level(self, temp_project_dir: Path) -> None:
        """Test environment override for log level."""
        with patch.dict(os.environ, {"CPA_LOGGING__LEVEL": "DEBUG"}):
            manager = ConfigManager(temp_project_dir)
            assert manager.logging.level == "DEBUG"

    def test_env_override_base_url(self, temp_project_dir: Path) -> None:
        """Test environment override for base URL."""
        with patch.dict(os.environ, {"CPA_FRAMEWORK__BASE_URL": "https://test.example.com"}):
            manager = ConfigManager(temp_project_dir)
            assert manager.framework.base_url == "https://test.example.com"

    def test_env_override_with_file_config(self, temp_project_dir: Path, config_file_content: str) -> None:
        """Test that env overrides take precedence over file config."""
        # Write config file
        config_dir = temp_project_dir / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(config_file_content)

        # Apply env override
        with patch.dict(os.environ, {"CPA_BROWSER__HEADLESS": "false"}):
            manager = ConfigManager(temp_project_dir)
            # File says true, env says false - env should win
            assert manager.browser.headless is False


# =============================================================================
# Configuration Export Tests
# =============================================================================


class TestConfigurationExport:
    """Tests for configuration export."""

    def test_to_dict(self, config_manager: ConfigManager) -> None:
        """Test exporting configuration as dictionary."""
        config_dict = config_manager.to_dict()

        assert isinstance(config_dict, dict)
        assert "framework" in config_dict
        assert "browser" in config_dict
        assert "execution" in config_dict

    def test_to_yaml(self, config_manager: ConfigManager) -> None:
        """Test exporting configuration as YAML string."""
        yaml_str = config_manager.to_yaml()

        assert isinstance(yaml_str, str)
        assert "framework:" in yaml_str
        assert "browser:" in yaml_str
        assert "execution:" in yaml_str


# =============================================================================
# Profile Config Tests
# =============================================================================


class TestProfileConfig:
    """Tests for ProfileConfig."""

    def test_get_profile_config(self) -> None:
        """Test getting profile configuration."""
        default_config = ProfileConfig.get_profile_config("default")

        assert isinstance(default_config, dict)
        assert "framework" in default_config
        assert "browser" in default_config

    def test_all_profiles_have_config(self) -> None:
        """Test that all defined profiles have configuration."""
        for profile in PROFILES:
            config = ProfileConfig.get_profile_config(profile)
            assert isinstance(config, dict)
            assert len(config) > 0

    def test_invalid_profile_returns_default(self) -> None:
        """Test that invalid profile returns default configuration."""
        config = ProfileConfig.get_profile_config("invalid_profile")

        assert config == ProfileConfig.get_profile_config("default")


# =============================================================================
# ConfigManager Class Methods
# =============================================================================


class TestConfigManagerClassMethods:
    """Tests for ConfigManager class methods."""

    def test_create_default_config(self, temp_project_dir: Path) -> None:
        """Test creating default configuration."""
        manager = ConfigManager.create_default_config(temp_project_dir)

        assert manager.framework.bdd_framework == FrameworkType.BEHAVE

        config_file = temp_project_dir / ".cpa" / "config.yaml"
        assert config_file.exists()

    def test_from_file(self, temp_project_dir: Path, config_file_content: str) -> None:
        """Test creating ConfigManager from file."""
        # Write config file
        config_dir = temp_project_dir / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(config_file_content)

        # Create manager from file
        manager = ConfigManager.from_file(config_file)

        assert manager.framework.template == "advanced"
        assert manager.framework.default_timeout == 60000


# =============================================================================
# Integration Tests
# =============================================================================


class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def test_full_configuration_workflow(self, temp_project_dir: Path, config_file_content: str) -> None:
        """Test complete configuration workflow."""
        # 1. Create default config
        manager = ConfigManager.create_default_config(temp_project_dir)
        assert manager.framework.template == "basic"

        # 2. Write custom config file
        config_file = temp_project_dir / ".cpa" / "config.yaml"
        config_file.write_text(config_file_content)

        # 3. Reload and verify custom values
        manager.reload()
        assert manager.framework.template == "advanced"
        assert manager.execution.parallel_workers == 4

        # 4. Update specific values
        manager.update(browser_headless=False, logging_level="DEBUG")
        assert manager.browser.headless is False
        assert manager.logging.level == "DEBUG"

        # 5. Export and verify
        yaml_str = manager.to_yaml()
        assert "advanced" in yaml_str
        assert "DEBUG" in yaml_str
