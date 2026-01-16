"""
HTML Report Generator for Test Results

Generates comprehensive HTML reports with:
- Test execution summary
- Pass/fail statistics
- Screenshot attachments
- Timeline visualization
- Error details and stack traces
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import base64


class ReportGenerator:
    """Generate HTML reports from test execution results."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.templates_dir = self.output_dir / "templates"
        self.reports_dir = self.output_dir / "latest"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Generate HTML report from test results.

        Args:
            test_results: List of test result dictionaries
            metadata: Optional metadata (timestamp, environment, etc.)

        Returns:
            Path to generated HTML report
        """
        # Calculate statistics
        stats = self._calculate_statistics(test_results)

        # Generate report data
        report_data = {
            "metadata": metadata or self._get_default_metadata(),
            "statistics": stats,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }

        # Generate HTML
        html_content = self._generate_html(report_data)

        # Write report
        report_path = self.reports_dir / "index.html"
        report_path.write_text(html_content, encoding='utf-8')

        # Also save JSON data for API access
        json_path = self.reports_dir / "results.json"
        json_path.write_text(json.dumps(report_data, indent=2), encoding='utf-8')

        return str(report_path)

    def _calculate_statistics(self, test_results: List[Dict]) -> Dict[str, Any]:
        """Calculate test statistics."""
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        failed = sum(1 for r in test_results if r.get("status") == "failed")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")

        # Calculate duration
        total_duration = sum(r.get("duration", 0) for r in test_results)

        # Group by feature
        features = {}
        for result in test_results:
            feature = result.get("feature", "Unknown")
            if feature not in features:
                features[feature] = {"total": 0, "passed": 0, "failed": 0}
            features[feature]["total"] += 1
            if result.get("status") == "passed":
                features[feature]["passed"] += 1
            elif result.get("status") == "failed":
                features[feature]["failed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round((passed / total * 100) if total > 0 else 0, 2),
            "total_duration": round(total_duration, 2),
            "features": features
        }

    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for report."""
        return {
            "framework": "AI Playwright Agent",
            "version": "1.0.0",
            "environment": "test",
            "generated_at": datetime.now().isoformat()
        }

    def _generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content from report data."""
        stats = report_data["statistics"]
        metadata = report_data["metadata"]
        results = report_data["test_results"]

        # Generate CSS styles
        styles = self._get_css_styles()

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {metadata.get('framework', 'Test Report')}</title>
    <style>{styles}</style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Test Execution Report</h1>
            <div class="metadata">
                <span>Framework: {metadata.get('framework', 'N/A')}</span>
                <span>Generated: {report_data['timestamp']}</span>
                <span>Environment: {metadata.get('environment', 'N/A')}</span>
            </div>
        </header>

        <section class="summary">
            <h2>Summary</h2>
            <div class="stats-grid">
                <div class="stat-card total">
                    <div class="stat-value">{stats['total']}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat-card passed">
                    <div class="stat-value">{stats['passed']}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-card failed">
                    <div class="stat-value">{stats['failed']}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card rate">
                    <div class="stat-value">{stats['pass_rate']}%</div>
                    <div class="stat-label">Pass Rate</div>
                </div>
            </div>
        </section>

        <section class="charts">
            <h2>Test Results Chart</h2>
            <div class="chart-container">
                <canvas id="resultsChart"></canvas>
            </div>
        </section>

        <section class="features">
            <h2>Results by Feature</h2>
            <table class="features-table">
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Total</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_features_table(stats['features'])}
                </tbody>
            </table>
        </section>

        <section class="test-results">
            <h2>Test Results</h2>
            <div class="filter-bar">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="passed">Passed</button>
                <button class="filter-btn" data-filter="failed">Failed</button>
            </div>
            {self._generate_test_results_html(results)}
        </section>
    </div>

    <script>
        // Chart.js configuration
        const ctx = document.getElementById('resultsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{stats['passed']}, {stats['failed']}, {stats['skipped']}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});

        // Filter functionality
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const filter = this.dataset.filter;
                document.querySelectorAll('.test-result').forEach(test => {{
                    if (filter === 'all' || test.dataset.status === filter) {{
                        test.style.display = 'block';
                    }} else {{
                        test.style.display = 'none';
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>
"""
        return html

    def _generate_features_table(self, features: Dict[str, Dict]) -> str:
        """Generate HTML table rows for features."""
        rows = []
        for feature_name, feature_stats in features.items():
            total = feature_stats["total"]
            passed = feature_stats["passed"]
            failed = feature_stats["failed"]
            pass_rate = round((passed / total * 100) if total > 0 else 0, 1)

            rows.append(f"""
                <tr>
                    <td>{feature_name}</td>
                    <td>{total}</td>
                    <td>{passed}</td>
                    <td>{failed}</td>
                    <td>{pass_rate}%</td>
                </tr>
            """)
        return "\n".join(rows)

    def _generate_test_results_html(self, results: List[Dict]) -> str:
        """Generate HTML for test results list."""
        items = []
        for idx, result in enumerate(results):
            status = result.get("status", "unknown")
            status_class = "passed" if status == "passed" else "failed"

            items.append(f"""
                <div class="test-result {status_class}" data-status="{status}">
                    <div class="result-header">
                        <span class="result-name">{result.get('name', 'Unknown Test')}</span>
                        <span class="result-status">{status.upper()}</span>
                    </div>
                    <div class="result-details">
                        <p><strong>Feature:</strong> {result.get('feature', 'Unknown')}</p>
                        <p><strong>Duration:</strong> {result.get('duration', 0):.2f}s</p>
                        {self._generate_error_html(result)}
                        {self._generate_screenshot_html(result)}
                    </div>
                </div>
            """)
        return "\n".join(items)

    def _generate_error_html(self, result: Dict) -> str:
        """Generate HTML for error details if test failed."""
        if result.get("status") != "failed":
            return ""

        error = result.get("error", {})
        return f"""
            <div class="error-section">
                <p><strong>Error:</strong> {error.get('message', 'Unknown error')}</p>
                <details>
                    <summary>Stack Trace</summary>
                    <pre>{error.get('traceback', 'No traceback available')}</pre>
                </details>
            </div>
        """

    def _generate_screenshot_html(self, result: Dict) -> str:
        """Generate HTML for screenshot if available."""
        screenshot_path = result.get("screenshot")
        if not screenshot_path or not os.path.exists(screenshot_path):
            return ""

        # Convert screenshot to base64
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode()

        return f"""
            <div class="screenshot-section">
                <p><strong>Screenshot:</strong></p>
                <a href="data:image/png;base64,{screenshot_data}" download="screenshot.png">
                    <img src="data:image/png;base64,{screenshot_data}" alt="Test Screenshot" style="max-width: 100%; height: auto;">
                </a>
            </div>
        """

    def _get_css_styles(self) -> str:
        """Get CSS styles for the report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }

        header h1 {
            margin-bottom: 10px;
        }

        .metadata {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            opacity: 0.9;
        }

        section {
            padding: 30px;
            border-bottom: 1px solid #e0e0e0;
        }

        section h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-card.total { border-left: 4px solid #007bff; }
        .stat-card.passed { border-left: 4px solid #28a745; }
        .stat-card.failed { border-left: 4px solid #dc3545; }
        .stat-card.rate { border-left: 4px solid #ffc107; }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
        }

        .chart-container {
            max-width: 400px;
            margin: 0 auto;
        }

        .features-table {
            width: 100%;
            border-collapse: collapse;
        }

        .features-table th,
        .features-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .features-table th {
            background: #f8f9fa;
            font-weight: 600;
        }

        .filter-bar {
            margin-bottom: 20px;
        }

        .filter-btn {
            padding: 8px 16px;
            margin-right: 10px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }

        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .test-result {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .test-result.passed {
            border-left: 4px solid #28a745;
        }

        .test-result.failed {
            border-left: 4px solid #dc3545;
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .result-name {
            font-weight: 600;
        }

        .result-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .test-result.passed .result-status {
            background: #d4edda;
            color: #155724;
        }

        .test-result.failed .result-status {
            background: #f8d7da;
            color: #721c24;
        }

        .result-details p {
            margin: 5px 0;
        }

        .error-section {
            margin-top: 10px;
            padding: 10px;
            background: #f8d7da;
            border-radius: 4px;
        }

        .error-section pre {
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            overflow-x: auto;
        }

        .screenshot-section {
            margin-top: 10px;
        }
        """
