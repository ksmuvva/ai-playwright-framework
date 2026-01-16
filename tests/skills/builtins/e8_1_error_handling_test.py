"""Unit tests for E8.1 - Error Handling skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e8_1_error_handling import (
    ErrorContext,
    ErrorHandlingAgent,
    ErrorRecord,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestErrorRecord:
    """Test suite for ErrorRecord dataclass."""

    @pytest.mark.unit
    def test_error_record_creation(self):
        record = ErrorRecord(
            error_id="err_001",
            error_type="ValueError",
            message="Test error",
            stack_trace="line 1",
        )
        assert record.error_id == "err_001"
        assert record.error_type == "ValueError"


class TestErrorContext:
    """Test suite for ErrorContext dataclass."""

    @pytest.mark.unit
    def test_error_context_creation(self):
        context = ErrorContext(
            context_id="ctx_001",
            workflow_id="wf_001",
            errors_handled=0,
        )
        assert context.context_id == "ctx_001"


class TestErrorHandlingAgent:
    """Test suite for ErrorHandlingAgent."""

    @pytest.fixture
    def agent(self):
        return ErrorHandlingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e8_1_error_handling"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_handle_error(self, agent):
        context = {
            "error_type": "ValueError",
            "message": "Test error",
        }
        result = await agent.run("handle", context)
        assert "handled" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_classify_error(self, agent):
        context = {"exception": ValueError("test")}
        result = await agent.run("classify", context)
        assert "error" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_suggest_recovery(self, agent):
        context = {"error_type": "timeout"}
        result = await agent.run("suggest_recovery", context)
        assert "recovery" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
