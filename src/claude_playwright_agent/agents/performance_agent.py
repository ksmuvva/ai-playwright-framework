"""
Performance Testing Agent.

Provides performance testing capabilities:
- Load time measurement
- Resource monitoring
- Performance profiling
- Bottleneck identification
- Load testing with multiple virtual users
- Network request analysis
- Resource profiling
"""

import asyncio
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from playwright.async_api import Page, Browser, BrowserContext

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
    image_bytes: int = 0
    script_count: int = 0
    stylesheet_count: int = 0
    image_count: int = 0
    font_count: int = 0
    network_requests: int = 0
    cache_hit_ratio: float = 0


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
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    min_response_time_ms: float = 0
    max_response_time_ms: float = 0


@dataclass
class ResourceProfile:
    """Resource profiling results."""

    total_size_bytes: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_domain: dict[str, int] = field(default_factory=dict)
    large_resources: list[dict] = field(default_factory=list)
    slow_requests: list[dict] = field(default_factory=list)


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
            timing = await page.evaluate("() => performance.timing.toJSON()")

            if timing:
                if timing.get("loadEventEnd") and timing.get("navigationStart"):
                    metrics.page_load_time_ms = timing["loadEventEnd"] - timing["navigationStart"]

                if timing.get("domContentLoadedEventEnd") and timing.get("navigationStart"):
                    metrics.dom_content_loaded_ms = (
                        timing["domContentLoadedEventEnd"] - timing["navigationStart"]
                    )

            # Get Paint timing
            paint_timing = await page.evaluate("""() => {
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
            resources = await page.evaluate("""() => {
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

    async def run_load_test(
        self,
        browser: Browser,
        url: str,
        virtual_users: int = 10,
        duration_seconds: int = 60,
        spawn_rate: int = 2,
    ) -> dict[str, Any]:
        """
        Run a load test with multiple virtual users.

        Args:
            browser: Playwright browser instance
            url: URL to test
            virtual_users: Number of virtual users
            duration_seconds: Test duration in seconds
            spawn_rate: Users spawned per second

        Returns:
            Load test results
        """
        results: dict[str, Any] = {
            "virtual_users": virtual_users,
            "duration_seconds": duration_seconds,
            "url": url,
        }

        response_times: list[float] = []
        errors: list[str] = []
        requests_count = 0
        successful_requests = 0

        async def user_session(context: BrowserContext) -> None:
            """Run a single user session."""
            page = await context.new_page()
            try:
                start = time.time()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                elapsed = (time.time() - start) * 1000

                nonlocal requests_count, successful_requests
                requests_count += 1
                response_times.append(elapsed)

                if response and response.status < 400:
                    successful_requests += 1
                else:
                    errors.append(f"Status: {response.status if response else 'No response'}")

            except Exception as e:
                errors.append(str(e))
                response_times.append(30000)
            finally:
                await page.close()

        async def run_test() -> None:
            """Execute the load test."""
            nonlocal requests_count, successful_requests

            contexts: list[BrowserContext] = []
            users_started = 0

            while users_started < virtual_users:
                context = await browser.new_context()
                contexts.append(context)
                asyncio.create_task(user_session(context))
                users_started += 1
                await asyncio.sleep(1 / spawn_rate)

            await asyncio.sleep(duration_seconds)

            for context in contexts:
                await context.close()

        start_time = time.time()
        await run_test()
        total_time = time.time() - start_time

        response_times.sort()
        n = len(response_times)

        if n == 0:
            return {
                "success": False,
                "error": "No requests completed",
                **results,
            }

        avg_time = sum(response_times) / n
        min_time = response_times[0]
        max_time = response_times[-1]
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        result = LoadTestResult(
            virtual_users=virtual_users,
            requests_per_second=requests_count / total_time if total_time > 0 else 0,
            average_response_time_ms=avg_time,
            p95_response_time_ms=response_times[p95_idx] if n > p95_idx else avg_time,
            p99_response_time_ms=response_times[p99_idx] if n > p99_idx else avg_time,
            error_rate=(len(errors) / requests_count * 100) if requests_count > 0 else 0,
            throughput=successful_requests / total_time if total_time > 0 else 0,
            total_requests=requests_count,
            successful_requests=successful_requests,
            failed_requests=len(errors),
            min_response_time_ms=min_time,
            max_response_time_ms=max_time,
        )

        return {
            "success": result.error_rate < 5,
            "load_test": {
                "virtual_users": result.virtual_users,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "requests_per_second": round(result.requests_per_second, 2),
                "average_response_time_ms": round(result.average_response_time_ms, 2),
                "min_response_time_ms": round(result.min_response_time_ms, 2),
                "max_response_time_ms": round(result.max_response_time_ms, 2),
                "p95_response_time_ms": round(result.p95_response_time_ms, 2),
                "p99_response_time_ms": round(result.p99_response_time_ms, 2),
                "error_rate": round(result.error_rate, 2),
                "throughput": round(result.throughput, 2),
                "duration_seconds": round(total_time, 2),
            },
            "status": "passed" if result.error_rate < 5 else "failed",
            "errors": errors[:10],
            **results,
        }

    async def profile_resources(self, page: Page) -> dict[str, Any]:
        """
        Profile page resources in detail.

        Args:
            page: Playwright page object

        Returns:
            Detailed resource profile
        """
        profile = ResourceProfile()

        resource_data = await page.evaluate("""() => {
            const entries = performance.getEntriesByType('resource');
            const byType = {};
            const byDomain = {};
            const largeResources = [];
            const slowRequests = [];

            entries.forEach(entry => {
                const size = entry.transferSize || 0;
                const duration = entry.duration || 0;

                const type = entry.name.split('.').pop().split('?')[0].toLowerCase() || 'other';
                byType[type] = (byType[type] || 0) + size;

                try {
                    const domain = new URL(entry.name).hostname;
                    byDomain[domain] = (byDomain[domain] || 0) + size;
                } catch (e) {
                    byDomain['local'] = (byDomain['local'] || 0) + size;
                }

                if (size > 500 * 1024) {
                    largeResources.push({
                        url: entry.name.substring(0, 100),
                        size_kb: (size / 1024).toFixed(2),
                        type: type,
                    });
                }

                if (duration > 1000) {
                    slowRequests.push({
                        url: entry.name.substring(0, 100),
                        duration_ms: duration.toFixed(2),
                        type: type,
                    });
                }
            });

            return {
                totalSize: entries.reduce((sum, e) => sum + (e.transferSize || 0), 0),
                byType,
                byDomain,
                largeResources: largeResources.slice(0, 10),
                slowRequests: slowRequests.slice(0, 10),
                count: entries.length,
            };
        }""")

        profile.total_size_bytes = resource_data.get("totalSize", 0)
        profile.by_type = resource_data.get("byType", {})
        profile.by_domain = resource_data.get("byDomain", {})
        profile.large_resources = resource_data.get("largeResources", [])
        profile.slow_requests = resource_data.get("slowRequests", [])

        return {
            "total_size_mb": round(profile.total_size_bytes / (1024 * 1024), 2),
            "resource_count": resource_data.get("count", 0),
            "by_type": {k: round(v / 1024, 2) for k, v in profile.by_type.items()},
            "by_domain": {k: round(v / 1024, 2) for k, v in profile.by_domain.items()},
            "large_resources": profile.large_resources,
            "slow_requests": profile.slow_requests,
            "recommendations": self._get_resource_recommendations(profile),
        }

    def _get_resource_recommendations(self, profile: ResourceProfile) -> list[str]:
        """Generate resource optimization recommendations."""
        recommendations = []

        if profile.total_size_bytes > 2 * 1024 * 1024:
            recommendations.append("Total page size exceeds 2MB - consider optimizing")

        for resource_type, size in profile.by_type.items():
            if resource_type in ["js", "javascript"] and size > 500 * 1024:
                recommendations.append(
                    f"JavaScript ({size / 1024:.0f}KB) - Consider code splitting"
                )
            elif resource_type in ["css", "stylesheet"] and size > 100 * 1024:
                recommendations.append(
                    f"CSS ({size / 1024:.0f}KB) - Consider critical CSS extraction"
                )

        for resource in profile.large_resources[:3]:
            recommendations.append(
                f"Large resource: {resource['url'][:50]}... ({resource['size_kb']}KB)"
            )

        for request in profile.slow_requests[:3]:
            recommendations.append(
                f"Slow request: {request['url'][:50]}... ({request['duration_ms']}ms)"
            )

        if not recommendations:
            recommendations.append("Resource profile looks good!")

        return recommendations

    async def analyze_network_waterfall(self, page: Page, url: str) -> dict[str, Any]:
        """
        Analyze network request waterfall.

        Args:
            page: Playwright page object
            url: URL to analyze

        Returns:
            Waterfall analysis with timing breakdown
        """
        await page.goto(url, wait_until="networkidle")

        waterfall_data = await page.evaluate("""() => {
            const entries = performance.getEntriesByType('resource')
                .sort((a, b) => a.startTime - b.startTime);

            const firstPaint = performance.getEntriesByType('paint')
                .find(e => e.name === 'first-contentful-paint')?.startTime || 0;

            let totalBlockingTime = 0;
            let lastEndTime = 0;

            const requests = entries.map(entry => {
                const start = entry.startTime;
                const duration = entry.duration;
                const end = start + duration;

                const ttfb = entry.responseStart - entry.requestStart;
                const download = entry.responseEnd - entry.responseStart;

                if (start < lastEndTime) {
                    totalBlockingTime += lastEndTime - start;
                }
                lastEndTime = end;

                return {
                    url: entry.name.substring(0, 80),
                    start_ms: start.toFixed(2),
                    duration_ms: duration.toFixed(2),
                    ttfb_ms: ttfb.toFixed(2),
                    download_ms: download.toFixed(2),
                    size_kb: ((entry.transferSize || 0) / 1024).toFixed(2),
                };
            });

            return {
                requests: requests,
                first_paint_ms: firstPaint.toFixed(2),
                total_requests: entries.length,
                total_duration_ms: (lastEndTime - entries[0]?.startTime || 0).toFixed(2),
                total_blocking_time_ms: totalBlockingTime.toFixed(2),
            };
        }""")

        return {
            "url": url,
            "waterfall": waterfall_data["requests"],
            "first_paint_ms": waterfall_data["first_paint_ms"],
            "total_requests": waterfall_data["total_requests"],
            "total_duration_ms": waterfall_data["total_duration_ms"],
            "total_blocking_time_ms": waterfall_data["total_blocking_time_ms"],
            "bottlenecks": self._identify_waterfall_bottlenecks(waterfall_data),
        }

    def _identify_waterfall_bottlenecks(self, waterfall_data: dict) -> list[dict]:
        """Identify bottlenecks in waterfall data."""
        bottlenecks = []

        requests = waterfall_data.get("requests", [])

        for i, req in enumerate(requests):
            ttfb = float(req.get("ttfb_ms", 0))
            if ttfb > 1000:
                bottlenecks.append(
                    {
                        "url": req["url"],
                        "issue": "High Time to First Byte",
                        "impact_ms": ttfb,
                        "recommendation": "Check server response time or CDN configuration",
                    }
                )

            download = float(req.get("download_ms", 0))
            size = float(req.get("size_kb", 0))
            if download > 500 and size > 500:
                bottlenecks.append(
                    {
                        "url": req["url"],
                        "issue": "Slow resource download",
                        "impact_ms": download,
                        "size_kb": size,
                        "recommendation": "Compress or lazy-load this resource",
                    }
                )

        return bottlenecks[:5]
