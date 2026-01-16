"""Unit tests for E1.5 - Dependency Management skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from claude_playwright_agent.skills.builtins.e1_5_dependency_management import (
    DependencyManagementAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestDependencyManagementAgent:
    """Test suite for DependencyManagementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return DependencyManagementAgent()

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
        assert agent.name == "e1_5_dependency_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_has_core_dependencies(self, agent):
        """Verify agent defines core dependencies."""
        assert hasattr(agent, "CORE_DEPENDENCIES")
        assert "playwright" in agent.CORE_DEPENDENCIES
        assert "click" in agent.CORE_DEPENDENCIES
        assert "rich" in agent.CORE_DEPENDENCIES
        assert "pydantic" in agent.CORE_DEPENDENCIES

    @pytest.mark.unit
    def test_agent_has_framework_dependencies(self, agent):
        """Verify agent defines framework dependencies."""
        assert hasattr(agent, "FRAMEWORK_DEPENDENCIES")
        assert "behave" in agent.FRAMEWORK_DEPENDENCIES
        assert "pytest-bdd" in agent.FRAMEWORK_DEPENDENCIES

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty tracking."""
        assert hasattr(agent, "_installed_packages")
        assert hasattr(agent, "_installed_browsers")
        assert agent._installed_packages == {}
        assert agent._installed_browsers == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_check_dependencies_all_installed(self, agent, temp_project_path):
        """Test checking dependencies when all are installed."""
        # Mock the version check to return installed versions
        agent._get_installed_version = MagicMock(return_value="1.40.0")
        agent._compare_versions = MagicMock(return_value=0)

        context = {
            "project_path": str(temp_project_path),
            "framework": "behave",
        }

        result = await agent.run("check_dependencies", context)

        assert "dependencies" in result.lower()
        # Should indicate all dependencies are met

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_check_dependencies_missing(self, agent, temp_project_path):
        """Test checking dependencies with missing packages."""
        # Mock to return None (not installed)
        agent._get_installed_version = MagicMock(return_value=None)

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("check_dependencies", context)

        assert "dependencies" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_install_dependencies(self, agent, temp_project_path):
        """Test installing dependencies."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            context = {
                "project_path": str(temp_project_path),
                "framework": "behave",
            }

            result = await agent.run("install_dependencies", context)

            assert "dependencies" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_check_browsers(self, agent, temp_project_path):
        """Test checking browser installation."""
        agent._installed_browsers = {"chromium": True, "firefox": False}

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("check_browsers", context)

        assert "browser" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_install_browsers(self, agent, temp_project_path):
        """Test installing browsers."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            context = {
                "project_path": str(temp_project_path),
                "browsers": ["chromium", "firefox"],
            }

            result = await agent.run("install_browsers", context)

            assert "browser" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_requirements(self, agent, temp_project_path):
        """Test generating requirements file."""
        context = {
            "project_path": str(temp_project_path),
            "output_file": "requirements.txt",
            "framework": "behave",
        }

        result = await agent.run("generate_requirements", context)

        assert "requirements" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_update_dependencies(self, agent, temp_project_path):
        """Test updating dependencies."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            context = {
                "project_path": str(temp_project_path),
            }

            result = await agent.run("update_dependencies", context)

            assert "dependencies" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_dependency_status(self, agent, temp_project_path):
        """Test getting dependency status."""
        agent._installed_packages = {"playwright": "1.40.0", "click": "8.0.0"}
        agent._installed_browsers = {"chromium": True}

        context = {
            "project_path": str(temp_project_path),
        }

        result = await agent.run("get_dependency_status", context)

        assert "status" in result.lower()
        assert "playwright" in result.lower()

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
    def test_get_installed_version(self, agent):
        """Test getting installed package version."""
        # This test verifies the method exists and can be called
        assert hasattr(agent, "_get_installed_version")
        assert callable(agent._get_installed_version)

    @pytest.mark.unit
    def test_compare_versions(self, agent):
        """Test version comparison."""
        # This test verifies the method exists and can be called
        assert hasattr(agent, "_compare_versions")
        assert callable(agent._compare_versions)

        # Test basic version comparison
        assert agent._compare_versions("1.40.0", "1.40.0") == 0
        assert agent._compare_versions("1.41.0", "1.40.0") > 0
        assert agent._compare_versions("1.39.0", "1.40.0") < 0
