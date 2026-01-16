# E6.2 - Network Recording

**Skill:** `e6_2_network_recording`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Records and analyzes network traffic during test execution.

## Capabilities

- Record HAR files
- Mock network requests
- Intercept responses
- Analyze network performance

## Usage

```python
agent = NetworkRecordingAgent()
har = await agent.run("record_har", {"url": "https://example.com"})
```

## See Also

- [E6.1 - Advanced Recording](./e6_1_advanced_recording.md)
- [E6.3 - Visual Regression](./e6_3_visual_regression.md)
