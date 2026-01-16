"""Unit tests for E4.1 - Deduplication Agent skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e4_1_deduplication_agent import (
    AnalysisStage,
    DeduplicationAgent,
    PatternMatch,
    SelectorFrequency,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestAnalysisStage:
    """Test suite for AnalysisStage enum."""

    @pytest.mark.unit
    def test_analysis_stage_values(self):
        """Test analysis stage enum values."""
        assert AnalysisStage.INITIALIZED.value == "initialized"
        assert AnalysisStage.COLLECTING.value == "collecting"
        assert AnalysisStage.ANALYZING.value == "analyzing"
        assert AnalysisStage.GROUPING.value == "grouping"
        assert AnalysisStage.COMPLETED.value == "completed"


class TestSelectorFrequency:
    """Test suite for SelectorFrequency dataclass."""

    @pytest.mark.unit
    def test_selector_frequency_creation(self):
        """Test creating selector frequency data."""
        freq = SelectorFrequency(
            raw_selector="#submit-btn",
            count=5,
            confidence=0.9,
        )

        assert freq.raw_selector == "#submit-btn"
        assert freq.count == 5
        assert freq.confidence == 0.9

    @pytest.mark.unit
    def test_selector_frequency_to_dict(self):
        """Test converting to dictionary."""
        freq = SelectorFrequency(raw_selector="#btn", count=3)
        result = freq.to_dict()

        assert isinstance(result, dict)
        assert result["raw_selector"] == "#btn"
        assert result["count"] == 3


class TestPatternMatch:
    """Test suite for PatternMatch dataclass."""

    @pytest.mark.unit
    def test_pattern_match_creation(self):
        """Test creating a pattern match."""
        match = PatternMatch(
            pattern_type="selector",
            pattern_value="#submit-btn",
            strength=0.85,
        )

        assert match.pattern_type == "selector"
        assert match.pattern_value == "#submit-btn"
        assert match.strength == 0.85


class TestDeduplicationAgent:
    """Test suite for DeduplicationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return DeduplicationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e4_1_deduplication_agent"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_analyze_recording(self, agent):
        """Test analyzing a recording."""
        context = {
            "task_type": "analyze_recording",
            "recording_id": "rec_001",
            "actions": [{"selector": "#btn"}],
        }

        result = await agent.run("analyze_recording", context)

        assert "analyzed" in result.lower() or "recording" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_find_patterns(self, agent):
        """Test finding patterns across recordings."""
        context = {
            "task_type": "find_patterns",
            "recordings": ["rec_001", "rec_002"],
        }

        result = await agent.run("find_patterns", context)

        assert "pattern" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_group_selectors(self, agent):
        """Test grouping similar selectors."""
        context = {
            "task_type": "group_selectors",
            "selectors": ["#btn", "#submit-btn", "button[type='submit']"],
        }

        result = await agent.run("group_selectors", context)

        assert "group" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
