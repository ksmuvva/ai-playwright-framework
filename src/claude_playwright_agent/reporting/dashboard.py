"""
Real-time Dashboard for Test Execution

Provides live test execution monitoring with WebSocket support.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Real-time test status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestEvent:
    """A test execution event."""
    timestamp: str
    test_name: str
    status: TestStatus
    duration: float = 0.0
    error_message: str = ""
    screenshot: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "screenshot": self.screenshot,
        }


@dataclass
class DashboardMetrics:
    """Dashboard metrics."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    running: int = 0
    duration: float = 0.0
    start_time: str = ""
    tests_per_second: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "running": self.running,
            "duration": self.duration,
            "start_time": self.start_time,
            "tests_per_second": self.tests_per_second,
        }


class RealTimeDashboard:
    """
    Real-time test execution dashboard.

    Features:
    - Live test execution updates
    - WebSocket streaming
    - Historical trends
    - Flaky test detection
    """

    def __init__(self, port: int = 8765):
        """
        Initialize the dashboard.

        Args:
            port: Port for WebSocket server
        """
        self.port = port
        self.events: list[TestEvent] = []
        self.metrics = DashboardMetrics()
        self.clients = set()
        self._running = False
        self._test_results: dict[str, dict] = {}

    async def start_test_run(self, total_tests: int):
        """Start a new test run."""
        self.metrics = DashboardMetrics(
            total_tests=total_tests,
            start_time=datetime.now().isoformat(),
        )
        self.events = []
        self._test_results = {}

        await self._broadcast({
            "type": "test_run_started",
            "data": self.metrics.to_dict(),
        })

        logger.info(f"Dashboard: Test run started with {total_tests} tests")

    async def update_test_status(
        self,
        test_name: str,
        status: TestStatus,
        duration: float = 0.0,
        error_message: str = "",
        screenshot: Optional[str] = None,
    ):
        """Update test status."""
        event = TestEvent(
            timestamp=datetime.now().isoformat(),
            test_name=test_name,
            status=status,
            duration=duration,
            error_message=error_message,
            screenshot=screenshot,
        )

        self.events.append(event)

        # Update metrics
        if status == TestStatus.RUNNING:
            self.metrics.running += 1
        elif status == TestStatus.PASSED:
            self.metrics.running -= 1
            self.metrics.passed += 1
        elif status == TestStatus.FAILED:
            self.metrics.running -= 1
            self.metrics.failed += 1
        elif status == TestStatus.SKIPPED:
            self.metrics.skipped += 1

        # Update duration
        elapsed = datetime.now() - datetime.fromisoformat(self.metrics.start_time)
        self.metrics.duration = elapsed.total_seconds()

        # Calculate tests per second
        if self.metrics.duration > 0:
            completed = self.metrics.passed + self.metrics.failed + self.metrics.skipped
            self.metrics.tests_per_second = completed / self.metrics.duration

        # Store result
        self._test_results[test_name] = event.to_dict()

        # Broadcast update
        await self._broadcast({
            "type": "test_update",
            "data": event.to_dict(),
            "metrics": self.metrics.to_dict(),
        })

    async def finish_test_run(self):
        """Finish the test run."""
        self.metrics.running = 0

        elapsed = datetime.now() - datetime.fromisoformat(self.metrics.start_time)
        self.metrics.duration = elapsed.total_seconds()

        await self._broadcast({
            "type": "test_run_finished",
            "data": self.metrics.to_dict(),
        })

        logger.info(f"Dashboard: Test run finished - {self.metrics.passed}/{self.metrics.total_tests} passed")

    async def _broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_json = json.dumps(message)

        # In a real implementation, this would use WebSockets
        # For now, just log
        logger.debug(f"Broadcast: {message_json}")

    def get_metrics(self) -> DashboardMetrics:
        """Get current metrics."""
        return self.metrics

    def get_events(self, limit: int = 100) -> list[dict]:
        """Get recent events."""
        return [e.to_dict() for e in self.events[-limit:]]

    def get_test_results(self) -> dict[str, dict]:
        """Get all test results."""
        return self._test_results

    def generate_html_report(self, output_path: Path):
        """Generate HTML dashboard report."""
        html = self._generate_html()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        logger.info(f"Dashboard report generated: {output_path}")

    def _generate_html(self) -> str:
        """Generate HTML dashboard."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: bold; }}
        .metric-label {{ color: #666; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .running {{ color: #007bff; }}
        .events {{ max-height: 400px; overflow-y: auto; background: #f9f9f9; padding: 15px; border-radius: 8px; }}
        .event {{ padding: 10px; margin-bottom: 5px; border-left: 4px solid #ccc; background: white; }}
        .event.passed {{ border-left-color: #28a745; }}
        .event.failed {{ border-left-color: #dc3545; }}
        .event.running {{ border-left-color: #007bff; }}
    </style>
</head>
<body>
    <h1>Test Execution Dashboard</h1>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value passed">{self.metrics.passed}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value failed">{self.metrics.failed}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value skipped">{self.metrics.skipped}</div>
            <div class="metric-label">Skipped</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{self.metrics.duration:.1f}s</div>
            <div class="metric-label">Duration</div>
        </div>
    </div>

    <h2>Test Events</h2>
    <div class="events">
        {self._generate_events_html()}
    </div>

    <h2>Progress Chart</h2>
    <canvas id="progressChart" style="max-height: 300px;"></canvas>

    <script>
        const ctx = document.getElementById('progressChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{self.metrics.passed}, {self.metrics.failed}, {self.metrics.skipped}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    def _generate_events_html(self) -> str:
        """Generate events HTML."""
        events_html = []

        for event in self.events[-50:]:  # Last 50 events
            status_class = event.status.value
            events_html.append(f"""
            <div class="event {status_class}">
                <strong>{event.test_name}</strong> - {event.status.value}
                {f"({event.duration:.2f}s)" if event.duration > 0 else ""}
                {f"<br><small>{event.error_message}</small>" if event.error_message else ""}
            </div>
""")

        return "\n".join(events_html)


class FlakyTestDetector:
    """
    Detect flaky tests based on historical execution data.

    A test is considered flaky if it fails intermittently
    on the same code version.
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize the detector.

        Args:
            threshold: Flakiness threshold (0.0 to 1.0)
        """
        self.threshold = threshold
        self._test_history: dict[str, list[dict]] = {}

    def record_execution(
        self,
        test_name: str,
        passed: bool,
        commit_sha: str,
        timestamp: str,
    ):
        """Record a test execution."""
        if test_name not in self._test_history:
            self._test_history[test_name] = []

        self._test_history[test_name].append({
            "passed": passed,
            "commit_sha": commit_sha,
            "timestamp": timestamp,
        })

    def analyze_flakiness(self, test_name: str) -> Optional[dict]:
        """Analyze if a test is flaky."""
        if test_name not in self._test_history:
            return None

        history = self._test_history[test_name]

        if len(history) < 3:  # Need at least 3 runs
            return None

        # Group by commit SHA
        by_commit: dict[str, list[dict]] = {}
        for run in history:
            commit = run["commit_sha"]
            if commit not in by_commit:
                by_commit[commit] = []
            by_commit[commit].append(run)

        # Check for mixed results on same commit
        flaky_commits = 0
        total_commits = len(by_commit)

        for commit, runs in by_commit.items():
            if len(runs) > 1:
                results = [r["passed"] for r in runs]
                if True in results and False in results:
                    flaky_commits += 1

        # Calculate flakiness score
        flakiness_score = flaky_commits / total_commits if total_commits > 0 else 0

        if flakiness_score >= self.threshold:
            return {
                "test_name": test_name,
                "flaky": True,
                "flakiness_score": flakiness_score,
                "total_runs": len(history),
                "flaky_commits": flaky_commits,
                "recent_failures": sum(1 for r in history[-10:] if not r["passed"]),
            }

        return None

    def get_all_flaky_tests(self) -> list[dict]:
        """Get all flaky tests."""
        flaky_tests = []

        for test_name in self._test_history:
            analysis = self.analyze_flakiness(test_name)
            if analysis and analysis["flaky"]:
                flaky_tests.append(analysis)

        # Sort by flakiness score
        flaky_tests.sort(key=lambda x: x["flakiness_score"], reverse=True)

        return flaky_tests

    def get_statistics(self) -> dict:
        """Get detector statistics."""
        total_tests = len(self._test_history)
        flaky_tests = self.get_all_flaky_tests()

        return {
            "total_tests": total_tests,
            "flaky_tests": len(flaky_tests),
            "flakiness_rate": len(flaky_tests) / total_tests if total_tests > 0 else 0,
            "threshold": self.threshold,
        }
