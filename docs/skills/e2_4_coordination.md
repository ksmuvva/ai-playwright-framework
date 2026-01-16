# E2.4 - Task Queue & Coordination

**Skill:** `e2_4_task_queue_scheduling`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Task Queue & Coordination skill manages task scheduling, queuing, and distribution across available workers. It supports priority-based scheduling and dependency management.

## Capabilities

- Queue tasks for execution
- Schedule based on priority
- Manage task dependencies
- Distribute tasks to workers
- Track task completion

## Usage

```python
queue = TaskQueueAgent()

# Enqueue task
await queue.run("enqueue", {
    "task_id": "task_001",
    "task_type": "test_execution",
    "priority": "high",
    "data": {...}
})

# Dequeue next task
task = await queue.run("dequeue", {
    "worker_id": "worker_001"
})

# Get queue status
status = await queue.run("status", {})
```

## Task Priority Levels

| Priority | Value | Description |
|----------|-------|-------------|
| `critical` | 100 | System-critical tasks |
| `high` | 75 | Important tasks |
| `normal` | 50 | Standard tasks |
| `low` | 25 | Background tasks |

## See Also

- [E2.1 - Orchestration Core](./e2_1_orchestration.md)
- [E2.3 - Inter-Agent Communication](./e2_3_communication.md)
