# E4.2 - Element Deduplication

**Skill:** `e4_2_element_deduplication`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Identifies and merges duplicate element interactions to reduce test redundancy.

## Capabilities

- Compare element selectors
- Calculate similarity scores
- Cluster similar elements
- Generate optimized selectors

## Usage

```python
agent = ElementDeduplicationAgent()
result = await agent.run("deduplicate", {"actions": [...]})
```

## See Also

- [E4.1 - Element Grouping](./e4_1_deduplication.md)
- [E4.3 - Component Extraction](./e4_3_component_extraction.md)
