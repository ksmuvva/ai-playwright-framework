"""
Memory-Powered Self-Healing Engine

Integrates memory system with self-healing to learn from past healing attempts.
"""

import logging
from typing import Any, Optional

from .analytics import HealingAnalytics
from ..agents.self_healing import (
    SelfHealingEngine,
    HealingAttempt as AgentHealingAttempt,
    SelectorHealing,
    HealingStrategy,
    HealingStatus,
)

logger = logging.getLogger(__name__)


class MemoryPoweredSelfHealingEngine(SelfHealingEngine):
    """
    Self-healing engine with memory integration.

    Learns from past healing attempts to improve future healing success rates.
    Uses the memory system to:
    1. Remember successful healing strategies for specific selectors
    2. Recall previous healing attempts when encountering failures
    3. Track healing effectiveness over time
    4. Provide intelligent recommendations based on history
    """

    def __init__(self, memory_manager, analytics: Optional[HealingAnalytics] = None):
        """
        Initialize memory-powered self-healing engine.

        Args:
            memory_manager: MemoryManager instance for storing/retrieving healing history
            analytics: Optional HealingAnalytics for tracking effectiveness
        """
        super().__init__()
        self.memory = memory_manager
        self.analytics = analytics or HealingAnalytics()

    async def heal_selector(
        self,
        selector: str,
        test_name: str = "",
        page_context: Optional[dict[str, Any]] = None,
    ) -> AgentHealingAttempt:
        """
        Attempt to heal a broken selector using memory-assisted strategy selection.

        Args:
            selector: The broken selector
            test_name: Name of the failing test
            page_context: Optional page state context

        Returns:
            HealingAttempt with result
        """
        # Check memory for previous successful healings of this selector
        previous_healings = await self._recall_previous_healings(selector)

        if previous_healings:
            # Use the most successful previous healing
            best_previous = max(previous_healings, key=lambda h: h.get("confidence", 0))

            logger.info(
                f"Found previous healing for '{selector}': "
                f"{best_previous.get('healed_selector')} "
                f"(confidence: {best_previous.get('confidence', 0)})"
            )

            # Create healing from memory
            healing = SelectorHealing(
                original_selector=selector,
                healed_selector=best_previous.get("healed_selector", ""),
                strategy=HealingStrategy(best_previous.get("strategy", "fallback_selector")),
                status=HealingStatus.APPROVED,
                confidence=best_previous.get("confidence", 0.8),
                test_name=test_name,
                approved_by="memory",
            )

            # Record in analytics
            self.analytics.record_attempt(
                page_name=page_context.get("page_name", "unknown") if page_context else "unknown",
                action="click",
                original_selector=selector,
                healed_selector=healing.healed_selector,
                strategy_used=healing.strategy.value,
                success=True,
                confidence=healing.confidence,
            )

            return AgentHealingAttempt(
                healing=healing,
                success=True,
            )

        # No previous healing found, use standard healing logic
        logger.info(f"No previous healings found for '{selector}', using standard strategies")
        result = super().heal_selector(selector, test_name, page_context)

        # Remember successful healings
        if result.success and result.healing.healed_selector:
            await self._remember_successful_healing(
                selector=selector,
                healed_selector=result.healing.healed_selector,
                strategy=result.healing.strategy,
                confidence=result.healing.confidence,
                test_name=test_name,
            )

        # Record attempt in analytics
        self.analytics.record_attempt(
            page_name=page_context.get("page_name", "unknown") if page_context else "unknown",
            action="click",
            original_selector=selector,
            healed_selector=result.healing.healed_selector if result.success else None,
            strategy_used=result.healing.strategy.value if result.healing else "unknown",
            success=result.success,
            confidence=result.healing.confidence if result.healing else 0.0,
            error_message=result.error_message if not result.success else None,
        )

        return result

    async def _recall_previous_healings(self, selector: str) -> list[dict]:
        """
        Recall previous healing attempts for a selector.

        Args:
            selector: The selector to look up

        Returns:
            List of previous healing dictionaries
        """
        if not self.memory:
            return []

        try:
            # Search for memories with selector_healing tag
            memories = await self.memory.recall_by_tags(
                tags=["selector_healing", selector.replace("#", "_").replace(".", "_")],
                count=10,
            )

            # Extract healing data
            healings = []
            for memory in memories:
                if memory.value and isinstance(memory.value, dict):
                    healings.append(memory.value)

            return healings
        except Exception as e:
            logger.error(f"Failed to recall previous healings: {e}")
            return []

    async def _remember_successful_healing(
        self,
        selector: str,
        healed_selector: str,
        strategy: HealingStrategy,
        confidence: float,
        test_name: str,
    ) -> bool:
        """
        Remember a successful healing attempt.

        Args:
            selector: Original selector
            healed_selector: Successful healed selector
            strategy: Strategy used
            confidence: Confidence score
            test_name: Test name

        Returns:
            True if stored successfully
        """
        if not self.memory:
            return False

        try:
            from ..skills.builtins.e10_1_memory_manager import MemoryType, MemoryPriority

            # Create safe tag from selector
            safe_tag = selector.replace("#", "_").replace(".", "_").replace("[", "_").replace("]", "_")

            await self.memory.store(
                key=f"healing:{selector}:{test_name}",
                value={
                    "selector": selector,
                    "healed_selector": healed_selector,
                    "strategy": strategy.value,
                    "confidence": confidence,
                    "test_name": test_name,
                },
                type=MemoryType.SEMANTIC,  # Store as semantic knowledge
                priority=MemoryPriority.HIGH if confidence > 0.8 else MemoryPriority.MEDIUM,
                tags=["selector_healing", safe_tag, "successful"],
            )

            logger.info(f"Remembered successful healing: {selector} -> {healed_selector}")
            return True
        except Exception as e:
            logger.error(f"Failed to remember healing: {e}")
            return False

    async def get_healing_recommendations(self) -> list[str]:
        """
        Get healing recommendations based on analytics.

        Returns:
            List of recommendation strings
        """
        return self.analytics.generate_recommendations()

    async def get_healing_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive healing statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "overall": self.analytics.get_overall_stats(),
            "strategies": {
                name: {
                    "total_attempts": stats.total_attempts,
                    "success_rate": stats.success_rate,
                    "avg_confidence": stats.avg_confidence,
                }
                for name, stats in self.analytics.get_strategy_stats().items()
            },
            "failing_selectors": self.analytics.get_failing_selectors(10),
            "page_failures": self.analytics.get_page_failure_stats(),
        }

    async def learn_from_test_execution(
        self,
        test_name: str,
        outcome: str,
        healing_attempts: list[AgentHealingAttempt],
    ) -> None:
        """
        Learn from a complete test execution.

        Args:
            test_name: Name of the test
            outcome: Test outcome (passed, failed, skipped)
            healing_attempts: List of healing attempts during the test
        """
        if not self.memory:
            return

        try:
            from ..skills.builtins.e10_1_memory_manager import MemoryType, MemoryPriority

            # Remember test execution
            await self.memory.store(
                key=f"test_execution:{test_name}",
                value={
                    "test_name": test_name,
                    "outcome": outcome,
                    "healing_count": len(healing_attempts),
                    "successful_healings": sum(1 for h in healing_attempts if h.success),
                },
                type=MemoryType.EPISODIC,
                priority=MemoryPriority.MEDIUM,
                tags=["test_execution", outcome],
            )

            logger.info(f"Remembered test execution: {test_name} ({outcome})")
        except Exception as e:
            logger.error(f"Failed to remember test execution: {e}")


def create_memory_powered_healing_engine(
    memory_manager,
    enable_analytics: bool = True,
) -> MemoryPoweredSelfHealingEngine:
    """
    Factory function to create a memory-powered self-healing engine.

    Args:
        memory_manager: MemoryManager instance
        enable_analytics: Whether to enable analytics tracking

    Returns:
        MemoryPoweredSelfHealingEngine instance
    """
    analytics = HealingAnalytics() if enable_analytics else None
    return MemoryPoweredSelfHealingEngine(
        memory_manager=memory_manager,
        analytics=analytics,
    )
