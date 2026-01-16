"""Unit tests for E1.3 - Project Initialization skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from claude_playwright_agent.skills.builtins.e1_3_project_initialization import (
    ProjectInitializationAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestProjectInitializationAgent:
    """Test suite for ProjectInitializationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ProjectInitializationAgent()

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
        assert agent.name == "e1_3_project_initialization"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_initialize_project_new(self, agent, temp_project_path):
        """Test initializing a new project."""
        context = {
            "project_path": str(temp_project_path),
            "project_name": "test-project",
            "framework": "behave",
            "template": "basic",
        }

        result = await agent.run("initialize_project", context)

        assert "initialized successfully" in result.lower()
        assert "test-project" in result
        assert (temp_project_path / ".cpa").exists()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_initialize_project_existing(self, agent, temp_project_path):
        """Test initializing an already initialized project."""
        # Create .cpa directory to simulate existing project
        (temp_project_path / ".cpa").mkdir(parents=True, exist_ok=True)

        context = {
            "project_path": str(temp_project_path),
            "project_name": "test-project",
        }

        result = await agent.run("initialize_project", context)

        assert "already initialized" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_directory_structure(self, agent, temp_project_path):
        """Test creating directory structure."""
        context = {
            "project_path": str(temp_project_path),
            "framework": "behave",
        }

        result = await agent.run("create_directory_structure", context)

        assert "directory structure created" in result.lower()
        assert (temp_project_path / ".cpa").exists()
        assert (temp_project_path / "features").exists()
        assert (temp_project_path / "features" / "steps").exists()
        assert (temp_project_path / "pages").exists()
        assert (temp_project_path / "recordings").exists()
        assert (temp_project_path / "reports").exists()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_directory_structure_pytest(self, agent, temp_project_path):
        """Test creating directory structure for pytest-bdd."""
        context = {
            "project_path": str(temp_project_path),
            "framework": "pytest-bdd",
        }

        result = await agent.run("create_directory_structure", context)

        assert "directory structure created" in result.lower()
        assert (temp_project_path / "tests").exists()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_framework_files_behave(self, agent, temp_project_path):
        """Test generating Behave framework files."""
        # Create directories first
        (temp_project_path / "features").mkdir(parents=True, exist_ok=True)
        (temp_project_path / "features" / "steps").mkdir(parents=True, exist_ok=True)

        context = {
            "project_path": str(temp_project_path),
            "framework": "behave",
        }

        result = await agent.run("generate_framework_files", context)

        assert "framework files" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_config_files(self, agent, temp_project_path):
        """Test creating configuration files."""
        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("create_config_files", context)

        assert "config files" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_setup_state(self, agent, temp_project_path):
        """Test setting up state."""
        # Create .cpa directory
        (temp_project_path / ".cpa").mkdir(parents=True, exist_ok=True)

        context = {
            "project_path": str(temp_project_path),
            "project_name": "test-project",
        }

        result = await agent.run("setup_state", context)

        assert "state" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_project_valid(self, agent, temp_project_path):
        """Test validating a valid project."""
        # Create project structure
        (temp_project_path / ".cpa").mkdir(parents=True, exist_ok=True)
        (temp_project_path / "features").mkdir(parents=True, exist_ok=True)

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("validate_project", context)

        assert "valid" in result.lower() or "success" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_project_invalid(self, agent, temp_project_path):
        """Test validating an invalid project."""
        # Empty directory - no .cpa folder
        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("validate_project", context)

        assert "invalid" in result.lower() or "not" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent, temp_project_path):
        """Test running agent with invalid task type."""
        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
