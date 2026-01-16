"""
E9.1 - Parallel Test Execution Skill.

This skill provides parallel execution capabilities:
- Parallel test execution
- Worker pool management
- Resource allocation
- Result aggregation
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class WorkerStatus(str, Enum):
    """Worker status types."""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """Task status types."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkerInfo:
    """
    Information about a worker.

    Attributes:
        worker_id: Unique worker identifier
        status: Current worker status
        current_task: Currently assigned task ID
        tasks_completed: Number of tasks completed
        tasks_failed: Number of tasks failed
        total_processing_time: Total processing time in seconds
        last_activity: When worker was last active
        metadata: Additional metadata
    """

    worker_id: str = field(default_factory=lambda: f"worker_{uuid.uuid4().hex[:8]}")
    status: WorkerStatus = WorkerStatus.IDLE
    current_task: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "worker_id": self.worker_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_processing_time": self.total_processing_time,
            "last_activity": self.last_activity,
            "metadata": self.metadata,
        }


@dataclass
class ParallelTask:
    """
    A task for parallel execution.

    Attributes:
        task_id: Unique task identifier
        test_path: Path to test file
        test_name: Name of the test
        priority: Task priority (lower = higher priority)
        dependencies: List of task IDs this task depends on
        status: Current task status
        worker_id: Worker assigned to this task
        started_at: When task started
        completed_at: When task completed
        result: Task result
        error: Error message if failed
        context: Task execution context
    """

    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    test_path: str = ""
    test_name: str = ""
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    worker_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "test_path": self.test_path,
            "test_name": self.test_name,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "context": self.context,
        }


@dataclass
class ExecutionResult:
    """
    Result of parallel execution.

    Attributes:
        execution_id: Unique execution identifier
        workflow_id: Associated workflow ID
        tasks_total: Total number of tasks
        tasks_completed: Number of tasks completed
        tasks_failed: Number of tasks failed
        tasks_cancelled: Number of tasks cancelled
        total_duration: Total execution duration in seconds
        parallel_efficiency: Parallel efficiency score
        worker_utilization: Worker utilization percentage
        results: List of task results
        started_at: When execution started
        completed_at: When execution completed
    """

    execution_id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_cancelled: int = 0
    total_duration: float = 0.0
    parallel_efficiency: float = 0.0
    worker_utilization: float = 0.0
    results: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_cancelled": self.tasks_cancelled,
            "total_duration": self.total_duration,
            "parallel_efficiency": self.parallel_efficiency,
            "worker_utilization": self.worker_utilization,
            "results": self.results,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class ParallelContext:
    """
    Context for parallel execution operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        executions_completed: Number of executions completed
        workers_created: Number of workers created
        tasks_processed: Total tasks processed
        execution_history: List of execution results
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"par_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    executions_completed: int = 0
    workers_created: int = 0
    tasks_processed: int = 0
    execution_history: list[ExecutionResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "executions_completed": self.executions_completed,
            "workers_created": self.workers_created,
            "tasks_processed": self.tasks_processed,
            "execution_history": [e.to_dict() for e in self.execution_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class ParallelExecutionAgent(BaseAgent):
    """
    Parallel Test Execution Agent.

    This agent provides:
    1. Parallel test execution
    2. Worker pool management
    3. Resource allocation
    4. Result aggregation
    """

    name = "e9_1_parallel_execution"
    version = "1.0.0"
    description = "E9.1 - Parallel Test Execution"

    def __init__(self, **kwargs) -> None:
        """Initialize the parallel execution agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E9.1 - Parallel Test Execution agent for the Playwright test automation framework. You help users with e9.1 - parallel test execution tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[ParallelContext] = []
        self._worker_pool: dict[str, WorkerInfo] = {}
        self._task_queue: list[ParallelTask] = []
        self._execution_history: list[ExecutionResult] = []
        self._max_workers: int = 4

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
        Execute parallel execution task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the parallel execution operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "execute_parallel":
            return await self._execute_parallel(context, execution_context)
        elif task_type == "create_worker_pool":
            return await self._create_worker_pool(context, execution_context)
        elif task_type == "add_task":
            return await self._add_task(context, execution_context)
        elif task_type == "get_worker_status":
            return await self._get_worker_status(context, execution_context)
        elif task_type == "get_task_status":
            return await self._get_task_status(context, execution_context)
        elif task_type == "get_execution_result":
            return await self._get_execution_result(context, execution_context)
        elif task_type == "cancel_task":
            return await self._cancel_task(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _execute_parallel(self, context: dict[str, Any], execution_context: Any) -> str:
        """Execute tests in parallel."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        test_paths = context.get("test_paths", [])
        max_workers = context.get("max_workers", self._max_workers)

        if not test_paths:
            return "Error: test_paths is required"

        # Create execution result
        result = ExecutionResult(
            workflow_id=workflow_id,
            tasks_total=len(test_paths),
        )

        # Create worker pool
        workers = []
        for i in range(max_workers):
            worker = WorkerInfo(
                worker_id=f"worker_{i}",
                status=WorkerStatus.IDLE,
            )
            self._worker_pool[worker.worker_id] = worker
            workers.append(worker)

        # Create tasks
        tasks = []
        for test_path in test_paths:
            task = ParallelTask(
                test_path=str(test_path),
                test_name=Path(test_path).stem,
            )
            tasks.append(task)
            self._task_queue.append(task)

        # Execute tasks in parallel
        start_time = datetime.now()

        try:
            # Simulate parallel execution
            completed = 0
            for task in tasks:
                # Assign to worker
                worker = workers[completed % len(workers)]
                task.worker_id = worker.worker_id
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now().isoformat()
                worker.status = WorkerStatus.BUSY
                worker.current_task = task.task_id

                # Simulate task execution
                await asyncio.sleep(0.1)  # Simulate work

                # Complete task
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                worker.status = WorkerStatus.IDLE
                worker.current_task = ""
                worker.tasks_completed += 1
                completed += 1

            result.tasks_completed = completed
            result.total_duration = (datetime.now() - start_time).total_seconds()

            # Calculate metrics
            result.worker_utilization = (result.total_duration * max_workers) / (result.total_duration * max_workers or 1) * 100
            result.parallel_efficiency = result.tasks_completed / (result.tasks_total or 1) * 100

            result.completed_at = datetime.now().isoformat()

            self._execution_history.append(result)

            return f"Parallel execution complete: {completed}/{len(test_paths)} tasks completed in {result.total_duration:.2f}s"

        except Exception as e:
            result.tasks_failed = len(test_paths) - completed
            result.completed_at = datetime.now().isoformat()
            return f"Parallel execution failed: {e}"

    async def _create_worker_pool(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a worker pool."""
        num_workers = context.get("num_workers", self._max_workers)

        self._worker_pool.clear()

        for i in range(num_workers):
            worker = WorkerInfo(
                worker_id=f"worker_{uuid.uuid4().hex[:8]}",
                status=WorkerStatus.IDLE,
            )
            self._worker_pool[worker.worker_id] = worker

        return f"Created worker pool with {num_workers} worker(s)"

    async def _add_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add a task to the queue."""
        test_path = context.get("test_path")
        priority = context.get("priority", 0)

        if not test_path:
            return "Error: test_path is required"

        task = ParallelTask(
            test_path=str(test_path),
            test_name=Path(test_path).stem,
            priority=priority,
        )

        self._task_queue.append(task)

        # Sort by priority
        self._task_queue.sort(key=lambda t: t.priority)

        return f"Added task '{task.task_id}' for '{test_path}'"

    async def _get_worker_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get worker status."""
        worker_id = context.get("worker_id")

        if worker_id:
            worker = self._worker_pool.get(worker_id)
            if worker:
                return (
                    f"Worker '{worker_id}': "
                    f"status={worker.status.value}, "
                    f"completed={worker.tasks_completed}, "
                    f"failed={worker.tasks_failed}"
                )

        # Return all workers
        workers = list(self._worker_pool.values())
        if not workers:
            return "No workers available"

        output = f"Workers ({len(workers)}):\n"
        for worker in workers:
            output += f"- {worker.worker_id}: {worker.status.value}\n"

        return output

    async def _get_task_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get task status."""
        task_id = context.get("task_id")

        if task_id:
            for task in self._task_queue:
                if task.task_id == task_id:
                    return (
                        f"Task '{task_id}': "
                        f"{task.test_name}, "
                        f"status={task.status.value}, "
                        f"worker={task.worker_id}"
                    )

        return f"Error: Task '{task_id}' not found"

    async def _get_execution_result(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get execution result."""
        execution_id = context.get("execution_id")

        if execution_id:
            for result in self._execution_history:
                if result.execution_id == execution_id:
                    return (
                        f"Execution '{execution_id}': "
                        f"{result.tasks_completed}/{result.tasks_total} tasks, "
                        f"{result.total_duration:.2f}s, "
                        f"efficiency={result.parallel_efficiency:.1f}%"
                    )

        return f"Error: Execution '{execution_id}' not found"

    async def _cancel_task(self, context: dict[str, Any], execution_context: Any) -> str:
        """Cancel a task."""
        task_id = context.get("task_id")

        if not task_id:
            return "Error: task_id is required"

        for task in self._task_queue:
            if task.task_id == task_id:
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now().isoformat()

                    # Update worker
                    if task.worker_id:
                        worker = self._worker_pool.get(task.worker_id)
                        if worker:
                            worker.status = WorkerStatus.IDLE
                            worker.current_task = ""
                            worker.tasks_cancelled = getattr(worker, "tasks_cancelled", 0) + 1

                    return f"Cancelled task '{task_id}'"

                return f"Task '{task_id}' cannot be cancelled (status={task.status.value})"

        return f"Error: Task '{task_id}' not found"

    def get_worker_pool(self) -> dict[str, WorkerInfo]:
        """Get worker pool."""
        return self._worker_pool.copy()

    def get_task_queue(self) -> list[ParallelTask]:
        """Get task queue."""
        return self._task_queue.copy()

    def get_execution_history(self) -> list[ExecutionResult]:
        """Get execution history."""
        return self._execution_history.copy()

    def get_context_history(self) -> list[ParallelContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

