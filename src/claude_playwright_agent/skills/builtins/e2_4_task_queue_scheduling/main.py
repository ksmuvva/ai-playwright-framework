"""
E2.4 - Task Queue & Scheduling Skill.

This skill provides task queue and scheduling:
- Priority-based task queuing
- Task scheduling and dispatching
- Deadline management
- Task dependency resolution
- Context preservation throughout scheduling
"""

import asyncio
import heapq
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_playwright_agent.agents.base import BaseAgent


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status in queue."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """
    Context for tasks in the queue.

    Attributes:
        task_id: Unique task identifier
        workflow_id: Associated workflow ID
        parent_task_id: Parent task in dependency chain
        queue_context: Context from when task was queued
        scheduling_context: Scheduling metadata
        execution_context: Execution context for when task runs
        metadata: Additional task metadata
    """

    task_id: str
    workflow_id: str = ""
    parent_task_id: str = ""
    queue_context: dict[str, Any] = field(default_factory=dict)
    scheduling_context: dict[str, Any] = field(default_factory=dict)
    execution_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "parent_task_id": self.parent_task_id,
            "queue_context": self.queue_context,
            "scheduling_context": self.scheduling_context,
            "execution_context": self.execution_context,
            "metadata": self.metadata,
        }


@dataclass
class QueuedTask:
    """
    A task in the scheduling queue.

    Attributes:
        task_id: Unique task identifier
        task_type: Type of task to execute
        priority: Task priority
        status: Current task status
        payload: Task payload/data
        context: Task context
        dependencies: List of task IDs this task depends on
        deadline: Task deadline (ISO format)
        created_at: Task creation time
        scheduled_at: Task scheduled time
        dispatched_at: Task dispatch time
        completed_at: Task completion time
        agent_id: ID of agent assigned to execute task
        result: Task result (when completed)
        error: Error message if failed
    """

    task_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    context: TaskContext = field(default_factory=TaskContext)
    dependencies: list[str] = field(default_factory=list)
    deadline: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    scheduled_at: str = ""
    dispatched_at: str = ""
    completed_at: str = ""
    agent_id: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    # For priority queue ordering
    def __lt__(self, other: "QueuedTask") -> bool:
        """Compare tasks for priority queue ordering."""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }
        return priority_order[self.priority] < priority_order[other.priority]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "payload": self.payload,
            "context": self.context.to_dict(),
            "dependencies": self.dependencies,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
            "agent_id": self.agent_id,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class ScheduleResult:
    """Result of task scheduling."""

    success: bool
    task_id: str
    scheduled_position: int = 0
    estimated_start: str = ""
    error: str = ""


class TaskQueueSchedulingAgent(BaseAgent):
    """
    Task Queue and Scheduling Agent.

    This agent provides:
    1. Priority-based task queuing
    2. Task scheduling and dispatching
    3. Deadline management
    4. Task dependency resolution
    5. Context preservation throughout scheduling
    """

    name = "e2_4_task_queue_scheduling"
    version = "1.0.0"
    description = "E2.4 - Task Queue & Scheduling"

    def __init__(self, **kwargs) -> None:
        """Initialize the task queue scheduling agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E2.4 - Task Queue & Scheduling agent for the Playwright test automation framework. You help users with e2.4 - task queue & scheduling tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._task_queue: list[QueuedTask] = []
        self._tasks: dict[str, QueuedTask] = {}
        self._task_dependencies: dict[str, set[str]] = {}  # task_id -> dependents
        self._dispatch_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._scheduler_running = False

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
        Execute scheduling task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the scheduling operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context", {})
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "enqueue_task":
            return await self._enqueue_task(context, execution_context)
        elif task_type == "schedule_tasks":
            return await self._schedule_tasks(context, execution_context)
        elif task_type == "dispatch_task":
            return await self._dispatch_task(context, execution_context)
        elif task_type == "get_next_task":
            return await self._get_next_task(context, execution_context)
        elif task_type == "complete_task":
            return await self._complete_task(context, execution_context)
        elif task_type == "cancel_task":
            return await self._cancel_task(context, execution_context)
        elif task_type == "get_queue_status":
            return await self._get_queue_status(context, execution_context)
        elif task_type == "add_dependency":
            return await self._add_dependency(context, execution_context)
        elif task_type == "set_deadline":
            return await self._set_deadline(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _enqueue_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Enqueue a task with context."""
        task_type = context.get("task_type", "")
        payload = context.get("payload", {})
        priority = context.get("priority", TaskPriority.NORMAL)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        task_id = context.get("task_id", f"task_{uuid.uuid4().hex[:8]}")
        dependencies = context.get("dependencies", [])
        deadline = context.get("deadline", "")

        if not task_type:
            return "Error: task_type is required"

        # Create task context with execution context
        task_context = TaskContext(
            task_id=task_id,
            workflow_id=workflow_id,
            queue_context={
                "enqueued_at": datetime.now().isoformat(),
                "enqueued_by": getattr(execution_context, "task_id", execution_context.get("task_id", "unknown")),
            },
            execution_context=execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context,
        )

        # Create queued task
        queued_task = QueuedTask(
            task_id=task_id,
            task_type=task_type,
            priority=TaskPriority(priority) if isinstance(priority, str) else priority,
            payload=payload,
            context=task_context,
            dependencies=dependencies,
            deadline=deadline,
        )

        async with self._lock:
            # Store task
            self._tasks[task_id] = queued_task

            # Add to dependency graph
            for dep_id in dependencies:
                if dep_id not in self._task_dependencies:
                    self._task_dependencies[dep_id] = set()
                self._task_dependencies[dep_id].add(task_id)

            # Add to priority queue
            heapq.heappush(self._task_queue, queued_task)

        return f"Task '{task_id}' enqueued with priority {queued_task.priority.value}"

    async def _schedule_tasks(self, context: dict[str, Any], execution_context: Any) -> str:
        """Schedule tasks from the queue."""
        max_tasks = context.get("max_tasks", 10)

        scheduled_count = 0
        scheduled_tasks = []

        async with self._lock:
            # Check tasks in priority order
            temp_queue = []

            while self._task_queue and scheduled_count < max_tasks:
                task = heapq.heappop(self._task_queue)

                # Check if dependencies are met
                if self._are_dependencies_met(task):
                    task.status = TaskStatus.SCHEDULED
                    task.scheduled_at = datetime.now().isoformat()
                    task.context.scheduling_context["scheduled_at"] = task.scheduled_at
                    scheduled_tasks.append(task)
                    scheduled_count += 1
                else:
                    # Put back in queue
                    temp_queue.append(task)

            # Put unscheduled tasks back
            for task in temp_queue:
                heapq.heappush(self._task_queue, task)

        return f"Scheduled {scheduled_count} task(s): {[t.task_id for t in scheduled_tasks]}"

    async def _dispatch_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Dispatch a task to an agent."""
        task_id = context.get("task_id")
        agent_id = context.get("agent_id")

        if not task_id or task_id not in self._tasks:
            return f"Error: Task '{task_id}' not found"

        task = self._tasks[task_id]

        if task.status != TaskStatus.SCHEDULED:
            return f"Error: Task '{task_id}' is not scheduled"

        async with self._lock:
            task.status = TaskStatus.DISPATCHED
            task.dispatched_at = datetime.now().isoformat()
            task.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
            task.context.scheduling_context["dispatched_at"] = task.dispatched_at
            task.context.scheduling_context["dispatched_to"] = task.agent_id

            # Add to dispatch queue
            await self._dispatch_queue.put(task)

        return f"Task '{task_id}' dispatched to agent '{task.agent_id}'"

    async def _get_next_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get the next task to dispatch."""
        agent_id = context.get("agent_id", "unknown")
        timeout = context.get("timeout", 5)

        try:
            # Wait for task from dispatch queue
            task = await asyncio.wait_for(self._dispatch_queue.get(), timeout=timeout)

            # Update status
            task.status = TaskStatus.RUNNING
            task.context.scheduling_context["started_at"] = datetime.now().isoformat()

            return f"Task '{task.task_id}' ready for agent '{agent_id}' with context"

        except asyncio.TimeoutError:
            return f"No task available for agent '{agent_id}'"

    async def _complete_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Mark a task as completed."""
        task_id = context.get("task_id")
        result = context.get("result", {})
        error = context.get("error", "")

        if not task_id or task_id not in self._tasks:
            return f"Error: Task '{task_id}' not found"

        task = self._tasks[task_id]

        async with self._lock:
            task.completed_at = datetime.now().isoformat()

            if error:
                task.status = TaskStatus.FAILED
                task.error = error
            else:
                task.status = TaskStatus.COMPLETED
                task.result = result

            task.context.scheduling_context["completed_at"] = task.completed_at

            # Notify dependent tasks
            if task_id in self._task_dependencies:
                for dependent_id in self._task_dependencies[task_id]:
                    dependent = self._tasks.get(dependent_id)
                    if dependent and dependent.dependencies:
                        dependent.dependencies.remove(task_id)

        return f"Task '{task_id}' marked as {task.status.value}"

    async def _cancel_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Cancel a task."""
        task_id = context.get("task_id")

        if not task_id or task_id not in self._tasks:
            return f"Error: Task '{task_id}' not found"

        task = self._tasks[task_id]

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return f"Error: Cannot cancel {task.status.value} task '{task_id}'"

        async with self._lock:
            task.status = TaskStatus.CANCELLED
            task.context.scheduling_context["cancelled_at"] = datetime.now().isoformat()

        return f"Task '{task_id}' cancelled"

    async def _get_queue_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get queue status."""
        pending_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        scheduled_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.SCHEDULED)
        running_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        completed_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)

        return (
            f"Queue status: {pending_count} pending, {scheduled_count} scheduled, "
            f"{running_count} running, {completed_count} completed"
        )

    async def _add_dependency(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add dependency between tasks."""
        task_id = context.get("task_id")
        depends_on = context.get("depends_on")

        if not task_id or not depends_on:
            return "Error: task_id and depends_on are required"

        if task_id not in self._tasks:
            return f"Error: Task '{task_id}' not found"

        task = self._tasks[task_id]

        async with self._lock:
            if depends_on not in task.dependencies:
                task.dependencies.append(depends_on)

            if depends_on not in self._task_dependencies:
                self._task_dependencies[depends_on] = set()
            self._task_dependencies[depends_on].add(task_id)

        return f"Task '{task_id}' now depends on '{depends_on}'"

    async def _set_deadline(self, context: dict[str, Any], execution_context: Any) -> str:
        """Set deadline for a task."""
        task_id = context.get("task_id")
        deadline = context.get("deadline")

        if not task_id or not deadline:
            return "Error: task_id and deadline are required"

        if task_id not in self._tasks:
            return f"Error: Task '{task_id}' not found"

        task = self._tasks[task_id]
        task.deadline = deadline
        task.context.scheduling_context["deadline"] = deadline

        return f"Deadline '{deadline}' set for task '{task_id}'"

    def _are_dependencies_met(self, task: QueuedTask) -> bool:
        """Check if task dependencies are met."""
        return not task.dependencies or all(
            dep_id in self._tasks and self._tasks[dep_id].status == TaskStatus.COMPLETED
            for dep_id in task.dependencies
        )

    def get_task(self, task_id: str) -> QueuedTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> dict[str, QueuedTask]:
        """Get all tasks."""
        return self._tasks.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

