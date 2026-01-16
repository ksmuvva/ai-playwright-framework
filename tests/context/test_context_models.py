"""
Tests for context tracking models.
"""

import pytest

from claude_playwright_agent.context.models import (
    TaskContext,
    ExecutionContext,
    ContextChain,
    create_task_context,
    create_execution_context,
)


class TestTaskContext:
    """Tests for TaskContext model."""

    def test_create_task_context(self):
        """Test creating a task context."""
        context = TaskContext(
            workflow_id="wf_001",
            recording_id="rec_001",
            project_path="/test/project",
        )

        assert context.task_id
        assert context.workflow_id == "wf_001"
        assert context.recording_id == "rec_001"
        assert context.project_path == "/test/project"
        assert context.status == "pending"
        assert context.started_at == ""
        assert context.completed_at == ""

    def test_task_context_to_dict(self):
        """Test converting task context to dictionary."""
        context = TaskContext(
            workflow_id="wf_001",
            recording_id="rec_001",
            tags=["@smoke", "@critical"],
            metadata={"priority": "high"},
        )

        data = context.to_dict()

        assert data["workflow_id"] == "wf_001"
        assert data["recording_id"] == "rec_001"
        assert data["tags"] == ["@smoke", "@critical"]
        assert data["metadata"]["priority"] == "high"

    def test_task_context_from_dict(self):
        """Test creating task context from dictionary."""
        data = {
            "task_id": "task_123",
            "workflow_id": "wf_001",
            "recording_id": "rec_001",
            "status": "running",
            "tags": ["@smoke"],
        }

        context = TaskContext.from_dict(data)

        assert context.task_id == "task_123"
        assert context.workflow_id == "wf_001"
        assert context.status == "running"

    def test_task_context_start(self):
        """Test marking task as started."""
        context = TaskContext()
        assert context.started_at == ""
        assert context.status == "pending"

        context.start()
        assert context.started_at
        assert context.status == "running"

    def test_task_context_complete(self):
        """Test marking task as completed."""
        context = TaskContext()
        context.start()
        assert context.completed_at == ""

        context.complete()
        assert context.completed_at
        assert context.status == "completed"

    def test_task_context_fail(self):
        """Test marking task as failed."""
        context = TaskContext()
        context.start()

        context.fail("Test error")
        assert context.completed_at
        assert context.status == "failed"
        assert context.metadata["error"] == "Test error"


class TestContextChain:
    """Tests for ContextChain model."""

    def test_create_context_chain(self):
        """Test creating a context chain."""
        chain = ContextChain()
        assert chain.chain == []
        assert chain.timestamps == {}
        assert chain.metadata == {}

    def test_add_agent_to_chain(self):
        """Test adding agents to chain."""
        chain = ContextChain()
        chain.add_agent("parser_agent", {"duration": "1s"})
        chain.add_agent("dedup_agent", {"groups": 3})
        chain.add_agent("bdd_agent", {"scenarios": 5})

        assert len(chain.chain) == 3
        assert chain.chain == ["parser_agent", "dedup_agent", "bdd_agent"]
        assert "parser_agent" in chain.timestamps
        assert chain.metadata["parser_agent"]["duration"] == "1s"

    def test_chain_contains(self):
        """Test checking if agent is in chain."""
        chain = ContextChain()
        chain.add_agent("parser_agent")
        chain.add_agent("dedup_agent")

        assert chain.contains("parser_agent")
        assert chain.contains("dedup_agent")
        assert not chain.contains("bdd_agent")

    def test_chain_get_position(self):
        """Test getting agent position in chain."""
        chain = ContextChain()
        chain.add_agent("parser_agent")
        chain.add_agent("dedup_agent")
        chain.add_agent("bdd_agent")

        assert chain.get_position("parser_agent") == 0
        assert chain.get_position("dedup_agent") == 1
        assert chain.get_position("bdd_agent") == 2
        assert chain.get_position("unknown") == -1

    def test_chain_to_dict(self):
        """Test converting chain to dictionary."""
        chain = ContextChain()
        chain.add_agent("parser_agent")

        data = chain.to_dict()
        assert data["chain"] == ["parser_agent"]
        assert "parser_agent" in data["timestamps"]

    def test_chain_from_dict(self):
        """Test creating chain from dictionary."""
        data = {
            "chain": ["parser_agent", "dedup_agent"],
            "timestamps": {
                "parser_agent": "2025-01-12T10:00:00",
                "dedup_agent": "2025-01-12T10:00:01",
            },
            "metadata": {},
        }

        chain = ContextChain.from_dict(data)
        assert chain.chain == ["parser_agent", "dedup_agent"]
        assert len(chain.timestamps) == 2


class TestExecutionContext:
    """Tests for ExecutionContext model."""

    def test_create_execution_context(self):
        """Test creating an execution context."""
        task_ctx = TaskContext(workflow_id="wf_001")
        exec_ctx = ExecutionContext(parent_context=task_ctx)

        assert exec_ctx.parent_context == task_ctx
        assert exec_ctx.current_agent == ""
        assert exec_ctx.start_time
        assert exec_ctx.data == {}
        assert exec_ctx.agent_data == {}

    def test_execution_context_set_shared_data(self):
        """Test setting shared data."""
        task_ctx = TaskContext()
        exec_ctx = ExecutionContext(parent_context=task_ctx)

        exec_ctx.set_shared_data("recording_id", "rec_001")
        exec_ctx.set_shared_data("total_actions", 15)

        assert exec_ctx.get_shared_data("recording_id") == "rec_001"
        assert exec_ctx.get_shared_data("total_actions") == 15
        assert exec_ctx.get_shared_data("nonexistent") is None
        assert exec_ctx.get_shared_data("nonexistent", "default") == "default"

    def test_execution_context_set_agent_data(self):
        """Test setting agent-specific data."""
        task_ctx = TaskContext()
        exec_ctx = ExecutionContext(parent_context=task_ctx)

        exec_ctx.set_agent_data("parser_agent", {"actions": 15})
        exec_ctx.set_agent_data("dedup_agent", {"groups": 3})

        assert exec_ctx.get_agent_data("parser_agent")["actions"] == 15
        assert exec_ctx.get_agent_data("dedup_agent")["groups"] == 3
        assert exec_ctx.get_agent_data("unknown") == {}

    def test_execution_context_merge_agent_data(self):
        """Test merging agent data."""
        task_ctx = TaskContext()
        exec_ctx = ExecutionContext(parent_context=task_ctx)

        exec_ctx.set_agent_data("parser_agent", {"actions": 15})
        exec_ctx.merge_agent_data("parser_agent", {"files": 1})

        data = exec_ctx.get_agent_data("parser_agent")
        assert data["actions"] == 15
        assert data["files"] == 1

    def test_execution_context_to_dict(self):
        """Test converting execution context to dictionary."""
        task_ctx = TaskContext(workflow_id="wf_001")
        exec_ctx = ExecutionContext(parent_context=task_ctx)
        exec_ctx.set_shared_data("test", "value")

        data = exec_ctx.to_dict()
        assert data["parent_context"]["workflow_id"] == "wf_001"
        assert data["data"]["test"] == "value"

    def test_execution_context_from_dict(self):
        """Test creating execution context from dictionary."""
        data = {
            "parent_context": {
                "task_id": "task_123",
                "workflow_id": "wf_001",
                "recording_id": "",
                "project_path": "",
                "created_at": "2025-01-12T10:00:00",
                "started_at": "",
                "completed_at": "",
                "status": "pending",
                "metadata": {},
                "tags": [],
                "parent_task_id": "",
            },
            "context_chain": {"chain": [], "timestamps": {}, "metadata": {}},
            "current_agent": "parser_agent",
            "start_time": "2025-01-12T10:00:00",
            "updated_time": "2025-01-12T10:00:01",
            "data": {"key": "value"},
            "agent_data": {},
        }

        exec_ctx = ExecutionContext.from_dict(data)
        assert exec_ctx.current_agent == "parser_agent"
        assert exec_ctx.data["key"] == "value"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_task_context_with_params(self):
        """Test create_task_context convenience function."""
        context = create_task_context(
            workflow_id="wf_001",
            recording_id="rec_001",
            project_path="/test",
            tags=["@smoke"],
            metadata={"priority": "high"},
        )

        assert context.workflow_id == "wf_001"
        assert context.recording_id == "rec_001"
        assert context.tags == ["@smoke"]
        assert context.metadata["priority"] == "high"

    def test_create_execution_context_default(self):
        """Test create_execution_context with default task context."""
        exec_ctx = create_execution_context()

        assert exec_ctx.parent_context.task_id
        assert isinstance(exec_ctx.context_chain, ContextChain)

    def test_create_execution_context_with_task(self):
        """Test create_execution_context with existing task context."""
        task_ctx = TaskContext(workflow_id="wf_001")
        exec_ctx = create_execution_context(task_ctx)

        assert exec_ctx.parent_context == task_ctx
