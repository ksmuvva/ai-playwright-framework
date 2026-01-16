"""Unit tests for E3.4 - Selector Analysis skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e3_4_selector_analysis import (
    SelectorAnalysisAgent,
    SelectorInfo,
    SelectorType,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestSelectorType:
    """Test suite for SelectorType enum."""

    @pytest.mark.unit
    def test_selector_type_values(self):
        """Test selector type enum values."""
        assert SelectorType.CSS.value == "css"
        assert SelectorType.XPATH.value == "xpath"
        assert SelectorType.TEXT.value == "text"
        assert SelectorType.ROLE.value == "role"


class TestSelectorInfo:
    """Test suite for SelectorInfo dataclass."""

    @pytest.mark.unit
    def test_selector_info_creation(self):
        """Test creating selector info."""
        info = SelectorInfo(
            selector_id="sel_001",
            selector="#submit-btn",
            selector_type=SelectorType.CSS,
            confidence=0.95,
        )

        assert info.selector_id == "sel_001"
        assert info.selector == "#submit-btn"
        assert info.selector_type == SelectorType.CSS


class TestSelectorAnalysisAgent:
    """Test suite for SelectorAnalysisAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return SelectorAnalysisAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e3_4_selector_analysis"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_analyze_selector(self, agent):
        """Test analyzing a selector."""
        context = {
            "task_type": "analyze_selector",
            "selector": "#submit-btn",
        }

        result = await agent.run("analyze_selector", context)

        assert "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_classify_selector(self, agent):
        """Test classifying a selector type."""
        context = {
            "task_type": "classify_selector",
            "selector": "#submit-btn",
        }

        result = await agent.run("classify_selector", context)

        assert "css" in result.lower() or "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_optimize_selector(self, agent):
        """Test optimizing a selector."""
        context = {
            "task_type": "optimize_selector",
            "selector": "div > div > div > #submit-btn",
        }

        result = await agent.run("optimize_selector", context)

        assert "optimized" in result.lower() or "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
