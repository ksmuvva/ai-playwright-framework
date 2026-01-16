"""
Tests for the Test Reporting module.

Tests cover:
- ReportFormat and ReportSection models
- TestReport model and statistics
- ReportGenerator initialization
- HTML report generation
- JSON report generation
"""

from pathlib import Path
from unittest.mock import patch
import tempfile

import pytest

from claude_playwright_agent.agents.reporting import (
    ReportFormat,
    ReportGenerator,
    ReportSection,
    TestMetric,
    TestReport,
    create_report,
)


# =============================================================================
# Model Tests
# =============================================================================


class TestTestMetric:
    """Tests for TestMetric model."""

    def test_create_metric(self) -> None:
        """Test creating a metric."""
        metric = TestMetric(
            name="Response Time",
            value=1.5,
            unit="s",
            description="Average response time",
        )

        assert metric.name == "Response Time"
        assert metric.value == 1.5
        assert metric.unit == "s"
        assert metric.description == "Average response time"

    def test_metric_to_dict(self) -> None:
        """Test converting metric to dictionary."""
        metric = TestMetric(
            name="Pass Rate",
            value=85,
            unit="%",
        )

        data = metric.to_dict()

        assert data["name"] == "Pass Rate"
        assert data["value"] == 85
        assert data["unit"] == "%"


class TestReportSection:
    """Tests for ReportSection model."""

    def test_create_section(self) -> None:
        """Test creating a report section."""
        section = ReportSection(
            title="Summary",
            content="All tests passed",
            status="success",
        )

        assert section.title == "Summary"
        assert section.content == "All tests passed"
        assert section.status == "success"

    def test_section_to_dict(self) -> None:
        """Test converting section to dictionary."""
        section = ReportSection(
            title="Issues",
            content="Some tests failed",
            status="error",
        )

        data = section.to_dict()

        assert data["title"] == "Issues"
        assert data["content"] == "Some tests failed"
        assert data["status"] == "error"
        assert "timestamp" in data


class TestTestReport:
    """Tests for TestReport model."""

    def test_create_report(self) -> None:
        """Test creating a report."""
        report = TestReport(
            title="Test Report",
            framework="behave",
        )

        assert report.title == "Test Report"
        assert report.framework == "behave"
        assert report.total_tests == 0

    def test_calculate_statistics(self) -> None:
        """Test statistics calculation."""
        report = TestReport(
            title="Test Report",
            framework="behave",
            total_tests=10,
            passed=8,
            failed=2,
        )

        report.calculate_statistics()

        assert report.pass_rate == 80.0
        assert report.end_time != ""

    def test_add_metric(self) -> None:
        """Test adding a metric."""
        report = TestReport(title="Test Report", framework="behave")

        report.add_metric("Total Tests", 10, "count")

        assert len(report.metrics) == 1
        assert report.metrics[0].name == "Total Tests"
        assert report.metrics[0].value == 10

    def test_add_section(self) -> None:
        """Test adding a section."""
        report = TestReport(title="Test Report", framework="behave")

        report.add_section("Summary", "Tests completed")

        assert len(report.sections) == 1
        assert report.sections[0].title == "Summary"
        assert report.sections[0].content == "Tests completed"

    def test_report_to_dict(self) -> None:
        """Test converting report to dictionary."""
        report = TestReport(
            title="Test Report",
            framework="behave",
            total_tests=5,
            passed=3,
            failed=2,
        )

        data = report.to_dict()

        assert data["title"] == "Test Report"
        assert data["framework"] == "behave"
        assert data["total_tests"] == 5
        assert data["passed"] == 3
        assert data["failed"] == 2

    def test_report_to_json(self) -> None:
        """Test converting report to JSON."""
        report = TestReport(
            title="Test Report",
            framework="playwright",
        )

        json_str = report.to_json()

        assert '"title": "Test Report"' in json_str
        assert '"framework": "playwright"' in json_str


# =============================================================================
# ReportGenerator Tests
# =============================================================================


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        generator = ReportGenerator("My Report", "pytest-bdd")

        assert generator.report.title == "My Report"
        assert generator.report.framework == "pytest-bdd"

    def test_add_test_result_passed(self) -> None:
        """Test adding a passed test result."""
        generator = ReportGenerator()

        generator.add_test_result(
            name="login test",
            status="passed",
            duration=1.5,
        )

        report = generator.report
        assert report.total_tests == 1
        assert report.passed == 1
        assert report.failed == 0
        assert report.duration == 1.5
        assert len(report.test_results) == 1

    def test_add_test_result_failed(self) -> None:
        """Test adding a failed test result."""
        generator = ReportGenerator()

        generator.add_test_result(
            name="checkout test",
            status="failed",
            duration=2.0,
            error_message="AssertionError",
            stack_trace="at test_checkout.py:42",
        )

        report = generator.report
        assert report.total_tests == 1
        assert report.failed == 1
        assert report.passed == 0

    def test_add_test_result_skipped(self) -> None:
        """Test adding a skipped test result."""
        generator = ReportGenerator()

        generator.add_test_result(
            name="slow test",
            status="skipped",
        )

        report = generator.report
        assert report.total_tests == 1
        assert report.skipped == 1

    def test_add_test_result_error(self) -> None:
        """Test adding an error test result."""
        generator = ReportGenerator()

        generator.add_test_result(
            name="broken test",
            status="error",
        )

        report = generator.report
        assert report.total_tests == 1
        assert report.errors == 1

    def test_set_duration(self) -> None:
        """Test setting total duration."""
        generator = ReportGenerator()

        generator.set_duration(5.5)

        assert generator.report.duration == 5.5

    def test_generate_html_basic(self) -> None:
        """Test basic HTML generation."""
        generator = ReportGenerator("Test Run", "behave")

        html = generator.generate_html()

        assert "<!DOCTYPE html>" in html
        assert "Test Run" in html
        assert "behave" in html
        assert "<html" in html
        assert "</html>" in html

    def test_generate_html_with_results(self) -> None:
        """Test HTML generation with test results."""
        generator = ReportGenerator()

        generator.add_test_result("test1", "passed", 1.0)
        generator.add_test_result("test2", "failed", 2.0)

        html = generator.generate_html()

        assert "test1" in html
        assert "test2" in html
        assert "passed" in html
        assert "failed" in html
        assert "1.00s" in html
        assert "2.00s" in html

    def test_generate_html_with_metrics(self) -> None:
        """Test HTML generation with metrics."""
        generator = ReportGenerator()
        generator.report.add_metric("Response Time", 1.5, "s", "Average response")
        generator.report.add_metric("Throughput", 100, "req/s", "Requests per second")

        html = generator.generate_html()

        assert "Response Time" in html
        assert "1.5 s" in html
        assert "Throughput" in html
        assert "100 req/s" in html

    def test_generate_html_with_sections(self) -> None:
        """Test HTML generation with sections."""
        generator = ReportGenerator()
        generator.report.add_section("Summary", "All tests passed")
        generator.report.add_section("Details", "See results below")

        html = generator.generate_html()

        assert "Summary" in html
        assert "All tests passed" in html
        assert "Details" in html

    def test_generate_json_basic(self) -> None:
        """Test basic JSON generation."""
        generator = ReportGenerator("JSON Report", "playwright")

        json_str = generator.generate_json()

        data = eval(json_str)
        assert data["title"] == "JSON Report"
        assert data["framework"] == "playwright"

    def test_generate_json_with_results(self) -> None:
        """Test JSON generation with test results."""
        generator = ReportGenerator()

        generator.add_test_result("test1", "passed", 1.0)
        generator.add_test_result("test2", "failed", 2.0, "Error occurred")

        json_str = generator.generate_json()

        data = eval(json_str)
        assert data["total_tests"] == 2
        assert data["passed"] == 1
        assert data["failed"] == 1
        assert len(data["test_results"]) == 2

    def test_save_html(self, tmp_path: Path) -> None:
        """Test saving HTML report to file."""
        generator = ReportGenerator()
        generator.add_test_result("test1", "passed")

        output_file = tmp_path / "reports" / "test_report.html"
        generator.save_html(output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "test1" in content

    def test_save_json(self, tmp_path: Path) -> None:
        """Test saving JSON report to file."""
        generator = ReportGenerator()
        generator.add_test_result("test1", "passed")

        output_file = tmp_path / "reports" / "test_report.json"
        generator.save_json(output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert '"title"' in content
        assert "test1" in content

    def test_save_creates_directories(self, tmp_path: Path) -> None:
        """Test that save creates missing directories."""
        generator = ReportGenerator()

        # Path with non-existent directories
        output_file = tmp_path / "deep" / "nested" / "reports" / "test.html"
        generator.save_html(output_file)

        assert output_file.exists()
        assert output_file.parent.exists()


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_report_basic(self) -> None:
        """Test creating a report with convenience function."""
        generator = create_report("My Report", "behave")

        assert generator.report.title == "My Report"
        assert generator.report.framework == "behave"

    def test_create_report_with_results(self) -> None:
        """Test creating a report with test results."""
        test_results = [
            {"name": "test1", "status": "passed", "duration": 1.0},
            {"name": "test2", "status": "failed", "duration": 2.0},
        ]

        generator = create_report(test_results=test_results)

        assert generator.report.total_tests == 2
        assert generator.report.passed == 1
        assert generator.report.failed == 1

    def test_format_enum_values(self) -> None:
        """Test format enum has correct values."""
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.JSON.value == "json"


class TestReportStatistics:
    """Tests for report statistics calculation."""

    def test_pass_rate_calculation(self) -> None:
        """Test pass rate is calculated correctly."""
        report = TestReport(
            title="Test Report",
            framework="behave",
            total_tests=10,
            passed=7,
            failed=2,
            skipped=1,
        )

        report.calculate_statistics()

        assert report.pass_rate == 70.0

    def test_pass_rate_zero_tests(self) -> None:
        """Test pass rate with zero tests."""
        report = TestReport(title="Test Report", framework="behave")

        report.calculate_statistics()

        assert report.pass_rate == 0.0

    def test_all_passed_rate(self) -> None:
        """Test pass rate when all tests passed."""
        report = TestReport(
            title="Test Report",
            framework="behave",
            total_tests=5,
            passed=5,
        )

        report.calculate_statistics()

        assert report.pass_rate == 100.0


class TestHTMLStructure:
    """Tests for HTML report structure."""

    def test_html_contains_head(self) -> None:
        """Test HTML contains head section."""
        generator = ReportGenerator()
        html = generator.generate_html()

        assert "<head>" in html
        assert "</head>" in html
        assert "<title>" in html
        assert "</title>" in html
        assert "<style>" in html
        assert "</style>" in html

    def test_html_contains_body(self) -> None:
        """Test HTML contains body section."""
        generator = ReportGenerator()
        html = generator.generate_html()

        assert "<body>" in html
        assert "</body>" in html

    def test_html_contains_summary_cards(self) -> None:
        """Test HTML contains summary stat cards."""
        generator = ReportGenerator()
        generator.add_test_result("test1", "passed")

        html = generator.generate_html()

        assert "stat-card" in html
        assert "Total Tests" in html
        assert "Passed" in html

    def test_html_styling_present(self) -> None:
        """Test HTML contains CSS styling."""
        generator = ReportGenerator()
        html = generator.generate_html()

        assert "background:" in html
        assert "padding:" in html
        assert "border-radius:" in html
