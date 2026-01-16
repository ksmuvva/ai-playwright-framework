"""Unit tests for E2.4 - Task Queue & Scheduling skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e2_4_task_queue_scheduling import (
    QueuedTask,
    SchedulePriority,
    TaskQueue,
    TaskQueueSchedulingAgent,
    TaskSchedule,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestSchedulePriority:
    """Test suite for SchedulePriority enum."""

    @pytest.mark.unit
    def test_schedule_priority_values(self):
        """Test schedule priority enum values."""
        assert SchedulePriority.CRITICAL.value == "critical"
        assert SchedulePriority.HIGH.value == "high"
        assert SchedulePriority.NORMAL.value == "normal"
        assert SchedulePriority.LOW.value == "low"


class TestQueuedTask:
    """Test suite for QueuedTask dataclass."""

    @pytest.mark.unit
    def test_queued_task_creation(self):
        """Test creating a queued task."""
        task = QueuedTask(
            task_id="task_001",
            workflow_id="wf_001",
            agent_id="agent_001",
            task_type="test_task",
            payload={"data": "test"},
            priority=SchedulePriority.HIGH,
        )

        assert task.task_id == "task_001"
        assert task.workflow_id == "wf_001"
        assert task.agent_id == "agent_001"
        assert task.priority == SchedulePriority.HIGH

    @pytest.mark.unit
    def test_queued_task_to_dict(self):
        """Test converting queued task to dictionary."""
        task = QueuedTask(
            task_id="task_001",
            workflow_id="wf_001",
            agent_id="agent_001",
            task_type="test_task",
        )

        result = task.to_dict()

        assert isinstance(result, dict)
        assert result["task_id"] == "task_001"


class TestTaskQueue:
    """Test suite for TaskQueue dataclass."""

    @pytest.mark.unit
    def test_task_queue_creation(self):
        """Test creating a task queue."""
        queue = TaskQueue(
            queue_id="queue_001",
            queue_name="test_queue",
            max_size=100,
        )

        assert queue.queue_id == "queue_001"
        assert queue.queue_name == "test_queue"
        assert queue.max_size == 100


class TestTaskSchedule:
    """Test suite for TaskSchedule dataclass."""

    @pytest.mark.unit
    def test_task_schedule_creation(self):
        """Test creating a task schedule."""
        schedule = TaskSchedule(
            schedule_id="sched_001",
            task_id="task_001",
            scheduled_time="2024-01-01T00:00:00Z",
            repeat_interval=60,
        )

        assert schedule.schedule_id == "sched_001"
        assert schedule.task_id == "task_001"
        assert schedule.scheduled_time == "2024-01-01T00:00:00Z"


class TestTaskQueueSchedulingAgent:
    """Test suite for TaskQueueSchedulingAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return TaskQueueSchedulingAgent()

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
        assert agent.name == "e2_4_task_queue_scheduling"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty registries."""
        assert hasattr(agent, "_task_queues")
        assert hasattr(agent, "_schedules")
        assert agent._task_queues == {}
        assert agent._schedules == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_enqueue_task(self, agent):
        """Test enqueuing a task."""
        context = {
            "task_type": "enqueue_task",
            "queue_id": "queue_001",
            "workflow_id": "wf_001",
            "agent_id": "agent_001",
            "task_type": "test_task",
            "payload": {"data": "test"},
            "priority": SchedulePriority.NORMAL,
        }

        result = await agent.run("enqueue_task", context)

        assert "enqueued" in result.lower() or "added" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_dequeue_task(self, agent):
        """Test dequeuing a task."""
        context = {
            "task_type": "dequeue_task",
            "queue_id": "queue_001",
        }

        result = await agent.run("dequeue_task", context)

        assert "task" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_queue(self, agent):
        """Test creating a task queue."""
        context = {
            "task_type": "create_queue",
            "queue_id": "queue_001",
            "queue_name": "test_queue",
            "max_size": 100,
        }

        result = await agent.run("create_queue", context)

        assert "created" in result.lower() or "queue" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_schedule_task(self, agent):
        """Test scheduling a task."""
        context = {
            "task_type": "schedule_task",
            "task_id": "task_001",
            "scheduled_time": "2024-01-01T00:00:00Z",
        }

        result = await agent.run("schedule_task", context)

        assert "scheduled" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_queue_status(self, agent):
        """Test getting queue status."""
        agent._task_queues["queue_001"] = TaskQueue(
            queue_id="queue_001",
            queue_name="test_queue",
        )

        context = {
            "task_type": "get_queue_status",
            "queue_id": "queue_001",
        }

        result = await agent.run("get_queue_status", context)

        assert "queue" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_process_queue(self, agent):
        """Test processing a queue."""
        context = {
            "task_type": "process_queue",
            "queue_id": "queue_001",
        }

        result = await agent.run("process_queue", context)

        assert "processed" in result.lower() or "queue" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_task_queues(self, agent):
        """Test getting task queues."""
        agent._task_queues["queue_001"] = TaskQueue(
            queue_id="queue_001",
            queue_name="test_queue",
        )

        result = agent.get_task_queues()

        assert "queue_001" in result

    @pytest.mark.unit
    def test_get_schedules(self, agent):
        """Test getting schedules."""
        result = agent.get_schedules()

        assert isinstance(result, dict)
