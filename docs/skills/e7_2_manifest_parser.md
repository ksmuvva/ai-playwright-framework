# E7.2 - Manifest Parser

**Skill:** `e7_2_manifest_parser`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Parses and validates skill manifest files (skill.yaml).

## Capabilities

- Parse YAML manifests
- Validate manifest structure
- Extract skill metadata
- Handle manifest errors

## Usage

```python
from claude_playwright_agent.skills.manifest import parse_manifest

manifest = parse_manifest("path/to/skill.yaml")
```

## See Also

- [E7.1 - Skill Registry](./e7_1_registry.md)
- [E7.3 - Custom Skills](./e7_3_custom_skill.md)
