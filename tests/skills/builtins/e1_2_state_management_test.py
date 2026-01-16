"""Unit tests for E1.2 - State Management skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from claude_playwright_agent.skills.builtins.e1_2_state_management import (
    StateManagementAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestStateManagementAgent:
    """Test suite for StateManagementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return StateManagementAgent()

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock StateManager."""
        manager = MagicMock()
        manager.add_recording = MagicMock(return_value="rec_001")
        manager.add_scenario = MagicMock(return_value="scen_001")
        manager.add_test_run = MagicMock(return_value="run_001")
        manager.get_recordings = MagicMock(return_value=[])
        manager.get_scenario = MagicMock(return_value=None)
        manager.get_all_scenarios = MagicMock(return_value=[])
        manager.get_test_runs = MagicMock(return_value=[])
        manager.create_backup = MagicMock(return_value=Path("/tmp/backup.zip"))
        manager.restore_backup = MagicMock()
        manager.get_project_metadata = MagicMock(
            return_value=MagicMock(name="TestProject", version="1.0.0")
        )
        manager.update_project_metadata = MagicMock()
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
        assert agent.name == "e1_2_state_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes without StateManager."""
        assert hasattr(agent, "_state_manager")
        assert agent._state_manager is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_recording(self, agent, mock_state_manager, temp_project_path):
        """Test adding a recording to state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "recording_path": str(temp_project_path / "test_recording.js"),
            "recording_data": {
                "name": "Test Recording",
                "actions": [{"action": "click"}],
            },
        }

        result = await agent.run("add_recording", context)

        assert "added to state" in result.lower()
        assert "rec_001" in result
        mock_state_manager.add_recording.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_recording_missing_path(self, agent, mock_state_manager, temp_project_path):
        """Test adding a recording without path."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            # Missing recording_path
        }

        result = await agent.run("add_recording", context)

        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_scenario(self, agent, mock_state_manager, temp_project_path):
        """Test adding a scenario to state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "scenario_data": {
                "feature": "Authentication",
                "scenario_name": "User Login",
                "steps": [{"keyword": "Given", "text": "user is on login page"}],
                "recording_id": "rec_001",
                "tags": ["smoke"],
            },
        }

        result = await agent.run("add_scenario", context)

        assert "added to state" in result.lower()
        assert "scen_001" in result
        mock_state_manager.add_scenario.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_scenario_missing_data(self, agent, mock_state_manager, temp_project_path):
        """Test adding a scenario without data."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "scenario_data": {},
        }

        result = await agent.run("add_scenario", context)

        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_test_run(self, agent, mock_state_manager, temp_project_path):
        """Test adding a test run to state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "run_data": {
                "total": 10,
                "passed": 8,
                "failed": 1,
                "skipped": 1,
                "duration": 5000,
            },
        }

        result = await agent.run("add_test_run", context)

        assert "added to state" in result.lower()
        assert "run_001" in result
        mock_state_manager.add_test_run.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_recordings(self, agent, mock_state_manager, temp_project_path):
        """Test getting recordings from state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_recordings", context)

        assert "recording" in result.lower()
        mock_state_manager.get_recordings.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_scenarios_all(self, agent, mock_state_manager, temp_project_path):
        """Test getting all scenarios from state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_scenarios", context)

        assert "scenario" in result.lower()
        mock_state_manager.get_all_scenarios.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_scenarios_by_id(self, agent, mock_state_manager, temp_project_path):
        """Test getting a specific scenario from state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "scenario_id": "scen_001",
        }

        result = await agent.run("get_scenarios", context)

        assert "scenario" in result.lower()
        mock_state_manager.get_scenario.assert_called_once_with("scen_001")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_test_runs(self, agent, mock_state_manager, temp_project_path):
        """Test getting test runs from state."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "limit": 50,
        }

        result = await agent.run("get_test_runs", context)

        assert "test run" in result.lower()
        mock_state_manager.get_test_runs.assert_called_once_with(limit=50)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_backup(self, agent, mock_state_manager, temp_project_path):
        """Test creating a state backup."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("create_backup", context)

        assert "backup created" in result.lower()
        mock_state_manager.create_backup.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_restore_backup(self, agent, mock_state_manager, temp_project_path):
        """Test restoring a state backup."""
        agent._state_manager = mock_state_manager

        backup_path = str(temp_project_path / "backups" / "backup.zip")
        context = {
            "project_path": str(temp_project_path),
            "backup_path": backup_path,
        }

        result = await agent.run("restore_backup", context)

        assert "restored from" in result.lower()
        mock_state_manager.restore_backup.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_restore_backup_missing_path(self, agent, mock_state_manager, temp_project_path):
        """Test restoring a backup without path."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            # Missing backup_path
        }

        result = await agent.run("restore_backup", context)

        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_project_metadata(self, agent, mock_state_manager, temp_project_path):
        """Test getting project metadata."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_project_metadata", context)

        assert "testproject" in result.lower()
        assert "v1.0.0" in result
        mock_state_manager.get_project_metadata.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_update_project_metadata(self, agent, mock_state_manager, temp_project_path):
        """Test updating project metadata."""
        agent._state_manager = mock_state_manager

        context = {
            "project_path": str(temp_project_path),
            "name": "Updated Project",
            "framework_type": "behave",
        }

        result = await agent.run("update_project_metadata", context)

        assert "updated" in result.lower()
        mock_state_manager.update_project_metadata.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent, temp_project_path):
        """Test running agent with invalid task type."""
        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_state_manager(self, agent, mock_state_manager):
        """Test getting the StateManager instance."""
        agent._state_manager = mock_state_manager

        result = agent.get_state_manager()

        assert result == mock_state_manager
