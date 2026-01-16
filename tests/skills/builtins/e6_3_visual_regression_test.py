"""Unit tests for E6.3 - Visual Regression skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e6_3_visual_regression import (
    VisualBaseline,
    VisualDiff,
    VisualRegressionAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestVisualBaseline:
    """Test suite for VisualBaseline dataclass."""

    @pytest.mark.unit
    def test_visual_baseline_creation(self):
        """Test creating a visual baseline."""
        baseline = VisualBaseline(
            baseline_id="base_001",
            name="homepage_baseline",
            screenshot_path="/screenshots/home.png",
        )

        assert baseline.baseline_id == "base_001"
        assert baseline.name == "homepage_baseline"


class TestVisualDiff:
    """Test suite for VisualDiff dataclass."""

    @pytest.mark.unit
    def test_visual_diff_creation(self):
        """Test creating a visual diff."""
        diff = VisualDiff(
            diff_id="diff_001",
            baseline_id="base_001",
            diff_percentage=0.05,
            has_differences=True,
        )

        assert diff.diff_id == "diff_001"
        assert diff.diff_percentage == 0.05
        assert diff.has_differences is True


class TestVisualRegressionAgent:
    """Test suite for VisualRegressionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return VisualRegressionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e6_3_visual_regression"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_capture_baseline(self, agent):
        """Test capturing visual baseline."""
        context = {
            "task_type": "capture_baseline",
            "name": "homepage",
            "selector": "#main-content",
        }

        result = await agent.run("capture_baseline", context)

        assert "baseline" in result.lower() or "captured" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_compare_screenshots(self, agent):
        """Test comparing screenshots."""
        context = {
            "task_type": "compare",
            "baseline_path": "/baseline.png",
            "current_path": "/current.png",
        }

        result = await agent.run("compare", context)

        assert "compared" in result.lower() or "diff" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_diff_image(self, agent):
        """Test generating diff image."""
        context = {
            "task_type": "generate_diff",
            "baseline_path": "/baseline.png",
            "current_path": "/current.png",
        }

        result = await agent.run("generate_diff", context)

        assert "diff" in result.lower() or "generated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
