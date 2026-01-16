"""
Tests for Metrics Module.

Tests cover:
- Metrics collection
- Metric types (counter, gauge, histogram)
- Metrics aggregation
- Dashboard generation
- Report export
"""

from pathlib import Path

import pytest

from claude_playwright_agent.metrics import (
    MetricType,
    MetricValue,
    Metric,
    MetricsCollector,
    MetricsDashboard,
    get_metrics_collector,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def collector() -> MetricsCollector:
    """Create a metrics collector."""
    return MetricsCollector()


@pytest.fixture
def dashboard(collector: MetricsCollector) -> MetricsDashboard:
    """Create a metrics dashboard."""
    return MetricsDashboard(collector)


# =============================================================================
# MetricValue Tests
# =============================================================================


class TestMetricValue:
    """Tests for MetricValue class."""

    def test_create_metric_value(self) -> None:
        """Test creating a metric value."""
        value = MetricValue(
            value=42.0,
            timestamp="2024-01-01T00:00:00",
            labels={"test": "label"},
        )

        assert value.value == 42.0
        assert value.timestamp == "2024-01-01T00:00:00"
        assert value.labels == {"test": "label"}

    def test_to_dict(self) -> None:
        """Test converting metric value to dictionary."""
        value = MetricValue(value=42.0, timestamp="2024-01-01T00:00:00")

        data = value.to_dict()

        assert data["value"] == 42.0
        assert data["timestamp"] == "2024-01-01T00:00:00"
        assert data["labels"] == {}


# =============================================================================
# Metric Tests
# =============================================================================


class TestMetric:
    """Tests for Metric class."""

    def test_create_metric(self) -> None:
        """Test creating a metric."""
        metric = Metric(
            name="test_metric",
            type=MetricType.COUNTER,
            description="A test metric",
            unit="tests",
        )

        assert metric.name == "test_metric"
        assert metric.type == MetricType.COUNTER
        assert metric.description == "A test metric"
        assert metric.unit == "tests"
        assert len(metric.values) == 0

    def test_add_value(self) -> None:
        """Test adding values to a metric."""
        metric = Metric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test",
        )

        metric.add_value(10.0)
        metric.add_value(20.0)

        assert len(metric.values) == 2
        assert metric.values[0].value == 10.0
        assert metric.values[1].value == 20.0

    def test_get_latest(self) -> None:
        """Test getting latest value."""
        metric = Metric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test",
        )

        assert metric.get_latest() is None

        metric.add_value(10.0)
        metric.add_value(20.0)

        latest = metric.get_latest()
        assert latest is not None
        assert latest.value == 20.0

    def test_get_average(self) -> None:
        """Test getting average value."""
        metric = Metric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test",
        )

        assert metric.get_average() == 0.0

        metric.add_value(10.0)
        metric.add_value(20.0)
        metric.add_value(30.0)

        assert metric.get_average() == 20.0

    def test_get_min(self) -> None:
        """Test getting minimum value."""
        metric = Metric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test",
        )

        metric.add_value(10.0)
        metric.add_value(5.0)
        metric.add_value(20.0)

        assert metric.get_min() == 5.0

    def test_get_max(self) -> None:
        """Test getting maximum value."""
        metric = Metric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test",
        )

        metric.add_value(10.0)
        metric.add_value(5.0)
        metric.add_value(20.0)

        assert metric.get_max() == 20.0

    def test_to_dict(self) -> None:
        """Test converting metric to dictionary."""
        metric = Metric(
            name="test_metric",
            type=MetricType.COUNTER,
            description="Test metric",
            unit="count",
        )
        metric.add_value(42.0)

        data = metric.to_dict()

        assert data["name"] == "test_metric"
        assert data["type"] == "counter"
        assert data["description"] == "Test metric"
        assert data["unit"] == "count"
        assert data["latest"]["value"] == 42.0
        assert data["average"] == 42.0


# =============================================================================
# MetricsCollector Tests
# =============================================================================


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_initialization(self, collector: MetricsCollector) -> None:
        """Test collector initialization with default metrics."""
        assert len(collector.metrics) > 0
        assert "tests_total" in collector.metrics
        assert "tests_passed" in collector.metrics
        assert "tests_failed" in collector.metrics

    def test_register_metric(self, collector: MetricsCollector) -> None:
        """Test registering a new metric."""
        metric = collector.register_metric(
            name="custom_metric",
            metric_type=MetricType.GAUGE,
            description="Custom metric",
            unit="units",
        )

        assert metric.name == "custom_metric"
        assert "custom_metric" in collector.metrics

    def test_increment_counter(self, collector: MetricsCollector) -> None:
        """Test incrementing a counter metric."""
        collector.increment("tests_total")
        collector.increment("tests_total", 5.0)

        metric = collector.get_metric("tests_total")
        assert metric is not None
        assert metric.get_latest().value == 6.0

    def test_set_gauge(self, collector: MetricsCollector) -> None:
        """Test setting a gauge metric value."""
        collector.set("memory_usage", 512.0)
        collector.set("memory_usage", 256.0)

        metric = collector.get_metric("memory_usage")
        assert metric is not None
        assert metric.get_latest().value == 256.0

    def test_record_histogram(self, collector: MetricsCollector) -> None:
        """Test recording histogram values."""
        collector.record("test_duration", 1.5)
        collector.record("test_duration", 2.0)
        collector.record("test_duration", 1.0)

        metric = collector.get_metric("test_duration")
        assert metric is not None
        assert len(metric.values) == 3
        assert metric.get_average() == 1.5

    def test_get_metric(self, collector: MetricsCollector) -> None:
        """Test getting a metric by name."""
        metric = collector.get_metric("tests_total")
        assert metric is not None
        assert metric.name == "tests_total"

        nonexistent = collector.get_metric("nonexistent")
        assert nonexistent is None

    def test_get_all_metrics(self, collector: MetricsCollector) -> None:
        """Test getting all metrics."""
        metrics = collector.get_all_metrics()

        assert isinstance(metrics, dict)
        assert len(metrics) > 0
        assert "tests_total" in metrics

    def test_to_dict(self, collector: MetricsCollector) -> None:
        """Test converting all metrics to dictionary."""
        collector.increment("tests_total", 10)
        collector.set("memory_usage", 512)

        data = collector.to_dict()

        assert isinstance(data, dict)
        assert "tests_total" in data
        assert "memory_usage" in data
        assert data["tests_total"]["latest"]["value"] == 10.0

    def test_increment_with_labels(self, collector: MetricsCollector) -> None:
        """Test incrementing with labels."""
        collector.increment("tests_total", 1, labels={"test_name": "login"})

        metric = collector.get_metric("tests_total")
        latest = metric.get_latest()
        assert latest.labels["test_name"] == "login"


# =============================================================================
# MetricsDashboard Tests
# =============================================================================


class TestMetricsDashboard:
    """Tests for MetricsDashboard class."""

    def test_initialization(self, dashboard: MetricsDashboard) -> None:
        """Test dashboard initialization."""
        assert dashboard.collector is not None

    def test_generate_report(self, dashboard: MetricsDashboard) -> None:
        """Test generating metrics report."""
        dashboard.collector.increment("tests_total", 100)
        dashboard.collector.increment("tests_passed", 90)
        dashboard.collector.increment("tests_failed", 10)

        report = dashboard.generate_report()

        assert "generated_at" in report
        assert "summary" in report
        assert "metrics" in report
        assert report["summary"]["total_metrics"] > 0

    def test_generate_summary(self, dashboard: MetricsDashboard) -> None:
        """Test summary generation."""
        dashboard.collector.increment("tests_total", 50)
        dashboard.collector.increment("tests_passed", 45)
        dashboard.collector.increment("tests_failed", 5)

        report = dashboard.generate_report()
        summary = report["summary"]

        assert "total_metrics" in summary
        assert "total_values" in summary
        assert "metrics_by_type" in summary
        assert "test_summary" in summary

        test_summary = summary["test_summary"]
        assert test_summary["total"] == 50
        assert test_summary["passed"] == 45
        assert test_summary["failed"] == 5
        assert test_summary["pass_rate"] == 90.0

    def test_generate_html_dashboard(self, dashboard: MetricsDashboard, tmp_path: Path) -> None:
        """Test generating HTML dashboard."""
        dashboard.collector.increment("tests_total", 10)

        output_path = tmp_path / "dashboard.html"
        dashboard.generate_html_dashboard(output_path)

        assert output_path.exists()
        content = output_path.read_text()

        assert "<!DOCTYPE html>" in content
        assert "Metrics Dashboard" in content
        assert "tests_total" in content

    def test_html_dashboard_categories(self, dashboard: MetricsDashboard, tmp_path: Path) -> None:
        """Test HTML dashboard includes all categories."""
        dashboard.collector.increment("tests_total", 10)
        dashboard.collector.increment("agent_executions", 5)
        dashboard.collector.increment("recordings_ingested", 3)
        dashboard.collector.set("memory_usage", 512)

        output_path = tmp_path / "dashboard.html"
        dashboard.generate_html_dashboard(output_path)

        content = output_path.read_text()

        assert "Test Execution" in content
        assert "Agents" in content
        assert "Recordings" in content
        assert "System" in content


# =============================================================================
# Global Collector Tests
# =============================================================================


class TestGlobalCollector:
    """Tests for global metrics collector."""

    def test_get_metrics_collector_singleton(self) -> None:
        """Test that get_metrics_collector returns singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_global_collector_persists(self) -> None:
        """Test that global collector persists across calls."""
        collector = get_metrics_collector()
        collector.increment("tests_total", 5)

        collector2 = get_metrics_collector()
        metric = collector2.get_metric("tests_total")

        assert metric is not None
        assert metric.get_latest().value == 5.0


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_metric_aggregations(self) -> None:
        """Test aggregations on empty metric."""
        metric = Metric(
            name="empty",
            type=MetricType.GAUGE,
            description="Empty metric",
        )

        assert metric.get_latest() is None
        assert metric.get_average() == 0.0
        assert metric.get_min() == 0.0
        assert metric.get_max() == 0.0

    def test_increment_nonexistent_metric(self, collector: MetricsCollector) -> None:
        """Test incrementing a metric that doesn't exist creates it."""
        collector.increment("new_metric", 10)

        metric = collector.get_metric("new_metric")
        assert metric is not None
        assert metric.get_latest().value == 10.0

    def test_report_with_no_data(self, dashboard: MetricsDashboard) -> None:
        """Test generating report with no metric data."""
        report = dashboard.generate_report()

        assert "summary" in report
        assert "metrics" in report
        assert report["summary"]["total_metrics"] > 0

    def test_metric_with_unicode_description(self, collector: MetricsCollector) -> None:
        """Test metric with unicode characters in description."""
        metric = collector.register_metric(
            name="unicode_test",
            metric_type=MetricType.GAUGE,
            description="Test with émojis 🎉",
        )

        assert "émojis" in metric.description
        assert "🎉" in metric.description
