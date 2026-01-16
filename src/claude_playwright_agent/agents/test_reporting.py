"""
Test Reporting & Analytics for Claude Playwright Agent.

This module implements:
- HTML/JSON test report generation
- Test history tracking over time
- Flakiness detection and analysis
- Performance metrics collection
- Code coverage integration
- Trend analysis
"""

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from collections import defaultdict


# =============================================================================
# Report Models
# =============================================================================


class ReportFormat(str, Enum):
    """Report output formats."""

    HTML = "html"
    JSON = "json"
    JUNIT = "junit"
    MARKDOWN = "markdown"


class TrendDirection(str, Enum):
    """Trend direction for metrics."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


@dataclass
class TestMetric:
    """
    A single test metric.

    Attributes:
        name: Metric name
        value: Metric value
        unit: Unit of measurement
        timestamp: When metric was recorded
    """

    name: str
    value: float
    unit: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }


@dataclass
class FlakyTestResult:
    """
    Result of flakiness analysis for a test.

    Attributes:
        test_name: Name of the test
        flaky_score: Score from 0-1 (higher = more flaky)
        total_runs: Total number of runs
        failed_runs: Number of failed runs
        pass_rate: Pass rate percentage
        failure_patterns: Detected failure patterns
        recommendation: Suggested action
    """

    test_name: str
    flaky_score: float
    total_runs: int
    failed_runs: int
    pass_rate: float
    failure_patterns: list[str] = field(default_factory=list)
    recommendation: str = ""

    def is_flaky(self, threshold: float = 0.3) -> bool:
        """Check if test is considered flaky."""
        return self.flaky_score >= threshold

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "flaky_score": round(self.flaky_score, 3),
            "total_runs": self.total_runs,
            "failed_runs": self.failed_runs,
            "pass_rate": round(self.pass_rate, 2),
            "failure_patterns": self.failure_patterns,
            "recommendation": self.recommendation,
            "is_flaky": self.is_flaky(),
        }


@dataclass
class TrendAnalysis:
    """
    Analysis of metric trends over time.

    Attributes:
        metric_name: Name of the metric
        direction: Trend direction
        change_percent: Percentage change
        current_value: Current metric value
        previous_value: Previous metric value
        confidence: Confidence in trend (0-1)
    """

    metric_name: str
    direction: TrendDirection
    change_percent: float
    current_value: float
    previous_value: float
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "direction": self.direction.value,
            "change_percent": round(self.change_percent, 2),
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class TestReport:
    """
    Comprehensive test execution report.

    Attributes:
        report_id: Unique report identifier
        timestamp: When report was generated
        framework: Test framework used
        total_tests: Total number of tests
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        duration: Total execution duration
        pass_rate: Pass rate percentage
        test_results: Detailed test results
        metrics: Collected metrics
        flaky_tests: Flaky test analysis
        trends: Trend analysis
    """

    report_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    framework: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    pass_rate: float = 0.0
    test_results: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[TestMetric] = field(default_factory=list)
    flaky_tests: list[FlakyTestResult] = field(default_factory=list)
    trends: list[TrendAnalysis] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "framework": self.framework,
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "duration": self.duration,
                "pass_rate": round(self.pass_rate, 2),
            },
            "test_results": self.test_results,
            "metrics": [m.to_dict() for m in self.metrics],
            "flaky_tests": [f.to_dict() for f in self.flaky_tests],
            "trends": [t.to_dict() for t in self.trends],
        }


# =============================================================================
# Test Report Generator
# =============================================================================


class TestReportGenerator:
    """
    Generate comprehensive test reports.

    Features:
    - HTML report generation
    - JSON export
    - JUnit XML format
    - Markdown reports
    - Performance metrics
    - Flakiness analysis
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the report generator.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._report_dir = self._project_path / ".cpa" / "reports"

    def generate_report(
        self,
        execution_results: list[dict[str, Any]],
        format: ReportFormat = ReportFormat.HTML,
        output_path: Path | None = None,
    ) -> TestReport:
        """
        Generate a test report.

        Args:
            execution_results: Test execution results
            format: Report format
            output_path: Optional output path

        Returns:
            Generated TestReport
        """
        import uuid

        # Build report
        report = TestReport(
            report_id=f"report_{uuid.uuid4().hex[:8]}",
        )

        # Aggregate results
        for result in execution_results:
            report.total_tests += 1
            status = result.get("status", "unknown")

            if status == "passed":
                report.passed += 1
            elif status == "failed":
                report.failed += 1
            elif status == "skipped":
                report.skipped += 1

            report.duration += result.get("duration", 0.0)
            report.test_results.append(result)

        # Calculate pass rate
        if report.total_tests > 0:
            report.pass_rate = (report.passed / report.total_tests) * 100

        # Add metrics
        self._add_metrics(report, execution_results)

        # Generate output
        if output_path is None:
            output_path = self._report_dir / f"{report.report_id}.{format.value}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == ReportFormat.HTML:
            self._write_html_report(report, output_path)
        elif format == ReportFormat.JSON:
            self._write_json_report(report, output_path)
        elif format == ReportFormat.JUNIT:
            self._write_junit_report(report, output_path)
        elif format == ReportFormat.MARKDOWN:
            self._write_markdown_report(report, output_path)

        return report

    def _add_metrics(
        self,
        report: TestReport,
        execution_results: list[dict[str, Any]],
    ) -> None:
        """Add performance metrics to report."""
        durations = [r.get("duration", 0.0) for r in execution_results]

        if durations:
            report.metrics.append(TestMetric(
                name="avg_duration",
                value=statistics.mean(durations),
                unit="seconds",
            ))
            report.metrics.append(TestMetric(
                name="max_duration",
                value=max(durations),
                unit="seconds",
            ))
            report.metrics.append(TestMetric(
                name="min_duration",
                value=min(durations),
                unit="seconds",
            ))

            if len(durations) > 1:
                report.metrics.append(TestMetric(
                    name="duration_stddev",
                    value=statistics.stdev(durations),
                    unit="seconds",
                ))

        report.metrics.append(TestMetric(
            name="throughput",
            value=len(execution_results) / report.duration if report.duration > 0 else 0,
            unit="tests/second",
        ))

    def _write_html_report(self, report: TestReport, output_path: Path) -> None:
        """Write HTML report."""
        html = self._generate_html_template(report)
        output_path.write_text(html, encoding="utf-8")

    def _generate_html_template(self, report: TestReport) -> str:
        """Generate HTML report template."""
        status_color = "#10b981" if report.pass_rate >= 80 else "#f59e0b" if report.pass_rate >= 50 else "#ef4444"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {report.timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-card h3 {{ font-size: 14px; color: #6b7280; margin-bottom: 5px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; }}
        .summary-card.passed .value {{ color: #10b981; }}
        .summary-card.failed .value {{ color: #ef4444; }}
        .summary-card.skipped .value {{ color: #f59e0b; }}
        .summary-card.rate .value {{ color: {status_color}; }}
        .test-results {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .test-results h2 {{ margin-bottom: 20px; }}
        .test-item {{ padding: 15px; border-bottom: 1px solid #e5e7eb; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item.passed {{ border-left: 4px solid #10b981; }}
        .test-item.failed {{ border-left: 4px solid #ef4444; }}
        .test-item.skipped {{ border-left: 4px solid #f59e0b; }}
        .test-name {{ font-weight: 600; margin-bottom: 5px; }}
        .test-meta {{ font-size: 14px; color: #6b7280; }}
        .metrics {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 30px; }}
        .metrics h2 {{ margin-bottom: 20px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .metric {{ background: #f9fafb; padding: 15px; border-radius: 6px; }}
        .metric-name {{ font-size: 12px; color: #6b7280; }}
        .metric-value {{ font-size: 20px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Execution Report</h1>
            <p>{report.timestamp}</p>
        </div>

        <div class="summary">
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="value">{report.passed}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value">{report.failed}</div>
            </div>
            <div class="summary-card skipped">
                <h3>Skipped</h3>
                <div class="value">{report.skipped}</div>
            </div>
            <div class="summary-card rate">
                <h3>Pass Rate</h3>
                <div class="value">{report.pass_rate:.1f}%</div>
            </div>
        </div>

        <div class="test-results">
            <h2>Test Results</h2>
        """

        for test in report.test_results:
            status = test.get("status", "unknown")
            html += f"""
            <div class="test-item {status}">
                <div class="test-name">{test.get('name', 'Unknown')}</div>
                <div class="test-meta">
                    Status: {status} | Duration: {test.get('duration', 0):.2f}s
                </div>
            </div>
            """

        html += """
        </div>
        """

        if report.metrics:
            html += """
        <div class="metrics">
            <h2>Performance Metrics</h2>
            <div class="metric-grid">
            """
            for metric in report.metrics:
                html += f"""
                <div class="metric">
                    <div class="metric-name">{metric.name.replace('_', ' ').title()}</div>
                    <div class="metric-value">{metric.value:.2f} {metric.unit}</div>
                </div>
                """
            html += """
            </div>
        </div>
        """

        html += """
    </div>
</body>
</html>
        """
        return html

    def _write_json_report(self, report: TestReport, output_path: Path) -> None:
        """Write JSON report."""
        output_path.write_text(
            json.dumps(report.to_dict(), indent=2),
            encoding="utf-8"
        )

    def _write_junit_report(self, report: TestReport, output_path: Path) -> None:
        """Write JUnit XML report."""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<testsuites name="{report.framework}" tests="{report.total_tests}" '
        xml += f'failures="{report.failed}" skipped="{report.skipped}" '
        xml += f'time="{report.duration:.3f}">\n'

        for test in report.test_results:
            xml += f'  <testcase name="{test.get("name", "unknown")}" '
            xml += f'time="{test.get("duration", 0):.3f}">\n'

            status = test.get("status", "")
            if status == "failed":
                error_msg = test.get("error_message", "Test failed")
                xml += f'    <failure message="{error_msg}"/>\n'
            elif status == "skipped":
                xml += '    <skipped/>\n'

            xml += '  </testcase>\n'

        xml += '</testsuites>'
        output_path.write_text(xml, encoding="utf-8")

    def _write_markdown_report(self, report: TestReport, output_path: Path) -> None:
        """Write Markdown report."""
        md = f"""# Test Execution Report

**Generated:** {report.timestamp}
**Report ID:** {report.report_id}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {report.total_tests} |
| Passed | {report.passed} |
| Failed | {report.failed} |
| Skipped | {report.skipped} |
| Pass Rate | {report.pass_rate:.1f}% |
| Duration | {report.duration:.2f}s |

## Test Results

"""

        for test in report.test_results:
            status_icon = "✅" if test.get("status") == "passed" else "❌" if test.get("status") == "failed" else "⏭️"
            md += f"- {status_icon} **{test.get('name', 'Unknown')}** - {test.get('status', 'unknown').title()} ({test.get('duration', 0):.2f}s)\n"

        if report.metrics:
            md += "\n## Performance Metrics\n\n"
            for metric in report.metrics:
                md += f"- **{metric.name.replace('_', ' ').title()}**: {metric.value:.2f} {metric.unit}\n"

        output_path.write_text(md, encoding="utf-8")


# =============================================================================
# Test History Tracker
# =============================================================================


class TestHistoryTracker:
    """
    Track test execution history over time.

    Features:
    - Store historical test results
    - Query historical data
    - Calculate trends
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the history tracker.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._history_file = self._project_path / ".cpa" / "test_history.json"
        self._history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._load_history()

    def _load_history(self) -> None:
        """Load history from disk."""
        if self._history_file.exists():
            try:
                data = json.loads(self._history_file.read_text(encoding="utf-8"))
                self._history = defaultdict(list, data)
            except Exception:
                pass

    def _save_history(self) -> None:
        """Save history to disk."""
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        self._history_file.write_text(
            json.dumps(dict(self._history), indent=2),
            encoding="utf-8"
        )

    def record_execution(
        self,
        test_name: str,
        status: str,
        duration: float,
        timestamp: str | None = None,
    ) -> None:
        """
        Record a test execution.

        Args:
            test_name: Name of the test
            status: Test status
            duration: Execution duration
            timestamp: Optional timestamp
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        self._history[test_name].append({
            "status": status,
            "duration": duration,
            "timestamp": timestamp,
        })
        self._save_history()

    def get_history(
        self,
        test_name: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get execution history for a test.

        Args:
            test_name: Name of the test
            limit: Maximum number of records

        Returns:
            List of historical executions
        """
        return self._history[test_name][-limit:]

    def get_all_history(self) -> dict[str, list[dict[str, Any]]]:
        """Get all test history."""
        return dict(self._history)

    def get_pass_rate(
        self,
        test_name: str,
        window: int = 10,
    ) -> float:
        """
        Calculate pass rate for a test.

        Args:
            test_name: Name of the test
            window: Number of recent executions to consider

        Returns:
            Pass rate percentage
        """
        history = self.get_history(test_name, limit=window)

        if not history:
            return 100.0

        passed = sum(1 for h in history if h["status"] == "passed")
        return (passed / len(history)) * 100


# =============================================================================
# Flakiness Detector
# =============================================================================


class FlakinessDetector:
    """
    Detect flaky tests based on historical data.

    Features:
    - Flakiness score calculation
    - Pattern detection
    - Recommendations
    """

    def __init__(
        self,
        history_tracker: TestHistoryTracker | None = None,
    ) -> None:
        """
        Initialize the flakiness detector.

        Args:
            history_tracker: Optional history tracker
        """
        self._history_tracker = history_tracker or TestHistoryTracker()

    def analyze_test(
        self,
        test_name: str,
        min_runs: int = 5,
    ) -> FlakyTestResult:
        """
        Analyze a test for flakiness.

        Args:
            test_name: Name of the test
            min_runs: Minimum runs required for analysis

        Returns:
            FlakyTestResult with analysis
        """
        history = self._history_tracker.get_history(test_name)

        if len(history) < min_runs:
            return FlakyTestResult(
                test_name=test_name,
                flaky_score=0.0,
                total_runs=len(history),
                failed_runs=0,
                pass_rate=100.0,
                recommendation="Not enough data to analyze",
            )

        total_runs = len(history)
        failed_runs = sum(1 for h in history if h["status"] == "failed")
        pass_rate = ((total_runs - failed_runs) / total_runs) * 100

        # Calculate flakiness score based on:
        # 1. Variance in results
        # 2. Frequency of failures
        # 3. Randomness patterns

        # Simple flakiness score: higher when failures are intermittent
        if failed_runs == 0:
            flaky_score = 0.0
        elif failed_runs == total_runs:
            # Consistently failing = not flaky, just broken
            flaky_score = 0.1
        else:
            # Intermittent failures = flaky
            flaky_score = min(1.0, (failed_runs / total_runs) * 2)

        # Detect patterns
        patterns = self._detect_patterns(history)

        # Generate recommendation
        if flaky_score >= 0.5:
            recommendation = "Test is highly flaky. Review test for timing issues, race conditions, or external dependencies."
        elif flaky_score >= 0.3:
            recommendation = "Test shows some flakiness. Consider adding explicit waits or stabilizing test environment."
        elif failed_runs > 0:
            recommendation = "Test fails consistently. Debug and fix the underlying issue."
        else:
            recommendation = "Test appears stable."

        return FlakyTestResult(
            test_name=test_name,
            flaky_score=flaky_score,
            total_runs=total_runs,
            failed_runs=failed_runs,
            pass_rate=pass_rate,
            failure_patterns=patterns,
            recommendation=recommendation,
        )

    def analyze_all(
        self,
        min_runs: int = 5,
    ) -> list[FlakyTestResult]:
        """
        Analyze all tests for flakiness.

        Args:
            min_runs: Minimum runs required for analysis

        Returns:
            List of FlakyTestResults
        """
        results = []
        all_history = self._history_tracker.get_all_history()

        for test_name in all_history:
            result = self.analyze_test(test_name, min_runs)
            results.append(result)

        # Sort by flakiness score (descending)
        results.sort(key=lambda r: r.flaky_score, reverse=True)

        return results

    def _detect_patterns(
        self,
        history: list[dict[str, Any]],
    ) -> list[str]:
        """Detect failure patterns in test history."""
        patterns = []

        if not history:
            return patterns

        # Check for timing issues
        durations = [h.get("duration", 0) for h in history]
        if durations and max(durations) > min(durations) * 3:
            patterns.append("High duration variance (possible timing issue)")

        # Check for alternating failures
        failures = [i for i, h in enumerate(history) if h["status"] == "failed"]
        if len(failures) >= 2:
            gaps = [failures[i+1] - failures[i] for i in range(len(failures)-1)]
            if statistics.mean(gaps) < 3:
                patterns.append("Frequent intermittent failures")

        return patterns


# =============================================================================
# Trend Analyzer
# =============================================================================


class TrendAnalyzer:
    """
    Analyze trends in test metrics over time.

    Features:
    - Trend direction calculation
    - Change percentage
    - Confidence scoring
    """

    def __init__(
        self,
        history_tracker: TestHistoryTracker | None = None,
    ) -> None:
        """
        Initialize the trend analyzer.

        Args:
            history_tracker: Optional history tracker
        """
        self._history_tracker = history_tracker or TestHistoryTracker()

    def analyze_metric_trend(
        self,
        test_name: str,
        metric_name: str,
        window: int = 10,
    ) -> TrendAnalysis:
        """
        Analyze trend for a specific metric.

        Args:
            test_name: Name of the test
            metric_name: Name of the metric (e.g., "duration", "pass_rate")
            window: Number of recent executions to consider

        Returns:
            TrendAnalysis with results
        """
        history = self._history_tracker.get_history(test_name, limit=window)

        if len(history) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNKNOWN,
                change_percent=0.0,
                current_value=0.0,
                previous_value=0.0,
                confidence=0.0,
            )

        # Extract metric values
        if metric_name == "duration":
            values = [h.get("duration", 0) for h in history]
        elif metric_name == "pass_rate":
            # Calculate rolling pass rate
            window_size = min(5, len(values))
            values = []
            for i in range(len(history) - window_size + 1):
                window_data = history[i:i+window_size]
                passed = sum(1 for h in window_data if h["status"] == "passed")
                values.append((passed / len(window_data)) * 100)
        else:
            values = []

        if not values:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNKNOWN,
                change_percent=0.0,
                current_value=0.0,
                previous_value=0.0,
                confidence=0.0,
            )

        current_value = values[-1]
        previous_value = values[0]

        # Calculate change
        if previous_value != 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
        else:
            change_percent = 0.0

        # Determine direction
        if abs(change_percent) < 5:
            direction = TrendDirection.STABLE
        elif change_percent > 0:
            # For duration, increasing is bad; for pass_rate, increasing is good
            if metric_name == "duration":
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.IMPROVING
        else:
            if metric_name == "duration":
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DECLINING

        # Calculate confidence based on variance
        confidence = min(1.0, len(values) / 10)

        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            change_percent=change_percent,
            current_value=current_value,
            previous_value=previous_value,
            confidence=confidence,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_test_report(
    execution_results: list[dict[str, Any]],
    format: ReportFormat = ReportFormat.HTML,
    project_path: Path | str | None = None,
) -> TestReport:
    """
    Generate a test report.

    Args:
        execution_results: Test execution results
        format: Report format
        project_path: Optional project path

    Returns:
        Generated TestReport
    """
    generator = TestReportGenerator(project_path=Path(project_path) if project_path else None)
    return generator.generate_report(execution_results, format)


def detect_flaky_tests(
    min_runs: int = 5,
    project_path: Path | str | None = None,
) -> list[FlakyTestResult]:
    """
    Detect flaky tests.

    Args:
        min_runs: Minimum runs required for analysis
        project_path: Optional project path

    Returns:
        List of flaky tests
    """
    tracker = TestHistoryTracker(project_path=Path(project_path) if project_path else None)
    detector = FlakinessDetector(tracker)
    return detector.analyze_all(min_runs)


def analyze_trends(
    test_name: str,
    metric_name: str,
    window: int = 10,
    project_path: Path | str | None = None,
) -> TrendAnalysis:
    """
    Analyze trends for a test metric.

    Args:
        test_name: Name of the test
        metric_name: Name of the metric
        window: Number of recent executions
        project_path: Optional project path

    Returns:
        Trend analysis
    """
    tracker = TestHistoryTracker(project_path=Path(project_path) if project_path else None)
    analyzer = TrendAnalyzer(tracker)
    return analyzer.analyze_metric_trend(test_name, metric_name, window)
