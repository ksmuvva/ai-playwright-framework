# E9.5 - Performance Monitoring

**Skill:** `e9_5_performance_monitoring`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Monitors application performance during test execution and identifies bottlenecks.

## Capabilities

- Collect performance metrics
- Detect performance bottlenecks
- Generate performance snapshots
- Track resource usage
- Alert on performance degradation

## Metrics Collected

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Page Load Time | Time to load page | < 3s |
| Time to First Byte (TTFB) | Server response time | < 600ms |
| First Contentful Paint (FCP) | First render time | < 1.8s |
| Largest Contentful Paint (LCP) | Largest element render | < 2.5s |
| Cumulative Layout Shift (CLS) | Layout stability | < 0.1 |

## Usage

```python
agent = PerformanceMonitoringAgent()

# Collect metrics
metrics = await agent.run("collect", {
    "url": "https://example.com"
})

# Detect bottlenecks
bottlenecks = await agent.run("detect_bottlenecks", {
    "threshold": 3000
})

# Create snapshot
snapshot = await agent.run("snapshot", {})
```

## See Also

- [E9.1 - Parallel Execution](./e9_1_parallel_execution.md)
- [E9.3 - Test Reporting](./e9_3_test_reporting.md)
