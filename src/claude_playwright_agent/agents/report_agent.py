"""
Report Agent - Agent for generating intelligent test reports.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    """
    Agent for generating intelligent test reports.

    Handles:
    - Failure clustering
    - Executive summaries
    - Trend analysis with historical data
    - AI insights
    - HTML report generation
    - Flakiness detection
    """

    def __init__(
        self,
        mcp_servers: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize the Report Agent."""
        system_prompt = """You are a test reporting expert specializing in making test results actionable.

Your responsibilities:
1. Cluster similar failures to identify patterns
2. Generate executive summaries for stakeholders
3. Provide actionable insights
4. Identify trends over time
5. Highlight flaky tests
6. Create comprehensive HTML reports

When creating reports:
- Focus on business impact
- Highlight high-priority issues
- Provide clear next steps
- Use visualizations when helpful
- Be concise and actionable

For clustering:
- Group failures by root cause
- Identify systemic issues
- Flag patterns that need attention

For summaries:
- Use business language
- Quantify impact
- Suggest priorities

For trend analysis:
- Track metrics over time
- Identify improving/degrading patterns
- Predict future test health"""

        default_tools = [
            "Read",
            "Write",
            "analyze_results",
            "cluster_failures",
            "generate_summary",
            "generate_html_report",
            "detect_flaky_tests",
            "analyze_trends",
        ]

        super().__init__(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools or default_tools,
        )
        self.history_dir = Path(".test_history")
        self.history_dir.mkdir(exist_ok=True)

    async def analyze_results(
        self,
        results_path: str,
    ) -> dict[str, Any]:
        """
        Analyze test results.

        Args:
            results_path: Path to test results JSON

        Returns:
            Analysis with insights and patterns
        """
        await self.initialize()

        with open(results_path, "r") as f:
            results = json.load(f)

        prompt = f"""Analyze these test results from: {results_path}

Please provide:
1. Overall health assessment
2. Key failure patterns
3. Flaky tests identified
4. Recommendations for improvement
5. Priority issues to address

Test Results:
{json.dumps(results, indent=2)}"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            analysis_text = "\n".join(response_parts)

            metrics = self._calculate_metrics(results)

            return {
                "results_path": results_path,
                "analysis": analysis_text,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            }

    def _calculate_metrics(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculate basic metrics from test results."""
        total = results.get("total_tests", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        skipped = results.get("skipped", 0)
        duration = results.get("duration", 0)

        pass_rate = (passed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(pass_rate, 2),
            "duration": duration,
            "status": "healthy"
            if pass_rate >= 95
            else "warning"
            if pass_rate >= 80
            else "critical",
        }

    async def cluster_failures(
        self,
        test_results: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Cluster similar failures.

        Args:
            test_results: Test results dictionary

        Returns:
            Failure clusters with common themes
        """
        failures = test_results.get("failures", [])
        if not failures:
            return {"clusters": [], "message": "No failures to cluster"}

        prompt = f"""Cluster these test failures by root cause:

{json.dumps(failures, indent=2)}

Please provide:
1. Failure clusters (group by similar root causes)
2. Cluster names and descriptions
3. Number of failures in each cluster
4. Affected tests
5. Suggested fix approach for each cluster"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "clusters": "\n".join(response_parts),
                "failure_count": len(failures),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_executive_summary(
        self,
        analysis: dict[str, Any],
        format: str = "markdown",
    ) -> dict[str, Any]:
        """
        Generate executive summary.

        Args:
            analysis: Results analysis
            format: Output format (markdown or html)

        Returns:
            Executive summary in specified format
        """
        prompt = f"""Generate an executive summary from this analysis:

{json.dumps(analysis, indent=2)}

The summary should:
- Be suitable for non-technical stakeholders
- Focus on business impact
- Quantify risk and coverage
- Provide clear next steps
- Be concise (under 300 words)"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            summary = "\n".join(response_parts)

            if format == "html":
                summary = self._render_html(summary, analysis)

            return {
                "summary": summary,
                "format": format,
                "timestamp": datetime.now().isoformat(),
            }

    def _render_html(self, summary: str, analysis: dict[str, Any]) -> str:
        """Render summary as HTML."""
        metrics = analysis.get("metrics", {})
        status_color = {
            "healthy": "#28a745",
            "warning": "#ffc107",
            "critical": "#dc3545",
        }.get(metrics.get("status", "unknown"), "#6c757d")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Executive Summary</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; padding: 20px; }}
        .metric {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: {status_color}; }}
        .metric-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; }}
        .content {{ padding: 20px; }}
        .timestamp {{ color: #6c757d; font-size: 12px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Executive Summary</h1>
        </div>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{metrics.get("total", 0)}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value">{metrics.get("passed", 0)}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{metrics.get("failed", 0)}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{metrics.get("pass_rate", 0)}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>
        <div class="content">
            <h2>Summary</h2>
            <p>{summary}</p>
            <p class="timestamp">Generated: {datetime.now().isoformat()}</p>
        </div>
    </div>
</body>
</html>"""
        return html

    async def detect_flaky_tests(
        self, test_results: dict[str, Any], history_depth: int = 5
    ) -> dict[str, Any]:
        """
        Detect flaky tests based on historical data.

        Args:
            test_results: Current test results
            history_depth: Number of historical runs to consider

        Returns:
            Flaky test analysis with confidence scores
        """
        flaky_tests = []
        test_runs = self._load_history(history_depth)

        current_runs = test_results.get("runs", [])
        test_names = {r.get("name") for r in current_runs}

        for test_name in test_names:
            history = [r for r in test_runs if r.get("name") == test_name]
            current_run = [r for r in current_runs if r.get("name") == test_name]

            if len(history) < 2:
                continue

            failure_count = sum(1 for r in history if r.get("status") == "failed")
            pass_count = sum(1 for r in history if r.get("status") == "passed")
            total_runs = len(history)

            if total_runs > 0:
                failure_rate = failure_count / total_runs

                if 0 < failure_rate < 1.0:
                    flakiness_score = round((1 - abs(0.5 - failure_rate) * 2) * 100, 2)
                    flaky_tests.append(
                        {
                            "name": test_name,
                            "failure_rate": round(failure_rate * 100, 2),
                            "flakiness_score": flakiness_score,
                            "total_runs": total_runs,
                            "passes": pass_count,
                            "failures": failure_count,
                            "status": "likely_flaky" if flakiness_score > 50 else "watch",
                        }
                    )

        flaky_tests.sort(key=lambda x: x["flakiness_score"], reverse=True)

        return {
            "flaky_tests": flaky_tests,
            "total_tests_analyzed": len(test_names),
            "flaky_count": len([t for t in flaky_tests if t["status"] == "likely_flaky"]),
            "watch_count": len([t for t in flaky_tests if t["status"] == "watch"]),
            "timestamp": datetime.now().isoformat(),
        }

    def _load_history(self, depth: int) -> list[dict[str, Any]]:
        """Load historical test runs."""
        history_file = self.history_dir / "test_history.json"
        if not history_file.exists():
            return []

        with open(history_file, "r") as f:
            data = json.load(f)
            return data[-depth:] if len(data) > depth else data

    def _save_to_history(self, test_results: dict[str, Any]) -> None:
        """Save current test results to history."""
        history_file = self.history_dir / "test_history.json"

        existing = []
        if history_file.exists():
            with open(history_file, "r") as f:
                existing = json.load(f)

        run_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self._calculate_metrics(test_results),
            "results": test_results,
        }

        existing.append(run_data)

        max_history = 30
        if len(existing) > max_history:
            existing = existing[-max_history:]

        with open(history_file, "w") as f:
            json.dump(existing, f, indent=2)

    async def analyze_trends(
        self, test_results: dict[str, Any], metric: str = "pass_rate"
    ) -> dict[str, Any]:
        """
        Analyze test trends over historical data.

        Args:
            test_results: Current test results
            metric: Metric to track (pass_rate, total, failed, duration)

        Returns:
            Trend analysis with predictions
        """
        self._save_to_history(test_results)
        history = self._load_history(30)

        if len(history) < 3:
            return {
                "message": "Not enough historical data for trend analysis",
                "data_points": len(history),
                "required": 3,
            }

        values = [h.get("metrics", {}).get(metric, 0) for h in history]

        if len(values) < 2:
            return {"message": "Insufficient data points"}

        changes = [values[i] - values[i - 1] for i in range(1, len(values))]
        avg_change = sum(changes) / len(changes) if changes else 0

        recent_avg = sum(values[-3:]) / min(3, len(values))
        overall_avg = sum(values) / len(values)

        trend = "stable"
        if avg_change > 1:
            trend = "improving"
        elif avg_change < -1:
            trend = "degrading"

        predictions = []
        if len(values) >= 5:
            import statistics

            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            predictions = [
                {"period": "next_run", "predicted": round(values[-1] + avg_change, 2)},
                {
                    "period": "next_week",
                    "predicted": round(values[-1] + (avg_change * 7), 2),
                },
            ]

        return {
            "metric": metric,
            "current_value": values[-1],
            "recent_average": round(recent_avg, 2),
            "overall_average": round(overall_avg, 2),
            "trend": trend,
            "avg_change_per_run": round(avg_change, 2),
            "data_points": len(values),
            "predictions": predictions,
            "history": values,
            "timestamp": datetime.now().isoformat(),
        }

    async def generate_html_report(
        self,
        test_results: dict[str, Any],
        analysis: dict[str, Any],
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a comprehensive HTML report.

        Args:
            test_results: Test results dictionary
            analysis: Analysis results
            output_path: Optional output path for the report

        Returns:
            Report generation results with file path
        """
        metrics = analysis.get("metrics", {})
        status_color = {
            "healthy": "#28a745",
            "warning": "#ffc107",
            "critical": "#dc3545",
        }.get(metrics.get("status", "unknown"), "#6c757d")

        failures = test_results.get("failures", [])
        passed = test_results.get("passed", [])

        failure_rows = ""
        for failure in failures[:20]:
            failure_rows += f"""
            <tr>
                <td>{failure.get("name", "Unknown")}</td>
                <td>{failure.get("error", "Unknown error")[:100]}</td>
                <td>{failure.get("file", "Unknown")}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
        .header {{ background: {status_color}; color: white; padding: 20px; }}
        .header h1 {{ margin: 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: #e0e0e0; }}
        .metric {{ text-align: center; padding: 20px; background: white; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: {status_color}; }}
        .metric-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; margin-top: 5px; }}
        .section {{ padding: 20px; }}
        .section h2 {{ margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .status-pass {{ color: #28a745; }}
        .status-fail {{ color: #dc3545; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
        .badge-pass {{ background: #d4edda; color: #155724; }}
        .badge-fail {{ background: #f8d7da; color: #721c24; }}
        .trend-improving {{ color: #28a745; }}
        .trend-degrading {{ color: #dc3545; }}
        .trend-stable {{ color: #6c757d; }}
        .footer {{ text-align: center; color: #6c757d; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>Test Execution Report</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{metrics.get("total", 0)}</div>
                    <div class="metric-label">Total Tests</div>
                </div>
                <div class="metric">
                    <div class="metric-value status-pass">{metrics.get("passed", 0)}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value status-fail">{metrics.get("failed", 0)}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get("skipped", 0)}</div>
                    <div class="metric-label">Skipped</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get("pass_rate", 0)}%</div>
                    <div class="metric-label">Pass Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get("duration", 0)}s</div>
                    <div class="metric-label">Duration</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section">
                <h2>Analysis</h2>
                <p>{analysis.get("analysis", "No analysis available")}</p>
            </div>
        </div>

        <div class="card">
            <div class="section">
                <h2>Failed Tests ({len(failures)})</h2>
                {f"<table><tr><th>Test Name</th><th>Error</th><th>File</th></tr>{failure_rows}</table>" if failure_rows else "<p>No failures!</p>"}
            </div>
        </div>

        <div class="footer">
            <p>Claude Playwright Framework - Test Report</p>
        </div>
    </div>
</body>
</html>"""

        output = output_path or f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        with open(output, "w", encoding="utf-8") as f:
            f.write(html)

        return {
            "report_path": output,
            "report_size": len(html),
            "timestamp": datetime.now().isoformat(),
        }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "analyze_results")

        if action == "analyze_results":
            return await self.analyze_results(results_path=input_data["results_path"])
        elif action == "cluster_failures":
            return await self.cluster_failures(test_results=input_data["test_results"])
        elif action == "generate_executive_summary":
            return await self.generate_executive_summary(
                analysis=input_data["analysis"],
                format=input_data.get("format", "markdown"),
            )
        elif action == "generate_html_report":
            return await self.generate_html_report(
                test_results=input_data["test_results"],
                analysis=input_data["analysis"],
                output_path=input_data.get("output_path"),
            )
        elif action == "detect_flaky_tests":
            return await self.detect_flaky_tests(
                test_results=input_data["test_results"],
                history_depth=input_data.get("history_depth", 5),
            )
        elif action == "analyze_trends":
            return await self.analyze_trends(
                test_results=input_data["test_results"],
                metric=input_data.get("metric", "pass_rate"),
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
