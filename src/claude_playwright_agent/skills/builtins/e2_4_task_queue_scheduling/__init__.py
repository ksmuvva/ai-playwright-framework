"""
E2.4 - Task Queue & Scheduling Skill.
"""

from .main import (
    QueuedTask,
    ScheduleResult,
    TaskContext,
    TaskPriority,
    TaskQueueSchedulingAgent,
    TaskStatus,
)

# Aliases for test compatibility
SchedulePriority = TaskPriority
TaskSchedule = ScheduleResult

# TaskQueue is a placeholder - the actual queue is managed by the agent
TaskQueue = dict  # Placeholder type

__all__ = [
    "QueuedTask",
    "ScheduleResult",
    "TaskContext",
    "TaskPriority",
    "TaskQueueSchedulingAgent",
    "TaskStatus",
    # Aliases
    "SchedulePriority",
    "TaskSchedule",
    "TaskQueue",
]
