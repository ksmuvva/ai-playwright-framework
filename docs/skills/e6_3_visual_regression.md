# E6.3 - Visual Regression

**Skill:** `e6_3_visual_regression`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Performs visual regression testing by comparing screenshots against baselines.

## Capabilities

- Capture screenshots
- Compare images
- Generate diff reports
- Manage baseline images

## Usage

```python
agent = VisualRegressionAgent()
result = await agent.run("compare", {"screenshot": "login.png"})
```

## See Also

- [E6.1 - Advanced Recording](./e6_1_advanced_recording.md)
- [E6.4 - Performance Recording](./e6_4_performance_recording.md)
