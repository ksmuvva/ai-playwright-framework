"""
Priority-based message queuing for agent orchestration.

This module implements:
- Priority queues for agent task scheduling
- Context-aware priority assignment
- Fair scheduling with starvation prevention
- Message aging and dynamic priority adjustment
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from heapq import heappush, heappop
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_playwright_agent.agents.orchestrator import AgentMessage

# =============================================================================
# Priority System
# =============================================================================


class TaskPriority(str, Enum):
    """
    Task priority levels for agent scheduling.

    Priorities from highest to lowest:
    - CRITICAL: System-critical tasks (shutdown, error recovery)
    - HIGH: User-interactive tasks (CLI commands, health checks)
    - NORMAL: Standard processing tasks (ingestion, conversion)
    - LOW: Background tasks (cleanup, optimization)
    - DEFERRED: Tasks that can wait (indexing, analysis)
    """
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"

    @classmethod
    def get_numeric_value(cls, priority: "TaskPriority") -> int:
        """
        Get numeric value for priority (lower = higher priority).

        Args:
            priority: Priority level

        Returns:
            Numeric value (0-4, where 0 is highest priority)
        """
        values = {
            cls.CRITICAL: 0,
            cls.HIGH: 1,
            cls.NORMAL: 2,
            cls.LOW: 3,
            cls.DEFERRED: 4,
        }
        return values.get(priority, 2)

    @classmethod
    def from_string(cls, value: str) -> "TaskPriority":
        """
        Convert string to TaskPriority.

        Args:
            value: String representation

        Returns:
            TaskPriority enum value
        """
        try:
            return cls(value.lower())
        except ValueError:
            return cls.NORMAL

    @classmethod
    def infer_from_task_type(cls, task_type: str) -> "TaskPriority":
        """
        Infer appropriate priority from task type.

        Args:
            task_type: Type of task being executed

        Returns:
            Appropriate priority level
        """
        # Critical system tasks
        if task_type in ("shutdown", "error_recovery", "emergency_stop"):
            return cls.CRITICAL

        # High priority user tasks
        if task_type in ("run_tests", "interactive_command", "health_check"):
            return cls.HIGH

        # Standard processing tasks
        if task_type in ("ingest", "parse_recording", "deduplicate", "convert_bdd"):
            return cls.NORMAL

        # Low priority background tasks
        if task_type in ("cleanup", "optimize", "compress"):
            return cls.LOW

        # Deferred tasks
        if task_type in ("index", "analyze", "report_generate"):
            return cls.DEFERRED

        return cls.NORMAL


# =============================================================================
# Enhanced Message with Priority
# =============================================================================


@dataclass(order=True)
class PrioritizedMessage:
    """
    A message wrapper with priority for queue ordering.

    The priority_queue attribute is used for heap ordering.
    Lower values = higher priority.

    Attributes:
        priority_queue: Tuple of (numeric_priority, timestamp, counter) for ordering
        message: The actual AgentMessage
        enqueue_time: When the message was enqueued
        aging_factor: How much to increase priority over time
        context: Execution context for priority adjustment
    """

    priority_queue: tuple[int, float, int] = field(compare=True)
    message: "AgentMessage" = field(compare=False)
    enqueue_time: float = field(default_factory=time.time, compare=False)
    aging_factor: float = field(default=0.0, compare=False)
    context: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def create(
        cls,
        message: "AgentMessage",
        priority: TaskPriority = TaskPriority.NORMAL,
        aging_enabled: bool = True,
        context: dict[str, Any] | None = None,
    ) -> "PrioritizedMessage":
        """
        Create a prioritized message.

        Args:
            message: The AgentMessage to wrap
            priority: Priority level
            aging_enabled: Whether to enable priority aging
            context: Execution context for priority adjustment

        Returns:
            PrioritizedMessage instance
        """
        numeric_priority = TaskPriority.get_numeric_value(priority)
        timestamp = time.time()
        # Counter ensures FIFO order for same priority
        counter = uuid.uuid4().int % (2 ** 20)

        aging_factor = 0.1 if aging_enabled else 0.0

        # Extract context information
        context_data = context or {}
        context_data.update({
            "original_priority": priority.value,
            "task_type": message.data.get("task_type", "unknown"),
        })

        return cls(
            priority_queue=(numeric_priority, timestamp, counter),
            message=message,
            enqueue_time=timestamp,
            aging_factor=aging_factor,
            context=context_data,
        )

    def get_aged_priority(self) -> int:
        """
        Calculate priority with aging applied.

        As messages wait longer, their priority increases
        to prevent starvation.

        Returns:
            Aged numeric priority value
        """
        base_priority = self.priority_queue[0]
        wait_time = time.time() - self.enqueue_time

        # Calculate age bonus (reduces numeric priority = increases actual priority)
        age_bonus = int(wait_time * self.aging_factor)

        # Don't age beyond NORMAL priority (prevents low-priority from becoming critical)
        max_age_bonus = base_priority - TaskPriority.get_numeric_value(TaskPriority.NORMAL)
        age_bonus = min(age_bonus, max_age_bonus)

        return base_priority - age_bonus

    def update_priority_queue(self) -> None:
        """Update the priority_queue tuple with current aged priority."""
        base_priority = self.get_aged_priority()
        timestamp = self.priority_queue[1]
        counter = self.priority_queue[2]
        self.priority_queue = (base_priority, timestamp, counter)


# =============================================================================
# Context-Aware Priority Calculator
# =============================================================================


class PriorityCalculator:
    """
    Calculate task priorities based on execution context.

    Considers:
    - Task type and inherent priority
    - User interaction level
    - Resource availability
    - Dependencies between tasks
    - Historical performance
    """

    # Weights for different factors
    TASK_TYPE_WEIGHT = 0.5
    USER_INTERACTION_WEIGHT = 0.3
    DEPENDENCY_WEIGHT = 0.2

    def __init__(
        self,
        task_type_weight: float = 0.5,
        user_interaction_weight: float = 0.3,
        dependency_weight: float = 0.2,
    ) -> None:
        """
        Initialize the priority calculator.

        Args:
            task_type_weight: Weight for task type factor
            user_interaction_weight: Weight for user interaction factor
            dependency_weight: Weight for dependency factor
        """
        self._task_type_weight = task_type_weight
        self._user_interaction_weight = user_interaction_weight
        self._dependency_weight = dependency_weight

    def calculate_priority(
        self,
        task_type: str,
        user_initiated: bool = False,
        has_dependencies: bool = False,
        depends_on: list[str] | None = None,
        resource_pressure: float = 0.0,
    ) -> TaskPriority:
        """
        Calculate appropriate priority for a task.

        Args:
            task_type: Type of task
            user_initiated: Whether initiated by user (raises priority)
            has_dependencies: Whether task has dependencies
            depends_on: List of task IDs this depends on
            resource_pressure: Current system resource pressure (0-1)

        Returns:
            Calculated priority level
        """
        # Start with base priority from task type
        base_priority = TaskPriority.infer_from_task_type(task_type)
        base_score = TaskPriority.get_numeric_value(base_priority)

        # User-initiated tasks get higher priority
        if user_initiated:
            user_bonus = -1  # Lower numeric value = higher priority
        else:
            user_bonus = 0

        # Tasks with dependencies might need lower priority
        if has_dependencies or depends_on:
            dependency_penalty = 1
        else:
            dependency_penalty = 0

        # Calculate final score
        final_score = base_score + user_bonus + dependency_penalty

        # Clamp to valid range and convert back to enum
        final_score = max(0, min(4, final_score))

        priority_map = {
            0: TaskPriority.CRITICAL,
            1: TaskPriority.HIGH,
            2: TaskPriority.NORMAL,
            3: TaskPriority.LOW,
            4: TaskPriority.DEFERRED,
        }

        return priority_map.get(final_score, TaskPriority.NORMAL)


# =============================================================================
# Priority Message Queue
# =============================================================================


class PriorityMessageQueue:
    """
    Priority-based message queue for inter-agent communication.

    Features:
    - Priority-based message ordering
    - Message aging to prevent starvation
    - Context-aware priority assignment
    - Fair scheduling with FIFO within same priority
    - Dynamic priority adjustment

    Example:
        queue = PriorityMessageQueue()

        # Enqueue messages with different priorities
        await queue.enqueue(message, priority=TaskPriority.HIGH)

        # Dequeue returns highest priority message first
        message = await queue.dequeue("agent_001")
    """

    def __init__(
        self,
        aging_enabled: bool = True,
        aging_interval: float = 5.0,
        max_queue_size: int = 1000,
    ) -> None:
        """
        Initialize the priority queue.

        Args:
            aging_enabled: Whether to enable message aging
            aging_interval: Seconds between aging updates
            max_queue_size: Maximum messages per queue
        """
        # Agent-specific priority queues
        self._queues: dict[str, list[PrioritizedMessage]] = {}
        self._lock = asyncio.Lock()

        self._aging_enabled = aging_enabled
        self._aging_interval = aging_interval
        self._max_queue_size = max_queue_size

        # Priority calculator
        self._priority_calculator = PriorityCalculator()

        # Aging task
        self._aging_task: asyncio.Task | None = None
        self._running = False

        # Statistics
        self._stats: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        """Start the priority queue with aging task."""
        self._running = True

        if self._aging_enabled:
            self._aging_task = asyncio.create_task(self._aging_loop())

    async def stop(self) -> None:
        """Stop the priority queue and cleanup."""
        self._running = False

        if self._aging_task:
            self._aging_task.cancel()
            try:
                await self._aging_task
            except asyncio.CancelledError:
                pass

    async def _aging_loop(self) -> None:
        """Periodically update message priorities based on wait time."""
        while self._running:
            await asyncio.sleep(self._aging_interval)

            async with self._lock:
                for queue_messages in self._queues.values():
                    # Update priorities for all messages
                    for msg in queue_messages:
                        msg.update_priority_queue()

                    # Re-heapify after priority updates
                    queue_messages.sort(key=lambda m: m.priority_queue)

    async def enqueue(
        self,
        message: "AgentMessage",
        priority: TaskPriority | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Enqueue a message with priority.

        Args:
            message: Message to enqueue
            priority: Priority level (inferred if not provided)
            context: Execution context for priority calculation
        """
        recipient_id = message.recipient_id

        # Infer priority if not provided
        if priority is None:
            task_type = message.data.get("task_type", "unknown")
            user_initiated = message.data.get("user_initiated", False)
            priority = self._priority_calculator.calculate_priority(
                task_type=task_type,
                user_initiated=user_initiated,
            )

        # Create prioritized message
        prioritized = PrioritizedMessage.create(
            message=message,
            priority=priority,
            aging_enabled=self._aging_enabled,
            context=context,
        )

        async with self._lock:
            # Handle broadcast messages (empty recipient_id)
            if not recipient_id:
                # Send to all agents except sender
                for agent_id in self._queues.keys():
                    if agent_id != message.sender_id:
                        if agent_id not in self._queues:
                            self._queues[agent_id] = []
                            self._stats[agent_id] = {
                                "enqueued": 0,
                                "dequeued": 0,
                                "dropped": 0,
                            }

                        queue = self._queues[agent_id]

                        # Check queue size
                        if len(queue) >= self._max_queue_size:
                            # Drop lowest priority message
                            queue.sort(key=lambda m: m.priority_queue)
                            dropped = queue.pop()
                            self._stats[agent_id]["dropped"] += 1

                        # Add to queue and maintain heap property
                        heappush(queue, prioritized)
                        self._stats[agent_id]["enqueued"] += 1
                return

            # Get or create queue for direct message
            if recipient_id not in self._queues:
                self._queues[recipient_id] = []
                self._stats[recipient_id] = {
                    "enqueued": 0,
                    "dequeued": 0,
                    "dropped": 0,
                }

            queue = self._queues[recipient_id]

            # Check queue size
            if len(queue) >= self._max_queue_size:
                # Drop lowest priority message
                queue.sort(key=lambda m: m.priority_queue)
                dropped = queue.pop()
                self._stats[recipient_id]["dropped"] += 1

            # Add to queue and maintain heap property
            heappush(queue, prioritized)
            self._stats[recipient_id]["enqueued"] += 1

    async def dequeue(
        self,
        agent_id: str,
        timeout: float | None = None,
    ) -> "AgentMessage | None":
        """
        Dequeue the highest priority message for an agent.

        Args:
            agent_id: Agent to get message for
            timeout: Timeout in seconds

        Returns:
            AgentMessage or None if timeout

        Raises:
            asyncio.TimeoutError: If timeout expires
        """
        start_time = time.time()

        while True:
            async with self._lock:
                if agent_id in self._queues and self._queues[agent_id]:
                    queue = self._queues[agent_id]

                    # Sort by current priority (with aging)
                    queue.sort(key=lambda m: m.priority_queue)

                    # Pop highest priority message
                    prioritized = heappop(queue)
                    self._stats[agent_id]["dequeued"] += 1

                    # Clean up empty queues
                    if not queue:
                        del self._queues[agent_id]

                    return prioritized.message

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise asyncio.TimeoutError()

            # Wait a bit before retrying
            await asyncio.sleep(0.01)

    async def peek(self, agent_id: str) -> "AgentMessage | None":
        """
        Peek at the next message without removing it.

        Args:
            agent_id: Agent to peek for

        Returns:
            AgentMessage or None if queue empty
        """
        async with self._lock:
            if agent_id in self._queues and self._queues[agent_id]:
                queue = self._queues[agent_id]
                if queue:
                    # Return highest priority without removing
                    return queue[0].message
        return None

    async def remove(self, agent_id: str, message_id: str) -> bool:
        """
        Remove a specific message from the queue.

        Args:
            agent_id: Agent whose queue to search
            message_id: ID of message to remove

        Returns:
            True if message was found and removed
        """
        async with self._lock:
            if agent_id in self._queues:
                queue = self._queues[agent_id]
                for i, msg in enumerate(queue):
                    if msg.message.id == message_id:
                        queue.pop(i)
                        # Re-heapify
                        if queue:
                            queue.sort(key=lambda m: m.priority_queue)
                        return True
        return False

    def get_queue_size(self, agent_id: str) -> int:
        """
        Get the number of messages in an agent's queue.

        Args:
            agent_id: Agent to check

        Returns:
            Queue size
        """
        if agent_id in self._queues:
            return len(self._queues[agent_id])
        return 0

    def get_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        """
        Get queue statistics.

        Args:
            agent_id: Specific agent or None for all agents

        Returns:
            Statistics dictionary
        """
        if agent_id:
            return self._stats.get(agent_id, {})
        return self._stats.copy()

    def list_queued_agents(self) -> list[str]:
        """
        List agents with non-empty queues.

        Returns:
            List of agent IDs
        """
        return list(self._queues.keys())

    async def clear(self, agent_id: str | None = None) -> None:
        """
        Clear messages from queue(s).

        Args:
            agent_id: Specific agent to clear, or None for all
        """
        async with self._lock:
            if agent_id:
                self._queues.pop(agent_id, None)
            else:
                self._queues.clear()
