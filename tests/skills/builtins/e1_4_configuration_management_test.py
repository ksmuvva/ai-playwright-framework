"""Unit tests for E1.4 - Configuration Management skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e1_4_configuration_management import (
    ConfigurationManagementAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestConfigurationManagementAgent:
    """Test suite for ConfigurationManagementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ConfigurationManagementAgent()

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock ConfigManager."""
        manager = MagicMock()
        manager.get = MagicMock(return_value="test_value")
        manager.set = MagicMock()
        manager.update = MagicMock()
        manager.validate = MagicMock(return_value=True)
        manager.switch_profile = MagicMock()
        manager.export = MagicMock(return_value=Path("/tmp/config.json"))
        manager.import_config = MagicMock()
        manager.list_profiles = MagicMock(return_value=["default", "dev", "prod"])
        return manager

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert hasattr(agent, "description")
        assert agent.name == "e1_4_configuration_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes without ConfigManager."""
        assert hasattr(agent, "_config_manager")
        assert agent._config_manager is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_config(self, agent, mock_config_manager, temp_project_path):
        """Test getting a configuration value."""
        agent._config_manager = mock_config_manager
        mock_config_manager.get.return_value = "test_value"

        context = {
            "project_path": str(temp_project_path),
            "key": "framework.type",
        }

        result = await agent.run("get_config", context)

        assert "configuration value" in result.lower()
        assert "framework.type" in result.lower()
        mock_config_manager.get.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_config_missing_key(self, agent, mock_config_manager, temp_project_path):
        """Test getting config without key."""
        agent._config_manager = mock_config_manager

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_config", context)

        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_set_config(self, agent, mock_config_manager, temp_project_path):
        """Test setting a configuration value."""
        agent._config_manager = mock_config_manager

        context = {
            "project_path": str(temp_project_path),
            "key": "framework.type",
            "value": "behave",
        }

        result = await agent.run("set_config", context)

        assert "set" in result.lower() or "updated" in result.lower()
        mock_config_manager.set.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_update_config(self, agent, mock_config_manager, temp_project_path):
        """Test updating configuration."""
        agent._config_manager = mock_config_manager

        context = {
            "project_path": str(temp_project_path),
            "updates": {"framework": {"type": "behave"}},
        }

        result = await agent.run("update_config", context)

        assert "updated" in result.lower()
        mock_config_manager.update.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_config_valid(self, agent, mock_config_manager, temp_project_path):
        """Test validating valid configuration."""
        agent._config_manager = mock_config_manager
        mock_config_manager.validate.return_value = []

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("validate_config", context)

        assert "valid" in result.lower() or "no errors" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_config_invalid(self, agent, mock_config_manager, temp_project_path):
        """Test validating invalid configuration."""
        agent._config_manager = mock_config_manager
        mock_config_manager.validate.return_value = ["Error 1", "Error 2"]

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("validate_config", context)

        assert "error" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_switch_profile(self, agent, mock_config_manager, temp_project_path):
        """Test switching configuration profile."""
        agent._config_manager = mock_config_manager

        context = {
            "project_path": str(temp_project_path),
            "profile": "dev",
        }

        result = await agent.run("switch_profile", context)

        assert "switched" in result.lower() or "dev" in result
        mock_config_manager.switch_profile.assert_called_once_with("dev")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_export_config(self, agent, mock_config_manager, temp_project_path):
        """Test exporting configuration."""
        agent._config_manager = mock_config_manager
        mock_config_manager.export.return_value = Path("/tmp/export.json")

        context = {
            "project_path": str(temp_project_path),
            "output_path": "/tmp/export.json",
        }

        result = await agent.run("export_config", context)

        assert "exported" in result.lower()
        mock_config_manager.export.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_import_config(self, agent, mock_config_manager, temp_project_path):
        """Test importing configuration."""
        agent._config_manager = mock_config_manager

        context = {
            "project_path": str(temp_project_path),
            "import_path": "/tmp/config.json",
        }

        result = await agent.run("import_config", context)

        assert "imported" in result.lower()
        mock_config_manager.import_config.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_all_profiles(self, agent, mock_config_manager, temp_project_path):
        """Test getting all profiles."""
        agent._config_manager = mock_config_manager
        mock_config_manager.list_profiles.return_value = ["default", "dev", "prod"]

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_all_profiles", context)

        assert "profile" in result.lower()
        mock_config_manager.list_profiles.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent, temp_project_path):
        """Test running agent with invalid task type."""
        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
