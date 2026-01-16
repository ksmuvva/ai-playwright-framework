# E2.5 - Health Monitoring & Collaboration

**Skill:** `e2_5_health_monitoring`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Health Monitoring & Collaboration skill monitors agent health, detects failures, and coordinates recovery actions. It provides real-time status tracking and automatic failover capabilities.

## Capabilities

- Monitor agent health
- Detect agent failures
- Trigger recovery actions
- Coordinate collaborative tasks
- Aggregate health metrics

## Usage

```python
health = HealthMonitorAgent()

# Check agent health
status = await health.run("check_health", {
    "agent_id": "agent_001"
})

# Register health check
await health.run("register_check", {
    "agent_id": "agent_001",
    "check_interval": 30
})

# Get system health
system_health = await health.run("system_health", {})
```

## Health Status

| Status | Description | Action |
|--------|-------------|--------|
| `healthy` | Agent is functioning normally | None |
| `degraded` | Agent has issues but is operational | Monitor closely |
| `unhealthy` | Agent has failed | Initiate recovery |
| `unknown` | Agent status cannot be determined | Investigate |

## See Also

- [E2.1 - Orchestration Core](./e2_1_orchestration.md)
- [E2.2 - Agent Lifecycle](./e2_2_lifecycle.md)
