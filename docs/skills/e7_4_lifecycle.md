# E7.4 - Skill Lifecycle

**Skill:** `e7_4_skill_lifecycle`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Manages the lifecycle of skills from loading to execution to cleanup.

## Capabilities

- Load skills
- Initialize skills
- Execute skills
- Cleanup skills

## Usage

```python
lifecycle = SkillLifecycleAgent()
await lifecycle.run("load", {"skill": "my_skill"})
await lifecycle.run("initialize", {"skill": "my_skill"})
```

## See Also

- [E7.1 - Skill Registry](./e7_1_registry.md)
- [E7.5 - Skill Discovery](./e7_5_discovery.md)
