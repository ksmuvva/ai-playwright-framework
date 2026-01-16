# E2.3 - Inter-Agent Communication

**Skill:** `e2_3_inter_agent_communication`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Inter-Agent Communication skill enables agents to exchange messages, share data, and coordinate actions. It provides a messaging infrastructure with support for different communication patterns.

## Capabilities

- Send messages between agents
- Broadcast messages to multiple agents
- Request-response patterns
- Event streaming
- Message queuing

## Usage

```python
comm = CommunicationAgent()

# Send message
await comm.run("send", {
    "from": "agent_001",
    "to": "agent_002",
    "message": {"type": "data", "content": {...}}
})

# Broadcast message
await comm.run("broadcast", {
    "from": "orchestrator",
    "message": {"type": "shutdown", "immediate": true}
})

# Receive messages
messages = await comm.run("receive", {
    "agent_id": "agent_002"
})
```

## Message Format

```python
{
  "message_id": "msg_001",
  "from_agent": "agent_001",
  "to_agent": "agent_002",
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "data|command|event",
  "content": {...}
}
```

## See Also

- [E2.1 - Orchestration Core](./e2_1_orchestration.md)
- [E2.4 - Task Queue](./e2_4_coordination.md)
