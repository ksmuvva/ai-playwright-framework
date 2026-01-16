"""
Self-Healing Selectors Module for Claude Playwright Agent.

This module handles:
- Automatic selector healing when tests fail
- Alternative selector generation
- Healing strategy application
- Healing approval workflow
- Healing history tracking
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Self-Healing Models
# =============================================================================


class HealingStatus(str, Enum):
    """Status of a healing attempt."""

    PENDING = "pending"
    ATTEMPTED = "attempted"
    SUCCESS = "success"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPLIED = "auto_applied"


class HealingStrategy(str, Enum):
    """Strategies for healing broken selectors."""

    FALLBACK_SELECTOR = "fallback_selector"
    ARIA_ATTRIBUTES = "aria_attributes"
    DATA_TESTID = "data_testid"
    TEXT_CONTENT = "text_content"
    ROLE_BASED = "role_based"
    PARENT_RELATIVE = "parent_relative"
    SIBLING_RELATIVE = "sibling_relative"
    PARTIAL_MATCH = "partial_match"
    REGEX_PATTERN = "regex_pattern"


@dataclass
class SelectorHealing:
    """A single selector healing attempt."""

    original_selector: str
    healed_selector: str
    strategy: HealingStrategy
    status: HealingStatus
    confidence: float = 0.0
    test_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    attempts: int = 0
    last_attempt: str = ""
    approved_by: str = ""  # "auto" or user
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_selector": self.original_selector,
            "healed_selector": self.healed_selector,
            "strategy": self.strategy.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class HealingAttempt:
    """Result of a healing attempt."""

    healing: SelectorHealing
    success: bool
    error_message: str = ""
    execution_time: float = 0.0
    screenshot_path: str = ""
    before_state: dict[str, Any] = field(default_factory=dict)
    after_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "healing": self.healing.to_dict(),
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "screenshot_path": self.screenshot_path,
            "before_state": self.before_state,
            "after_state": self.after_state,
        }


@dataclass
class HealingConfig:
    """Configuration for self-healing behavior."""

    enabled: bool = True
    max_attempts: int = 3
    auto_apply_threshold: float = 0.8  # Confidence above this applies automatically
    require_approval: bool = True
    allowed_strategies: list[HealingStrategy] = field(default_factory=list)
    track_history: bool = True
    history_size: int = 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "max_attempts": self.max_attempts,
            "auto_apply_threshold": self.auto_apply_threshold,
            "require_approval": self.require_approval,
            "allowed_strategies": [s.value for s in self.allowed_strategies],
            "track_history": self.track_history,
            "history_size": self.history_size,
        }


# =============================================================================
# Self-Healing Engine
# =============================================================================


class SelfHealingEngine:
    """
    Auto-heal broken selectors during test execution.

    Features:
    - Generate alternative selectors
    - Apply healing strategies
    - Track healing history
    - Approval workflow for selector changes
    """

    # Common fragile patterns that need healing
    FRAGILE_PATTERNS = [
        r":nth-child\(\d+\)",
        r":nth-of-type\(\d+\)",
        r">\s*[a-z]+\s*>\s*[a-z]+",  # Deep nesting
        r"\[class*=['\"][^'\"]*\['\"]",  # Wildcard class attributes
    ]

    # Selector type patterns for detection
    SELECTOR_TYPES = {
        "id": r"#[-_a-zA-Z][-_a-zA-Z0-9]*",
        "class": r"\.[-_a-zA-Z][-_a-zA-Z0-9]*",
        "data_attr": r'\[data-[-a-z]+=(["\'])[^"\']+\1\]',
        "attr": r'\[[-a-z]+=(["\'])[^"\']+\1\]',
        "tag": r"^[a-z]+",
        "role": r'role=[\'"]?([a-zA-Z]+)[\'"]?',
    }

    def __init__(self, config: HealingConfig | None = None) -> None:
        """
        Initialize the self-healing engine.

        Args:
            config: Healing configuration
        """
        self._config = config or HealingConfig()
        self._history: list[SelectorHealing] = []

    def analyze_selector(
        self,
        selector: str,
        page_context: dict[str, Any] | None = None,
    ) -> list[SelectorHealing]:
        """
        Analyze a selector and generate healing options.

        Args:
            selector: The broken selector
            page_context: Optional page state context

        Returns:
            List of potential healings sorted by confidence
        """
        healings = []

        if not selector:
            return healings

        # Generate alternatives using different strategies
        healings.extend(self._generate_fallback_selectors(selector))
        healings.extend(self._generate_aria_alternatives(selector))
        healings.extend(self._generate_data_testid_alternatives(selector))
        healings.extend(self._generate_role_based_alternatives(selector))
        healings.extend(self._generate_text_based_alternatives(selector, page_context))
        healings.extend(self._generate_parent_relative_alternatives(selector))
        healings.extend(self._generate_sibling_relative_alternatives(selector))

        # Sort by confidence
        healings.sort(key=lambda h: h.confidence, reverse=True)

        # Filter by allowed strategies
        if self._config.allowed_strategies:
            healings = [
                h for h in healings
                if h.strategy in self._config.allowed_strategies
            ]

        # Filter by threshold (but keep DATA_TESTID and fallback selectors)
        healings = [
            h for h in healings
            if h.confidence >= self._config.auto_apply_threshold
            or h.strategy in [HealingStrategy.DATA_TESTID, HealingStrategy.FALLBACK_SELECTOR]
        ]

        return healings

    def heal_selector(
        self,
        selector: str,
        test_name: str = "",
        page_context: dict[str, Any] | None = None,
    ) -> HealingAttempt:
        """
        Attempt to heal a broken selector.

        Args:
            selector: The broken selector
            test_name: Name of the failing test
            page_context: Optional page state context

        Returns:
            HealingAttempt with result
        """
        healings = self.analyze_selector(selector, page_context)

        if not healings:
            return HealingAttempt(
                healing=SelectorHealing(
                    original_selector=selector,
                    healed_selector="",
                    strategy=HealingStrategy.FALLBACK_SELECTOR,
                    status=HealingStatus.FAILED,
                    confidence=0.0,
                    test_name=test_name,
                ),
                success=False,
                error_message="No healing options found",
            )

        # Try the best healing option
        best_healing = healings[0]

        # Set the test name
        best_healing.test_name = test_name

        # Check if auto-apply is allowed
        if best_healing.confidence >= self._config.auto_apply_threshold:
            best_healing.status = HealingStatus.AUTO_APPLIED
            best_healing.approved_by = "auto"
        else:
            best_healing.status = HealingStatus.PENDING

        best_healing.attempts += 1
        best_healing.last_attempt = datetime.now().isoformat()

        # Track history
        if self._config.track_history:
            self._add_to_history(best_healing)

        return HealingAttempt(
            healing=best_healing,
            success=best_healing.status in [HealingStatus.AUTO_APPLIED, HealingStatus.APPROVED],
        )

    def approve_healing(
        self,
        healing: SelectorHealing,
        approved_by: str = "user",
    ) -> SelectorHealing:
        """
        Approve a healing attempt.

        Args:
            healing: The healing to approve
            approved_by: Who approved (user or auto)

        Returns:
            The updated healing
        """
        healing.status = HealingStatus.APPROVED
        healing.approved_by = approved_by

        return healing

    def reject_healing(
        self,
        healing: SelectorHealing,
        reason: str = "",
    ) -> SelectorHealing:
        """
        Reject a healing attempt.

        Args:
            healing: The healing to reject
            reason: Reason for rejection

        Returns:
            The updated healing
        """
        healing.status = HealingStatus.REJECTED
        healing.rejection_reason = reason

        return healing

    def get_history(
        self,
        selector: str | None = None,
        limit: int = 50,
    ) -> list[SelectorHealing]:
        """
        Get healing history.

        Args:
            selector: Optional filter by original selector
            limit: Maximum number of results

        Returns:
            List of healings
        """
        history = self._history

        if selector:
            history = [h for h in history if h.original_selector == selector]

        # Sort by timestamp descending
        history = sorted(history, key=lambda h: h.timestamp, reverse=True)

        return history[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get healing statistics."""
        total = len(self._history)
        successful = len([h for h in self._history if h.status == HealingStatus.SUCCESS])
        auto_applied = len([h for h in self._history if h.status == HealingStatus.AUTO_APPLIED])
        pending = len([h for h in self._history if h.status == HealingStatus.PENDING])

        # Strategy effectiveness
        strategy_counts: dict[HealingStrategy, int] = {}
        for healing in self._history:
            if healing.status == HealingStatus.SUCCESS:
                strategy_counts[healing.strategy] = strategy_counts.get(healing.strategy, 0) + 1

        return {
            "total_healings": total,
            "successful": successful,
            "auto_applied": auto_applied,
            "pending": pending,
            "success_rate": successful / total if total > 0 else 0.0,
            "strategy_effectiveness": {k.value: v for k, v in strategy_counts.items()},
        }

    def _generate_fallback_selectors(self, selector: str) -> list[SelectorHealing]:
        """Generate fallback selectors by removing fragile parts."""
        healings = []

        # Remove nth-child pseudo-classes
        fallback = re.sub(r":nth-child\(\d+\)", "", selector)
        if fallback != selector:
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector=fallback,
                strategy=HealingStrategy.FALLBACK_SELECTOR,
                status=HealingStatus.PENDING,
                confidence=0.6,
            ))

        # Remove nth-of-type pseudo-classes
        fallback = re.sub(r":nth-of-type\(\d+\)", "", selector)
        if fallback != selector:
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector=fallback,
                strategy=HealingStrategy.FALLBACK_SELECTOR,
                status=HealingStatus.PENDING,
                confidence=0.6,
            ))

        return healings

    def _generate_aria_alternatives(self, selector: str) -> list[SelectorHealing]:
        """Generate ARIA-based alternatives."""
        healings = []

        # Extract element type from selector
        match = re.search(r'^([a-z]+)', selector)
        if match:
            tag = match.group(1)

            # Try role-based selectors
            if tag == "button":
                healings.append(SelectorHealing(
                    original_selector=selector,
                    healed_selector='role="button"',
                    strategy=HealingStrategy.ARIA_ATTRIBUTES,
                    status=HealingStatus.PENDING,
                    confidence=0.8,
                ))
            elif tag == "input":
                healings.append(SelectorHealing(
                    original_selector=selector,
                    healed_selector='role="textbox"',
                    strategy=HealingStrategy.ARIA_ATTRIBUTES,
                    status=HealingStatus.PENDING,
                    confidence=0.7,
                ))
            elif tag == "a":
                healings.append(SelectorHealing(
                    original_selector=selector,
                    healed_selector='role="link"',
                    strategy=HealingStrategy.ARIA_ATTRIBUTES,
                    status=HealingStatus.PENDING,
                    confidence=0.7,
                ))

        return healings

    def _generate_data_testid_alternatives(self, selector: str) -> list[SelectorHealing]:
        """Generate data-testid based alternatives."""
        healings = []

        # Extract element name/identifier from selector
        match = re.search(r'[\.#]([a-z][-_a-z0-9]*)', selector)
        if match:
            element_id = match.group(1)

            # Generate data-testid selector
            data_testid = f'[data-testid="{element_id}"]'
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector=data_testid,
                strategy=HealingStrategy.DATA_TESTID,
                status=HealingStatus.PENDING,
                confidence=0.9,  # High confidence for data-testid
            ))

        return healings

    def _generate_role_based_alternatives(self, selector: str) -> list[SelectorHealing]:
        """Generate role-based selector alternatives."""
        healings = []

        # Try get_by_role pattern
        # For buttons
        if "button" in selector.lower() or "btn" in selector.lower() or "submit" in selector.lower():
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector='get_by_role("button")',
                strategy=HealingStrategy.ROLE_BASED,
                status=HealingStatus.PENDING,
                confidence=0.75,
            ))

        # For inputs
        if "input" in selector.lower():
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector='get_by_role("textbox")',
                strategy=HealingStrategy.ROLE_BASED,
                status=HealingStatus.PENDING,
                confidence=0.7,
            ))

        # For links
        if "link" in selector.lower() or "a." in selector:
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector='get_by_role("link")',
                strategy=HealingStrategy.ROLE_BASED,
                status=HealingStatus.PENDING,
                confidence=0.7,
            ))

        return healings

    def _generate_text_based_alternatives(
        self,
        selector: str,
        page_context: dict[str, Any] | None = None,
    ) -> list[SelectorHealing]:
        """Generate text-based selector alternatives."""
        healings = []

        # Extract text from context if available
        if page_context and "text_content" in page_context:
            text = page_context["text_content"]
            if text:
                # Use getByText or get_by_role with name
                healings.append(SelectorHealing(
                    original_selector=selector,
                    healed_selector=f'get_by_text("{text}")',
                    strategy=HealingStrategy.TEXT_CONTENT,
                    status=HealingStatus.PENDING,
                    confidence=0.65,
                ))

        return healings

    def _generate_parent_relative_alternatives(self, selector: str) -> list[SelectorHealing]:
        """Generate parent-relative selector alternatives."""
        healings = []

        # Remove last part of selector and use parent
        parts = selector.split(">")
        if len(parts) > 1:
            parent = ">".join(parts[:-1])
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector=f"{parent} *",  # Any child
                strategy=HealingStrategy.PARENT_RELATIVE,
                status=HealingStatus.PENDING,
                confidence=0.5,
            ))

        return healings

    def _generate_sibling_relative_alternatives(self, selector: str) -> list[SelectorHealing]:
        """Generate sibling-relative selector alternatives."""
        healings = []

        # Look for patterns like .parent .child
        match = re.match(r'([.\[][^\s>]+)\s+([.\[][^\s>]+)', selector)
        if match:
            parent, sibling = match.groups()

            # Try following sibling
            healings.append(SelectorHealing(
                original_selector=selector,
                healed_selector=f"{parent} ~ {sibling}",
                strategy=HealingStrategy.SIBLING_RELATIVE,
                status=HealingStatus.PENDING,
                confidence=0.55,
            ))

        return healings

    def _add_to_history(self, healing: SelectorHealing) -> None:
        """Add healing to history."""
        self._history.append(healing)

        # Trim history if needed
        if len(self._history) > self._config.history_size:
            self._history = self._history[-self._config.history_size :]


# =============================================================================
# Convenience Functions
# =============================================================================


def analyze_selector_for_healing(
    selector: str,
    page_context: dict[str, Any] | None = None,
    config: HealingConfig | None = None,
) -> list[SelectorHealing]:
    """
    Analyze a selector and generate healing options.

    Args:
        selector: The broken selector
        page_context: Optional page state context
        config: Optional healing configuration

    Returns:
        List of potential healings sorted by confidence
    """
    engine = SelfHealingEngine(config)
    return engine.analyze_selector(selector, page_context)


def heal_selector(
    selector: str,
    test_name: str = "",
    page_context: dict[str, Any] | None = None,
    config: HealingConfig | None = None,
) -> HealingAttempt:
    """
    Attempt to heal a broken selector.

    Args:
        selector: The broken selector
        test_name: Name of the failing test
        page_context: Optional page state context
        config: Optional healing configuration

    Returns:
        HealingAttempt with result
    """
    engine = SelfHealingEngine(config)
    return engine.heal_selector(selector, test_name, page_context)
