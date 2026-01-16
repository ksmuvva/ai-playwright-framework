"""Unit tests for E6.5 - Recording Enhancement skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e6_5_recording_enhancement import (
    RecordingEnhancementAgent,
    SmartSelector,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestSmartSelector:
    """Test suite for SmartSelector dataclass."""

    @pytest.mark.unit
    def test_smart_selector_creation(self):
        """Test creating a smart selector."""
        selector = SmartSelector(
            selector_id="sel_001",
            original_selector="div > div > button",
            enhanced_selector="button[type='submit']",
            strategy="data_test_id",
            confidence=0.95,
        )

        assert selector.selector_id == "sel_001"
        assert selector.strategy == "data_test_id"
        assert selector.confidence == 0.95


class TestRecordingEnhancementAgent:
    """Test suite for RecordingEnhancementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return RecordingEnhancementAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e6_5_recording_enhancement"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_enhance_selector(self, agent):
        """Test enhancing a selector."""
        context = {
            "task_type": "enhance_selector",
            "selector": "div > div > button",
        }

        result = await agent.run("enhance_selector", context)

        assert "enhanced" in result.lower() or "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_optimize_recording(self, agent):
        """Test optimizing a recording."""
        context = {
            "task_type": "optimize_recording",
            "actions": [
                {"action": "click", "selector": "div > div > button"},
            ],
        }

        result = await agent.run("optimize_recording", context)

        assert "optimized" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_wait_strategy(self, agent):
        """Test adding wait strategy."""
        context = {
            "task_type": "add_wait",
            "selector": "#dynamic-content",
            "strategy": "visible",
        }

        result = await agent.run("add_wait", context)

        assert "wait" in result.lower() or "strategy" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
