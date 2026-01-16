"""Unit tests for E6.4 - Performance Recording skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e6_4_performance_recording import (
    PerformanceMetric,
    PerformanceRecordingAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestPerformanceMetric:
    """Test suite for PerformanceMetric dataclass."""

    @pytest.mark.unit
    def test_performance_metric_creation(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric(
            metric_id="metric_001",
            metric_name="page_load_time",
            value=1250,
            unit="ms",
        )

        assert metric.metric_id == "metric_001"
        assert metric.metric_name == "page_load_time"
        assert metric.value == 1250
        assert metric.unit == "ms"


class TestPerformanceRecordingAgent:
    """Test suite for PerformanceRecordingAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return PerformanceRecordingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e6_4_performance_recording"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_record_metrics(self, agent):
        """Test recording performance metrics."""
        context = {
            "task_type": "record_metrics",
            "url": "https://example.com",
        }

        result = await agent.run("record_metrics", context)

        assert "metrics" in result.lower() or "recorded" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_measure_page_load(self, agent):
        """Test measuring page load time."""
        context = {
            "task_type": "measure_page_load",
            "url": "https://example.com",
        }

        result = await agent.run("measure_page_load", context)

        assert "load" in result.lower() or "time" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_capture_resource_timing(self, agent):
        """Test capturing resource timing."""
        context = {
            "task_type": "resource_timing",
        }

        result = await agent.run("resource_timing", context)

        assert "resource" in result.lower() or "timing" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
