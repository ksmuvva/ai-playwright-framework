# E4.1 - Element Grouping & Deduplication

**Skill:** `e4_1_deduplication_agent`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Analyzes recordings to group similar elements and deduplicate redundant actions, reducing test suite size and improving maintainability.

## Capabilities

- Group similar selectors
- Detect duplicate actions
- Merge redundant steps
- Optimize action sequences

## Usage

```python
agent = DeduplicationAgent()
result = await agent.run("analyze", {"recording": {...}})
```

## See Also

- [E4.2 - Element Deduplication](./e4_2_element_deduplication.md)
- [E4.3 - Component Extraction](./e4_3_component_extraction.md)
