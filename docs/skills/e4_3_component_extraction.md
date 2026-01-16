# E4.3 - Component Extraction

**Skill:** `e4_3_component_extraction`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Extracts reusable UI components from recordings for better test organization.

## Capabilities

- Identify UI components
- Extract component boundaries
- Generate component abstractions
- Create reusable elements

## Usage

```python
agent = ComponentExtractionAgent()
result = await agent.run("extract", {"recording": {...}})
```

## See Also

- [E4.1 - Element Grouping](./e4_1_deduplication.md)
- [E4.4 - Page Object Generation](./e4_4_page_object_generation.md)
