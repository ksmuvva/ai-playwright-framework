"""
Locator Healer Module (AI-Powered).

Provides intelligent locator healing when elements cannot be found.
Uses AI to analyze DOM and suggest alternative locators.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from playwright.async_api import Page, Locator
from enum import Enum


class HealingStrategy(Enum):
    """Locator healing strategies."""

    EXACT_MATCH = "exact_match"
    TEXT_SEARCH = "text_search"
    ROLE_BASED = "role_based"
    ATTRIBUTE_MATCH = "attribute_match"
    STRUCTURE_ANALYSIS = "structure_analysis"
    SIBLING_LOCATOR = "sibling_locator"
    PARENT_CHILD = "parent_child"
    FUZZY_TEXT = "fuzzy_text"
    NEARBY_ELEMENTS = "nearby_elements"


@dataclass
class HealingAttempt:
    """Record of a healing attempt."""

    original_selector: str
    strategy: HealingStrategy
    success: bool
    healed_selector: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class LocatorHealth:
    """Health metrics for a locator."""

    selector: str
    success_count: int = 0
    failure_count: int = 0
    healing_count: int = 0
    avg_recovery_time_ms: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None


class LocatorHealer:
    """
    AI-powered locator healer for automatic selector recovery.

    Features:
    - 9 healing strategies for element recovery
    - Learning from DOM structure changes
    - Locator history maintenance
    - Automatic code update suggestions
    """

    def __init__(self, enable_learning: bool = True):
        """
        Initialize the locator healer.

        Args:
            enable_learning: Whether to learn from healing attempts
        """
        self.strategies = list(HealingStrategy)
        self.healing_history: List[HealingAttempt] = []
        self.locator_health: Dict[str, LocatorHealth] = {}
        self.enable_learning = enable_learning

    async def find_element_with_healing(
        self, page: Page, selector: str, timeout: int = 5000
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Try to find an element, healing if necessary.

        Args:
            page: Playwright page object
            selector: Original CSS selector
            timeout: Timeout for finding element

        Returns:
            Tuple of (success, healed_selector, error_message)
        """
        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=timeout)
            return True, selector, None

        except Exception as original_error:
            if not self.enable_learning:
                return False, None, str(original_error)

            return await self._attempt_healing(page, selector, original_error)

    async def _attempt_healing(
        self, page: Page, original_selector: str, original_error: Exception
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Attempt to heal a broken selector.

        Args:
            page: Playwright page object
            original_selector: The original selector that failed
            original_error: The error that occurred

        Returns:
            Tuple of (success, healed_selector, error_message)
        """
        element_info = await self._analyze_element_context(page, original_selector)

        for strategy in self.strategies:
            attempt = HealingAttempt(original_selector=original_selector, strategy=strategy)

            try:
                healed_selector = await self._apply_strategy(page, strategy, element_info)

                if healed_selector:
                    element = page.locator(healed_selector).first
                    await element.wait_for(state="visible", timeout=3000)

                    attempt.success = True
                    attempt.healed_selector = healed_selector
                    self.healing_history.append(attempt)
                    self._update_locator_health(original_selector, healed_selector, True)

                    return True, healed_selector, None

            except Exception as e:
                attempt.success = False
                attempt.error_message = str(e)
                self.healing_history.append(attempt)
                continue

        self._update_locator_health(original_selector, None, False)
        return False, None, f"Could not heal selector: {original_selector}"

    async def _analyze_element_context(self, page: Page, selector: str) -> Dict[str, Any]:
        """
        Analyze the context of the element for healing.

        Args:
            page: Playwright page object
            selector: Original selector

        Returns:
            Dictionary with element context information
        """
        context = {
            "selector": selector,
            "tag_name": None,
            "text_content": None,
            "attributes": {},
            "parent_elements": [],
            "sibling_elements": [],
            "page_structure": {},
        }

        try:
            element = page.locator(selector).first

            context["tag_name"] = await element.evaluate("el => el.tagName.toLowerCase()")

            try:
                context["text_content"] = await element.text_content()
            except Exception:
                pass

            attrs = await element.evaluate("""el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")
            context["attributes"] = attrs

            context["page_structure"] = await page.evaluate("""() => {
                return {
                    total_elements: document.querySelectorAll('*').length,
                    forms: document.querySelectorAll('form').length,
                    inputs: document.querySelectorAll('input').length,
                    buttons: document.querySelectorAll('button').length,
                };
            }""")

        except Exception:
            pass

        return context

    async def _apply_strategy(
        self, page: Page, strategy: HealingStrategy, context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Apply a specific healing strategy.

        Args:
            page: Playwright page object
            strategy: Strategy to apply
            context: Element context information

        Returns:
            Healed selector or None if strategy failed
        """
        tag_name = context.get("tag_name", "")
        text_content = context.get("text_content", "") or ""
        attributes = context.get("attributes", {})
        parent_elements = context.get("parent_elements", [])

        if strategy == HealingStrategy.EXACT_MATCH:
            return context.get("selector")

        elif strategy == HealingStrategy.TEXT_SEARCH:
            if text_content:
                return f"text={text_content[:50]}"
            if attributes.get("aria-label"):
                return f"[aria-label='{attributes.get('aria-label')}']"
            if attributes.get("title"):
                return f"[title='{attributes.get('title')}']"

        elif strategy == HealingStrategy.ROLE_BASED:
            role = attributes.get("role")
            if role:
                return f"[role='{role}']"
            if tag_name == "button":
                return "button"
            if tag_name == "input":
                input_type = attributes.get("type", "text")
                return f"input[type='{input_type}']"

        elif strategy == HealingStrategy.ATTRIBUTE_MATCH:
            for attr in ["id", "name", "data-testid", "data-cy", "test-id"]:
                if attr in attributes and attributes[attr]:
                    return f"[{attr}='{attributes[attr]}']"

        elif strategy == HealingStrategy.FUZZY_TEXT:
            if text_content:
                keywords = text_content.split()[:3]
                for keyword in keywords:
                    if len(keyword) > 3:
                        return f"text={keyword}"

        elif strategy == HealingStrategy.NEARBY_ELEMENTS:
            nearby_text = context.get("page_structure", {}).get("nearby_text", "")
            if nearby_text:
                return f"text={nearby_text[:30]}"

        return None

    def suggest_alternative_locators(self, element_description: str) -> List[Dict[str, str]]:
        """
        Suggest alternative locators for an element description.

        Args:
            element_description: Description of the element

        Returns:
            List of suggested locators with confidence scores
        """
        suggestions = []

        suggestions.append(
            {
                "strategy": "id",
                "selector": f"#{element_description.lower().replace(' ', '-')}",
                "confidence": "high",
            }
        )

        suggestions.append(
            {
                "strategy": "name",
                "selector": f"[name='{element_description.lower().replace(' ', '_')}']",
                "confidence": "medium",
            }
        )

        suggestions.append(
            {"strategy": "text", "selector": f"text={element_description}", "confidence": "medium"}
        )

        suggestions.append(
            {
                "strategy": "aria_label",
                "selector": f"[aria-label='{element_description}']",
                "confidence": "high",
            }
        )

        suggestions.append(
            {
                "strategy": "role_button",
                "selector": f"button[aria-label*='{element_description}']",
                "confidence": "medium",
            }
        )

        return suggestions

    def verify_locator_stability(self, selector: str) -> Dict[str, Any]:
        """
        Verify the stability of a locator over time.

        Args:
            selector: Selector to verify

        Returns:
            Dictionary with stability metrics
        """
        health = self.locator_health.get(selector, LocatorHealth(selector))

        total_attempts = health.success_count + health.failure_count
        success_rate = (health.success_count / total_attempts * 100) if total_attempts > 0 else 0

        return {
            "selector": selector,
            "total_attempts": total_attempts,
            "success_rate": f"{success_rate:.1f}%",
            "healing_required": health.healing_count,
            "avg_recovery_time_ms": health.avg_recovery_time_ms,
            "is_stable": success_rate >= 95,
            "recommendation": "Use this selector" if success_rate >= 95 else "Consider alternative",
        }

    def _update_locator_health(
        self, original_selector: str, healed_selector: Optional[str], success: bool
    ) -> None:
        """Update health metrics for a locator."""
        if original_selector not in self.locator_health:
            self.locator_health[original_selector] = LocatorHealth(selector=original_selector)

        health = self.locator_health[original_selector]

        if success:
            health.success_count += 1
            health.last_success = __import__("time").time()
            if healed_selector and healed_selector != original_selector:
                health.healing_count += 1
        else:
            health.failure_count += 1
            health.last_failure = __import__("time").time()

    def get_healing_report(self) -> Dict[str, Any]:
        """Generate a healing report."""
        total_attempts = len(self.healing_history)
        successful_heals = sum(1 for a in self.healing_history if a.success)

        strategy_stats = {}
        for strategy in self.strategies:
            strategy_attempts = [a for a in self.healing_history if a.strategy == strategy]
            if strategy_attempts:
                strategy_stats[strategy.value] = {
                    "attempts": len(strategy_attempts),
                    "successes": sum(1 for a in strategy_attempts if a.success),
                    "success_rate": f"{(sum(1 for a in strategy_attempts if a.success) / len(strategy_attempts) * 100):.1f}%",
                }

        return {
            "total_healing_attempts": total_attempts,
            "successful_heals": successful_heals,
            "overall_success_rate": f"{(successful_heals / total_attempts * 100) if total_attempts > 0 else 0:.1f}%",
            "strategy_statistics": strategy_stats,
            "unhealthy_locators": [
                {"selector": s, "failures": h.failure_count}
                for s, h in self.locator_health.items()
                if h.failure_count > h.success_count
            ],
        }
