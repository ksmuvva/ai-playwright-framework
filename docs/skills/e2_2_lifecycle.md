# E2.2 - Agent Lifecycle Management

**Skill:** `e2_2_lifecycle_management`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Agent Lifecycle Management skill handles the complete lifecycle of agents from initialization to shutdown. It manages agent creation, configuration, execution, and cleanup.

## Capabilities

- Initialize agents with configuration
- Start and stop agents
- Monitor agent health
- Handle agent failures
- Clean up resources

## Lifecycle States

```
CREATED → CONFIGURED → STARTING → RUNNING → STOPPING → STOPPED
                                      ↓
                                   FAILED
```

## Usage

```python
lifecycle = LifecycleAgent()

# Initialize agent
await lifecycle.run("initialize", {
    "agent_id": "agent_001",
    "config": {...}
})

# Start agent
await lifecycle.run("start", {
    "agent_id": "agent_001"
})

# Stop agent
await lifecycle.run("stop", {
    "agent_id": "agent_001"
})
```

## See Also

- [E2.1 - Orchestration Core](./e2_1_orchestration.md)
- [E2.5 - Health Monitoring](./e2_5_health_monitoring.md)
