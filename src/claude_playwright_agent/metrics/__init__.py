"""
Metrics Module for Claude Playwright Agent.

This module provides metrics collection and dashboard generation:
- Test execution metrics
- Performance tracking
- Trends analysis
- Dashboard visualization
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: str
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
        }


@dataclass
class Metric:
    """A metric with history."""
    name: str
    type: MetricType
    description: str
    values: list[MetricValue] = field(default_factory=list)
    unit: str = ""
    labels: dict[str, str] = field(default_factory=dict)

    def add_value(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Add a value to the metric."""
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.now().isoformat(),
            labels=labels or {},
        )
        self.values.append(metric_value)

    def get_latest(self) -> Optional[MetricValue]:
        """Get the latest value."""
        return self.values[-1] if self.values else None

    def get_average(self) -> float:
        """Get average value."""
        if not self.values:
            return 0.0
        return sum(v.value for v in self.values) / len(self.values)

    def get_min(self) -> float:
        """Get minimum value."""
        if not self.values:
            return 0.0
        return min(v.value for v in self.values)

    def get_max(self) -> float:
        """Get maximum value."""
        if not self.values:
            return 0.0
        return max(v.value for v in self.values)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        latest = self.get_latest()
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "unit": self.unit,
            "labels": self.labels,
            "latest": latest.to_dict() if latest else None,
            "average": self.get_average(),
            "min": self.get_min(),
            "max": self.get_max(),
            "count": len(self.values),
        }


class MetricsCollector:
    """Collect and manage metrics."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self.metrics: dict[str, Metric] = {}
        self._init_default_metrics()

    def _init_default_metrics(self) -> None:
        """Initialize default metrics."""
        # Test execution metrics
        self.register_metric(
            "tests_total",
            MetricType.COUNTER,
            "Total number of tests executed",
            unit="tests",
        )
        self.register_metric(
            "tests_passed",
            MetricType.COUNTER,
            "Number of tests passed",
            unit="tests",
        )
        self.register_metric(
            "tests_failed",
            MetricType.COUNTER,
            "Number of tests failed",
            unit="tests",
        )
        self.register_metric(
            "tests_skipped",
            MetricType.COUNTER,
            "Number of tests skipped",
            unit="tests",
        )

        # Performance metrics
        self.register_metric(
            "test_duration",
            MetricType.HISTOGRAM,
            "Test execution duration",
            unit="seconds",
        )
        self.register_metric(
            "test_duration_avg",
            MetricType.GAUGE,
            "Average test duration",
            unit="seconds",
        )

        # Agent metrics
        self.register_metric(
            "agent_executions",
            MetricType.COUNTER,
            "Number of agent executions",
            unit="executions",
        )
        self.register_metric(
            "agent_duration",
            MetricType.HISTOGRAM,
            "Agent execution duration",
            unit="seconds",
        )

        # Recording metrics
        self.register_metric(
            "recordings_ingested",
            MetricType.COUNTER,
            "Number of recordings ingested",
            unit="recordings",
        )
        self.register_metric(
            "scenarios_generated",
            MetricType.COUNTER,
            "Number of BDD scenarios generated",
            unit="scenarios",
        )

        # System metrics
        self.register_metric(
            "memory_usage",
            MetricType.GAUGE,
            "Memory usage",
            unit="MB",
        )
        self.register_metric(
            "cpu_usage",
            MetricType.GAUGE,
            "CPU usage",
            unit="percent",
        )

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        unit: str = "",
    ) -> Metric:
        """
        Register a new metric.

        Args:
            name: Metric name
            metric_type: Type of metric
            description: Metric description
            unit: Metric unit

        Returns:
            The registered Metric
        """
        metric = Metric(
            name=name,
            type=metric_type,
            description=description,
            unit=unit,
        )
        self.metrics[name] = metric
        return metric

    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to add
            labels: Optional labels
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.COUNTER, "")

        metric = self.metrics[name]
        latest = metric.get_latest()
        current_value = latest.value if latest else 0.0
        metric.add_value(current_value + value, labels)

    def set(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.GAUGE, "")

        self.metrics[name].add_value(value, labels)

    def record(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Record a value for a histogram/summary metric.

        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.HISTOGRAM, "")

        self.metrics[name].add_value(value, labels)

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        return self.metrics.get(name)

    def get_all_metrics(self) -> dict[str, Metric]:
        """Get all metrics."""
        return self.metrics.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert all metrics to dictionary."""
        return {
            name: metric.to_dict()
            for name, metric in self.metrics.items()
        }


class MetricsDashboard:
    """Generate metrics dashboard."""

    def __init__(self, collector: MetricsCollector) -> None:
        """Initialize the dashboard."""
        self.collector = collector

    def generate_report(self) -> dict[str, Any]:
        """Generate metrics report."""
        metrics = self.collector.get_all_metrics()

        # Group metrics by category
        categories = {
            "Test Execution": [
                "tests_total", "tests_passed", "tests_failed", "tests_skipped",
                "test_duration", "test_duration_avg",
            ],
            "Agents": [
                "agent_executions", "agent_duration",
            ],
            "Recordings": [
                "recordings_ingested", "scenarios_generated",
            ],
            "System": [
                "memory_usage", "cpu_usage",
            ],
        }

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary(metrics),
            "metrics": {},
        }

        for category, metric_names in categories.items():
            report["metrics"][category] = {
                name: metrics[name].to_dict()
                for name in metric_names
                if name in metrics
            }

        return report

    def _generate_summary(self, metrics: dict[str, Metric]) -> dict[str, Any]:
        """Generate summary statistics."""
        summary = {
            "total_metrics": len(metrics),
            "total_values": sum(len(m.values) for m in metrics.values()),
            "metrics_by_type": {},
        }

        # Count by type
        for metric in metrics.values():
            metric_type = metric.type.value
            summary["metrics_by_type"][metric_type] = (
                summary["metrics_by_type"].get(metric_type, 0) + 1
            )

        # Test summary
        tests_total = metrics.get("tests_total")
        tests_passed = metrics.get("tests_passed")
        tests_failed = metrics.get("tests_failed")

        if tests_total and tests_total.get_latest():
            total = tests_total.get_latest().value
            passed_latest = tests_passed.get_latest() if tests_passed else None
            failed_latest = tests_failed.get_latest() if tests_failed else None
            passed = passed_latest.value if passed_latest else 0
            failed = failed_latest.value if failed_latest else 0

            summary["test_summary"] = {
                "total": int(total),
                "passed": int(passed),
                "failed": int(failed),
                "pass_rate": (passed / total * 100) if total > 0 else 0.0,
            }

        return summary

    def generate_html_dashboard(self, output_path: Path) -> None:
        """Generate HTML dashboard."""
        report = self.generate_report()
        html = self._render_html_dashboard(report)
        output_path.write_text(html, encoding="utf-8")

    def _render_html_dashboard(self, report: dict[str, Any]) -> str:
        """Render HTML dashboard."""
        summary = report["summary"]
        metrics = report["metrics"]

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Playwright Agent - Metrics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .timestamp {{
            color: #666;
            font-size: 14px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .summary-card h3 {{
            color: #666;
            font-size: 14px;
            font-weight: normal;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }}

        .summary-card .value.success {{
            color: #10b981;
        }}

        .summary-card .value.error {{
            color: #ef4444;
        }}

        .summary-card .unit {{
            font-size: 14px;
            color: #999;
            margin-left: 5px;
        }}

        .category {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .category h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}

        .metric-card {{
            background: #f9fafb;
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #667eea;
        }}

        .metric-card .name {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}

        .metric-card .description {{
            font-size: 12px;
            color: #999;
            margin-bottom: 10px;
        }}

        .metric-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}

        .metric-card .stats {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }}

        .metric-card .stats span {{
            background: white;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .test-summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
        }}

        .test-summary .metric {{
            text-align: center;
        }}

        .test-summary .metric .label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}

        .test-summary .metric .value {{
            font-size: 28px;
            font-weight: bold;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Metrics Dashboard</h1>
            <p class="timestamp">Generated: {report['generated_at']}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Metrics</h3>
                <div class="value">{summary['total_metrics']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Data Points</h3>
                <div class="value">{summary['total_values']}</div>
            </div>
            {self._render_test_summary(summary.get('test_summary'))}
        </div>

        {self._render_categories(metrics)}
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""

    def _render_test_summary(self, test_summary: dict[str, Any] | None) -> str:
        """Render test summary section."""
        if not test_summary:
            return ""

        return f"""
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <div class="value {'success' if test_summary['pass_rate'] >= 80 else 'error' if test_summary['pass_rate'] < 50 else ''}">{test_summary['pass_rate']:.1f}%</div>
            </div>
        """

    def _render_categories(self, metrics: dict[str, dict[str, Any]]) -> str:
        """Render metric categories."""
        html = ""

        for category_name, category_metrics in metrics.items():
            html += f"""
        <div class="category">
            <h2>{category_name}</h2>
            <div class="metric-grid">
"""

            for metric_name, metric_data in category_metrics.items():
                html += self._render_metric_card(metric_name, metric_data)

            html += """
            </div>
        </div>
"""

        return html

    def _render_metric_card(self, name: str, metric: dict[str, Any]) -> str:
        """Render a single metric card."""
        latest = metric.get("latest")
        latest_value = latest["value"] if latest else 0.0
        unit = metric.get("unit", "")

        return f"""
                <div class="metric-card">
                    <div class="name">{name}</div>
                    <div class="description">{metric.get('description', '')}</div>
                    <div class="value">{latest_value:.2f}{f' <span class="unit">{unit}</span>' if unit else ''}</div>
                    <div class="stats">
                        <span>Avg: {metric.get('average', 0):.2f}</span>
                        <span>Min: {metric.get('min', 0):.2f}</span>
                        <span>Max: {metric.get('max', 0):.2f}</span>
                    </div>
                </div>
"""


# Singleton instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


# Export main components
__all__ = [
    "MetricType",
    "MetricValue",
    "Metric",
    "MetricsCollector",
    "MetricsDashboard",
    "get_metrics_collector",
]
