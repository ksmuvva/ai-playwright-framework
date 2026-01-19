"""
Performance Testing Agent.

Provides performance testing capabilities:
- Load time measurement
- Resource monitoring
- Performance profiling
- Bottleneck identification
"""

import time
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from playwright.async_api import Page, Browser

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""

    page_load_time_ms: float = 0
    dom_content_loaded_ms: float = 0
    first_contentful_paint_ms: float = 0
    largest_contentful_paint_ms: float = 0
    time_to_interactive_ms: float = 0
    total_bytes: int = 0
    resource_count: int = 0
    js_heap_size: int = 0
    css_heap_size: int = 0


@dataclass
class LoadTestResult:
    """Load test results."""

    virtual_users: int
    requests_per_second: float
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    throughput: float


class PerformanceAgent(BaseAgent):
    """
    Agent for performance testing operations.

    Handles:
    - Page load time measurement
    - Resource monitoring
    - Load testing
    - Performance profiling
    - Bottleneck identification
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        """
        Initialize the performance agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()

        system_prompt = """You are the Performance Testing Agent for Claude Playwright Agent.

Your role is to:
1. Measure page load performance metrics
2. Monitor resource utilization
3. Identify performance bottlenecks
4. Generate load test scenarios
5. Analyze and report performance data

You provide:
- Detailed performance metrics
- Bottleneck identification
- Optimization recommendations
- Performance trend analysis
"""
        super().__init__(system_prompt=system_prompt)

    async def measure_page_performance(
        self,
        page: Page,
        url: str,
    ) -> dict[str, Any]:
        """
        Measure performance metrics for a page.

        Args:
            page: Playwright page object
            url: URL to measure

        Returns:
            Performance metrics
        """
        metrics = PerformanceMetrics()

        try:
            # Navigate and measure
            start_time = time.time()

            await page.goto(url, wait_until="domcontentloaded")

            metrics.dom_content_loaded_ms = (time.time() - start_time) * 1000

            # Get performance timing
            timing = page.evaluate("() => performance.timing.toJSON()")

            if timing:
                if timing.get("loadEventEnd") and timing.get("navigationStart"):
                    metrics.page_load_time_ms = timing["loadEventEnd"] - timing["navigationStart"]

                if timing.get("domContentLoadedEventEnd") and timing.get("navigationStart"):
                    metrics.dom_content_loaded_ms = (
                        timing["domContentLoadedEventEnd"] - timing["navigationStart"]
                    )

            # Get Paint timing
            paint_timing = page.evaluate("""() => {
                const timing = performance.getEntriesByType('paint');
                const result = {};
                timing.forEach(entry => {
                    result[entry.name] = entry.startTime;
                });
                return result;
            }""")

            if paint_timing:
                metrics.first_contentful_paint_ms = paint_timing.get("first-contentful-paint", 0)

            # Get resource information
            resources = page.evaluate("""() => {
                const entries = performance.getEntriesByType('resource');
                let totalBytes = 0;
                const types = {js: 0, css: 0, img: 0, other: 0};

                entries.forEach(entry => {
                    totalBytes += entry.transferSize || 0;

                    if (entry.name.includes('.js')) types.js += entry.transferSize || 0;
                    else if (entry.name.includes('.css')) types.css += entry.transferSize || 0;
                    else if (entry.name.match(/\\.(jpg|jpeg|png|gif|svg|webp)/)) types.img += entry.transferSize || 0;
                    else types.other += entry.transferSize || 0;
                });

                return {
                    count: entries.length,
                    totalBytes,
                    types
                };
            }""")

            if resources:
                metrics.resource_count = resources["count"]
                metrics.total_bytes = resources["totalBytes"]
                metrics.js_heap_size = resources["types"]["js"]
                metrics.css_heap_size = resources["types"]["css"]

            # Calculate Time to Interactive
            metrics.time_to_interactive_ms = await self._measure_tti(page)

            return {
                "success": True,
                "url": url,
                "metrics": {
                    "page_load_time_ms": metrics.page_load_time_ms,
                    "dom_content_loaded_ms": metrics.dom_content_loaded_ms,
                    "first_contentful_paint_ms": metrics.first_contentful_paint_ms,
                    "largest_contentful_paint_ms": metrics.largest_contentful_paint_ms,
                    "time_to_interactive_ms": metrics.time_to_interactive_ms,
                    "total_bytes": metrics.total_bytes,
                    "resource_count": metrics.resource_count,
                    "js_heap_size": metrics.js_heap_size,
                    "css_heap_size": metrics.css_heap_size,
                },
                "score": self._calculate_performance_score(metrics),
                "recommendations": self._get_optimization_recommendations(metrics),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Performance measurement failed: {e}",
            }

    async def _measure_tti(self, page: Page) -> float:
        """Measure Time to Interactive."""
        try:
            start_measure = time.time()

            await page.wait_for_function(
                """
                () => {
                    return window.performance.getEntriesByType('resource').length > 0 &&
                           document.readyState === 'complete' &&
                           typeof window.__tti === 'object';
                }
            """,
                timeout=10000,
            )

            return (time.time() - start_measure) * 1000

        except Exception:
            return 0

    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> dict[str, Any]:
        """Calculate overall performance score."""
        score = 100

        # Deduct for slow load times
        if metrics.page_load_time_ms > 3000:
            score -= 20
        elif metrics.page_load_time_ms > 2000:
            score -= 10

        if metrics.first_contentful_paint_ms > 1800:
            score -= 15

        if metrics.time_to_interactive_ms > 4000:
            score -= 15

        # Deduct for large resources
        if metrics.total_bytes > 2 * 1024 * 1024:  # 2MB
            score -= 20
        elif metrics.total_bytes > 1 * 1024 * 1024:  # 1MB
            score -= 10

        return {
            "overall": max(0, min(100, score)),
            "grade": self._get_grade(max(0, min(100, score))),
            "details": {
                "load_performance": self._rate_metric(metrics.page_load_time_ms, 2000, 3000),
                "render_performance": self._rate_metric(
                    metrics.first_contentful_paint_ms, 1000, 1800
                ),
                "resource_efficiency": self._rate_resource(metrics.total_bytes),
            },
        }

    def _rate_metric(self, value: float, good: float, poor: float) -> str:
        """Rate a metric as good, average, or poor."""
        if value <= good:
            return "good"
        elif value <= poor:
            return "average"
        else:
            return "poor"

    def _rate_resource(self, bytes: int) -> str:
        """Rate resource size."""
        if bytes < 500 * 1024:  # 500KB
            return "good"
        elif bytes < 1 * 1024 * 1024:  # 1MB
            return "average"
        else:
            return "poor"

    def _get_grade(self, score: int) -> str:
        """Get letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _get_optimization_recommendations(self, metrics: PerformanceMetrics) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if metrics.page_load_time_ms > 3000:
            recommendations.append("Consider optimizing server response time")

        if metrics.first_contentful_paint_ms > 1800:
            recommendations.append("Optimize Critical Rendering Path")
            recommendations.append("Inline critical CSS")
            recommendations.append("Defer non-critical JavaScript")

        if metrics.total_bytes > 2 * 1024 * 1024:
            recommendations.append("Compress and optimize images")
            recommendations.append("Implement lazy loading")
            recommendations.append("Consider code splitting for JavaScript")

        if metrics.js_heap_size > 500 * 1024:
            recommendations.append("Reduce JavaScript bundle size")
            recommendations.append("Remove unused code")

        if metrics.css_heap_size > 100 * 1024:
            recommendations.append("Optimize CSS delivery")

        if not recommendations:
            recommendations.append("Performance is excellent! No optimizations needed.")

        return recommendations

    async def analyze_test_performance(
        self, test_name: str, execution_time_ms: float
    ) -> dict[str, Any]:
        """Analyze the performance of a test execution."""
        baseline = await self._get_baseline_performance(test_name)

        return {
            "test_name": test_name,
            "execution_time_ms": execution_time_ms,
            "baseline_ms": baseline.get("average_ms", 0),
            "variance_percent": (
                (execution_time_ms - baseline.get("average_ms", 0))
                / baseline.get("average_ms", 1)
                * 100
            )
            if baseline.get("average_ms")
            else 0,
            "status": self._get_performance_status(execution_time_ms, baseline),
            "recommendations": await self._generate_performance_recommendations(
                test_name, execution_time_ms, baseline
            ),
        }

    async def _get_baseline_performance(self, test_name: str) -> dict:
        """Get baseline performance for a test."""
        baseline = await self.recall(f"performance_baseline_{test_name}")
        return baseline or {"average_ms": 0, "samples": 0}

    def _get_performance_status(self, execution_time_ms: float, baseline: dict) -> str:
        """Determine performance status."""
        if baseline.get("average_ms", 0) == 0:
            return "baseline_needed"

        variance = (execution_time_ms - baseline["average_ms"]) / baseline["average_ms"]

        if variance > 0.5:
            return "regression"
        elif variance > 0.2:
            return "degraded"
        elif variance < -0.2:
            return "improved"
        else:
            return "stable"

    async def _generate_performance_recommendations(
        self,
        test_name: str,
        execution_time_ms: float,
        baseline: dict,
    ) -> list[str]:
        """Generate performance recommendations."""
        recommendations = []

        if baseline.get("average_ms", 0) == 0:
            recommendations.append("Run test multiple times to establish baseline")
            return recommendations

        if execution_time_ms > baseline["average_ms"] * 1.5:
            recommendations.append("Execution time increased significantly")
            recommendations.append("Review recent changes to application or test")
            recommendations.append("Check for resource contention")

        if execution_time_ms < baseline["average_ms"] * 0.8:
            recommendations.append("Execution time improved - consider updating baseline")

        return recommendations

    async def store_baseline(self, test_name: str, execution_time_ms: float) -> None:
        """Store test execution as baseline."""
        baseline = await self._get_baseline_performance(test_name)

        samples = baseline.get("samples", 0)
        current_avg = baseline.get("average_ms", 0)

        new_avg = ((current_avg * samples) + execution_time_ms) / (samples + 1)

        await self.remember(
            key=f"performance_baseline_{test_name}",
            value={
                "average_ms": new_avg,
                "samples": samples + 1,
                "last_updated": time.time(),
            },
            memory_type="long_term",
            priority="low",
            tags=["performance", "baseline", test_name],
        )
