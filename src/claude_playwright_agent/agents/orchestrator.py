"""
Agent Orchestration System for Claude Playwright Agent.

This module implements:
- Message queue for inter-agent communication
- Priority-based task scheduling
- Agent lifecycle management
- OrchestratorAgent for coordinating specialist agents
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.priority_messaging import (
    PriorityMessageQueue,
    TaskPriority,
    PrioritizedMessage,
)
from claude_playwright_agent.agents.resource_limits import (
    ResourceLimitManager,
    ResourceLimitError,
    ResourceType,
)
from claude_playwright_agent.agents.event_broadcasting import (
    EventBus,
    EventType,
    AgentEvent,
    get_event_bus,
)
from claude_playwright_agent.state import StateManager, AgentStatus

# =============================================================================
# Agent Message Types
# =============================================================================


class MessageType(str, Enum):
    """Message types for agent communication."""
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"
    SHUTDOWN = "shutdown"
    HEARTBEAT = "heartbeat"


@dataclass
class AgentMessage:
    """
    Message passed between agents.

    Attributes:
        id: Unique message identifier
        type: Message type
        sender_id: ID of the sending agent
        recipient_id: ID of the recipient agent (empty for broadcast)
        timestamp: Message creation time
        data: Message payload
        correlation_id: ID for correlating request/response
    """

    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex}")
    type: MessageType = MessageType.TASK
    sender_id: str = "orchestrator"
    recipient_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            timestamp=data["timestamp"],
            data=data["data"],
            correlation_id=data.get("correlation_id", ""),
        )


@dataclass
class AgentTask:
    """
    Task assigned to an agent by the orchestrator.

    Attributes:
        id: Unique task identifier
        task_type: Type of task (ingest, parse, deduplicate, etc.)
        input_data: Task input data
        agent_id: ID of agent assigned to the task
        status: Current task status
        created_at: Task creation time
        started_at: Task start time
        completed_at: Task completion time
        result: Task result
        error: Error message if failed
    """

    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex}")
    task_type: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    status: AgentStatus = AgentStatus.SPAWNING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    completed_at: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "input_data": self.input_data,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


# =============================================================================
# Message Queue (Priority-Enabled)
# =============================================================================


class MessageQueue:
    """
    Async message queue with priority support for inter-agent communication.

    Features:
    - Thread-safe message passing
    - Priority-based message ordering
    - Agent-specific queues
    - Broadcast messaging
    - Message aging to prevent starvation
    - Context-aware priority assignment

    This class wraps PriorityMessageQueue for backward compatibility.
    """

    def __init__(
        self,
        aging_enabled: bool = True,
        aging_interval: float = 5.0,
        max_queue_size: int = 1000,
    ) -> None:
        """
        Initialize the message queue.

        Args:
            aging_enabled: Whether to enable message aging
            aging_interval: Seconds between aging updates
            max_queue_size: Maximum messages per queue
        """
        self._priority_queue = PriorityMessageQueue(
            aging_enabled=aging_enabled,
            aging_interval=aging_interval,
            max_queue_size=max_queue_size,
        )
        self._started = False

    async def start(self) -> None:
        """Start the priority queue."""
        if not self._started:
            await self._priority_queue.start()
            self._started = True

    def get_queue(self, agent_id: str) -> "MessageQueue":
        """
        Get or create queue for an agent (for backward compatibility).

        This method pre-initializes a queue for an agent.
        Note: This returns the MessageQueue itself, not the internal queue.

        Args:
            agent_id: Agent identifier

        Returns:
            self (for backward compatibility)
        """
        # Pre-initialize the agent's queue by checking its size
        _ = self._priority_queue.get_queue_size(agent_id)
        return self

    async def stop(self) -> None:
        """Stop the priority queue."""
        if self._started:
            await self._priority_queue.stop()
            self._started = False

    async def send(
        self,
        message: AgentMessage,
        priority: TaskPriority | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Send a message to a recipient with optional priority.

        Args:
            message: Message to send
            priority: Optional priority level (inferred if not provided)
            context: Optional execution context for priority calculation
        """
        if message.recipient_id:
            # Direct message
            await self._priority_queue.enqueue(message, priority, context)
        else:
            # Broadcast to all agents
            # We need to get all agents and send to each one
            # For now, we'll enqueue with a special broadcast marker
            await self._priority_queue.enqueue(message, priority, context)

    async def receive(
        self,
        agent_id: str,
        timeout: float | None = None,
    ) -> AgentMessage:
        """
        Receive the highest priority message for an agent.

        Args:
            agent_id: Agent identifier
            timeout: Timeout in seconds

        Returns:
            Received message

        Raises:
            asyncio.TimeoutError: If timeout expires
        """
        message = await self._priority_queue.dequeue(agent_id, timeout)
        if message is None:
            raise asyncio.TimeoutError()
        return message

    def has_message(self, agent_id: str) -> bool:
        """
        Check if agent has pending messages.

        Args:
            agent_id: Agent identifier

        Returns:
            True if messages are pending
        """
        return self._priority_queue.get_queue_size(agent_id) > 0

    async def close(self, agent_id: str) -> None:
        """
        Close queue for an agent.

        Args:
            agent_id: Agent identifier
        """
        await self._priority_queue.clear(agent_id)

    async def peek(self, agent_id: str) -> AgentMessage | None:
        """
        Peek at the next message without removing it.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentMessage or None if queue empty
        """
        return await self._priority_queue.peek(agent_id)

    def get_queue_size(self, agent_id: str) -> int:
        """
        Get the number of messages in an agent's queue.

        Args:
            agent_id: Agent identifier

        Returns:
            Queue size
        """
        return self._priority_queue.get_queue_size(agent_id)

    def get_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        """
        Get queue statistics.

        Args:
            agent_id: Specific agent or None for all agents

        Returns:
            Statistics dictionary
        """
        return self._priority_queue.get_stats(agent_id)


# =============================================================================
# Agent Lifecycle Manager
# =============================================================================


class AgentLifecycleManager:
    """
    Manages the lifecycle of specialist agents.

    Features:
    - Spawn agents with context tracking
    - Monitor agent health with heartbeat
    - Timeout detection and recovery
    - Context-aware health checks
    - Handle agent completion
    - Clean up terminated agents
    - Resource limit enforcement
    """

    def __init__(
        self,
        project_path: Path | None = None,
        heartbeat_interval: float = 30.0,
        agent_timeout: float = 300.0,
        max_concurrent_agents: int = 10,
        enable_resource_limits: bool = True,
    ) -> None:
        """
        Initialize the lifecycle manager.

        Args:
            project_path: Path to project root
            heartbeat_interval: Seconds between heartbeat checks
            agent_timeout: Seconds before agent is considered timed out
            max_concurrent_agents: Maximum number of concurrent agents
            enable_resource_limits: Whether to enable resource limit tracking
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._state = StateManager(self._project_path)
        self._agents: dict[str, BaseAgent] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._agent_timeout = agent_timeout
        # Health tracking: agent_id -> last_heartbeat_time
        self._last_heartbeat: dict[str, float] = {}
        # Health metrics: agent_id -> heartbeat_count
        self._heartbeat_count: dict[str, int] = {}
        # Context tracking
        self._agent_contexts: dict[str, str] = {}  # agent_id -> task_id
        # Resource limit management
        self._enable_resource_limits = enable_resource_limits
        self._resource_manager: ResourceLimitManager | None = None
        if enable_resource_limits:
            self._resource_manager = ResourceLimitManager(
                max_concurrent_agents=max_concurrent_agents,
            )

    async def spawn_agent(
        self,
        agent_id: str,
        agent_type: str,
        agent: BaseAgent,
        task_id: str = "",
    ) -> None:
        """
        Spawn a new agent.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (ingest, parse, deduplicate, etc.)
            agent: Agent instance
            task_id: Optional task ID for context tracking

        Raises:
            ResourceLimitError: If resource limits prevent spawning
        """
        async with self._lock:
            # Check resource limits before spawning
            if self._resource_manager:
                try:
                    import psutil
                    process = psutil.Process()
                    await self._resource_manager.register_agent(
                        agent_id,
                        process=process,
                        context={"agent_type": agent_type, "task_id": task_id},
                    )
                except ResourceLimitError as e:
                    self._state.update_agent_task(
                        agent_id,
                        AgentStatus.FAILED,
                        error_message=f"Resource limit exceeded: {e}",
                    )
                    raise

            # Store agent
            self._agents[agent_id] = agent

            # Initialize agent
            await agent.initialize()

            # Record in state
            self._state.add_agent_task(
                agent_id=agent_id,
                agent_type=agent_type,
                parent_task_id=task_id,
            )
            self._state.update_agent_task(agent_id, AgentStatus.RUNNING)

            # Initialize health tracking
            self._last_heartbeat[agent_id] = time.time()
            self._heartbeat_count[agent_id] = 0

            # Store context mapping
            if task_id:
                self._agent_contexts[agent_id] = task_id

            # Start heartbeat task
            self._tasks[agent_id] = asyncio.create_task(
                self._monitor_agent(agent_id, agent)
            )

    async def terminate_agent(self, agent_id: str) -> None:
        """
        Terminate an agent.

        Args:
            agent_id: Agent identifier
        """
        async with self._lock:
            # Unregister from resource manager
            if self._resource_manager:
                final_usage = await self._resource_manager.unregister_agent(agent_id)
                if final_usage:
                    # Store final resource usage in state
                    self._state.update_agent_task(
                        agent_id,
                        AgentStatus.COMPLETED,
                        result={"resource_usage": final_usage.to_dict()},
                    )

            if agent_id in self._agents:
                # Cleanup agent
                agent = self._agents[agent_id]
                await agent.cleanup()
                del self._agents[agent_id]

            # Cancel monitoring task
            if agent_id in self._tasks:
                task = self._tasks[agent_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self._tasks[agent_id]

            # Clean up health tracking
            self._last_heartbeat.pop(agent_id, None)
            self._heartbeat_count.pop(agent_id, None)

            # Clean up context mapping
            task_id = self._agent_contexts.pop(agent_id, None)
            if task_id:
                # Note: Context cleanup is handled by ContextPropagator
                pass

            # Update state
            self._state.update_agent_task(agent_id, AgentStatus.COMPLETED)

    async def _monitor_agent(self, agent_id: str, agent: BaseAgent) -> None:
        """
        Monitor agent health with heartbeat and timeout detection.

        Args:
            agent_id: Agent identifier
            agent: Agent instance
        """
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval)

                # Check if agent still exists
                if agent_id not in self._agents:
                    break

                # Update heartbeat tracking
                current_time = time.time()
                self._last_heartbeat[agent_id] = current_time
                self._heartbeat_count[agent_id] = self._heartbeat_count.get(agent_id, 0) + 1

                # Check for timeout
                time_since_heartbeat = current_time - self._last_heartbeat.get(agent_id, current_time)
                if time_since_heartbeat > self._agent_timeout:
                    # Agent timed out
                    self._state.update_agent_task(
                        agent_id,
                        AgentStatus.TIMEOUT,
                        error_message=f"Agent timeout after {time_since_heartbeat:.0f}s",
                    )
                    break

                # Update state with health metrics
                self._state.update_agent_task(
                    agent_id,
                    AgentStatus.RUNNING,
                    result={
                        "heartbeat_count": self._heartbeat_count.get(agent_id, 0),
                        "last_heartbeat": current_time,
                    },
                )

        except asyncio.CancelledError:
            # Normal shutdown
            raise
        except Exception as e:
            # Log error and mark as failed
            self._state.update_agent_task(
                agent_id,
                AgentStatus.FAILED,
                error_message=f"Health check failed: {e}",
            )

    def get_agent_health(self, agent_id: str) -> dict[str, Any] | None:
        """
        Get health metrics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Health metrics dict or None if agent not found
        """
        if agent_id not in self._last_heartbeat:
            return None

        health_info = {
            "agent_id": agent_id,
            "last_heartbeat": self._last_heartbeat.get(agent_id, 0),
            "heartbeat_count": self._heartbeat_count.get(agent_id, 0),
            "status": "running" if agent_id in self._agents else "terminated",
            "time_since_heartbeat": time.time() - self._last_heartbeat.get(agent_id, time.time()),
            "task_id": self._agent_contexts.get(agent_id, ""),
        }

        # Add resource usage if available
        if self._resource_manager:
            usage = self._resource_manager.get_usage(agent_id)
            if usage:
                health_info["resource_usage"] = usage.to_dict()

        return health_info

    def get_agent_status(self, agent_id: str) -> AgentStatus | None:
        """
        Get the status of an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent status or None if agent not found
        """
        agent_task = self._state.get_agent_task(agent_id)
        if agent_task:
            return agent_task.status
        return None

    def get_active_agents(self) -> list[str]:
        """
        Get list of active agent IDs.

        Returns:
            List of active agent IDs
        """
        return list(self._agents.keys())

    async def shutdown_all(self) -> None:
        """Shutdown all agents."""
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            await self.terminate_agent(agent_id)

        # Stop resource manager
        if self._resource_manager:
            await self._resource_manager.stop()

    async def start_resource_monitoring(self) -> None:
        """Start resource limit monitoring."""
        if self._resource_manager:
            await self._resource_manager.start()

    def get_resource_summary(self) -> dict[str, Any] | None:
        """
        Get resource usage summary.

        Returns:
            Resource summary or None if resource tracking disabled
        """
        if self._resource_manager:
            return self._resource_manager.get_summary()
        return None

    def get_resource_limits(self) -> dict[str, Any] | None:
        """
        Get configured resource limits.

        Returns:
            Resource limits or None if resource tracking disabled
        """
        if self._resource_manager:
            return {
                rt.value: limit.to_dict()
                for rt, limit in self._resource_manager.get_limits().items()
            }
        return None


# =============================================================================
# Orchestrator Agent
# =============================================================================


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent for coordinating specialist agents.

    The OrchestratorAgent:
    - Receives tasks from the CLI or other sources
    - Decomposes tasks into subtasks for specialist agents
    - Spawns and manages specialist agent lifecycles
    - Routes messages between agents
    - Aggregates results from multiple agents
    """

    def __init__(
        self,
        project_path: Path | None = None,
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            project_path: Path to project root
        """
        system_prompt = """You are the Orchestrator Agent for Claude Playwright Agent.

Your role is to:
1. Receive high-level tasks from the CLI
2. Decompose tasks into subtasks for specialist agents
3. Spawn and manage specialist agent lifecycles
4. Route messages between agents
5. Aggregate and return results

You coordinate the following specialist agents:
- IngestionAgent: Process Playwright recordings
- ParserAgent: Parse JavaScript files and extract actions
- DeduplicationAgent: Identify and deduplicate common elements
- BDDConversionAgent: Convert actions to Gherkin scenarios
- ExecutionAgent: Run BDD tests with Playwright
- ReportAgent: Generate test reports

Always track the status of each task and agent, and provide clear status updates.
"""
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._state = StateManager(self._project_path)
        self._message_queue = MessageQueue()
        self._lifecycle = AgentLifecycleManager(self._project_path)
        self._event_bus = get_event_bus()
        self._current_tasks: dict[str, AgentTask] = {}

        super().__init__(
            system_prompt=system_prompt,
            allowed_tools=[
                "spawn_agent",
                "terminate_agent",
                "send_message",
                "get_task_status",
                "list_agents",
                "send_message_priority",
                "get_queue_stats",
                "get_resource_stats",
                "get_resource_limits",
                "subscribe_events",
                "unsubscribe_events",
                "publish_event",
                "get_event_history",
            ],
        )

    async def initialize(self) -> None:
        """Initialize the orchestrator and start the priority queue."""
        await super().initialize()
        await self._message_queue.start()
        # Start resource monitoring
        await self._lifecycle.start_resource_monitoring()

    async def cleanup(self) -> None:
        """Cleanup the orchestrator and stop the priority queue."""
        await self._message_queue.stop()
        await self._lifecycle.shutdown_all()
        await super().cleanup()

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a high-level task.

        Args:
            input_data: Task input with 'task_type' and 'params'

        Returns:
            Processing results
        """
        task_type = input_data.get("task_type", "")
        params = input_data.get("params", {})

        # Create task record
        task = AgentTask(
            task_type=task_type,
            input_data=params,
        )
        self._current_tasks[task.id] = task

        try:
            # Route to appropriate handler
            if task_type == "ingest":
                result = await self._handle_ingest(params)
            elif task_type == "run_tests":
                result = await self._handle_run_tests(params)
            elif task_type == "generate_report":
                result = await self._handle_generate_report(params)
            elif task_type == "parse_recording":
                result = await self._handle_parse_recording(params)
            else:
                # Unknown task type - return failure
                task.status = AgentStatus.FAILED
                task.error = f"Unknown task type: {task_type}"
                task.completed_at = datetime.now().isoformat()

                return {
                    "success": False,
                    "task_id": task.id,
                    "error": task.error,
                }

            task.status = AgentStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now().isoformat()

            return {
                "success": True,
                "task_id": task.id,
                "result": result,
            }

        except Exception as e:
            task.status = AgentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()

            return {
                "success": False,
                "task_id": task.id,
                "error": str(e),
            }

    async def _handle_ingest(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle ingestion task."""
        recording_path = params.get("recording_path", "")
        # Implementation would spawn IngestionAgent
        return {
            "recording": recording_path,
            "scenarios_generated": 0,
            "message": "Ingestion completed",
        }

    async def _handle_run_tests(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle test execution task."""
        # Implementation would spawn ExecutionAgent
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "message": "Tests completed",
        }

    async def _handle_generate_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle report generation task."""
        # Implementation would spawn ReportAgent
        return {
            "report_path": "",
            "message": "Report generated",
        }

    async def _handle_parse_recording(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle recording parsing task."""
        # Implementation would spawn ParserAgent
        return {
            "actions": [],
            "message": "Recording parsed",
        }

    async def spawn_agent(
        self,
        agent_type: str,
        agent_id: str | None = None,
        task_id: str = "",
    ) -> str:
        """
        Spawn a specialist agent.

        Args:
            agent_type: Type of agent to spawn
            agent_id: Optional agent ID (auto-generated if not provided)
            task_id: Optional task ID for context tracking

        Returns:
            Agent ID of spawned agent
        """
        if agent_id is None:
            agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"

        # Import agent class
        if agent_type == "ingest":
            from claude_playwright_agent.agents.ingest_agent import IngestionAgent
            agent = IngestionAgent(project_path=self._project_path)
        elif agent_type == "test":
            from claude_playwright_agent.agents.test_agent import TestAgent
            agent = TestAgent(project_path=self._project_path)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        await self._lifecycle.spawn_agent(agent_id, agent_type, agent, task_id)
        return agent_id

    async def terminate_agent(self, agent_id: str) -> None:
        """
        Terminate a running agent.

        Args:
            agent_id: Agent ID to terminate
        """
        await self._lifecycle.terminate_agent(agent_id)

    async def send_message(self, message: AgentMessage) -> None:
        """
        Send a message to an agent.

        Args:
            message: Message to send
        """
        await self._message_queue.send(message)

    async def send_message_priority(
        self,
        message: AgentMessage,
        priority: str = "normal",
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Send a message to an agent with explicit priority.

        Args:
            message: Message to send
            priority: Priority level (critical, high, normal, low, deferred)
            context: Optional execution context for priority tracking
        """
        priority_enum = TaskPriority.from_string(priority)
        await self._message_queue.send(message, priority_enum, context)

    def get_queue_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        """
        Get queue statistics.

        Args:
            agent_id: Specific agent or None for all agents

        Returns:
            Queue statistics including enqueued, dequeued, and dropped counts
        """
        return self._message_queue.get_stats(agent_id)

    def get_resource_stats(self) -> dict[str, Any] | None:
        """
        Get resource usage statistics.

        Returns:
            Resource usage summary or None if tracking disabled
        """
        return self._lifecycle.get_resource_summary()

    def get_resource_limits(self) -> dict[str, Any] | None:
        """
        Get configured resource limits.

        Returns:
            Resource limits configuration or None if tracking disabled
        """
        return self._lifecycle.get_resource_limits()

    async def subscribe_events(
        self,
        agent_id: str,
        event_types: list[str] | None = None,
    ) -> None:
        """
        Subscribe an agent to events.

        Args:
            agent_id: Agent to subscribe
            event_types: Event types to subscribe (None = all)
        """
        types = None
        if event_types:
            types = [EventType(et) for et in event_types]

        await self._event_bus.subscribe(agent_id, types)

    async def unsubscribe_events(
        self,
        agent_id: str,
        event_types: list[str] | None = None,
    ) -> None:
        """
        Unsubscribe an agent from events.

        Args:
            agent_id: Agent to unsubscribe
            event_types: Event types to unsubscribe (None = all)
        """
        types = None
        if event_types:
            types = [EventType(et) for et in event_types]

        await self._event_bus.unsubscribe(agent_id, types)

    async def publish_event(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str = "orchestrator",
        correlation_id: str = "",
    ) -> int:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event data
            source: Source agent ID
            correlation_id: Optional correlation ID

        Returns:
            Number of subscribers the event was delivered to
        """
        return await self._event_bus.broadcast(
            EventType(event_type),
            source,
            data,
            correlation_id=correlation_id,
        )

    def get_event_history(
        self,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            source: Filter by source agent
            limit: Maximum events to return

        Returns:
            List of historical events
        """
        et = EventType(event_type) if event_type else None
        events = self._event_bus.get_history(agent_id=source, event_type=et, limit=limit)
        return [e.to_dict() for e in events]

    def get_event_stats(self) -> dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Event statistics
        """
        stats = self._event_bus.get_stats()
        return {
            "events_published": stats["events_published"],
            "events_delivered": stats["events_delivered"],
            "events_dropped": stats["events_dropped"],
            "active_subscriptions": stats["active_subscriptions"],
            "history_size": stats["history_size"],
        }

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get the status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status information
        """
        task = self._current_tasks.get(task_id)
        if task:
            return task.to_dict()
        return {"error": "Task not found"}

    def list_agents(self) -> list[dict[str, Any]]:
        """
        List all active agents.

        Returns:
            List of agent information
        """
        agents = []
        for agent_id in self._lifecycle.get_active_agents():
            status = self._lifecycle.get_agent_status(agent_id)
            agents.append({
                "agent_id": agent_id,
                "status": status.value if status else "unknown",
            })
        return agents

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and all agents."""
        await self._lifecycle.shutdown_all()
        await self.cleanup()


# =============================================================================
# Convenience Functions
# =============================================================================


_orchestrator_instance: OrchestratorAgent | None = None


def get_orchestrator(project_path: Path | None = None) -> OrchestratorAgent:
    """
    Get the singleton orchestrator instance.

    Args:
        project_path: Path to project root

    Returns:
        OrchestratorAgent instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent(project_path)
    return _orchestrator_instance
