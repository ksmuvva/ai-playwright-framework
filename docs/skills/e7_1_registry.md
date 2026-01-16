# E7.1 - Skill Registry

**Skill:** `e7_1_skill_registry`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Central registry for managing all available skills in the system.

## Capabilities

- Register skills
- List available skills
- Enable/disable skills
- Query skill metadata

## Usage

```python
from claude_playwright_agent.skills import get_registry

registry = get_registry()
registry.register(skill)
skills = registry.list_skills()
```

## See Also

- [E7.2 - Manifest Parser](./e7_2_manifest_parser.md)
- [E7.3 - Custom Skills](./e7_3_custom_skill.md)
