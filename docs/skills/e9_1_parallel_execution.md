# E9.1 - Parallel Execution

**Skill:** `e9_1_parallel_execution`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Enables parallel test execution across multiple workers and processes.

## Capabilities

- Distribute tests across workers
- Manage worker pools
- Aggregate parallel results
- Handle worker failures

## Usage

```python
agent = ParallelExecutionAgent()

await agent.run("execute_parallel", {
    "tests": [...],
    "workers": 4,
    "strategy": "file"
})
```

## Worker Strategies

| Strategy | Description |
|----------|-------------|
| `file` | One worker per test file |
| `class` | One worker per test class |
| `test` | One worker per test |
| `eager` | Distribute tests as they become available |

## See Also

- [E9.2 - CI/CD Integration](./e9_2_cicd_integration.md)
- [E9.3 - Test Reporting](./e9_3_test_reporting.md)
