# E5.4 - Scenario Optimization

**Skill:** `e5_4_scenario_optimization`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Optimizes BDD scenarios by removing redundancy and improving clarity.

## Capabilities

- Remove redundant steps
- Merge similar scenarios
- Generate scenario outlines
- Optimize step order

## Usage

```python
agent = ScenarioOptimizationAgent()
optimized = await agent.run("optimize", {"scenario": {...}})
```

## See Also

- [E5.1 - BDD Conversion](./e5_1_bdd_conversion.md)
- [E5.2 - Gherkin Generation](./e5_2_gherkin_generation.md)
