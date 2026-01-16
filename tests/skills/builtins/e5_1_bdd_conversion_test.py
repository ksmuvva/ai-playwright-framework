"""Unit tests for E5.1 - BDD Conversion skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e5_1_bdd_conversion import (
    BDDConversionAgent,
    ConversionContext,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestConversionContext:
    """Test suite for ConversionContext dataclass."""

    @pytest.mark.unit
    def test_conversion_context_creation(self):
        """Test creating a conversion context."""
        context = ConversionContext(
            conversion_id="conv_001",
            workflow_id="wf_001",
            source_format="playwright",
            target_format="gherkin",
        )

        assert context.conversion_id == "conv_001"
        assert context.workflow_id == "wf_001"


class TestBDDConversionAgent:
    """Test suite for BDDConversionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return BDDConversionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e5_1_bdd_conversion"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_convert_to_gherkin(self, agent):
        """Test converting to Gherkin format."""
        context = {
            "task_type": "convert_to_gherkin",
            "actions": [
                {"action": "click", "selector": "#login-btn"},
                {"action": "fill", "selector": "#username"},
            ],
        }

        result = await agent.run("convert_to_gherkin", context)

        assert "converted" in result.lower() or "gherkin" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_scenario(self, agent):
        """Test generating a BDD scenario."""
        context = {
            "task_type": "generate_scenario",
            "feature": "Authentication",
            "actions": [{"action": "click", "selector": "#login"}],
        }

        result = await agent.run("generate_scenario", context)

        assert "scenario" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
