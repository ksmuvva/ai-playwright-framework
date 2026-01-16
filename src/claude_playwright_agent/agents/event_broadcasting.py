"""
Inter-agent event broadcasting for Claude Playwright Agent.

This module implements:
- Event publishing and subscription system
- Event filtering based on agent interests
- Event history and replay
- Context-aware event delivery
- Event-based agent coordination
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable

# =============================================================================
# Event Types
# =============================================================================


class EventType(str, Enum):
    """Standard event types for agent communication."""
    # Lifecycle events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_TERMINATED = "agent_terminated"
    AGENT_FAILED = "agent_failed"
    AGENT_TIMEOUT = "agent_timeout"

    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"

    # Resource events
    RESOURCE_WARNING = "resource_warning"
    RESOURCE_EXCEEDED = "resource_exceeded"

    # Data events
    DATA_AVAILABLE = "data_available"
    DATA_PROCESSED = "data_processed"
    DATA_ERROR = "data_error"

    # System events
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"

    # Custom events
    CUSTOM = "custom"


@dataclass
class AgentEvent:
    """
    Event that can be broadcast between agents.

    Attributes:
        id: Unique event identifier
        type: Event type
        source: Source agent ID
        timestamp: Event creation time
        data: Event payload data
        context: Execution context for the event
        correlation_id: ID for correlating related events
        ttl: Time-to-live for event (seconds)
    """

    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    type: EventType = EventType.CUSTOM
    source: str = "system"
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    ttl: float | None = None

    def is_expired(self) -> bool:
        """Check if event has expired based on TTL."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentEvent":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            source=data["source"],
            timestamp=data["timestamp"],
            data=data["data"],
            context=data.get("context", {}),
            correlation_id=data.get("correlation_id", ""),
            ttl=data.get("ttl"),
        )


# =============================================================================
# Event Subscription
# =============================================================================


@dataclass
class EventSubscription:
    """
    Subscription to events for an agent.

    Attributes:
        agent_id: Agent subscribing to events
        event_types: List of event types to subscribe to
        filter_func: Optional function to filter events
        handler: Async function to call when event received
    """

    agent_id: str
    event_types: list[EventType] = field(default_factory=list)
    filter_func: Callable[[AgentEvent], bool] | None = None
    handler: Callable[[AgentEvent], Awaitable[None]] | None = None

    def matches(self, event: AgentEvent) -> bool:
        """
        Check if subscription matches an event.

        Args:
            event: Event to check

        Returns:
            True if subscription matches event
        """
        # Check event type
        if self.event_types and event.type not in self.event_types:
            return False

        # Check custom filter
        if self.filter_func and not self.filter_func(event):
            return False

        return True


# =============================================================================
# Event Bus
# =============================================================================


class EventBus:
    """
    Event bus for inter-agent communication.

    Features:
    - Publish/subscribe pattern for events
    - Event filtering and routing
    - Event history and replay
    - Wildcard subscriptions
    - Context-aware delivery
    """

    def __init__(
        self,
        max_history: int = 1000,
        enable_replay: bool = True,
    ) -> None:
        """
        Initialize the event bus.

        Args:
            max_history: Maximum events to keep in history
            enable_replay: Whether to enable event replay
        """
        self._subscriptions: dict[str, list[EventSubscription]] = {}
        self._event_history: list[AgentEvent] = []
        self._max_history = max_history
        self._enable_replay = enable_replay
        self._lock = asyncio.Lock()

        # Statistics
        self._stats: dict[str, int] = {
            "events_published": 0,
            "events_delivered": 0,
            "events_dropped": 0,
        }

    async def subscribe(
        self,
        agent_id: str,
        event_types: list[EventType] | None = None,
        filter_func: Callable[[AgentEvent], bool] | None = None,
        handler: Callable[[AgentEvent], Awaitable[None]] | None = None,
    ) -> None:
        """
        Subscribe an agent to events.

        Args:
            agent_id: Agent to subscribe
            event_types: Event types to subscribe (None = all)
            filter_func: Optional filter function
            handler: Optional async handler for events
        """
        async with self._lock:
            subscription = EventSubscription(
                agent_id=agent_id,
                event_types=event_types or [],
                filter_func=filter_func,
                handler=handler,
            )

            if agent_id not in self._subscriptions:
                self._subscriptions[agent_id] = []

            self._subscriptions[agent_id].append(subscription)

    async def unsubscribe(
        self,
        agent_id: str,
        event_types: list[EventType] | None = None,
    ) -> None:
        """
        Unsubscribe an agent from events.

        Args:
            agent_id: Agent to unsubscribe
            event_types: Event types to unsubscribe (None = all)
        """
        async with self._lock:
            if agent_id not in self._subscriptions:
                return

            if event_types is None:
                # Remove all subscriptions for agent
                del self._subscriptions[agent_id]
            else:
                # Remove specific event type subscriptions
                subs = self._subscriptions[agent_id]
                self._subscriptions[agent_id] = [
                    s for s in subs
                    if not any(et in s.event_types for et in event_types)
                ]

                if not self._subscriptions[agent_id]:
                    del self._subscriptions[agent_id]

    async def publish(
        self,
        event: AgentEvent,
        context: dict[str, Any] | None = None,
    ) -> int:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
            context: Optional context to add to event

        Returns:
            Number of subscribers the event was delivered to
        """
        # Add context if provided
        if context:
            event.context.update(context)

        # Check if event is expired
        if event.is_expired():
            self._stats["events_dropped"] += 1
            return 0

        async with self._lock:
            # Add to history
            if self._enable_replay:
                self._event_history.append(event)
                if len(self._event_history) > self._max_history:
                    self._event_history.pop(0)

            self._stats["events_published"] += 1

            # Find matching subscriptions
            delivered_count = 0
            delivery_tasks = []

            for agent_id, subscriptions in self._subscriptions.items():
                # Skip the source agent
                if agent_id == event.source:
                    continue

                for subscription in subscriptions:
                    if subscription.matches(event):
                        # Create delivery task
                        if subscription.handler:
                            task = asyncio.create_task(
                                self._deliver_event(subscription, event)
                            )
                            delivery_tasks.append(task)
                        delivered_count += 1

            # Wait for all deliveries (with timeout)
            if delivery_tasks:
                await asyncio.wait(delivery_tasks, timeout=5.0)

            self._stats["events_delivered"] += delivered_count
            return delivered_count

    async def _deliver_event(
        self,
        subscription: EventSubscription,
        event: AgentEvent,
    ) -> None:
        """
        Deliver an event to a subscription handler.

        Args:
            subscription: Subscription to deliver to
            event: Event to deliver
        """
        try:
            if subscription.handler:
                await subscription.handler(event)
        except Exception:
            # Log error but don't fail other deliveries
            pass

    async def broadcast(
        self,
        event_type: EventType,
        source: str,
        data: dict[str, Any],
        context: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> int:
        """
        Broadcast an event (convenience method).

        Args:
            event_type: Type of event
            source: Source agent ID
            data: Event data
            context: Optional context
            correlation_id: Optional correlation ID

        Returns:
            Number of subscribers delivered to
        """
        event = AgentEvent(
            type=event_type,
            source=source,
            data=data,
            context=context or {},
            correlation_id=correlation_id,
        )
        return await self.publish(event)

    def get_history(
        self,
        agent_id: str | None = None,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[AgentEvent]:
        """
        Get event history.

        Args:
            agent_id: Filter by source agent
            event_type: Filter by event type
            limit: Maximum events to return

        Returns:
            List of historical events
        """
        events = self._event_history

        # Apply filters
        if agent_id:
            events = [e for e in events if e.source == agent_id]

        if event_type:
            events = [e for e in events if e.type == event_type]

        # Return most recent first
        return list(reversed(events[-limit:]))

    async def replay(
        self,
        agent_id: str,
        since: float | None = None,
        event_types: list[EventType] | None = None,
    ) -> list[AgentEvent]:
        """
        Replay events for an agent that may have missed them.

        Args:
            agent_id: Agent to replay events for
            since: Timestamp to replay from (None = all history)
            event_types: Event types to replay (None = all)

        Returns:
            List of replayed events
        """
        events = []

        async with self._lock:
            for event in self._event_history:
                # Filter by time
                if since and event.timestamp < since:
                    continue

                # Filter by event type
                if event_types and event.type not in event_types:
                    continue

                # Check if agent would have received this event
                # (based on current subscriptions)
                subscriptions = self._subscriptions.get(agent_id, [])
                for subscription in subscriptions:
                    if subscription.matches(event):
                        events.append(event)
                        break

        return events

    def get_subscribers(self, event_type: EventType | None = None) -> list[str]:
        """
        Get list of subscribers.

        Args:
            event_type: Filter by event type (None = all subscribers)

        Returns:
            List of agent IDs
        """
        subscribers = set()

        for agent_id, subscriptions in self._subscriptions.items():
            for subscription in subscriptions:
                if event_type is None or event_type in subscription.event_types:
                    subscribers.add(agent_id)
                    break

        return list(subscribers)

    def get_stats(self) -> dict[str, int]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "active_subscriptions": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
            "history_size": len(self._event_history),
        }

    async def clear_history(self) -> None:
        """Clear event history."""
        async with self._lock:
            self._event_history.clear()


# =============================================================================
# Global Event Bus
# =============================================================================


_event_bus_instance: EventBus | None = None


def get_event_bus(
    max_history: int = 1000,
    enable_replay: bool = True,
) -> EventBus:
    """
    Get the singleton event bus instance.

    Args:
        max_history: Maximum events to keep in history
        enable_replay: Whether to enable event replay

    Returns:
        EventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus(
            max_history=max_history,
            enable_replay=enable_replay,
        )
    return _event_bus_instance
