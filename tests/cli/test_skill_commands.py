"""
Tests for the CLI skill commands.

Tests cover:
- list-skills command
- add-skill command
- remove-skill command
- enable-skill command
- disable-skill command
- skill-info command
- validate-skill command
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from claude_playwright_agent.cli.skill_commands import (
    add_skill_command,
    disable_skill_command,
    enable_skill_command,
    list_skills_command,
    register_skill_commands,
    remove_skill_command,
    skill_info_command,
    skills_group,
    validate_skill_command,
)
from claude_playwright_agent.skills import Skill, get_registry, register_skill


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_manifest(tmp_path: Path) -> Path:
    """Create a sample skill manifest file."""
    manifest_path = tmp_path / "skill.yaml"
    manifest_data = {
        "name": "test-skill",
        "version": "1.0.0",
        "description": "A test skill",
        "author": "Test Author",
        "license": "MIT",
        "tags": ["testing", "example"],
    }

    manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")
    return manifest_path


@pytest.fixture
def clean_registry() -> None:
    """Clean the global registry before each test."""
    get_registry().clear()
    yield
    get_registry().clear()


# =============================================================================
# Skills Group Tests
# =============================================================================


class TestSkillsGroup:
    """Tests for skills command group."""

    def test_skills_group_exists(self) -> None:
        """Test that skills group is created."""
        assert skills_group is not None
        assert skills_group.name == "skills"


# =============================================================================
# List Skills Command Tests
# =============================================================================


class TestListSkillsCommand:
    """Tests for list-skills command."""

    def test_list_empty(self, runner: CliRunner, clean_registry: None) -> None:
        """Test listing when no skills are registered."""
        result = runner.invoke(list_skills_command, [])

        assert result.exit_code == 0
        assert "No skills found" in result.output

    def test_list_skills(self, runner: CliRunner, clean_registry: None) -> None:
        """Test listing skills."""
        # Register some skills
        skill1 = Skill("skill1", "1.0", "First skill", enabled=True)
        skill2 = Skill("skill2", "2.0", "Second skill", enabled=False)
        register_skill(skill1)
        register_skill(skill2)

        # Test listing only enabled
        result = runner.invoke(list_skills_command, [])
        assert result.exit_code == 0
        assert "skill1" in result.output
        assert "skill2" not in result.output

        # Test listing all
        result = runner.invoke(list_skills_command, ["--all"])
        assert result.exit_code == 0
        assert "skill1" in result.output
        assert "skill2" in result.output

    def test_list_json_output(self, runner: CliRunner, clean_registry: None) -> None:
        """Test JSON output."""
        skill = Skill("test", "1.0", "Test", enabled=True)
        register_skill(skill)

        result = runner.invoke(list_skills_command, ["--json"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["total"] == 1
        assert data["skills"][0]["name"] == "test"


# =============================================================================
# Add Skill Command Tests
# =============================================================================


class TestAddSkillCommand:
    """Tests for add-skill command."""

    def test_add_skill_from_manifest(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding skill from manifest file."""
        result = runner.invoke(add_skill_command, [str(sample_manifest)])

        assert result.exit_code == 0
        assert "Added skill" in result.output
        assert "test-skill" in result.output

        # Verify skill was registered
        skill = get_registry().get("test-skill")
        assert skill is not None
        assert skill.version == "1.0.0"

    def test_add_skill_from_directory(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding skill from directory."""
        result = runner.invoke(add_skill_command, [str(sample_manifest.parent)])

        assert result.exit_code == 0
        assert "Added skill" in result.output

    def test_add_skill_duplicate(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding duplicate skill without force."""
        # Add skill first time
        runner.invoke(add_skill_command, [str(sample_manifest)])

        # Try to add again without force
        result = runner.invoke(add_skill_command, [str(sample_manifest)])

        assert result.exit_code != 0
        assert "already registered" in result.output

    def test_add_skill_force(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding duplicate skill with force flag."""
        # Add skill first time
        runner.invoke(add_skill_command, [str(sample_manifest)])

        # Add again with force
        result = runner.invoke(add_skill_command, [str(sample_manifest), "--force"])

        assert result.exit_code == 0
        assert "Added skill" in result.output

    def test_add_skill_with_name_override(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding skill with custom name."""
        result = runner.invoke(
            add_skill_command,
            [str(sample_manifest), "--name", "custom-name"],
        )

        assert result.exit_code == 0
        assert "custom-name" in result.output

        skill = get_registry().get("custom-name")
        assert skill is not None

    def test_add_skill_disabled(
        self,
        runner: CliRunner,
        sample_manifest: Path,
        clean_registry: None,
    ) -> None:
        """Test adding skill as disabled."""
        result = runner.invoke(
            add_skill_command,
            [str(sample_manifest), "--disabled"],
        )

        assert result.exit_code == 0
        assert "disabled" in result.output.lower()

        skill = get_registry().get("test-skill")
        assert skill.enabled is False

    def test_add_skill_invalid_manifest(
        self,
        runner: CliRunner,
        tmp_path: Path,
        clean_registry: None,
    ) -> None:
        """Test adding skill with invalid manifest."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("name: 123-invalid\nversion: 1.0.0\ndescription: Test")

        result = runner.invoke(add_skill_command, [str(manifest_path)])

        assert result.exit_code != 0
        assert "Invalid manifest" in result.output

    def test_add_skill_nonexistent(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test adding skill from non-existent path."""
        result = runner.invoke(add_skill_command, ["nonexistent.yaml"])

        assert result.exit_code != 0


# =============================================================================
# Remove Skill Command Tests
# =============================================================================


class TestRemoveSkillCommand:
    """Tests for remove-skill command."""

    def test_remove_skill(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test removing a skill."""
        skill = Skill("test", "1.0", "Test")
        register_skill(skill)

        result = runner.invoke(remove_skill_command, ["test", "--force"])

        assert result.exit_code == 0
        assert "Removed skill" in result.output

        assert get_registry().get("test") is None

    def test_remove_skill_nonexistent(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test removing non-existent skill."""
        result = runner.invoke(remove_skill_command, ["nonexistent", "--force"])

        assert result.exit_code != 0
        assert "not registered" in result.output


# =============================================================================
# Enable/Disable Skill Commands Tests
# =============================================================================


class TestEnableDisableSkillCommands:
    """Tests for enable-skill and disable-skill commands."""

    def test_enable_skill(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test enabling a skill."""
        skill = Skill("test", "1.0", "Test", enabled=False)
        register_skill(skill)

        result = runner.invoke(enable_skill_command, ["test"])

        assert result.exit_code == 0
        assert "Enabled skill" in result.output

        assert get_registry().get("test").enabled is True

    def test_enable_nonexistent(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test enabling non-existent skill."""
        result = runner.invoke(enable_skill_command, ["nonexistent"])

        assert result.exit_code != 0
        assert "not registered" in result.output

    def test_disable_skill(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test disabling a skill."""
        skill = Skill("test", "1.0", "Test", enabled=True)
        register_skill(skill)

        result = runner.invoke(disable_skill_command, ["test"])

        assert result.exit_code == 0
        assert "Disabled skill" in result.output

        assert get_registry().get("test").enabled is False


# =============================================================================
# Skill Info Command Tests
# =============================================================================


class TestSkillInfoCommand:
    """Tests for skill-info command."""

    def test_skill_info(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test showing skill info."""
        skill = Skill(
            name="test",
            version="1.0",
            description="Test skill",
            enabled=True,
        )
        register_skill(skill)

        result = runner.invoke(skill_info_command, ["test"])

        assert result.exit_code == 0
        assert "Name: test" in result.output
        assert "Version: 1.0" in result.output
        assert "enabled" in result.output.lower()

    def test_skill_info_json(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test skill info JSON output."""
        skill = Skill("test", "1.0", "Test")
        register_skill(skill)

        result = runner.invoke(skill_info_command, ["test", "--json"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["name"] == "test"
        assert data["version"] == "1.0"

    def test_skill_info_nonexistent(
        self,
        runner: CliRunner,
        clean_registry: None,
    ) -> None:
        """Test info for non-existent skill."""
        result = runner.invoke(skill_info_command, ["nonexistent"])

        assert result.exit_code != 0
        assert "not registered" in result.output


# =============================================================================
# Validate Skill Command Tests
# =============================================================================


class TestValidateSkillCommand:
    """Tests for validate-skill command."""

    def test_validate_valid_manifest(
        self,
        runner: CliRunner,
        sample_manifest: Path,
    ) -> None:
        """Test validating a valid manifest."""
        result = runner.invoke(validate_skill_command, [str(sample_manifest)])

        assert result.exit_code == 0
        assert "Manifest is valid" in result.output
        assert "test-skill" in result.output

    def test_validate_invalid_manifest(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test validating an invalid manifest."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("name: 123-invalid\nversion: 1.0.0")

        result = runner.invoke(validate_skill_command, [str(manifest_path)])

        assert result.exit_code != 0
        assert "Validation failed" in result.output

    def test_validate_directory(
        self,
        runner: CliRunner,
        sample_manifest: Path,
    ) -> None:
        """Test validating skill from directory."""
        result = runner.invoke(
            validate_skill_command,
            [str(sample_manifest.parent)],
        )

        assert result.exit_code == 0
        assert "Manifest is valid" in result.output


# =============================================================================
# Register Commands Tests
# =============================================================================


class TestRegisterSkillCommands:
    """Tests for registering skill commands with CLI."""

    def test_register_commands(self) -> None:
        """Test that register_skill_commands adds commands to CLI group."""
        from claude_playwright_agent.cli import cli

        # Create a mock CLI group
        mock_cli = MagicMock()

        # Register commands
        register_skill_commands(mock_cli)

        # Verify commands were added
        assert mock_cli.add_command.called

        # Check that the commands were added with correct names
        # Get all call args (both positional and keyword)
        all_calls = mock_cli.add_command.call_args_list

        # Extract command names from keyword arguments
        command_names_from_kwargs = []
        for call in all_calls:
            if len(call) > 1 and call[1] and 'name' in call[1]:
                command_names_from_kwargs.append(call[1]['name'])
            elif call[0] and hasattr(call[0][0], 'name'):
                command_names_from_kwargs.append(call[0][0].name)

        # Verify specific commands were registered
        assert "skills" in command_names_from_kwargs
        assert "list-skills" in command_names_from_kwargs
        assert "add-skill" in command_names_from_kwargs
        assert "remove-skill" in command_names_from_kwargs
