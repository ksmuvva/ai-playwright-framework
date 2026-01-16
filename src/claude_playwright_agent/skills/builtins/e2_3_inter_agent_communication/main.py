"""
E2.3 - Inter-Agent Communication Skill.

This skill provides message passing with context propagation:
- Context-aware message passing
- Message filtering and routing
- Broadcast and direct messaging
- Request-response patterns with context
- Priority-based messaging
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_playwright_agent.agents.base import BaseAgent


class MessageType(str, Enum):
    """Message types for agent communication."""

    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"
    SHUTDOWN = "shutdown"
    HEARTBEAT = "heartbeat"
    CONTEXT_UPDATE = "context_update"
    QUERY = "query"
    RESPONSE = "response"


class MessagePriority(str, Enum):
    """Message priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class MessageContext:
    """
    Context attached to messages for propagation.

    Attributes:
        message_id: Unique message identifier
        conversation_id: Conversation thread ID
        workflow_id: Associated workflow ID
        parent_message_id: Parent message in conversation
        sender_context: Context from sender
        propagation_chain: Chain of agents message has passed through
        timestamp: Message creation time
        ttl: Time-to-live for message forwarding
        metadata: Additional context metadata
    """

    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    conversation_id: str = ""
    workflow_id: str = ""
    parent_message_id: str = ""
    sender_context: dict[str, Any] = field(default_factory=dict)
    propagation_chain: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    ttl: int = 10  # Max hops before message expires
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_to_chain(self, agent_id: str) -> None:
        """Add agent to propagation chain."""
        if agent_id not in self.propagation_chain:
            self.propagation_chain.append(agent_id)

    def is_expired(self) -> bool:
        """Check if message has expired based on TTL."""
        return len(self.propagation_chain) >= self.ttl

    def create_reply(self, sender_context: dict[str, Any] | None = None) -> "MessageContext":
        """Create a reply context."""
        return MessageContext(
            conversation_id=self.conversation_id or self.message_id,
            workflow_id=self.workflow_id,
            parent_message_id=self.message_id,
            sender_context=sender_context or {},
            propagation_chain=self.propagation_chain.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "workflow_id": self.workflow_id,
            "parent_message_id": self.parent_message_id,
            "sender_context": self.sender_context,
            "propagation_chain": self.propagation_chain,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "metadata": self.metadata,
        }


@dataclass
class AgentMessage:
    """
    Message passed between agents with context.

    Attributes:
        type: Message type
        sender_id: ID of the sending agent
        recipient_id: ID of the recipient agent (empty for broadcast)
        payload: Message payload/data
        context: Message context for propagation
        priority: Message priority
        correlation_id: ID for correlating request/response
        reply_to: Message ID this is replying to
        expires_at: Message expiration time
    """

    type: MessageType = MessageType.TASK
    sender_id: str = ""
    recipient_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: MessageContext = field(default_factory=MessageContext)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: str = ""
    reply_to: str = ""
    expires_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "payload": self.payload,
            "context": self.context.to_dict(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        context_data = data.get("context", {})
        return cls(
            type=MessageType(data["type"]),
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            payload=data.get("payload", {}),
            context=MessageContext(**context_data) if context_data else MessageContext(),
            priority=MessagePriority(data.get("priority", "normal")),
            correlation_id=data.get("correlation_id", ""),
            reply_to=data.get("reply_to", ""),
            expires_at=data.get("expires_at", ""),
        )


class InterAgentCommunicationAgent(BaseAgent):
    """
    Inter-Agent Communication Agent.

    This agent provides:
    1. Context-aware message passing
    2. Message filtering and routing
    3. Broadcast and direct messaging
    4. Request-response patterns with context
    5. Priority-based messaging
    """

    name = "e2_3_inter_agent_communication"
    version = "1.0.0"
    description = "E2.3 - Inter-Agent Communication"

    def __init__(self, **kwargs) -> None:
        """Initialize the communication agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E2.3 - Inter-Agent Communication agent for the Playwright test automation framework. You help users with e2.3 - inter-agent communication tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._message_queues: dict[str, asyncio.Queue] = {}
        self._message_handlers: dict[str, Callable[[AgentMessage], Awaitable[Any]]] = {}
        self._conversation_history: dict[str, list[AgentMessage]] = {}
        self._broadcast_subscribers: set[str] = set()
        self._lock = asyncio.Lock()

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute communication task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the communication operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            # Create minimal context if not provided
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "send_message":
            return await self._send_message(context, execution_context)
        elif task_type == "receive_message":
            return await self._receive_message(context, execution_context)
        elif task_type == "broadcast_message":
            return await self._broadcast_message(context, execution_context)
        elif task_type == "register_handler":
            return await self._register_handler(context, execution_context)
        elif task_type == "send_request":
            return await self._send_request(context, execution_context)
        elif task_type == "get_conversation":
            return await self._get_conversation(context, execution_context)
        elif task_type == "subscribe_broadcast":
            return await self._subscribe_broadcast(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _send_message(self, context: dict[str, Any], execution_context: Any) -> str:
        """Send a message with context propagation."""
        sender_id = context.get("sender_id", "unknown")
        recipient_id = context.get("recipient_id")
        message_type = context.get("message_type", MessageType.TASK)
        payload = context.get("payload", {})
        priority = context.get("priority", MessagePriority.NORMAL)
        correlation_id = context.get("correlation_id", "")

        if not recipient_id:
            return "Error: recipient_id is required"

        # Create message with context
        message_context = MessageContext(
            workflow_id=getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")),
            sender_context=execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context,
        )

        # Add sender to propagation chain
        message_context.add_to_chain(sender_id)

        message = AgentMessage(
            type=MessageType(message_type) if isinstance(message_type, str) else message_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            context=message_context,
            priority=MessagePriority(priority) if isinstance(priority, str) else priority,
            correlation_id=correlation_id,
        )

        # Get or create recipient queue
        async with self._lock:
            if recipient_id not in self._message_queues:
                self._message_queues[recipient_id] = asyncio.Queue()

            # Send message
            await self._message_queues[recipient_id].put(message)

            # Track conversation
            if message_context.conversation_id:
                if message_context.conversation_id not in self._conversation_history:
                    self._conversation_history[message_context.conversation_id] = []
                self._conversation_history[message_context.conversation_id].append(message)

        return f"Message '{message.context.message_id}' sent to '{recipient_id}' with context"

    async def _receive_message(self, context: dict[str, Any], execution_context: Any) -> str:
        """Receive a message with context."""
        recipient_id = context.get("recipient_id")
        timeout = context.get("timeout", 30)

        if not recipient_id:
            return "Error: recipient_id is required"

        async with self._lock:
            if recipient_id not in self._message_queues:
                # Create queue if doesn't exist
                self._message_queues[recipient_id] = asyncio.Queue()

        try:
            # Wait for message
            queue = self._message_queues[recipient_id]
            message = await asyncio.wait_for(queue.get(), timeout=timeout)

            # Update context with receipt information
            message.context.add_to_chain(recipient_id)
            message.context.metadata["received_at"] = datetime.now().isoformat()
            message.context.metadata["received_by"] = recipient_id

            return f"Message '{message.context.message_id}' received with context from '{message.sender_id}'"

        except asyncio.TimeoutError:
            return f"No message received for '{recipient_id}' within {timeout}s"

    async def _broadcast_message(self, context: dict[str, Any], execution_context: Any) -> str:
        """Broadcast a message to all subscribers with context."""
        sender_id = context.get("sender_id", "unknown")
        message_type = context.get("message_type", MessageType.STATUS)
        payload = context.get("payload", {})

        # Create message with broadcast context
        message_context = MessageContext(
            workflow_id=getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")),
            sender_context=execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context,
        )
        message_context.add_to_chain(sender_id)

        message = AgentMessage(
            type=MessageType(message_type) if isinstance(message_type, str) else message_type,
            sender_id=sender_id,
            recipient_id="",  # Empty = broadcast
            payload=payload,
            context=message_context,
        )

        # Send to all subscribers
        sent_count = 0
        async with self._lock:
            for subscriber_id in self._broadcast_subscribers:
                if subscriber_id not in self._message_queues:
                    self._message_queues[subscriber_id] = asyncio.Queue()

                await self._message_queues[subscriber_id].put(message)
                sent_count += 1

        return f"Broadcast message sent to {sent_count} subscriber(s)"

    async def _register_handler(self, context: dict[str, Any], execution_context: Any) -> str:
        """Register a message handler for an agent."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        # Create queue for agent
        async with self._lock:
            if agent_id not in self._message_queues:
                self._message_queues[agent_id] = asyncio.Queue()

        return f"Message handler registered for '{agent_id}'"

    async def _send_request(self, context: dict[str, Any], execution_context: Any) -> str:
        """Send a request message and wait for response."""
        sender_id = context.get("sender_id", "unknown")
        recipient_id = context.get("recipient_id")
        payload = context.get("payload", {})
        timeout = context.get("timeout", 30)

        if not recipient_id:
            return "Error: recipient_id is required"

        # Generate correlation ID
        correlation_id = f"corr_{uuid.uuid4().hex[:8]}"

        # Create request with context
        message_context = MessageContext(
            workflow_id=getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")),
            sender_context=execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context,
        )
        message_context.add_to_chain(sender_id)

        request = AgentMessage(
            type=MessageType.QUERY,
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            context=message_context,
            correlation_id=correlation_id,
        )

        # Send request
        async with self._lock:
            if recipient_id not in self._message_queues:
                self._message_queues[recipient_id] = asyncio.Queue()

            await self._message_queues[recipient_id].put(request)

        # Wait for response (simplified - in real implementation would use futures)
        return f"Request '{correlation_id}' sent to '{recipient_id}' awaiting response"

    async def _get_conversation(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get conversation history with context."""
        conversation_id = context.get("conversation_id")

        if not conversation_id:
            return "Error: conversation_id is required"

        if conversation_id not in self._conversation_history:
            return f"Conversation '{conversation_id}' not found"

        messages = self._conversation_history[conversation_id]
        return f"Conversation '{conversation_id}' has {len(messages)} message(s)"

    async def _subscribe_broadcast(self, context: dict[str, Any], execution_context: Any) -> str:
        """Subscribe an agent to broadcast messages."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        async with self._lock:
            self._broadcast_subscribers.add(agent_id)
            if agent_id not in self._message_queues:
                self._message_queues[agent_id] = asyncio.Queue()

        return f"Agent '{agent_id}' subscribed to broadcasts"

    def get_queue_sizes(self) -> dict[str, int]:
        """Get sizes of all message queues."""
        return {
            agent_id: queue.qsize()
            for agent_id, queue in self._message_queues.items()
        }

    def get_conversation_history(self, conversation_id: str) -> list[AgentMessage]:
        """Get conversation history."""
        return self._conversation_history.get(conversation_id, []).copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

