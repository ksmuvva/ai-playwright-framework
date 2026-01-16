"""Unit tests for E3.2 - Playwright Parser skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e3_2_playwright_parser import (
    PlaywrightParserAgent,
    ParseResult,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestParseResult:
    """Test suite for ParseResult dataclass."""

    @pytest.mark.unit
    def test_parse_result_creation(self):
        """Test creating a parse result."""
        result = ParseResult(
            parse_id="parse_001",
            recording_id="rec_001",
            actions_count=10,
            selectors_found=5,
        )

        assert result.parse_id == "parse_001"
        assert result.recording_id == "rec_001"
        assert result.actions_count == 10


class TestPlaywrightParserAgent:
    """Test suite for PlaywrightParserAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return PlaywrightParserAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e3_2_playwright_parser"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_parse_recording(self, agent, temp_project_path):
        """Test parsing a recording."""
        recording_file = temp_project_path / "test_recording.js"
        recording_file.write_text("module.exports = { actions: [] };")

        context = {
            "task_type": "parse_recording",
            "recording_path": str(recording_file),
        }

        result = await agent.run("parse_recording", context)

        assert "parse" in result.lower() or "recording" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_extract_actions(self, agent):
        """Test extracting actions from recording."""
        context = {
            "task_type": "extract_actions",
            "recording_data": {"actions": [{"action": "click"}]},
        }

        result = await agent.run("extract_actions", context)

        assert "action" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
