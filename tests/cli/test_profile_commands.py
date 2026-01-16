"""
Tests for profile management CLI commands.
"""

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner


class TestProfileCommands:
    """Test profile command group."""

    def test_profile_group_exists(self):
        """Test that profile command group is registered."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "--help"])
        assert result.exit_code == 0
        assert "Advanced profile management commands" in result.output

    def test_profile_list(self):
        """Test listing all profiles."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "list"])
        assert result.exit_code == 0
        assert "Available Profiles" in result.output
        assert "Built-in" in result.output
        # Built-in profiles should be listed
        assert "default" in result.output
        assert "dev" in result.output
        assert "test" in result.output
        assert "prod" in result.output
        assert "ci" in result.output

    def test_profile_list_json(self):
        """Test listing profiles in JSON format."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "built_in" in data
        assert "custom" in data
        assert "total" in data
        assert len(data["built_in"]) == 5  # default, dev, test, prod, ci

    def test_profile_create_custom(self):
        """Test creating a custom profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                "profile", "create", "my-custom",
                "--extends", "dev",
                "--description", "My custom profile",
            ])
            assert result.exit_code == 0
            assert "Profile 'my-custom' created successfully" in result.output

            # Verify profile file exists
            profile_file = Path.cwd() / ".cpa" / "profiles" / "my-custom.yaml"
            assert profile_file.exists()

            # Verify profile content
            with open(profile_file) as f:
                config = yaml.safe_load(f)
                assert config["name"] == "my-custom"
                assert config["extends"] == "dev"
                assert config["description"] == "My custom profile"

    def test_profile_create_conflicts_builtin(self):
        """Test that creating profile with built-in name fails."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "profile", "create", "dev",
        ])
        assert result.exit_code == 1
        assert "conflicts with built-in profile" in result.output

    def test_profile_show_builtin(self):
        """Test showing a built-in profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "show", "dev"])
        assert result.exit_code == 0
        assert "Profile: dev" in result.output
        # Should show framework config
        assert "framework" in result.output.lower()

    def test_profile_show_custom(self):
        """Test showing a custom profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # First create a profile
            runner.invoke(cli, [
                "profile", "create", "test-profile",
                "--extends", "dev",
            ])

            # Show the profile
            result = runner.invoke(cli, [
                "profile", "show", "test-profile",
            ])
            assert result.exit_code == 0
            assert "Profile: test-profile" in result.output

    def test_profile_validate_builtin(self):
        """Test validating a built-in profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "validate", "dev"])
        assert result.exit_code == 0
        assert "Profile 'dev' is valid" in result.output

    def test_profile_validate_custom(self):
        """Test validating a custom profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a valid profile
            runner.invoke(cli, [
                "profile", "create", "valid-profile",
                "--extends", "dev",
            ])

            # Validate it
            result = runner.invoke(cli, [
                "profile", "validate", "valid-profile",
            ])
            assert result.exit_code == 0
            assert "Profile 'valid-profile' is valid" in result.output

    def test_profile_delete_custom(self):
        """Test deleting a custom profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a profile
            runner.invoke(cli, [
                "profile", "create", "to-delete",
            ])

            # Delete it
            result = runner.invoke(cli, [
                "profile", "delete", "to-delete",
                "--force",
            ])
            assert result.exit_code == 0
            assert "Profile 'to-delete' deleted" in result.output

            # Verify it's gone
            profile_file = Path.cwd() / ".cpa" / "profiles" / "to-delete.yaml"
            assert not profile_file.exists()

    def test_profile_delete_builtin_fails(self):
        """Test that deleting built-in profile fails."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "profile", "delete", "dev",
            "--force",
        ])
        assert result.exit_code == 1
        assert "Cannot delete built-in profile" in result.output

    def test_profile_export_import(self):
        """Test exporting and importing a profile."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            export_file = Path("exported.yaml")

            # Export dev profile
            result = runner.invoke(cli, [
                "profile", "export", "dev", str(export_file),
            ])
            assert result.exit_code == 0
            assert export_file.exists()

            # Import as new profile
            result = runner.invoke(cli, [
                "profile", "import", str(export_file),
                "--name", "imported-profile",
            ])
            assert result.exit_code == 0
            assert "Profile imported as 'imported-profile'" in result.output

            # Verify imported profile exists
            profile_file = Path.cwd() / ".cpa" / "profiles" / "imported-profile.yaml"
            assert profile_file.exists()

    def test_profile_diff(self):
        """Test comparing two profiles."""
        from claude_playwright_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["profile", "diff", "dev", "test"])
        assert result.exit_code == 0
        assert "Diff: dev vs test" in result.output


class TestProfileConfigIntegration:
    """Test profile integration with ConfigManager."""

    def test_config_manager_lists_custom_profiles(self):
        """Test that ConfigManager can list custom profiles."""
        from claude_playwright_agent.config import ConfigManager

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a custom profile
            from claude_playwright_agent.cli import cli
            runner.invoke(cli, [
                "profile", "create", "custom-1",
                "--extends", "dev",
            ])

            # Verify ConfigManager sees it
            config = ConfigManager(Path.cwd())
            profiles = config.list_profiles()
            assert "custom-1" in profiles["custom"]
            assert len(profiles["built_in"]) == 5

    def test_config_manager_loads_custom_profile(self):
        """Test that ConfigManager can load a custom profile."""
        from claude_playwright_agent.config import ConfigManager

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a custom profile
            from claude_playwright_agent.cli import cli
            runner.invoke(cli, [
                "profile", "create", "custom-2",
                "--extends", "dev",
            ])

            # Load using custom profile
            config = ConfigManager(Path.cwd(), profile="custom-2")
            # Should have loaded successfully
            assert config.get_profile() == "custom-2"
            # Should inherit dev settings
            assert config.browser.headless is False  # dev has headless=False
