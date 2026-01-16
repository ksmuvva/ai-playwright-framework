"""
Tests for CLI commands.

Tests cover:
- Init command
- Status command
- Config commands
- CLI utility functions
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from claude_playwright_agent.cli import cli, main


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


# =============================================================================
# CLI Main Tests
# =============================================================================


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_cli_version_flag(self, runner: CliRunner) -> None:
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Claude Playwright Agent" in result.output
        assert "init" in result.output
        assert "status" in result.output
        assert "config" in result.output

    def test_cli_no_command(self, runner: CliRunner) -> None:
        """Test CLI without command shows welcome message."""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "Welcome" in result.output


# =============================================================================
# Init Command Tests
# =============================================================================


class TestInitCommand:
    """Tests for the init command."""

    def test_init_basic(self, runner: CliRunner) -> None:
        """Test basic project initialization."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--name", "test-project"])

            assert result.exit_code == 0
            assert "initialized successfully" in result.output.lower()

            # Verify directories were created
            assert Path(".cpa").exists()
            assert Path("features").exists()
            assert Path("pages").exists()
            assert Path("steps").exists()
            assert Path("recordings").exists()
            assert Path("reports").exists()

    def test_init_with_framework(self, runner: CliRunner) -> None:
        """Test initialization with specific framework."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--framework", "pytest-bdd"])

            assert result.exit_code == 0
            assert "pytest-bdd" in result.output.lower()

    def test_init_with_template(self, runner: CliRunner) -> None:
        """Test initialization with specific template."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--template", "advanced"])

            assert result.exit_code == 0
            assert "advanced" in result.output.lower()

    def test_init_with_profile(self, runner: CliRunner) -> None:
        """Test initialization with specific profile."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--profile", "dev"])

            assert result.exit_code == 0
            assert "dev" in result.output.lower()

    def test_init_force(self, runner: CliRunner) -> None:
        """Test force initialization in existing directory."""
        with runner.isolated_filesystem():
            # Initialize first
            runner.invoke(cli, ["init"])

            # Should fail without force
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 1
            assert "already initialized" in result.output.lower()

            # Should succeed with force
            result = runner.invoke(cli, ["init", "--force"])
            assert result.exit_code == 0


# =============================================================================
# Status Command Tests
# =============================================================================


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_new_project(self, runner: CliRunner) -> None:
        """Test status for newly initialized project."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Project Metadata" in result.output
            assert "Statistics" in result.output

    def test_status_with_recordings(self, runner: CliRunner) -> None:
        """Test status showing recordings."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            # Add a recording via state manager
            from claude_playwright_agent.state import StateManager

            state = StateManager(Path.cwd())
            state.add_recording("test_recording", "/path/to/recording.js")

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Recordings" in result.output
            assert "1" in result.output  # Count

    def test_status_nonexistent_project(self, runner: CliRunner) -> None:
        """Test status for non-existent project."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()


# =============================================================================
# Config Command Tests
# =============================================================================


class TestConfigCommands:
    """Tests for config commands."""

    def test_config_show(self, runner: CliRunner) -> None:
        """Test config show command."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "Configuration Profile" in result.output
            assert "Framework" in result.output
            assert "Browser" in result.output
            assert "Execution" in result.output

    def test_config_set_single_value(self, runner: CliRunner) -> None:
        """Test config set with single value."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, ["config", "set", "browser.headless=false"])

            assert result.exit_code == 0
            assert "updated" in result.output.lower()

    def test_config_set_multiple_values(self, runner: CliRunner) -> None:
        """Test config set with multiple values."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, [
                "config", "set",
                "browser.headless=false",
                "execution.parallel_workers=4",
                "logging.level=DEBUG"
            ])

            assert result.exit_code == 0
            assert "updated" in result.output.lower()

    def test_config_set_invalid_format(self, runner: CliRunner) -> None:
        """Test config set with invalid format."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, ["config", "set", "invalid_format"])

            assert result.exit_code == 1
            assert "invalid" in result.output.lower()

    def test_config_validate_valid(self, runner: CliRunner) -> None:
        """Test config validate with valid configuration."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])

            result = runner.invoke(cli, ["config", "validate"])

            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_config_profile_switch(self, runner: CliRunner) -> None:
        """Test switching configuration profile."""
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init", "--profile", "default"])

            result = runner.invoke(cli, ["config", "profile", "dev"])

            assert result.exit_code == 0
            assert "dev" in result.output.lower()

    def test_config_help(self, runner: CliRunner) -> None:
        """Test config command help."""
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "show" in result.output
        assert "set" in result.output
        assert "validate" in result.output
        assert "profile" in result.output


# =============================================================================
# Integration Tests
# =============================================================================


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_full_init_workflow(self, runner: CliRunner) -> None:
        """Test complete init and status workflow."""
        with runner.isolated_filesystem():
            # Initialize project
            init_result = runner.invoke(cli, [
                "init",
                "--name", "integration-test",
                "--framework", "behave",
                "--template", "advanced",
                "--profile", "dev"
            ])
            assert init_result.exit_code == 0

            # Check status
            status_result = runner.invoke(cli, ["status"])
            assert status_result.exit_code == 0
            assert "integration-test" in status_result.output

            # Check config
            config_result = runner.invoke(cli, ["config", "show"])
            assert config_result.exit_code == 0
            assert "behave" in config_result.output
            assert "advanced" in config_result.output

    def test_config_update_workflow(self, runner: CliRunner) -> None:
        """Test configuration update workflow."""
        with runner.isolated_filesystem():
            # Initialize
            runner.invoke(cli, ["init"])

            # Update configuration
            set_result = runner.invoke(cli, [
                "config", "set",
                "browser.headless=false",
                "execution.parallel_workers=8"
            ])
            assert set_result.exit_code == 0

            # Verify updates
            show_result = runner.invoke(cli, ["config", "show"])
            assert show_result.exit_code == 0
            assert "False" in show_result.output
            assert "8" in show_result.output
