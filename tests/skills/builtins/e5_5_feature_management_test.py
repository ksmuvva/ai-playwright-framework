"""Unit tests for E5.5 - Feature Management skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e5_5_feature_management import (
    Feature,
    FeatureManagementAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestFeature:
    """Test suite for Feature dataclass."""

    @pytest.mark.unit
    def test_feature_creation(self):
        """Test creating a feature."""
        feature = Feature(
            feature_id="feat_001",
            feature_name="Authentication",
            file_path="features/login.feature",
            scenarios=["User Login", "User Logout"],
        )

        assert feature.feature_id == "feat_001"
        assert feature.feature_name == "Authentication"
        assert len(feature.scenarios) == 2


class TestFeatureManagementAgent:
    """Test suite for FeatureManagementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return FeatureManagementAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e5_5_feature_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with feature registry."""
        assert hasattr(agent, "_feature_registry")
        assert isinstance(agent._feature_registry, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_feature(self, agent):
        """Test creating a feature."""
        context = {
            "task_type": "create_feature",
            "feature_name": "Authentication",
            "description": "User authentication functionality",
        }

        result = await agent.run("create_feature", context)

        assert "created" in result.lower() or "feature" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_scenario(self, agent):
        """Test adding a scenario to feature."""
        context = {
            "task_type": "add_scenario",
            "feature_id": "feat_001",
            "scenario_name": "User Login",
        }

        result = await agent.run("add_scenario", context)

        assert "added" in result.lower() or "scenario" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_list_features(self, agent):
        """Test listing features."""
        context = {
            "task_type": "list_features",
        }

        result = await agent.run("list_features", context)

        assert "feature" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_organize_features(self, agent):
        """Test organizing features."""
        context = {
            "task_type": "organize_features",
            "criterion": "theme",
        }

        result = await agent.run("organize_features", context)

        assert "organized" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
