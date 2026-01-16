"""
Tests for the Agent Orchestrator system.

Tests cover:
- AgentMessage and AgentTask models
- MessageQueue functionality
- AgentLifecycleManager operations
- OrchestratorAgent basic functionality
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from claude_playwright_agent.agents import (
    AgentLifecycleManager,
    AgentMessage,
    AgentTask,
    MessageQueue,
    MessageType,
    OrchestratorAgent,
    get_orchestrator,
)
from claude_playwright_agent.state import AgentStatus


# =============================================================================
# AgentMessage Tests
# =============================================================================


class TestAgentMessage:
    """Tests for AgentMessage model."""

    def test_create_message(self) -> None:
        """Test creating a message."""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="orchestrator",
            recipient_id="agent_1",
            data={"action": "parse"},
        )

        assert message.type == MessageType.TASK
        assert message.sender_id == "orchestrator"
        assert message.recipient_id == "agent_1"
        assert message.data["action"] == "parse"

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="orchestrator",
            recipient_id="agent_1",
            data={"action": "parse"},
        )

        data = message.to_dict()

        assert data["type"] == "task"
        assert data["sender_id"] == "orchestrator"
        assert data["recipient_id"] == "agent_1"
        assert data["data"]["action"] == "parse"

    def test_message_from_dict(self) -> None:
        """Test creating message from dictionary."""
        data = {
            "id": "msg_123",
            "type": "task",
            "sender_id": "orchestrator",
            "recipient_id": "agent_1",
            "timestamp": "2025-01-11T00:00:00",
            "data": {"action": "parse"},
            "correlation_id": "",
        }

        message = AgentMessage.from_dict(data)

        assert message.id == "msg_123"
        assert message.type == MessageType.TASK
        assert message.sender_id == "orchestrator"


# =============================================================================
# AgentTask Tests
# =============================================================================


class TestAgentTask:
    """Tests for AgentTask model."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        task = AgentTask(
            task_type="ingest",
            input_data={"recording_path": "/path/to/recording.js"},
        )

        assert task.task_type == "ingest"
        assert task.input_data["recording_path"] == "/path/to/recording.js"
        assert task.status == AgentStatus.SPAWNING

    def test_task_to_dict(self) -> None:
        """Test converting task to dictionary."""
        task = AgentTask(
            task_type="ingest",
            input_data={"recording_path": "/path/to/recording.js"},
        )

        data = task.to_dict()

        assert data["task_type"] == "ingest"
        assert data["status"] == "spawning"
        assert data["input_data"]["recording_path"] == "/path/to/recording.js"


# =============================================================================
# MessageQueue Tests
# =============================================================================


class TestMessageQueue:
    """Tests for MessageQueue class."""

    @pytest.mark.asyncio
    async def test_send_and_receive_message(self) -> None:
        """Test sending and receiving a message."""
        queue = MessageQueue()
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="orchestrator",
            recipient_id="agent_1",
            data={"action": "parse"},
        )

        # Send message
        await queue.send(message)

        # Receive message
        received = await queue.receive("agent_1")

        assert received.id == message.id
        assert received.type == MessageType.TASK
        assert received.sender_id == "orchestrator"

    @pytest.mark.asyncio
    async def test_send_broadcast_message(self) -> None:
        """Test broadcasting a message."""
        queue = MessageQueue()

        # Create two agents by getting their queues
        queue.get_queue("agent_1")
        queue.get_queue("agent_2")

        message = AgentMessage(
            type=MessageType.STATUS,
            sender_id="orchestrator",
            recipient_id="",  # Empty means broadcast
            data={"status": "running"},
        )

        # Broadcast
        await queue.send(message)

        # Both agents should receive the message
        msg1 = await queue.receive("agent_1")
        msg2 = await queue.receive("agent_2")

        assert msg1.id == message.id
        assert msg2.id == message.id

    @pytest.mark.asyncio
    async def test_receive_timeout(self) -> None:
        """Test receive timeout."""
        queue = MessageQueue()

        with pytest.raises(asyncio.TimeoutError):
            await queue.receive("agent_1", timeout=0.1)

    @pytest.mark.asyncio
    async def test_has_message(self) -> None:
        """Test checking for pending messages."""
        queue = MessageQueue()
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="orchestrator",
            recipient_id="agent_1",
        )

        assert not queue.has_message("agent_1")

        await queue.send(message)

        assert queue.has_message("agent_1")

    @pytest.mark.asyncio
    async def test_close_queue(self) -> None:
        """Test closing agent queue."""
        queue = MessageQueue()
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="orchestrator",
            recipient_id="agent_1",
        )

        await queue.send(message)
        await queue.close("agent_1")

        # Queue should be removed
        assert not queue.has_message("agent_1")


# =============================================================================
# AgentLifecycleManager Tests
# =============================================================================


class TestAgentLifecycleManager:
    """Tests for AgentLifecycleManager class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test lifecycle manager initialization."""
        manager = AgentLifecycleManager(tmp_path)

        assert manager._project_path == tmp_path
        assert len(manager.get_active_agents()) == 0

    @pytest.mark.asyncio
    async def test_spawn_agent(self, tmp_path: Path) -> None:
        """Test spawning an agent."""
        manager = AgentLifecycleManager(tmp_path)

        # Create a mock agent
        agent = MagicMock()
        agent.initialize = AsyncMock()
        agent.cleanup = AsyncMock()

        await manager.spawn_agent("agent_1", "test", agent)

        # Verify agent was stored
        assert "agent_1" in manager.get_active_agents()

        # Verify initialize was called
        agent.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_agent(self, tmp_path: Path) -> None:
        """Test terminating an agent."""
        manager = AgentLifecycleManager(tmp_path)

        # Create a mock agent
        agent = MagicMock()
        agent.initialize = AsyncMock()
        agent.cleanup = AsyncMock()

        await manager.spawn_agent("agent_1", "test", agent)
        await manager.terminate_agent("agent_1")

        # Verify agent was removed
        assert "agent_1" not in manager.get_active_agents()

        # Verify cleanup was called
        agent.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_all(self, tmp_path: Path) -> None:
        """Test shutting down all agents."""
        manager = AgentLifecycleManager(tmp_path)

        # Create mock agents
        agent1 = MagicMock()
        agent1.initialize = AsyncMock()
        agent1.cleanup = AsyncMock()

        agent2 = MagicMock()
        agent2.initialize = AsyncMock()
        agent2.cleanup = AsyncMock()

        await manager.spawn_agent("agent_1", "test", agent1)
        await manager.spawn_agent("agent_2", "test", agent2)
        await manager.shutdown_all()

        # Verify all agents were removed
        assert len(manager.get_active_agents()) == 0


# =============================================================================
# OrchestratorAgent Tests
# =============================================================================


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test orchestrator initialization."""
        orchestrator = OrchestratorAgent(tmp_path)

        assert orchestrator._project_path == tmp_path
        assert isinstance(orchestrator._message_queue, MessageQueue)
        assert isinstance(orchestrator._lifecycle, AgentLifecycleManager)

    @pytest.mark.asyncio
    async def test_process_ingest_task(self, tmp_path: Path) -> None:
        """Test processing an ingest task."""
        orchestrator = OrchestratorAgent(tmp_path)
        await orchestrator.initialize()

        result = await orchestrator.process({
            "task_type": "ingest",
            "params": {
                "recording_path": "/path/to/recording.js",
            },
        })

        assert result["success"] is True
        assert "task_id" in result
        assert "result" in result

        await orchestrator.cleanup()

    @pytest.mark.asyncio
    async def test_process_unknown_task(self, tmp_path: Path) -> None:
        """Test processing an unknown task type."""
        orchestrator = OrchestratorAgent(tmp_path)
        await orchestrator.initialize()

        result = await orchestrator.process({
            "task_type": "unknown",
            "params": {},
        })

        assert result["success"] is False
        assert "error" in result

        await orchestrator.cleanup()

    @pytest.mark.asyncio
    async def test_list_agents(self, tmp_path: Path) -> None:
        """Test listing agents."""
        orchestrator = OrchestratorAgent(tmp_path)

        agents = orchestrator.list_agents()

        assert isinstance(agents, list)
        # No agents spawned yet
        assert len(agents) == 0


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_orchestrator(self, tmp_path: Path) -> None:
        """Test getting orchestrator instance."""
        from claude_playwright_agent.agents.orchestrator import _orchestrator_instance

        # Clear any existing instance
        import claude_playwright_agent.agents.orchestrator as orchestrator_module
        orchestrator_module._orchestrator_instance = None

        orchestrator = get_orchestrator(tmp_path)

        assert isinstance(orchestrator, OrchestratorAgent)
        assert orchestrator._project_path == tmp_path

    def test_get_orchestrator_singleton(self, tmp_path: Path) -> None:
        """Test that get_orchestrator returns singleton."""
        from claude_playwright_agent.agents.orchestrator import _orchestrator_instance

        # Clear any existing instance
        import claude_playwright_agent.agents.orchestrator as orchestrator_module
        orchestrator_module._orchestrator_instance = None

        orchestrator1 = get_orchestrator(tmp_path)
        orchestrator2 = get_orchestrator(tmp_path)

        # Should be the same instance
        assert orchestrator1 is orchestrator2
