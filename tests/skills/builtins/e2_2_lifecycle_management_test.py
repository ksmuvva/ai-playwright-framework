"""Unit tests for E2.2 - Lifecycle Management skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e2_2_lifecycle_management import (
    AgentLifecycleContext,
    LifecycleManagementAgent,
    LifecycleState,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestLifecycleState:
    """Test suite for LifecycleState enum."""

    @pytest.mark.unit
    def test_lifecycle_state_values(self):
        """Test lifecycle state enum values."""
        assert LifecycleState.CREATED.value == "created"
        assert LifecycleState.INITIALIZING.value == "initializing"
        assert LifecycleState.IDLE.value == "idle"
        assert LifecycleState.RUNNING.value == "running"
        assert LifecycleState.SUSPENDED.value == "suspended"
        assert LifecycleState.TERMINATING.value == "terminating"
        assert LifecycleState.TERMINATED.value == "terminated"
        assert LifecycleState.FAILED.value == "failed"


class TestAgentLifecycleContext:
    """Test suite for AgentLifecycleContext dataclass."""

    @pytest.mark.unit
    def test_lifecycle_context_creation(self):
        """Test creating a lifecycle context."""
        context = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
        )

        assert context.agent_id == "agent_001"
        assert context.agent_type == "TestAgent"
        assert context.workflow_id == "wf_001"
        assert context.task_id == "task_001"
        assert context.lifecycle_state == LifecycleState.CREATED

    @pytest.mark.unit
    def test_lifecycle_context_transition_to(self):
        """Test transitioning lifecycle state."""
        context = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
        )

        context.transition_to(LifecycleState.INITIALIZING)
        assert context.lifecycle_state == LifecycleState.INITIALIZING

        context.transition_to(LifecycleState.RUNNING)
        assert context.lifecycle_state == LifecycleState.RUNNING

    @pytest.mark.unit
    def test_lifecycle_context_to_dict(self):
        """Test converting lifecycle context to dictionary."""
        context = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
        )

        result = context.to_dict()

        assert isinstance(result, dict)
        assert result["agent_id"] == "agent_001"
        assert result["agent_type"] == "TestAgent"


class TestLifecycleManagementAgent:
    """Test suite for LifecycleManagementAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return LifecycleManagementAgent()

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
        assert agent.name == "e2_2_lifecycle_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty registry."""
        assert hasattr(agent, "_lifecycle_contexts")
        assert agent._lifecycle_contexts == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_spawn_agent(self, agent):
        """Test spawning a new agent."""
        context = {
            "task_type": "spawn_agent",
            "agent_type": "TestAgent",
            "workflow_id": "wf_001",
            "task_id": "task_001",
        }

        result = await agent.run("spawn_agent", context)

        assert "spawned" in result.lower() or "agent" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_initialize_agent(self, agent):
        """Test initializing an agent."""
        agent._lifecycle_contexts["agent_001"] = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
        )

        context = {
            "task_type": "initialize_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("initialize_agent", context)

        assert "initialized" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_start_agent(self, agent):
        """Test starting an agent."""
        agent._lifecycle_contexts["agent_001"] = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
            lifecycle_state=LifecycleState.IDLE,
        )

        context = {
            "task_type": "start_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("start_agent", context)

        assert "started" in result.lower() or "running" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_stop_agent(self, agent):
        """Test stopping an agent."""
        agent._lifecycle_contexts["agent_001"] = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
            lifecycle_state=LifecycleState.RUNNING,
        )

        context = {
            "task_type": "stop_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("stop_agent", context)

        assert "stopped" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_terminate_agent(self, agent):
        """Test terminating an agent."""
        agent._lifecycle_contexts["agent_001"] = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
            lifecycle_state=LifecycleState.RUNNING,
        )

        context = {
            "task_type": "terminate_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("terminate_agent", context)

        assert "terminated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_agent_status(self, agent):
        """Test getting agent status."""
        agent._lifecycle_contexts["agent_001"] = AgentLifecycleContext(
            agent_id="agent_001",
            agent_type="TestAgent",
            workflow_id="wf_001",
            task_id="task_001",
            lifecycle_state=LifecycleState.RUNNING,
        )

        context = {
            "task_type": "get_agent_status",
            "agent_id": "agent_001",
        }

        result = await agent.run("get_agent_status", context)

        assert "running" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
