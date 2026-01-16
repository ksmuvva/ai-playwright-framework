"""Unit tests for E2.3 - Inter-Agent Communication skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e2_3_inter_agent_communication import (
    AgentMessage,
    CommunicationProtocol,
    InterAgentCommunicationAgent,
    MessageType,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestMessageType:
    """Test suite for MessageType enum."""

    @pytest.mark.unit
    def test_message_type_values(self):
        """Test message type enum values."""
        assert MessageType.COMMAND.value == "command"
        assert MessageType.QUERY.value == "query"
        assert MessageType.RESPONSE.value == "response"
        assert MessageType.EVENT.value == "event"
        assert MessageType.NOTIFICATION.value == "notification"


class TestAgentMessage:
    """Test suite for AgentMessage dataclass."""

    @pytest.mark.unit
    def test_agent_message_creation(self):
        """Test creating an agent message."""
        message = AgentMessage(
            message_id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type=MessageType.COMMAND,
            payload={"action": "test"},
        )

        assert message.message_id == "msg_001"
        assert message.sender_id == "agent_001"
        assert message.receiver_id == "agent_002"
        assert message.message_type == MessageType.COMMAND

    @pytest.mark.unit
    def test_agent_message_to_dict(self):
        """Test converting message to dictionary."""
        message = AgentMessage(
            message_id="msg_001",
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type=MessageType.COMMAND,
            payload={"action": "test"},
        )

        result = message.to_dict()

        assert isinstance(result, dict)
        assert result["message_id"] == "msg_001"
        assert result["sender_id"] == "agent_001"


class TestCommunicationProtocol:
    """Test suite for CommunicationProtocol dataclass."""

    @pytest.mark.unit
    def test_communication_protocol_creation(self):
        """Test creating a communication protocol."""
        protocol = CommunicationProtocol(
            protocol_id="proto_001",
            protocol_name="test_protocol",
            version="1.0.0",
        )

        assert protocol.protocol_id == "proto_001"
        assert protocol.protocol_name == "test_protocol"
        assert protocol.version == "1.0.0"


class TestInterAgentCommunicationAgent:
    """Test suite for InterAgentCommunicationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return InterAgentCommunicationAgent()

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
        assert agent.name == "e2_3_inter_agent_communication"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty registries."""
        assert hasattr(agent, "_message_queues")
        assert hasattr(agent, "_message_history")
        assert agent._message_queues == {}
        assert agent._message_history == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_send_message(self, agent):
        """Test sending a message between agents."""
        context = {
            "task_type": "send_message",
            "sender_id": "agent_001",
            "receiver_id": "agent_002",
            "message_type": MessageType.COMMAND,
            "payload": {"action": "test"},
        }

        result = await agent.run("send_message", context)

        assert "sent" in result.lower() or "message" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_receive_message(self, agent):
        """Test receiving a message."""
        context = {
            "task_type": "receive_message",
            "agent_id": "agent_002",
        }

        result = await agent.run("receive_message", context)

        assert "message" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_broadcast_message(self, agent):
        """Test broadcasting a message to multiple agents."""
        context = {
            "task_type": "broadcast_message",
            "sender_id": "agent_001",
            "message_type": MessageType.EVENT,
            "payload": {"event": "test"},
            "recipients": ["agent_002", "agent_003"],
        }

        result = await agent.run("broadcast_message", context)

        assert "broadcast" in result.lower() or "sent" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_message_history(self, agent):
        """Test getting message history."""
        context = {
            "task_type": "get_message_history",
            "agent_id": "agent_001",
        }

        result = await agent.run("get_message_history", context)

        assert "history" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_agent(self, agent):
        """Test registering an agent for communication."""
        context = {
            "task_type": "register_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("register_agent", context)

        assert "registered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_unregister_agent(self, agent):
        """Test unregistering an agent."""
        agent._message_queues["agent_001"] = []

        context = {
            "task_type": "unregister_agent",
            "agent_id": "agent_001",
        }

        result = await agent.run("unregister_agent", context)

        assert "unregistered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_message_queues(self, agent):
        """Test getting message queues."""
        agent._message_queues["agent_001"] = []

        result = agent.get_message_queues()

        assert "agent_001" in result

    @pytest.mark.unit
    def test_get_message_history(self, agent):
        """Test getting message history."""
        result = agent.get_message_history()

        assert isinstance(result, list)
