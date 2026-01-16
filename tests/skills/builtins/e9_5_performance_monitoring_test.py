"""Unit tests for E9.5 - Performance Monitoring skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e9_5_performance_monitoring import (
    BottleneckInfo,
    PerformanceMetric,
    PerformanceMonitoringAgent,
    PerformanceSnapshot,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestPerformanceMetric:
    @pytest.mark.unit
    def test_performance_metric_creation(self):
        metric = PerformanceMetric(
            metric_id="met_001",
            name="response_time",
            value=150,
            unit="ms",
        )
        assert metric.name == "response_time"


class TestPerformanceSnapshot:
    @pytest.mark.unit
    def test_performance_snapshot_creation(self):
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_001",
            timestamp="2024-01-01T00:00:00Z",
            metrics=[],
        )
        assert snapshot.snapshot_id == "snap_001"


class TestBottleneckInfo:
    @pytest.mark.unit
    def test_bottleneck_info_creation(self):
        bottleneck = BottleneckInfo(
            bottleneck_id="bn_001",
            severity="high",
            location="/api/login",
        )
        assert bottleneck.severity == "high"


class TestPerformanceMonitoringAgent:
    @pytest.fixture
    def agent(self):
        return PerformanceMonitoringAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e9_5_performance_monitoring"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_collect_metrics(self, agent):
        context = {"url": "https://example.com"}
        result = await agent.run("collect", context)
        assert "metric" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_detect_bottlenecks(self, agent):
        context = {"threshold": 1000}
        result = await agent.run("detect_bottlenecks", context)
        assert "bottleneck" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_snapshot(self, agent):
        result = await agent.run("snapshot", {})
        assert "snapshot" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
