"""Unit tests for E8.4 - Progress Feedback skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e8_4_progress_feedback import (
    FeedbackMessage,
    ProgressFeedbackAgent,
    ProgressIndicator,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestProgressIndicator:
    @pytest.mark.unit
    def test_progress_indicator_creation(self):
        indicator = ProgressIndicator(
            indicator_id="ind_001",
            current=50,
            total=100,
        )
        assert indicator.current == 50


class TestFeedbackMessage:
    @pytest.mark.unit
    def test_feedback_message_creation(self):
        message = FeedbackMessage(
            message_id="msg_001",
            level="info",
            content="Processing...",
        )
        assert message.level == "info"


class TestProgressFeedbackAgent:
    @pytest.fixture
    def agent(self):
        return ProgressFeedbackAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e8_4_progress_feedback"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_update_progress(self, agent):
        context = {"current": 50, "total": 100}
        result = await agent.run("update", context)
        assert "progress" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_show_indicator(self, agent):
        context = {"style": "bar"}
        result = await agent.run("show", context)
        assert "indicator" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_send_feedback(self, agent):
        context = {"message": "Complete!"}
        result = await agent.run("feedback", context)
        assert "feedback" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
