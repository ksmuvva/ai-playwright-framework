# E5.2 - Gherkin Generation

**Skill:** `e5_2_gherkin_generation`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Generates well-structured Gherkin feature files from test recordings.

## Capabilities

- Generate feature files
- Create scenarios
- Add scenario outlines
- Include background sections

## Usage

```python
agent = GherkinGenerationAgent()
feature = await agent.run("generate", {"actions": [...]})
```

## See Also

- [E5.1 - BDD Conversion](./e5_1_bdd_conversion.md)
- [E5.3 - Step Definitions](./e5_3_step_definitions.md)
