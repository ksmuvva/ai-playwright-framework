# E6.4 - Performance Recording

**Skill:** `e6_4_performance_recording`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Records performance metrics during test execution including timing, resource usage, and page load metrics.

## Capabilities

- Measure page load times
- Track resource usage
- Record timing metrics
- Generate performance reports

## Usage

```python
agent = PerformanceRecordingAgent()
metrics = await agent.run("record", {"url": "https://example.com"})
```

## See Also

- [E6.1 - Advanced Recording](./e6_1_advanced_recording.md)
- [E6.5 - Recording Enhancement](./e6_5_recording_enhancement.md)
