"""
Inter-Agent Communication Module

Provides asynchronous message passing between agents.
Supports pub/sub messaging patterns for multi-agent workflows.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Priority levels for agent messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """
    Message passed between agents.

    Attributes:
        id: Unique message identifier
        sender: Name of the sending agent
        channel: Channel/topic name
        payload: Message data
        priority: Message priority
        timestamp: When message was created
        correlation_id: Optional ID for correlating request/response
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    channel: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "channel": self.channel,
            "payload": self.payload,
            "priority": self.priority.name,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender=data.get("sender", ""),
            channel=data.get("channel", ""),
            payload=data.get("payload", {}),
            priority=MessagePriority[data.get("priority", "NORMAL")],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            correlation_id=data.get("correlation_id")
        )


class AgentChannel:
    """
    A channel for agent communication (topic-based pub/sub).

    Example:
        >>> channel = AgentChannel("test_updates")
        >>> await channel.publish(AgentMessage(
        ...     sender="TestAgent",
        ...     channel="test_updates",
        ...     payload={"test": "status", "status": "passed"}
        ... ))
    """

    def __init__(self, name: str):
        """
        Initialize an agent channel.

        Args:
            name: Channel name
        """
        self.name = name
        self._subscribers: Set[str] = set()
        self._message_history: List[AgentMessage] = []
        self._max_history = 1000

    def subscribe(self, agent_id: str) -> None:
        """
        Subscribe an agent to this channel.

        Args:
            agent_id: Agent identifier
        """
        self._subscribers.add(agent_id)
        logger.debug(f"Agent {agent_id} subscribed to channel '{self.name}'")

    def unsubscribe(self, agent_id: str) -> None:
        """
        Unsubscribe an agent from this channel.

        Args:
            agent_id: Agent identifier
        """
        self._subscribers.discard(agent_id)
        logger.debug(f"Agent {agent_id} unsubscribed from channel '{self.name}'")

    def get_subscribers(self) -> Set[str]:
        """Get all subscribed agent IDs."""
        return self._subscribers.copy()

    def add_to_history(self, message: AgentMessage) -> None:
        """
        Add message to channel history.

        Args:
            message: Message to add
        """
        self._message_history.append(message)

        # Keep only recent messages
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

    def get_history(self, limit: int = 100) -> List[AgentMessage]:
        """
        Get message history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self._message_history[-limit:]

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"AgentChannel(name='{self.name}', subscribers={len(self._subscribers)})"


class AgentBus:
    """
    Async message bus for inter-agent communication.

    Implements pub/sub pattern with channels and message routing.

    Example:
        >>> bus = AgentBus()
        >>> await bus.start()
        >>>
        >>> # Subscribe to channel
        >>> bus.subscribe("test_channel", agent_instance)
        >>>
        >>> # Publish message
        >>> message = AgentMessage(
        ...     sender="Agent1",
        ...     channel="test_channel",
        ...     payload={"data": "value"}
        ... )
        >>> await bus.publish(message)
    """

    def __init__(self):
        """Initialize the agent bus."""
        self.channels: Dict[str, AgentChannel] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._subscriber_callbacks: Dict[str, Callable[[AgentMessage], None]] = {}

    async def start(self) -> None:
        """Start the message bus worker."""
        if self._running:
            logger.warning("AgentBus already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_messages())
        logger.info("AgentBus started")

    async def stop(self) -> None:
        """Stop the message bus worker."""
        if not self._running:
            return

        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("AgentBus stopped")

    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._deliver_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _deliver_message(self, message: AgentMessage) -> None:
        """
        Deliver message to all subscribers of its channel.

        Args:
            message: Message to deliver
        """
        channel = self.channels.get(message.channel)

        if not channel:
            logger.warning(f"Channel '{message.channel}' not found, message not delivered")
            return

        subscribers = channel.get_subscribers()

        if not subscribers:
            logger.debug(f"No subscribers for channel '{message.channel}'")
            return

        # Add to channel history
        channel.add_to_history(message)

        # Deliver to each subscriber
        for subscriber_id in subscribers:
            callback = self._subscriber_callbacks.get(subscriber_id)

            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(
                        f"Error delivering message to {subscriber_id}: {e}"
                    )

    def create_channel(self, channel_name: str) -> AgentChannel:
        """
        Create a new channel.

        Args:
            channel_name: Name for the channel

        Returns:
            Created AgentChannel
        """
        if channel_name in self.channels:
            logger.warning(f"Channel '{channel_name}' already exists")
            return self.channels[channel_name]

        channel = AgentChannel(channel_name)
        self.channels[channel_name] = channel
        logger.info(f"Created channel: {channel_name}")
        return channel

    def subscribe(
        self,
        channel_name: str,
        agent_id: str,
        callback: Callable[[AgentMessage], None]
    ) -> None:
        """
        Subscribe an agent to a channel.

        Args:
            channel_name: Channel to subscribe to
            agent_id: Agent identifier
            callback: Function to call when message received
        """
        # Create channel if it doesn't exist
        if channel_name not in self.channels:
            self.create_channel(channel_name)

        # Subscribe to channel
        self.channels[channel_name].subscribe(agent_id)

        # Store callback
        self._subscriber_callbacks[agent_id] = callback

        logger.info(f"Agent {agent_id} subscribed to '{channel_name}'")

    def unsubscribe(self, channel_name: str, agent_id: str) -> None:
        """
        Unsubscribe an agent from a channel.

        Args:
            channel_name: Channel to unsubscribe from
            agent_id: Agent identifier
        """
        if channel_name not in self.channels:
            logger.warning(f"Channel '{channel_name}' not found")
            return

        self.channels[channel_name].unsubscribe(agent_id)

        # Remove callback if agent has no more subscriptions
        has_other_subscriptions = any(
            agent_id in ch.get_subscribers()
            for ch in self.channels.values()
            if ch.name != channel_name
        )

        if not has_other_subscriptions:
            self._subscriber_callbacks.pop(agent_id, None)

        logger.info(f"Agent {agent_id} unsubscribed from '{channel_name}'")

    async def publish(self, message: AgentMessage) -> None:
        """
        Publish a message to a channel.

        Args:
            message: Message to publish
        """
        if not self._running:
            logger.warning("AgentBus not running, message not published")
            return

        await self._message_queue.put(message)
        logger.debug(
            f"Message published to '{message.channel}' "
            f"(id: {message.id}, sender: {message.sender})"
        )

    def get_channel(self, channel_name: str) -> Optional[AgentChannel]:
        """
        Get a channel by name.

        Args:
            channel_name: Channel name

        Returns:
            AgentChannel or None if not found
        """
        return self.channels.get(channel_name)

    def get_all_channels(self) -> Dict[str, AgentChannel]:
        """Get all channels."""
        return self.channels.copy()

    def get_channel_stats(self, channel_name: str) -> Dict[str, Any]:
        """
        Get statistics for a channel.

        Args:
            channel_name: Channel name

        Returns:
            Statistics dictionary
        """
        channel = self.channels.get(channel_name)

        if not channel:
            return {"error": "Channel not found"}

        history = channel.get_history()

        return {
            "name": channel.name,
            "subscribers": len(channel.get_subscribers()),
            "total_messages": len(history),
            "last_message": history[-1].to_dict() if history else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"AgentBus(channels={len(self.channels)}, running={self._running})"
