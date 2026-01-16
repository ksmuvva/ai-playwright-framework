"""Unit tests for E5.3 - Step Definitions skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e5_3_step_definitions import (
    StepDefinition,
    StepDefinitionsAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestStepDefinition:
    """Test suite for StepDefinition dataclass."""

    @pytest.mark.unit
    def test_step_definition_creation(self):
        """Test creating a step definition."""
        step = StepDefinition(
            step_id="step_001",
            step_text="the user is on the login page",
            step_keyword="Given",
            implementation="page.goto('/login')",
        )

        assert step.step_id == "step_001"
        assert step.step_text == "the user is on the login page"
        assert step.step_keyword == "Given"


class TestStepDefinitionsAgent:
    """Test suite for StepDefinitionsAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return StepDefinitionsAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e5_3_step_definitions"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_step_definition(self, agent):
        """Test generating a step definition."""
        context = {
            "task_type": "generate_step",
            "step_text": "the user clicks the login button",
            "selector": "#login-btn",
        }

        result = await agent.run("generate_step", context)

        assert "step" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_step(self, agent):
        """Test registering a step definition."""
        context = {
            "task_type": "register_step",
            "step_pattern": "the user clicks {button}",
            "implementation": "click(button)",
        }

        result = await agent.run("register_step", context)

        assert "registered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_lookup_step(self, agent):
        """Test looking up a step definition."""
        context = {
            "task_type": "lookup_step",
            "step_text": "the user clicks login",
        }

        result = await agent.run("lookup_step", context)

        assert "step" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
