"""Unit tests for E2.1 - Orchestrator Core skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e2_1_orchestrator_core import (
    ExecutionContext,
    OrchestratorCoreAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestExecutionContext:
    """Test suite for ExecutionContext dataclass."""

    @pytest.mark.unit
    def test_execution_context_creation(self):
        """Test creating an execution context."""
        context = ExecutionContext(
            workflow_id="wf_001",
            task_id="task_001",
            project_path="/tmp/project",
        )

        assert context.workflow_id == "wf_001"
        assert context.task_id == "task_001"
        assert context.project_path == "/tmp/project"
        assert context.agent_chain == []
        assert context.context_chain == []

    @pytest.mark.unit
    def test_execution_context_create_child(self):
        """Test creating a child context."""
        parent = ExecutionContext(
            workflow_id="wf_001",
            task_id="parent_task",
            recording_id="rec_001",
        )

        child = parent.create_child("child_task", "agent_001")

        assert child.workflow_id == parent.workflow_id
        assert child.task_id == "child_task"
        assert child.parent_context == parent
        assert child.recording_id == parent.recording_id
        assert "agent_001" in child.agent_chain
        assert "parent_task" in child.context_chain

    @pytest.mark.unit
    def test_execution_context_add_agent(self):
        """Test adding an agent to the context."""
        context = ExecutionContext(workflow_id="wf_001")

        context.add_agent("agent_001")
        context.add_agent("agent_002")

        assert "agent_001" in context.agent_chain
        assert "agent_002" in context.agent_chain
        assert len(context.agent_chain) == 2

    @pytest.mark.unit
    def test_execution_context_add_agent_no_duplicates(self):
        """Test adding duplicate agents doesn't create duplicates."""
        context = ExecutionContext(workflow_id="wf_001")

        context.add_agent("agent_001")
        context.add_agent("agent_001")

        assert context.agent_chain.count("agent_001") == 1

    @pytest.mark.unit
    def test_execution_context_update_metadata(self):
        """Test updating context metadata."""
        context = ExecutionContext(workflow_id="wf_001")

        context.update_metadata("key1", "value1")
        context.update_metadata("key2", 42)

        assert context.metadata["key1"] == "value1"
        assert context.metadata["key2"] == 42

    @pytest.mark.unit
    def test_execution_context_to_dict(self):
        """Test converting context to dictionary."""
        context = ExecutionContext(
            workflow_id="wf_001",
            task_id="task_001",
            metadata={"key": "value"},
        )

        result = context.to_dict()

        assert isinstance(result, dict)
        assert result["workflow_id"] == "wf_001"
        assert result["task_id"] == "task_001"
        assert result["metadata"] == {"key": "value"}


class TestOrchestratorCoreAgent:
    """Test suite for OrchestratorCoreAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OrchestratorCoreAgent()

    @pytest.fixture
    def mock_execution_context(self):
        """Create mock execution context."""
        return ExecutionContext(
            workflow_id="wf_001",
            task_id="task_001",
            project_path="/tmp/project",
        )

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
        assert agent.name == "e2_1_orchestrator_core"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty registries."""
        assert hasattr(agent, "_active_workflows")
        assert hasattr(agent, "_agent_registry")
        assert agent._active_workflows == {}
        assert agent._agent_registry == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_start_workflow(self, agent, mock_execution_context):
        """Test starting a new workflow."""
        context = {
            "task_type": "start_workflow",
            "workflow_id": "wf_001",
            "workflow_name": "Test Workflow",
            "agents": ["agent_001", "agent_002"],
        }

        result = await agent.run("start_workflow", context)

        assert "workflow" in result.lower()
        assert "wf_001" in result or "started" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_execute_agent(self, agent):
        """Test executing an agent in workflow."""
        agent._agent_registry["agent_001"] = MagicMock()
        agent._agent_registry["agent_001"].run = AsyncMock(return_value="Agent executed")

        context = {
            "task_type": "execute_agent",
            "workflow_id": "wf_001",
            "agent_id": "agent_001",
            "task": "test_task",
        }

        result = await agent.run("execute_agent", context)

        assert "executed" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_workflow_status(self, agent):
        """Test getting workflow status."""
        agent._active_workflows["wf_001"] = {"status": "running", "progress": 50}

        context = {
            "task_type": "get_workflow_status",
            "workflow_id": "wf_001",
        }

        result = await agent.run("get_workflow_status", context)

        assert "wf_001" in result or "running" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_complete_workflow(self, agent):
        """Test completing a workflow."""
        agent._active_workflows["wf_001"] = {"status": "running"}

        context = {
            "task_type": "complete_workflow",
            "workflow_id": "wf_001",
        }

        result = await agent.run("complete_workflow", context)

        assert "completed" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_active_workflows(self, agent):
        """Test getting active workflows."""
        agent._active_workflows["wf_001"] = {"status": "running"}

        result = agent.get_active_workflows()

        assert "wf_001" in result

    @pytest.mark.unit
    def test_get_agent_registry(self, agent):
        """Test getting agent registry."""
        agent._agent_registry["agent_001"] = MagicMock()

        result = agent.get_agent_registry()

        assert "agent_001" in result
