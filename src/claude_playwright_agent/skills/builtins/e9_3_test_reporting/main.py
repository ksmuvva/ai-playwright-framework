"""
E9.3 - Test Reporting & Analytics Skill.

This skill provides test reporting capabilities:
- Result aggregation
- Report generation
- Trend analysis
- Multiple export formats
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ReportFormat(str, Enum):
    """Report format types."""

    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"
    JUNIT = "junit"
    ALLURE = "allure"
    MARKDOWN = "markdown"


class TestStatus(str, Enum):
    """Test status types."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
    RUNNING = "running"


@dataclass
class TestResult:
    """
    A single test result.

    Attributes:
        result_id: Unique result identifier
        test_name: Name of the test
        status: Test status
        duration_ms: Test duration in milliseconds
        error_message: Error message if failed
        stack_trace: Stack trace if failed
        screenshot_path: Path to screenshot
        metadata: Additional metadata
        timestamp: When test completed
    """

    result_id: str = field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    test_name: str = ""
    status: TestStatus = TestStatus.PENDING
    duration_ms: int = 0
    error_message: str = ""
    stack_trace: str = ""
    screenshot_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "screenshot_path": self.screenshot_path,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class TestSuite:
    """
    A collection of test results.

    Attributes:
        suite_id: Unique suite identifier
        suite_name: Name of the test suite
        results: List of test results
        total_tests: Total number of tests
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        total_duration_ms: Total duration in milliseconds
        started_at: When suite started
        completed_at: When suite completed
    """

    suite_id: str = field(default_factory=lambda: f"suite_{uuid.uuid4().hex[:8]}")
    suite_name: str = ""
    results: list[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration_ms: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "results": [r.to_dict() for r in self.results],
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_duration_ms": self.total_duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TestReport:
    """
    A generated test report.

    Attributes:
        report_id: Unique report identifier
        workflow_id: Associated workflow ID
        title: Report title
        format: Report format
        suites: List of test suites
        summary: Report summary statistics
        generated_at: When report was generated
        file_path: Path to generated report file
        include_charts: Whether charts are included
    """

    report_id: str = field(default_factory=lambda: f"report_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    title: str = ""
    format: ReportFormat = ReportFormat.HTML
    suites: list[TestSuite] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: str = ""
    include_charts: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "workflow_id": self.workflow_id,
            "title": self.title,
            "format": self.format.value,
            "suites": [s.to_dict() for s in self.suites],
            "summary": self.summary,
            "generated_at": self.generated_at,
            "file_path": self.file_path,
            "include_charts": self.include_charts,
        }


@dataclass
class TrendData:
    """
    Trend analysis data.

    Attributes:
        trend_id: Unique trend identifier
        metric_name: Name of the metric
        data_points: List of data points
        timestamps: List of timestamps
        trend_direction: "up", "down", or "stable"
        change_percent: Percentage change
        baseline: Baseline value
    """

    trend_id: str = field(default_factory=lambda: f"trend_{uuid.uuid4().hex[:8]}")
    metric_name: str = ""
    data_points: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    trend_direction: str = "stable"
    change_percent: float = 0.0
    baseline: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trend_id": self.trend_id,
            "metric_name": self.metric_name,
            "data_points": self.data_points,
            "timestamps": self.timestamps,
            "trend_direction": self.trend_direction,
            "change_percent": self.change_percent,
            "baseline": self.baseline,
        }


@dataclass
class ReportingContext:
    """
    Context for reporting operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        reports_generated: Number of reports generated
        formats_supported: Number of formats supported
        trends_analyzed: Number of trends analyzed
        report_history: List of generated reports
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"rep_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    reports_generated: int = 0
    formats_supported: int = 0
    trends_analyzed: int = 0
    report_history: list[TestReport] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "reports_generated": self.reports_generated,
            "formats_supported": self.formats_supported,
            "trends_analyzed": self.trends_analyzed,
            "report_history": [r.to_dict() for r in self.report_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class TestReportingAgent(BaseAgent):
    """
    Test Reporting and Analytics Agent.

    This agent provides:
    1. Result aggregation
    2. Report generation
    3. Trend analysis
    4. Multiple export formats
    """

    name = "e9_3_test_reporting"
    version = "1.0.0"
    description = "E9.3 - Test Reporting & Analytics"

    def __init__(self, **kwargs) -> None:
        """Initialize the test reporting agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E9.3 - Test Reporting & Analytics agent for the Playwright test automation framework. You help users with e9.3 - test reporting & analytics tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[ReportingContext] = []
        self._report_registry: dict[str, TestReport] = {}
        self._suite_registry: dict[str, TestSuite] = {}
        self._trend_history: list[TrendData] = []

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """Execute reporting task."""
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "create_suite":
            return await self._create_suite(context, execution_context)
        elif task_type == "add_result":
            return await self._add_result(context, execution_context)
        elif task_type == "generate_report":
            return await self._generate_report(context, execution_context)
        elif task_type == "analyze_trends":
            return await self._analyze_trends(context, execution_context)
        elif task_type == "export_report":
            return await self._export_report(context, execution_context)
        elif task_type == "get_report":
            return await self._get_report(context, execution_context)
        elif task_type == "get_suite":
            return await self._get_suite(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _create_suite(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a test suite."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        suite_name = context.get("suite_name", "")

        suite = TestSuite(
            suite_name=suite_name,
        )

        self._suite_registry[suite.suite_id] = suite

        return f"Created test suite '{suite_name}' (ID: {suite.suite_id})"

    async def _add_result(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add a test result to a suite."""
        suite_id = context.get("suite_id")
        test_name = context.get("test_name", "")
        status = context.get("status", TestStatus.PASSED)
        duration_ms = context.get("duration_ms", 0)

        if isinstance(status, str):
            status = TestStatus(status)

        result = TestResult(
            test_name=test_name,
            status=status,
            duration_ms=duration_ms,
        )

        if suite_id:
            suite = self._suite_registry.get(suite_id)
            if suite:
                suite.results.append(result)
                suite.total_tests += 1
                if status == TestStatus.PASSED:
                    suite.passed += 1
                elif status == TestStatus.FAILED:
                    suite.failed += 1
                elif status == TestStatus.SKIPPED:
                    suite.skipped += 1

                return f"Added result: {test_name} -> {status.value}"

        return f"Added result: {test_name} -> {status.value}"

    async def _generate_report(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate a test report."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        title = context.get("title", "Test Report")
        report_format = context.get("format", ReportFormat.HTML)
        suite_ids = context.get("suite_ids", [])
        include_charts = context.get("include_charts", True)

        if isinstance(report_format, str):
            report_format = ReportFormat(report_format)

        # Collect suites
        suites = []
        total_tests = 0
        total_passed = 0
        total_failed = 0

        for suite_id in suite_ids:
            suite = self._suite_registry.get(suite_id)
            if suite:
                suites.append(suite)
                total_tests += suite.total_tests
                total_passed += suite.passed
                total_failed += suite.failed

        # Create summary
        summary = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": sum(s.skipped for s in suites),
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "total_duration_ms": sum(s.total_duration_ms for s in suites),
        }

        # Create report
        report = TestReport(
            workflow_id=workflow_id,
            title=title,
            format=report_format,
            suites=suites,
            summary=summary,
            include_charts=include_charts,
        )

        self._report_registry[report.report_id] = report

        return (
            f"Generated report '{title}': {total_tests} tests, "
            f"{summary['pass_rate']:.1f}% pass rate, "
            f"format={report_format.value}"
        )

    async def _analyze_trends(self, context: dict[str, Any], execution_context: Any) -> str:
        """Analyze test trends."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        metric_name = context.get("metric_name", "pass_rate")
        historical_data = context.get("historical_data", [])

        # Create trend data
        trend = TrendData(
            metric_name=metric_name,
            data_points=historical_data,
            timestamps=[datetime.now().isoformat()],
        )

        # Calculate trend
        if len(historical_data) >= 2:
            if historical_data[-1] > historical_data[-2]:
                trend.trend_direction = "up"
            elif historical_data[-1] < historical_data[-2]:
                trend.trend_direction = "down"
            else:
                trend.trend_direction = "stable"

            if historical_data[0] > 0:
                trend.change_percent = ((historical_data[-1] - historical_data[0]) / historical_data[0]) * 100

        self._trend_history.append(trend)

        return (
            f"Trend analysis for '{metric_name}': "
            f"{trend.trend_direction}, "
            f"{trend.change_percent:+.1f}% change"
        )

    async def _export_report(self, context: dict[str, Any], execution_context: Any) -> str:
        """Export report to file."""
        report_id = context.get("report_id")
        output_path = context.get("output_path", "")

        if not report_id:
            return "Error: report_id is required"

        report = self._report_registry.get(report_id)
        if not report:
            return f"Error: Report '{report_id}' not found"

        # Simulate export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.title.replace(' ', '_')}_{timestamp}.{report.format.value}"
        full_path = str(Path(output_path) / filename) if output_path else filename

        report.file_path = full_path

        return f"Exported report: {full_path}"

    async def _get_report(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get report by ID."""
        report_id = context.get("report_id")

        if not report_id:
            return "Error: report_id is required"

        report = self._report_registry.get(report_id)
        if report:
            return (
                f"Report '{report_id}': "
                f"{report.title}, "
                f"{report.summary.get('total_tests', 0)} tests, "
                f"{report.summary.get('pass_rate', 0):.1f}% pass rate"
            )

        return f"Error: Report '{report_id}' not found"

    async def _get_suite(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get suite by ID."""
        suite_id = context.get("suite_id")

        if not suite_id:
            return "Error: suite_id is required"

        suite = self._suite_registry.get(suite_id)
        if suite:
            return (
                f"Suite '{suite_id}': "
                f"{suite.suite_name}, "
                f"{suite.passed}/{suite.total_tests} passed"
            )

        return f"Error: Suite '{suite_id}' not found"

    def get_report_registry(self) -> dict[str, TestReport]:
        """Get report registry."""
        return self._report_registry.copy()

    def get_suite_registry(self) -> dict[str, TestSuite]:
        """Get suite registry."""
        return self._suite_registry.copy()

    def get_trend_history(self) -> list[TrendData]:
        """Get trend history."""
        return self._trend_history.copy()

    def get_context_history(self) -> list[ReportingContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

