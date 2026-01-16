"""Unit tests for E3.5 - Ingestion Logging skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e3_5_ingestion_logging import (
    IngestionLoggingAgent,
    LogEntry,
    LogLevel,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestLogLevel:
    """Test suite for LogLevel enum."""

    @pytest.mark.unit
    def test_log_level_values(self):
        """Test log level enum values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"


class TestLogEntry:
    """Test suite for LogEntry dataclass."""

    @pytest.mark.unit
    def test_log_entry_creation(self):
        """Test creating a log entry."""
        entry = LogEntry(
            entry_id="log_001",
            level=LogLevel.INFO,
            message="Test message",
            workflow_id="wf_001",
        )

        assert entry.entry_id == "log_001"
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"


class TestIngestionLoggingAgent:
    """Test suite for IngestionLoggingAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return IngestionLoggingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e3_5_ingestion_logging"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with log history."""
        assert hasattr(agent, "_log_history")
        assert isinstance(agent._log_history, list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_log_event(self, agent):
        """Test logging an event."""
        context = {
            "task_type": "log_event",
            "level": LogLevel.INFO,
            "message": "Test message",
            "workflow_id": "wf_001",
        }

        result = await agent.run("log_event", context)

        assert "logged" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_logs(self, agent):
        """Test getting logs."""
        context = {
            "task_type": "get_logs",
            "workflow_id": "wf_001",
        }

        result = await agent.run("get_logs", context)

        assert "log" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_clear_logs(self, agent):
        """Test clearing logs."""
        agent._log_history.append(LogEntry(
            entry_id="log_001",
            level=LogLevel.INFO,
            message="Test",
        ))

        context = {
            "task_type": "clear_logs",
            "workflow_id": "wf_001",
        }

        result = await agent.run("clear_logs", context)

        assert "cleared" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_log_history(self, agent):
        """Test getting log history."""
        result = agent.get_log_history()

        assert isinstance(result, list)
