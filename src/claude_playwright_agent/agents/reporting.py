"""
Test Reporting Module for Claude Playwright Agent.

This module handles:
- Generating HTML test reports
- Generating JSON test reports
- Aggregating test results
- Computing statistics and metrics
"""

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Report Models
# =============================================================================


class ReportFormat(str, Enum):
    """Supported report formats."""

    HTML = "html"
    JSON = "json"


@dataclass
class TestMetric:
    """Test execution metric."""

    name: str
    value: float | int
    unit: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass
class ReportSection:
    """Section in a test report."""

    title: str
    content: str
    status: str = "info"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "status": self.status,
            "timestamp": self.timestamp,
        }


@dataclass
class TestReport:
    """Complete test report."""

    title: str
    framework: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    pass_rate: float = 0.0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    test_results: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[TestMetric] = field(default_factory=list)
    sections: list[ReportSection] = field(default_factory=list)
    screenshots: list[dict[str, str]] = field(default_factory=list)

    def calculate_statistics(self) -> None:
        """Calculate report statistics."""
        self.pass_rate = (
            (self.passed / self.total_tests * 100)
            if self.total_tests > 0
            else 0.0
        )
        self.end_time = datetime.now().isoformat()

    def add_metric(self, name: str, value: float | int, unit: str = "", description: str = "") -> None:
        """Add a metric to the report."""
        self.metrics.append(TestMetric(name, value, unit, description))

    def add_section(self, title: str, content: str, status: str = "info") -> None:
        """Add a section to the report."""
        self.sections.append(ReportSection(title, content, status))

    def add_screenshot(self, name: str, image_path: Path | str) -> None:
        """Add a screenshot to the report."""
        image_path = Path(image_path)
        if image_path.exists():
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            self.screenshots.append({
                "name": name,
                "data": image_data,
                "timestamp": datetime.now().isoformat(),
            })

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "framework": self.framework,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration": self.duration,
            "pass_rate": self.pass_rate,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "test_results": self.test_results,
            "metrics": [m.to_dict() for m in self.metrics],
            "sections": [s.to_dict() for s in self.sections],
            "screenshots": self.screenshots,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# Report Generator
# =============================================================================


class ReportGenerator:
    """
    Generate test reports in various formats.

    Features:
    - HTML report generation with styling
    - JSON report generation
    - Statistics calculation
    - Screenshot embedding
    - Timeline visualization
    """

    # HTML template for reports
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-card.passed .value {{ color: #28a745; }}
        .stat-card.failed .value {{ color: #dc3545; }}
        .stat-card.skipped .value {{ color: #ffc107; }}
        .stat-card.total .value {{ color: #667eea; }}
        .stat-card .label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .section {{
            padding: 30px;
            border-bottom: 1px solid #e9ecef;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            margin-bottom: 20px;
            color: #495057;
        }}
        .test-list {{
            list-style: none;
        }}
        .test-item {{
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-item.passed {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .test-item.failed {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .test-item.skipped {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .test-item.error {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .test-name {{
            font-weight: 600;
            flex-grow: 1;
        }}
        .test-duration {{
            color: #6c757d;
            font-size: 0.9em;
            margin-left: 15px;
        }}
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .screenshot-item {{
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .screenshot-item img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .screenshot-item .caption {{
            padding: 10px;
            background: #f8f9fa;
            font-size: 0.9em;
            text-align: center;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }}
        .metric-card .name {{
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .metric-card .value {{
            font-size: 1.5em;
            color: #667eea;
        }}
        .metric-card .description {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 5px;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            display: flex;
            margin: 20px 0;
        }}
        .progress-bar .passed {{
            background: #28a745;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
        }}
        .progress-bar .failed {{
            background: #dc3545;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
        }}
        .progress-bar .skipped {{
            background: #ffc107;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                Framework: {framework} | Generated: {timestamp}
            </div>
        </div>

        <div class="summary">
            <div class="stat-card total">
                <div class="value">{total_tests}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="stat-card passed">
                <div class="value">{passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="value">{failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card skipped">
                <div class="value">{skipped}</div>
                <div class="label">Skipped</div>
            </div>
        </div>

        {progress_bar}

        {test_results_section}

        {metrics_section}

        {screenshots_section}

        {sections_html}
    </div>
</body>
</html>
"""

    def __init__(self, report_title: str = "Test Report", framework: str = "behave") -> None:
        """
        Initialize the report generator.

        Args:
            report_title: Title for the report
            framework: Test framework being used
        """
        self._report = TestReport(title=report_title, framework=framework)

    @property
    def report(self) -> TestReport:
        """Get the report object."""
        return self._report

    def add_test_result(
        self,
        name: str,
        status: str,
        duration: float = 0.0,
        error_message: str = "",
        stack_trace: str = "",
    ) -> None:
        """Add a test result to the report."""
        self._report.test_results.append({
            "name": name,
            "status": status,
            "duration": duration,
            "error_message": error_message,
            "stack_trace": stack_trace,
        })

        # Update totals
        self._report.total_tests += 1
        if status == "passed":
            self._report.passed += 1
        elif status == "failed":
            self._report.failed += 1
        elif status == "skipped":
            self._report.skipped += 1
        elif status == "error":
            self._report.errors += 1

        self._report.duration += duration

    def set_duration(self, duration: float) -> None:
        """Set the total duration."""
        self._report.duration = duration

    def generate_html(self) -> str:
        """Generate HTML report."""
        self._report.calculate_statistics()

        # Build test results HTML
        test_results_html = ""
        if self._report.test_results:
            test_items = []
            for test in self._report.test_results:
                test_items.append(f'''
                <li class="test-item {test['status']}">
                    <span class="test-name">{test['name']}</span>
                    <span class="test-duration">{test['duration']:.2f}s</span>
                </li>''')

            test_results_html = f'''
            <div class="section">
                <h2>Test Results</h2>
                <ul class="test-list">
                    {''.join(test_items)}
                </ul>
            </div>'''

        # Build metrics HTML
        metrics_html = ""
        if self._report.metrics:
            metric_cards = []
            for metric in self._report.metrics:
                metric_cards.append(f'''
                <div class="metric-card">
                    <div class="name">{metric.name}</div>
                    <div class="value">{metric.value} {metric.unit}</div>
                    <div class="description">{metric.description}</div>
                </div>''')

            metrics_html = f'''
            <div class="section">
                <h2>Metrics</h2>
                <div class="metrics-grid">
                    {''.join(metric_cards)}
                </div>
            </div>'''

        # Build screenshots HTML
        screenshots_html = ""
        if self._report.screenshots:
            screenshot_items = []
            for screenshot in self._report.screenshots:
                screenshot_items.append(f'''
                <div class="screenshot-item">
                    <img src="data:image/png;base64,{screenshot['data']}" alt="{screenshot['name']}">
                    <div class="caption">{screenshot['name']}</div>
                </div>''')

            screenshots_html = f'''
            <div class="section">
                <h2>Screenshots</h2>
                <div class="screenshot-grid">
                    {''.join(screenshot_items)}
                </div>
            </div>'''

        # Build additional sections HTML
        sections_html = ""
        for section in self._report.sections:
            sections_html += f'''
            <div class="section">
                <h2>{section.title}</h2>
                <div>{section.content}</div>
            </div>'''

        # Build progress bar
        progress_bar = ""
        if self._report.total_tests > 0:
            passed_width = (self._report.passed / self._report.total_tests) * 100
            failed_width = (self._report.failed / self._report.total_tests) * 100
            skipped_width = (self._report.skipped / self._report.total_tests) * 100

            progress_bar = f'''
            <div class="section">
                <h2>Test Progress</h2>
                <div class="progress-bar">
                    <div class="passed" style="width: {passed_width}%">Passed: {passed_width:.1f}%</div>
                    <div class="failed" style="width: {failed_width}%">Failed: {failed_width:.1f}%</div>
                    <div class="skipped" style="width: {skipped_width}%">Skipped: {skipped_width:.1f}%</div>
                </div>
            </div>'''

        # Render template
        return self.HTML_TEMPLATE.format(
            title=self._report.title,
            framework=self._report.framework,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=self._report.total_tests,
            passed=self._report.passed,
            failed=self._report.failed,
            skipped=self._report.skipped,
            progress_bar=progress_bar,
            test_results_section=test_results_html,
            metrics_section=metrics_html,
            screenshots_section=screenshots_html,
            sections_html=sections_html,
        )

    def generate_json(self) -> str:
        """Generate JSON report."""
        self._report.calculate_statistics()
        return self._report.to_json()

    def save_html(self, output_path: Path | str) -> None:
        """
        Save HTML report to file.

        Args:
            output_path: Path to save the HTML file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self.generate_html()
        output_path.write_text(html, encoding="utf-8")

    def save_json(self, output_path: Path | str) -> None:
        """
        Save JSON report to file.

        Args:
            output_path: Path to save the JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = self.generate_json()
        output_path.write_text(json_str, encoding="utf-8")


# =============================================================================
# Convenience Functions
# =============================================================================


def create_report(
    title: str = "Test Report",
    framework: str = "behave",
    test_results: list[dict[str, Any]] | None = None,
) -> ReportGenerator:
    """
    Create a new report generator.

    Args:
        title: Report title
        framework: Test framework name
        test_results: Optional list of test results

    Returns:
        ReportGenerator instance
    """
    generator = ReportGenerator(title, framework)

    if test_results:
        for result in test_results:
            generator.add_test_result(
                name=result.get("name", "Unknown"),
                status=result.get("status", "pending"),
                duration=result.get("duration", 0.0),
                error_message=result.get("error_message", ""),
                stack_trace=result.get("stack_trace", ""),
            )

    return generator
