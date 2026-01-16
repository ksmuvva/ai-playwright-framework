# E1.2 - State Management

**Skill:** `e1_2_state_management`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The State Management skill provides core functionality for managing application state throughout test execution. It handles state persistence, retrieval, and transformation across different test phases.

## Capabilities

- **State Persistence**: Save and load application state to/from files
- **State Transformation**: Transform state between different formats
- **State History**: Track changes to state over time
- **State Validation**: Validate state data integrity
- **Context Management**: Manage context data shared between skills

## Usage

### Basic Usage

```python
from claude_playwright_agent.skills import SkillLoader

loader = SkillLoader(project_path=Path.cwd(), include_builtins=True)
skill = loader.load_skill("path/to/e1_2_state_management/skill.yaml")

agent = skill.agent_class()

# Save state
await agent.run("save_state", {
    "state": {"counter": 42, "status": "running"},
    "state_id": "workflow_001"
})

# Load state
result = await agent.run("load_state", {
    "state_id": "workflow_001"
})
```

## Available Tasks

| Task | Description | Context Required |
|------|-------------|------------------|
| `save_state` | Save state to storage | `state`, `state_id` |
| `load_state` | Load state from storage | `state_id` |
| `update_state` | Update existing state | `state_id`, `updates` |
| `delete_state` | Delete state from storage | `state_id` |
| `list_states` | List all available states | None |
| `validate_state` | Validate state structure | `state` |

## Data Models

### StateEntry

```python
@dataclass
class StateEntry:
    state_id: str
    data: dict
    timestamp: str
    version: str
```

### StateSnapshot

```python
@dataclass
class StateSnapshot:
    snapshot_id: str
    state_id: str
    data: dict
    created_at: str
```

## Configuration

```yaml
# skill.yaml configuration options
state_storage_path: ".cpa/state"
max_history_size: 100
auto_save: true
compression: false
```

## Context Tracking

This skill automatically tracks:

- `_state_history`: List of all state operations performed
- `current_state_id`: ID of the currently active state
- `state_versions`: Version history for state entries

### Accessing Context History

```python
history = agent.get_context_history()
for entry in history:
    print(f"{entry['operation']}: {entry['state_id']}")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `StateNotFoundError` | Requested state ID doesn't exist | Check the state ID or list available states |
| `StateValidationError` | State data is invalid | Ensure state matches expected schema |
| `StorageError` | Cannot read/write state file | Check file permissions and disk space |

## Examples

### Example 1: Save and Load State

```python
# Save workflow state
context = {
    "workflow_id": "test_workflow_001",
    "test_count": 10,
    "passed": 8,
    "failed": 2
}

await agent.run("save_state", {
    "state": context,
    "state_id": "workflow_001"
})

# Later, load the state
result = await agent.run("load_state", {
    "state_id": "workflow_001"
})
# Returns: {state_data: {...}, loaded: true}
```

### Example 2: Update Existing State

```python
await agent.run("update_state", {
    "state_id": "workflow_001",
    "updates": {
        "test_count": 12,
        "passed": 10,
        "failed": 2
    }
})
```

### Example 3: State History Tracking

```python
# Get state history
history = agent.get_context_history()

for entry in history:
    if entry["operation"] == "save_state":
        print(f"Saved state {entry['state_id']} at {entry['timestamp']}")
```

## State Storage Format

States are stored as JSON files:

```
.cpa/state/
├── workflow_001.json
├── workflow_002.json
└── workflow_003.json
```

Example state file:

```json
{
  "state_id": "workflow_001",
  "data": {
    "workflow_id": "test_workflow_001",
    "test_count": 10,
    "passed": 8,
    "failed": 2
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

## Dependencies

None (this is a foundational skill)

## Troubleshooting

**Issue**: "State not found"
- **Solution**: Use `list_states` to see available states or verify the state ID

**Issue**: "State file corrupted"
- **Solution**: Delete the corrupted file and recreate the state

**Issue**: "Out of memory when loading large state"
- **Solution**: Consider using state snapshots or splitting large states

## Best Practices

1. **Use descriptive state IDs**: Include workflow type and timestamp
2. **Clean up old states**: Regularly remove unused states
3. **Validate state before saving**: Use the `validate_state` task
4. **Use state versioning**: Track state schema changes over time

## See Also

- [E1.1 - Project Initialization](./e1_1_project_init.md)
- [E1.3 - Configuration Management](./e1_3_config_management.md)
- [E1.4 - Context Tracking](./e1_4_context_tracking.md)
