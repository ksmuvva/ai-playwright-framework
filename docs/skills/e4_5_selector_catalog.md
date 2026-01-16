# E4.5 - Selector Catalog

**Skill:** `e4_5_selector_catalog`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Maintains a catalog of selectors used across tests for consistency and reusability.

## Capabilities

- Catalog selectors
- Find similar selectors
- Suggest optimal selectors
- Track selector usage

## Usage

```python
agent = SelectorCatalogAgent()
agent.add_selector("#login-button", "login_page")
similar = agent.find_similar("#login-btn")
```

## See Also

- [E4.1 - Element Grouping](./e4_1_deduplication.md)
- [E4.4 - Page Object Generation](./e4_4_page_object_generation.md)
