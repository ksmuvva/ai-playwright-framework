# E9.4 - API Validation

**Skill:** `e9_4_api_validation`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Validates API responses against schemas and contracts.

## Capabilities

- Validate JSON schemas
- Validate response structure
- Check response codes
- Validate headers
- Test API contracts

## Usage

```python
agent = APIValidationAgent()

# Validate response
result = await agent.run("validate", {
    "response": {...},
    "schema": {...}
})

# Check contract
result = await agent.run("check_contract", {
    "api": "/api/users",
    "method": "GET",
    "response": {...}
})
```

## See Also

- [E9.1 - Parallel Execution](./e9_1_parallel_execution.md)
- [E9.3 - Test Reporting](./e9_3_test_reporting.md)
