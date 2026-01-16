# E7.5 - Skill Discovery

**Skill:** `e7_5_discovery_agent`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Automatically discovers skills from built-in and custom locations.

## Capabilities

- Scan built-in skills
- Scan custom skill directories
- Discover skill manifests
- Load discovered skills

## Usage

```python
from claude_playwright_agent.skills import SkillLoader

loader = SkillLoader(project_path=Path.cwd(), include_builtins=True)
manifests = loader.discover_skills()
```

## See Also

- [E7.1 - Skill Registry](./e7_1_registry.md)
- [E7.2 - Manifest Parser](./e7_2_manifest_parser.md)
