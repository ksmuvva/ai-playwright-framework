# E9.2 - CI/CD Integration

**Skill:** `e9_2_cicd_integration`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Generates CI/CD pipeline configurations for popular platforms.

## Capabilities

- Generate GitHub Actions workflows
- Generate GitLab CI pipelines
- Generate Jenkins pipelines
- Support custom CI platforms

## Usage

```python
agent = CICDIntegrationAgent()

# Generate GitHub Actions
workflow = await agent.run("generate_github", {
    "project": "my_test_project"
})

# Generate GitLab CI
pipeline = await agent.run("generate_gitlab", {
    "project": "my_test_project"
})
```

## Output Examples

### GitHub Actions (.github/workflows/test.yml)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: cpa test
```

## See Also

- [E9.1 - Parallel Execution](./e9_1_parallel_execution.md)
- [E9.4 - API Validation](./e9_4_api_validation.md)
