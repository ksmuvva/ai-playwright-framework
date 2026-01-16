# E8.5 - Migration Tools

**Skill:** `e8_5_migration_tools`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Provides tools for migrating between versions, backing up data, and restoring state.

## Capabilities

- Create backups
- Restore from backups
- Migrate state between versions
- Rollback migrations

## Usage

```python
agent = MigrationToolsAgent()

# Create backup
await agent.run("backup", {
    "source": ".cpa/state",
    "destination": ".cpa/backups/backup_001"
})

# Migrate state
await agent.run("migrate", {
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "state": {...}
})
```

## See Also

- [E8.1 - Error Handling](./e8_1_error_handling.md)
- [E1.2 - State Management](../e1_2_state_management.md)
