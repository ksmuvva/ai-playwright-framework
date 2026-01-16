"""
Visual Regression Skill for Claude Playwright Agent.

This skill provides visual regression testing capabilities:
- Screenshot capture during tests
- Baseline comparison
- Diff generation
- Visual reports
"""

import json
from pathlib import Path
from typing import Any

from claude_playwright_agent.visual_regression import (
    VisualRegressionEngine,
    ScreenshotCapture,
    ScreenshotConfig,
    ComparisonStatus,
)


class VisualRegressionSkill:
    """
    Skill for visual regression testing.

    This skill integrates with the test framework to:
    1. Capture screenshots at key points
    2. Compare with baselines
    3. Generate diff images
    4. Produce visual reports
    """

    name = "visual_regression"
    version = "1.0.0"
    description = "Visual regression testing with screenshot comparison"
    author = "Claude Playwright Agent"
    enabled = True

    def __init__(
        self,
        baseline_dir: Path,
        output_dir: Path,
        threshold: float = 0.1,
    ):
        """
        Initialize the visual regression skill.

        Args:
            baseline_dir: Directory for baseline images
            output_dir: Directory for output images
            threshold: Similarity threshold (0.0 to 1.0)
        """
        self.engine = VisualRegressionEngine(
            baseline_dir=baseline_dir,
            output_dir=output_dir,
            threshold=threshold,
        )
        self.results: list[Any] = []

    def capture_screenshot(
        self,
        page,
        name: str,
        config: ScreenshotConfig | None = None,
    ) -> Path:
        """
        Capture a screenshot.

        Args:
            page: Playwright Page object
            name: Screenshot name
            config: Screenshot configuration

        Returns:
            Path to captured screenshot
        """
        if config is None:
            config = ScreenshotConfig()

        return ScreenshotCapture.capture(
            page=page,
            name=name,
            output_dir=self.engine.output_dir / "current",
            config=config,
        )

    def compare(
        self,
        name: str,
        update_baseline: bool = False,
    ) -> Any:
        """
        Compare screenshot with baseline.

        Args:
            name: Screenshot name
            update_baseline: Update baseline with current

        Returns:
            ComparisonResult
        """
        current_path = self.engine.get_current_path(name)
        result = self.engine.compare(current_path, name, update_baseline)
        self.results.append(result)
        return result

    def assert_visual(
        self,
        page,
        name: str,
        update_baseline: bool = False,
    ) -> None:
        """
        Capture and compare screenshot, raise assertion if different.

        Args:
            page: Playwright Page object
            name: Test name
            update_baseline: Update baseline with current

        Raises:
            AssertionError: If comparison fails
        """
        # Capture screenshot
        self.capture_screenshot(page, name)

        # Compare with baseline
        result = self.compare(name, update_baseline)

        # Assert if different
        if result.status == ComparisonStatus.DIFFERENT:
            raise AssertionError(
                f"Visual regression detected for '{name}':\n"
                f"  Similarity: {result.similarity_score:.2%}\n"
                f"  Diff pixels: {result.diff_pixels:,} / {result.total_pixels:,}\n"
                f"  Diff image: {result.diff_path}"
            )

    def generate_report(self, output_path: Path) -> None:
        """
        Generate visual regression report.

        Args:
            output_path: Path for report file
        """
        report = self.engine.generate_report(self.results)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save JSON report
        json_path = output_path.with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)

        # Generate HTML report
        html_path = output_path.with_suffix(".html")
        self._generate_html_report(report, html_path)

    def _generate_html_report(self, report: dict[str, Any], output_path: Path) -> None:
        """Generate HTML visual regression report."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary h1 {
            margin-top: 0;
            color: #333;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric {
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .metric.pass {
            background: #d4edda;
            color: #155724;
        }
        .metric.fail {
            background: #f8d7da;
            color: #721c24;
        }
        .metric.neutral {
            background: #e2e3e5;
            color: #383d41;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 14px;
            margin-top: 5px;
            opacity: 0.8;
        }
        .results {
            display: grid;
            gap: 15px;
        }
        .result {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .result.status-identical { border-left: 4px solid #28a745; }
        .result.status-similar { border-left: 4px solid #ffc107; }
        .result.status-different { border-left: 4px solid #dc3545; }
        .result.status-error { border-left: 4px solid #6c757d; }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .result-name {
            font-weight: bold;
            font-size: 16px;
        }
        .result-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-identical { background: #d4edda; color: #155724; }
        .status-similar { background: #fff3cd; color: #856404; }
        .status-different { background: #f8d7da; color: #721c24; }
        .status-error { background: #e2e3e5; color: #383d41; }

        .result-images {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .image-container {
            text-align: center;
        }
        .image-container label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .image-container img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .result-stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        .similarity-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .similarity-fill {
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="summary">
        <h1>📊 Visual Regression Report</h1>
        <div class="metrics">
"""

        summary = report["summary"]
        pass_rate = summary["pass_rate"]

        html += f"""
            <div class="metric {'pass' if pass_rate >= 80 else 'fail' if pass_rate < 50 else 'neutral'}">
                <div class="metric-value">{summary['total']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric pass">
                <div class="metric-value">{summary['identical']}</div>
                <div class="metric-label">Identical</div>
            </div>
            <div class="metric {'fail' if summary['different'] > 0 else 'neutral'}">
                <div class="metric-value">{summary['different']}</div>
                <div class="metric-label">Different</div>
            </div>
            <div class="metric {'pass' if pass_rate >= 80 else 'fail'}">
                <div class="metric-value">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
            <div class="metric neutral">
                <div class="metric-value">{summary['avg_similarity']:.1%}</div>
                <div class="metric-label">Avg Similarity</div>
            </div>
        </div>
    </div>

    <div class="results">
"""

        for i, result in enumerate(report["results"]):
            status = result["status"]
            name = f"Test {i + 1}"

            html += f"""
        <div class="result status-{status}">
            <div class="result-header">
                <span class="result-name">{name}</span>
                <span class="result-status status-{status}">{status.upper()}</span>
            </div>
            <div class="similarity-bar">
                <div class="similarity-fill" style="width: {result['similarity_score'] * 100}%"></div>
            </div>
            <div class="result-stats">
                <span>Similarity: {result['similarity_score']:.2%}</span>
                <span>Diff Pixels: {result['diff_pixels']:,} / {result['total_pixels']:,}</span>
            </div>
            <div class="result-images">
"""

            if result.get("baseline_path"):
                html += f"""
                <div class="image-container">
                    <label>Baseline</label>
                    <img src="{Path(result['baseline_path']).name}" alt="Baseline">
                </div>
"""

            if result.get("current_path"):
                html += f"""
                <div class="image-container">
                    <label>Current</label>
                    <img src="{Path(result['current_path']).name}" alt="Current">
                </div>
"""

            if result.get("diff_path"):
                html += f"""
                <div class="image-container">
                    <label>Diff</label>
                    <img src="{Path(result['diff_path']).name}" alt="Diff">
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

        output_path.write_text(html)


# Skill manifest for skill discovery
SKILL_MANIFEST = {
    "name": "visual_regression",
    "version": "1.0.0",
    "description": "Visual regression testing with screenshot comparison",
    "author": "Claude Playwright Agent",
    "enabled": True,
    "capabilities": [
        "capture_screenshot",
        "compare_baselines",
        "generate_diff",
        "visual_report",
    ],
    "dependencies": [
        "Pillow",
    ],
    "settings": {
        "baseline_dir": ".cpa/visual/baseline",
        "output_dir": ".cpa/visual/output",
        "threshold": 0.1,
    },
}


__all__ = [
    "VisualRegressionSkill",
    "SKILL_MANIFEST",
]
