# E6.1 - Advanced Recording

**Skill:** `e6_1_advanced_recording`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Provides advanced recording capabilities including video, screenshots, and traces.

## Capabilities

- Record video
- Capture screenshots
- Generate traces
- Collect artifacts

## Usage

```python
agent = AdvancedRecordingAgent()
await agent.run("record_video", {"test": "login_test"})
```

## See Also

- [E6.2 - Network Recording](./e6_2_network_recording.md)
- [E6.3 - Visual Regression](./e6_3_visual_regression.md)
