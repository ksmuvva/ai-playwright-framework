"""
Historical Trend Analysis for Test Results

Analyzes test execution data over time to identify trends,
regressions, and improvements.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, list
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class TestRun:
    """A test execution run."""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    commit_sha: str = ""
    branch: str = "main"

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests

    @property
    def flakiness(self) -> float:
        """Calculate flakiness rate (failed + skipped) / total."""
        if self.total_tests == 0:
            return 0.0
        return (self.failed + self.skipped) / self.total_tests

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": self.duration,
            "pass_rate": self.pass_rate,
            "flakiness": self.flakiness,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
        }


class TrendAnalyzer:
    """
    Analyze test execution trends over time.

    Features:
    - Pass rate trends
    - Performance regression detection
    - Flaky test identification
    - Historical comparison
    """

    def __init__(self, data_dir: str = ".cpa/trends"):
        """
        Initialize the trend analyzer.

        Args:
            data_dir: Directory to store trend data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._history: list[TestRun] = []
        self._load_history()

    def record_run(
        self,
        total_tests: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        commit_sha: str = "",
        branch: str = "main",
    ):
        """Record a test run."""
        run = TestRun(
            timestamp=datetime.now().isoformat(),
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            commit_sha=commit_sha,
            branch=branch,
        )

        self._history.append(run)
        self._save_history()

    def _load_history(self):
        """Load historical data."""
        history_file = self.data_dir / "history.json"

        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                self._history = [TestRun(**run) for run in data]
            except Exception as e:
                print(f"Warning: Failed to load history: {e}")

    def _save_history(self):
        """Save historical data."""
        history_file = self.data_dir / "history.json"

        data = [run.to_dict() for run in self._history]
        history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_pass_rate_trend(self, days: int = 30) -> dict:
        """
        Get pass rate trend over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend data
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [
            run for run in self._history
            if datetime.fromisoformat(run.timestamp) > cutoff
        ]

        if not recent_runs:
            return {"trend": "no_data", "pass_rates": []}

        pass_rates = [run.pass_rate for run in recent_runs]

        # Calculate trend
        if len(pass_rates) >= 2:
            first_half = pass_rates[:len(pass_rates)//2]
            second_half = pass_rates[len(pass_rates)//2:]

            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)

            if avg_second > avg_first + 0.05:
                trend = "improving"
            elif avg_second < avg_first - 0.05:
                trend = "regressing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "pass_rates": pass_rates,
            "current": pass_rates[-1] if pass_rates else 0,
            "average": statistics.mean(pass_rates) if pass_rates else 0,
            "min": min(pass_rates) if pass_rates else 0,
            "max": max(pass_rates) if pass_rates else 0,
            "stddev": statistics.stdev(pass_rates) if len(pass_rates) > 1 else 0,
        }

    def detect_performance_regression(self, window: int = 10) -> list[dict]:
        """
        Detect performance regressions (slowdowns in test execution).

        Args:
            window: Number of runs to average

        Returns:
            List of detected regressions
        """
        regressions = []

        if len(self._history) < window * 2:
            return regressions

        for i in range(window, len(self._history)):
            # Compare current window with previous window
            current_window = self._history[i-window:i]
            previous_window = self._history[i-window*2:i-window]

            current_avg = statistics.mean([r.duration for r in current_window])
            previous_avg = statistics.mean([r.duration for r in previous_window])

            # Detect if slowdown > 20%
            if current_avg > previous_avg * 1.2:
                regressions.append({
                    "detected_at": self._history[i-1].timestamp,
                    "severity": (current_avg - previous_avg) / previous_avg,
                    "previous_avg_duration": previous_avg,
                    "current_avg_duration": current_avg,
                    "slowdown_percent": ((current_avg - previous_avg) / previous_avg) * 100,
                })

        return regressions

    def compare_branches(self, days: int = 7) -> dict:
        """
        Compare test performance across branches.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with branch comparison
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Group by branch
        by_branch: dict[str, list[TestRun]] = defaultdict(list)
        for run in self._history:
            if datetime.fromisoformat(run.timestamp) > cutoff:
                by_branch[run.branch].append(run)

        # Calculate stats per branch
        comparison = {}
        for branch, runs in by_branch.items():
            if runs:
                pass_rates = [r.pass_rate for r in runs]
                durations = [r.duration for r in runs]

                comparison[branch] = {
                    "total_runs": len(runs),
                    "avg_pass_rate": statistics.mean(pass_rates),
                    "avg_duration": statistics.mean(durations),
                    "stability": 1 - statistics.stdev(pass_rates) if len(pass_rates) > 1 else 1,
                }

        return comparison

    def get_summary(self, days: int = 30) -> dict:
        """
        Get overall summary.

        Args:
            days: Number of days to analyze

        Returns:
            Summary dictionary
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [
            run for run in self._history
            if datetime.fromisoformat(run.timestamp) > cutoff
        ]

        if not recent_runs:
            return {
                "total_runs": 0,
                "avg_pass_rate": 0,
                "avg_duration": 0,
                "total_tests": 0,
            }

        pass_rates = [r.pass_rate for r in recent_runs]
        durations = [r.duration for r in recent_runs]

        return {
            "total_runs": len(recent_runs),
            "avg_pass_rate": statistics.mean(pass_rates),
            "avg_duration": statistics.mean(durations),
            "total_tests": sum(r.total_tests for r in recent_runs) / len(recent_runs),
            "trend": self.get_pass_rate_trend(days)["trend"],
            "regressions": len(self.detect_performance_regression()),
        }

    def generate_report(self, output_path: Path):
        """Generate HTML trend report."""
        summary = self.get_summary(30)
        pass_rate_trend = self.get_pass_rate_trend(30)
        branch_comparison = self.compare_branches(7)
        regressions = self.detect_performance_regression()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Trend Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .summary-card {{ background: #f5f5f5; padding: 15px; border-radius: 8px; }}
        .summary-value {{ font-size: 24px; font-weight: bold; }}
        .summary-label {{ color: #666; font-size: 14px; }}
        .trend-up {{ color: #28a745; }}
        .trend-down {{ color: #dc3545; }}
        .trend-stable {{ color: #ffc107; }}
        .regression {{ background: #f8d7da; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
        .branch {{ background: #e7f3ff; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Test Trend Analysis (Last 30 Days)</h1>

    <div class="summary">
        <div class="summary-card">
            <div class="summary-value">{summary['total_runs']}</div>
            <div class="summary-label">Total Runs</div>
        </div>
        <div class="summary-card">
            <div class="summary-value">{summary['avg_pass_rate']:.1%}</div>
            <div class="summary-label">Avg Pass Rate</div>
        </div>
        <div class="summary-card">
            <div class="summary-value">{summary['avg_duration']:.1f}s</div>
            <div class="summary-label">Avg Duration</div>
        </div>
        <div class="summary-card">
            <div class="summary-value trend-{pass_rate_trend['trend']}">{pass_rate_trend['trend'].upper()}</div>
            <div class="summary-label">Trend</div>
        </div>
    </div>

    <h2>Pass Rate Over Time</h2>
    <canvas id="passRateChart" style="max-height: 300px; margin-bottom: 30px;"></canvas>

    <h2>Performance Regressions</h2>
    {self._generate_regressions_html(regressions)}

    <h2>Branch Comparison (7 Days)</h2>
    {self._generate_branch_comparison_html(branch_comparison)}

    <script>
        const ctx = document.getElementById('passRateChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {list(range(len(pass_rate_trend['pass_rates'])))},
                datasets: [{{
                    label: 'Pass Rate',
                    data: {pass_rate_trend['pass_rates']},
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 1,
                        ticks: {{
                            callback: function(value) {{ return (value * 100) + '%'; }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    def _generate_regressions_html(self, regressions: list) -> str:
        """Generate regressions HTML."""
        if not regressions:
            return "<p>No performance regressions detected! ✅</p>"

        html = []
        for reg in regressions[-10:]:  # Last 10
            html.append(f"""
            <div class="regression">
                <strong>⚠️ Regression Detected</strong><br>
                Detected: {reg['detected_at']}<br>
                Slowdown: {reg['slowdown_percent']:.1f}%<br>
                Duration: {reg['previous_avg_duration']:.1f}s → {reg['current_avg_duration']:.1f}s
            </div>
""")

        return "\n".join(html)

    def _generate_branch_comparison_html(self, comparison: dict) -> str:
        """Generate branch comparison HTML."""
        if not comparison:
            return "<p>No branch data available.</p>"

        html = []
        for branch, stats in comparison.items():
            html.append(f"""
            <div class="branch">
                <strong>📂 {branch}</strong><br>
                Runs: {stats['total_runs']} |
                Pass Rate: {stats['avg_pass_rate']:.1%} |
                Duration: {stats['avg_duration']:.1f}s |
                Stability: {stats['stability']:.1%}
            </div>
""")

        return "\n".join(html)
