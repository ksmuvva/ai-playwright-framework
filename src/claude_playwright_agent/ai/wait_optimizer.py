"""
Wait Optimizer Module (AI-Powered).

Analyzes wait times and optimizes wait strategies for better test performance.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


@dataclass
class WaitMetrics:
    """Metrics for a specific wait operation."""

    wait_type: str
    element_selector: str
    total_waits: int = 0
    successful_waits: int = 0
    failed_waits: int = 0
    wait_times_ms: List[float] = field(default_factory=list)
    timeouts: int = 0


@dataclass
class OptimizationRecommendation:
    """Recommendation for wait optimization."""

    selector: str
    current_timeout: int
    recommended_timeout: int
    reason: str
    expected_improvement: str
    priority: str


class WaitOptimizer:
    """
    AI-powered wait optimizer for intelligent wait management.

    Features:
    - Analyze wait times vs success rates
    - Identify optimal wait strategies per element
    - Detect loading patterns
    - Suggest explicit vs implicit waits
    - Reduce test flakiness
    """

    def __init__(self):
        """Initialize the wait optimizer."""
        self.wait_history: List[Dict[str, Any]] = []
        self.element_metrics: Dict[str, WaitMetrics] = {}
        self.learning_rate = 0.1

    def record_wait(
        self, selector: str, wait_type: str, duration_ms: float, success: bool, timeout_used: int
    ) -> None:
        """
        Record a wait operation for analysis.

        Args:
            selector: Element selector
            wait_type: Type of wait performed
            duration_ms: Duration of the wait in milliseconds
            success: Whether the wait was successful
            timeout_used: Timeout that was used
        """
        wait_id = f"{selector}:{wait_type}"

        if wait_id not in self.element_metrics:
            self.element_metrics[wait_id] = WaitMetrics(
                wait_type=wait_type, element_selector=selector
            )

        metrics = self.element_metrics[wait_id]
        metrics.total_waits += 1
        metrics.wait_times_ms.append(duration_ms)

        if success:
            metrics.successful_waits += 1
        else:
            metrics.failed_waits += 1
            if duration_ms >= timeout_used:
                metrics.timeouts += 1

        self.wait_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "selector": selector,
                "wait_type": wait_type,
                "duration_ms": duration_ms,
                "success": success,
                "timeout_used": timeout_used,
            }
        )

    def analyze_element_behavior(self, selector: str) -> Dict[str, Any]:
        """
        Analyze the loading behavior of a specific element.

        Args:
            selector: Element selector to analyze

        Returns:
            Dictionary with behavior analysis
        """
        matching_metrics = [
            m for m in self.element_metrics.values() if m.element_selector == selector
        ]

        if not matching_metrics:
            return {"status": "no_data", "message": "No wait data available for this element"}

        combined_waits = []
        for metrics in matching_metrics:
            combined_waits.extend(metrics.wait_times_ms)

        total_waits = sum(m.total_waits for m in matching_metrics)
        successful = sum(m.successful_waits for m in matching_metrics)
        timeouts = sum(m.timeouts for m in matching_metrics)

        success_rate = (successful / total_waits * 100) if total_waits > 0 else 0
        avg_time = statistics.mean(combined_waits) if combined_waits else 0
        p95_time = sorted(combined_waits)[int(len(combined_waits) * 0.95)] if combined_waits else 0

        return {
            "selector": selector,
            "total_waits": total_waits,
            "success_rate": f"{success_rate:.1f}%",
            "timeouts": timeouts,
            "average_wait_ms": f"{avg_time:.0f}",
            "p95_wait_ms": f"{p95_time:.0f}",
            "loading_pattern": self._determine_loading_pattern(combined_waits),
            "recommendation": self._get_recommendation(success_rate, avg_time, p95_time),
        }

    def _determine_loading_pattern(self, wait_times: List[float]) -> str:
        """Determine the loading pattern based on wait times."""
        if not wait_times:
            return "unknown"

        avg_time = statistics.mean(wait_times)
        std_dev = statistics.stdev(wait_times) if len(wait_times) > 1 else 0

        if avg_time < 500:
            return "fast_loading"
        elif avg_time < 2000:
            return "normal_loading"
        elif avg_time < 5000:
            return "slow_loading"
        else:
            return "very_slow_loading"

    def _get_recommendation(self, success_rate: float, avg_time: float, p95_time: float) -> str:
        """Get optimization recommendation based on metrics."""
        if success_rate < 80:
            return "Consider increasing timeout or investigating element stability"
        elif success_rate > 99 and avg_time < p95_time * 0.5:
            return "Timeout can be reduced for faster failure detection"
        elif avg_time > 5000:
            return "Element loads slowly - consider using polling or progressive waiting"
        else:
            return "Current settings are appropriate"

    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate wait optimization recommendations.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        for wait_id, metrics in self.element_metrics.items():
            if metrics.total_waits < 5:
                continue

            success_rate = metrics.successful_waits / metrics.total_waits
            avg_time = statistics.mean(metrics.wait_times_ms) if metrics.wait_times_ms else 0
            p95_time = (
                sorted(metrics.wait_times_ms)[int(len(metrics.wait_times_ms) * 0.95)]
                if metrics.wait_times_ms
                else 0
            )

            if success_rate < 0.9:
                recommended_timeout = int(p95_time * 1.5) + 1000
                recommendations.append(
                    OptimizationRecommendation(
                        selector=metrics.element_selector,
                        current_timeout=30000,
                        recommended_timeout=recommended_timeout,
                        reason=f"Low success rate ({success_rate * 100:.1f}%) - element may need more time",
                        expected_improvement="Improved reliability for slow-loading elements",
                        priority="high",
                    )
                )

            elif success_rate > 0.99 and avg_time < 1000:
                recommended_timeout = max(3000, int(avg_time * 3))
                recommendations.append(
                    OptimizationRecommendation(
                        selector=metrics.element_selector,
                        current_timeout=30000,
                        recommended_timeout=recommended_timeout,
                        reason="Fast-loading element with high success rate - timeout can be reduced",
                        expected_improvement="Faster test execution with quick failure detection",
                        priority="low",
                    )
                )

        return sorted(
            recommendations,
            key=lambda r: (
                {"high": 0, "medium": 1, "low": 2}[r.priority],
                r.current_timeout - r.recommended_timeout,
            ),
        )

    def detect_power_apps_loading_patterns(self) -> Dict[str, Any]:
        """
        Detect Power Apps specific loading patterns.

        Returns:
            Dictionary with Power Apps loading analysis
        """
        power_apps_indicators = ["canvas-app", "powerapps", "[role='application']", ".model-app"]

        pa_metrics = {}
        for indicator in power_apps_indicators:
            analysis = self.analyze_element_behavior(indicator)
            if analysis.get("status") != "no_data":
                pa_metrics[indicator] = analysis

        if not pa_metrics:
            return {"status": "no_data", "message": "No Power Apps element data available"}

        avg_success_rate = statistics.mean(
            [float(m["success_rate"].replace("%", "")) for m in pa_metrics.values()]
        )

        slow_loading = [
            k
            for k, v in pa_metrics.items()
            if v.get("loading_pattern") in ["slow_loading", "very_slow_loading"]
        ]

        return {
            "status": "analyzed",
            "elements_found": len(pa_metrics),
            "average_success_rate": f"{avg_success_rate:.1f}%",
            "slow_loading_elements": slow_loading,
            "recommendations": [
                "Use wait_for_power_apps_load() instead of generic waits",
                "Consider implementing polling-based waiting for canvas apps",
                "Power Apps may benefit from longer initial timeouts (60s+)",
            ],
        }

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive optimization report.

        Returns:
            Dictionary with complete optimization analysis
        """
        total_waits = sum(m.total_waits for m in self.element_metrics.values())
        total_success = sum(m.successful_waits for m in self.element_metrics.values())
        overall_success = (total_success / total_waits * 100) if total_waits > 0 else 0

        return {
            "summary": {
                "total_wait_operations": total_waits,
                "overall_success_rate": f"{overall_success:.1f}%",
                "elements_monitored": len(self.element_metrics),
            },
            "element_analysis": [
                self.analyze_element_behavior(m.element_selector)
                for m in self.element_metrics.values()
            ],
            "recommendations": [
                {
                    "selector": r.selector,
                    "current_timeout": r.current_timeout,
                    "recommended_timeout": r.recommended_timeout,
                    "reason": r.reason,
                    "expected_improvement": r.expected_improvement,
                    "priority": r.priority,
                }
                for r in self.generate_optimization_recommendations()
            ],
            "power_apps_analysis": self.detect_power_apps_loading_patterns(),
        }
