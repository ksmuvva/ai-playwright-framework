# E8.1 - Error Handling

**Skill:** `e8_1_error_handling`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Provides comprehensive error handling, classification, and recovery mechanisms for test execution.

## Capabilities

- Catch and classify errors
- Provide error context
- Suggest recovery actions
- Generate error reports

## Error Classes

| Class | Description | Example |
|-------|-------------|---------|
| `SelectorError` | Element not found | Element not visible |
| `TimeoutError` | Operation timed out | Page load timeout |
| `AssertionError` | Test assertion failed | Expected value mismatch |
| `NetworkError` | Network failure | Connection refused |

## Usage

```python
agent = ErrorHandlingAgent()
try:
    await test_step()
except Exception as e:
    handled = await agent.run("handle_error", {
        "error": e,
        "context": {...}
    })
```

## See Also

- [E8.2 - Interactive Prompts](./e8_2_interactive_prompts.md)
- [E8.3 - CLI Help](./e8_3_cli_help.md)
