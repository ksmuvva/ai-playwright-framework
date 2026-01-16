# E2.1 - Orchestration Core

**Skill:** `e2_1_orchestrator_core`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Orchestration Core skill provides the central coordination mechanism for managing multiple agents and test execution workflows. It handles task distribution, result aggregation, and workflow state management.

## Capabilities

- Coordinate multiple agents
- Distribute tasks across workers
- Aggregate execution results
- Manage workflow lifecycle
- Handle agent communication

## Usage

```python
orchestrator = OrchestratorCoreAgent()

# Start workflow
await orchestrator.run("start_workflow", {
    "workflow_id": "test_suite_001",
    "tasks": ["test_login", "test_checkout", "test_payment"]
})

# Get workflow status
status = await orchestrator.run("get_status", {
    "workflow_id": "test_suite_001"
})
```

## Workflow States

| State | Description |
|-------|-------------|
| `pending` | Workflow is queued |
| `running` | Workflow is executing |
| `completed` | Workflow completed successfully |
| `failed` | Workflow failed |
| `cancelled` | Workflow was cancelled |

## See Also

- [E2.2 - Agent Lifecycle](./e2_2_lifecycle.md)
- [E2.3 - Inter-Agent Communication](./e2_3_communication.md)
