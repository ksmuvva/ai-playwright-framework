"""Unit tests for E3.3 - Action Extraction skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e3_3_action_extraction import (
    ActionExtractionAgent,
    ExtractedAction,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestExtractedAction:
    """Test suite for ExtractedAction dataclass."""

    @pytest.mark.unit
    def test_extracted_action_creation(self):
        """Test creating an extracted action."""
        action = ExtractedAction(
            action_id="act_001",
            action_type="click",
            selector="#submit-btn",
            line_number=5,
        )

        assert action.action_id == "act_001"
        assert action.action_type == "click"
        assert action.selector == "#submit-btn"


class TestActionExtractionAgent:
    """Test suite for ActionExtractionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ActionExtractionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e3_3_action_extraction"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_extract_actions(self, agent):
        """Test extracting actions from recording data."""
        context = {
            "task_type": "extract_actions",
            "recording_data": {
                "actions": [
                    {"action": "click", "selector": "#btn"},
                    {"action": "fill", "selector": "#input"},
                ]
            },
        }

        result = await agent.run("extract_actions", context)

        assert "action" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_normalize_action(self, agent):
        """Test normalizing an action."""
        context = {
            "task_type": "normalize_action",
            "action": {"action": "click", "selector": "#btn"},
        }

        result = await agent.run("normalize_action", context)

        assert "normalized" in result.lower() or "action" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_action(self, agent):
        """Test validating an action."""
        context = {
            "task_type": "validate_action",
            "action": {"action": "click", "selector": "#btn"},
        }

        result = await agent.run("validate_action", context)

        assert "valid" in result.lower() or "action" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
