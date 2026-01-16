"""
Self-Healing Analytics Module

Tracks and analyzes self-healing effectiveness during test execution.
Provides insights into:
- Healing success/failure rates
- Most effective strategies
- Frequently failing selectors
- Healing recommendations
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict
import json
from pathlib import Path


@dataclass
class HealingAttempt:
    """Represents a single self-healing attempt."""

    timestamp: str
    page_name: str
    action: str
    original_selector: str
    healed_selector: Optional[str]
    strategy_used: Optional[str]
    success: bool
    confidence: float
    error_message: Optional[str] = None


@dataclass
class StrategyStats:
    """Statistics for a healing strategy."""

    strategy_name: str
    total_attempts: int = 0
    successful_healings: int = 0
    failed_healings: int = 0
    avg_confidence: float = 0.0
    total_confidence: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_attempts == 0:
            return 0.0
        return round((self.successful_healings / self.total_attempts) * 100, 2)


class HealingAnalytics:
    """
    Track and analyze self-healing effectiveness.

    Example:
        >>> analytics = HealingAnalytics()
        >>> analytics.record_attempt(
        ...     page_name="LoginPage",
        ...     action="click",
        ...     original_selector="#login-btn",
        ...     healed_selector="button:has-text('Login')",
        ...     strategy="text_based",
        ...     success=True,
        ...     confidence=0.95
        ... )
        >>> stats = analytics.get_strategy_stats()
    """

    def __init__(self, output_dir: str = ".cpa/healing"):
        """
        Initialize HealingAnalytics.

        Args:
            output_dir: Directory to save analytics data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.attempts: List[HealingAttempt] = []
        self.selector_failures: Counter = Counter()
        self.page_failures: Dict[str, int] = defaultdict(int)

    def record_attempt(
        self,
        page_name: str,
        action: str,
        original_selector: str,
        healed_selector: Optional[str],
        strategy_used: Optional[str],
        success: bool,
        confidence: float,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record a self-healing attempt.

        Args:
            page_name: Name of the page where healing occurred
            action: Action being performed (click, fill, etc.)
            original_selector: Original selector that failed
            healed_selector: Healed selector (if successful)
            strategy_used: Strategy used for healing
            success: Whether healing was successful
            confidence: Confidence score of the healing (0-1)
            error_message: Error message if healing failed
        """
        attempt = HealingAttempt(
            timestamp=datetime.now().isoformat(),
            page_name=page_name,
            action=action,
            original_selector=original_selector,
            healed_selector=healed_selector,
            strategy_used=strategy_used,
            success=success,
            confidence=confidence,
            error_message=error_message
        )

        self.attempts.append(attempt)

        # Track selector failures
        if not success:
            self.selector_failures[original_selector] += 1
            self.page_failures[page_name] += 1

    def get_strategy_stats(self) -> Dict[str, StrategyStats]:
        """
        Get statistics grouped by healing strategy.

        Returns:
            Dictionary mapping strategy name to StrategyStats
        """
        strategy_stats: Dict[str, StrategyStats] = {}

        for attempt in self.attempts:
            strategy = attempt.strategy_used or "unknown"

            if strategy not in strategy_stats:
                strategy_stats[strategy] = StrategyStats(strategy_name=strategy)

            stats = strategy_stats[strategy]
            stats.total_attempts += 1
            stats.total_confidence += attempt.confidence

            if attempt.success:
                stats.successful_healings += 1
            else:
                stats.failed_healings += 1

        # Calculate average confidence
        for stats in strategy_stats.values():
            if stats.total_attempts > 0:
                stats.avg_confidence = round(stats.total_confidence / stats.total_attempts, 3)

        return strategy_stats

    def get_overall_stats(self) -> Dict[str, Any]:
        """
        Get overall healing statistics.

        Returns:
            Dictionary with overall statistics
        """
        if not self.attempts:
            return {
                "total_attempts": 0,
                "successful_healings": 0,
                "failed_healings": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0
            }

        total = len(self.attempts)
        successful = sum(1 for a in self.attempts if a.success)
        failed = total - successful
        total_confidence = sum(a.confidence for a in self.attempts)

        return {
            "total_attempts": total,
            "successful_healings": successful,
            "failed_healings": failed,
            "success_rate": round((successful / total) * 100, 2),
            "avg_confidence": round(total_confidence / total, 3)
        }

    def get_failing_selectors(self, top_n: int = 10) -> List[tuple[str, int]]:
        """
        Get most frequently failing selectors.

        Args:
            top_n: Number of top selectors to return

        Returns:
            List of (selector, failure_count) tuples
        """
        return self.selector_failures.most_common(top_n)

    def get_page_failure_stats(self) -> Dict[str, int]:
        """
        Get failure statistics grouped by page.

        Returns:
            Dictionary mapping page name to failure count
        """
        return dict(self.page_failures)

    def generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on analytics.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check overall success rate
        overall = self.get_overall_stats()
        if overall["success_rate"] < 50:
            recommendations.append(
                "⚠️ Low overall healing success rate (<50%). "
                "Consider reviewing selector strategies or improving selector robustness."
            )

        # Check for frequently failing selectors
        failing_selectors = self.get_failing_selectors(top_n=5)
        if failing_selectors:
            top_failure, count = failing_selectors[0]
            if count >= 3:
                recommendations.append(
                    f"❌ Selector '{top_failure}' has failed {count} times. "
                    "Consider updating this selector directly in page objects."
                )

        # Check strategy effectiveness
        strategy_stats = self.get_strategy_stats()
        ineffective_strategies = [
            name for name, stats in strategy_stats.items()
            if stats.total_attempts >= 3 and stats.success_rate < 30
        ]

        if ineffective_strategies:
            recommendations.append(
                f"⚠️ Strategies {', '.join(ineffective_strategies)} have low success rates. "
                "Consider adjusting their priority or configuration."
            )

        # Check for high-confidence failures
        high_conf_failures = [
            a for a in self.attempts
            if not a.success and a.confidence >= 0.8
        ]

        if len(high_conf_failures) >= 3:
            recommendations.append(
                f"⚠️ {len(high_conf_failures)} healings failed despite high confidence (≥0.8). "
                "Review confidence scoring in healing strategies."
            )

        if not recommendations:
            recommendations.append("✅ Healing performance looks good!")

        return recommendations

    def export_analytics(self, filepath: Optional[str] = None) -> str:
        """
        Export analytics to JSON file.

        Args:
            filepath: Optional custom filepath

        Returns:
            Path to exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"analytics_{timestamp}.json"
        else:
            filepath = Path(filepath)

        data = {
            "overall_stats": self.get_overall_stats(),
            "strategy_stats": {
                name: {
                    "total_attempts": stats.total_attempts,
                    "successful_healings": stats.successful_healings,
                    "failed_healings": stats.failed_healings,
                    "success_rate": stats.success_rate,
                    "avg_confidence": stats.avg_confidence
                }
                for name, stats in self.get_strategy_stats().items()
            },
            "failing_selectors": self.get_failing_selectors(20),
            "page_failures": self.get_page_failure_stats(),
            "recommendations": self.generate_recommendations(),
            "attempts": [
                {
                    "timestamp": a.timestamp,
                    "page_name": a.page_name,
                    "action": a.action,
                    "original_selector": a.original_selector,
                    "healed_selector": a.healed_selector,
                    "strategy_used": a.strategy_used,
                    "success": a.success,
                    "confidence": a.confidence,
                    "error_message": a.error_message
                }
                for a in self.attempts
            ]
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return str(filepath)

    def import_analytics(self, filepath: str) -> None:
        """
        Import analytics from JSON file.

        Args:
            filepath: Path to JSON file
        """
        data = json.loads(Path(filepath).read_text(encoding='utf-8'))

        # Clear existing data
        self.attempts.clear()
        self.selector_failures.clear()
        self.page_failures.clear()

        # Import attempts
        for attempt_data in data.get("attempts", []):
            self.attempts.append(HealingAttempt(**attempt_data))

            # Rebuild counters
            if not attempt_data["success"]:
                self.selector_failures[attempt_data["original_selector"]] += 1
                self.page_failures[attempt_data["page_name"]] += 1

    def clear(self) -> None:
        """Clear all analytics data."""
        self.attempts.clear()
        self.selector_failures.clear()
        self.page_failures.clear()

    def __len__(self) -> int:
        """Return number of recorded attempts."""
        return len(self.attempts)

    def __repr__(self) -> str:
        """String representation."""
        return f"HealingAnalytics(attempts={len(self.attempts)}, strategies={len(self.get_strategy_stats())})"
