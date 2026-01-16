"""Unit tests for E2.5 - Health Monitoring skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e2_5_health_monitoring import (
    AgentHealthStatus,
    HealthCheckResult,
    HealthMonitoringAgent,
    SystemMetrics,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestAgentHealthStatus:
    """Test suite for AgentHealthStatus enum."""

    @pytest.mark.unit
    def test_agent_health_status_values(self):
        """Test agent health status enum values."""
        assert AgentHealthStatus.HEALTHY.value == "healthy"
        assert AgentHealthStatus.DEGRADED.value == "degraded"
        assert AgentHealthStatus.UNHEALTHY.value == "unhealthy"
        assert AgentHealthStatus.UNKNOWN.value == "unknown"


class TestHealthCheckResult:
    """Test suite for HealthCheckResult dataclass."""

    @pytest.mark.unit
    def test_health_check_result_creation(self):
        """Test creating a health check result."""
        result = HealthCheckResult(
            agent_id="agent_001",
            status=AgentHealthStatus.HEALTHY,
            checks={"cpu": "ok", "memory": "ok"},
        )

        assert result.agent_id == "agent_001"
        assert result.status == AgentHealthStatus.HEALTHY
        assert result.checks["cpu"] == "ok"

    @pytest.mark.unit
    def test_health_check_result_to_dict(self):
        """Test converting health check result to dictionary."""
        result = HealthCheckResult(
            agent_id="agent_001",
            status=AgentHealthStatus.HEALTHY,
        )

        dict_result = result.to_dict()

        assert isinstance(dict_result, dict)
        assert dict_result["agent_id"] == "agent_001"
        assert dict_result["status"] == "healthy"


class TestSystemMetrics:
    """Test suite for SystemMetrics dataclass."""

    @pytest.mark.unit
    def test_system_metrics_creation(self):
        """Test creating system metrics."""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            active_agents=5,
            total_tasks=100,
        )

        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.active_agents == 5

    @pytest.mark.unit
    def test_system_metrics_to_dict(self):
        """Test converting system metrics to dictionary."""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
        )

        dict_metrics = metrics.to_dict()

        assert isinstance(dict_metrics, dict)
        assert dict_metrics["cpu_percent"] == 50.0


class TestHealthMonitoringAgent:
    """Test suite for HealthMonitoringAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return HealthMonitoringAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert hasattr(agent, "description")
        assert agent.name == "e2_5_health_monitoring"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty registries."""
        assert hasattr(agent, "_health_status")
        assert hasattr(agent, "_health_history")
        assert agent._health_status == {}
        assert agent._health_history == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_check_health(self, agent):
        """Test checking health of an agent."""
        context = {
            "task_type": "check_health",
            "agent_id": "agent_001",
        }

        result = await agent.run("check_health", context)

        assert "health" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_agent(self, agent):
        """Test registering an agent for health monitoring."""
        context = {
            "task_type": "register_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("register_agent", context)

        assert "registered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_unregister_agent(self, agent):
        """Test unregistering an agent from health monitoring."""
        agent._health_status["agent_001"] = AgentHealthStatus.HEALTHY

        context = {
            "task_type": "unregister_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("unregister_agent", context)

        assert "unregistered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_system_metrics(self, agent):
        """Test getting system metrics."""
        context = {
            "task_type": "get_system_metrics",
        }

        result = await agent.run("get_system_metrics", context)

        assert "metrics" in result.lower() or "cpu" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_health_summary(self, agent):
        """Test getting health summary."""
        agent._health_status["agent_001"] = AgentHealthStatus.HEALTHY
        agent._health_status["agent_002"] = AgentHealthStatus.DEGRADED

        context = {
            "task_type": "get_health_summary",
        }

        result = await agent.run("get_health_summary", context)

        assert "summary" in result.lower() or "health" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_set_health_status(self, agent):
        """Test setting health status for an agent."""
        context = {
            "task_type": "set_health_status",
            "agent_id": "agent_001",
            "status": AgentHealthStatus.HEALTHY,
        }

        result = await agent.run("set_health_status", context)

        assert "status" in result.lower() or "updated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_health_history(self, agent):
        """Test getting health history."""
        context = {
            "task_type": "get_health_history",
            "agent_id": "agent_001",
        }

        result = await agent.run("get_health_history", context)

        assert "history" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_health_status(self, agent):
        """Test getting health status registry."""
        agent._health_status["agent_001"] = AgentHealthStatus.HEALTHY

        result = agent.get_health_status()

        assert "agent_001" in result

    @pytest.mark.unit
    def test_get_health_history(self, agent):
        """Test getting health history."""
        result = agent.get_health_history()

        assert isinstance(result, list)
