"""Unit tests for E5.4 - Scenario Optimization skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e5_4_scenario_optimization import (
    OptimizationResult,
    ScenarioOptimizationAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestOptimizationResult:
    """Test suite for OptimizationResult dataclass."""

    @pytest.mark.unit
    def test_optimization_result_creation(self):
        """Test creating an optimization result."""
        result = OptimizationResult(
            result_id="opt_001",
            scenario_id="scen_001",
            original_steps=10,
            optimized_steps=7,
            improvement_percent=30.0,
        )

        assert result.result_id == "opt_001"
        assert result.original_steps == 10
        assert result.optimized_steps == 7
        assert result.improvement_percent == 30.0


class TestScenarioOptimizationAgent:
    """Test suite for ScenarioOptimizationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ScenarioOptimizationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e5_4_scenario_optimization"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_optimize_scenario(self, agent):
        """Test optimizing a scenario."""
        context = {
            "task_type": "optimize_scenario",
            "steps": [
                {"step": "Given user is on login page"},
                {"step": "When user enters username"},
                {"step": "When user enters password"},
            ],
        }

        result = await agent.run("optimize_scenario", context)

        assert "optimized" in result.lower() or "scenario" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_remove_redundancy(self, agent):
        """Test removing redundant steps."""
        context = {
            "task_type": "remove_redundancy",
            "steps": [
                {"step": "Navigate to /login"},
                {"step": "Navigate to /login"},
            ],
        }

        result = await agent.run("remove_redundancy", context)

        assert "redundancy" in result.lower() or "removed" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_merge_steps(self, agent):
        """Test merging similar steps."""
        context = {
            "task_type": "merge_steps",
            "steps": [
                {"step": "Enter username in #username field"},
                {"step": "Enter password in #password field"},
            ],
        }

        result = await agent.run("merge_steps", context)

        assert "merged" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
