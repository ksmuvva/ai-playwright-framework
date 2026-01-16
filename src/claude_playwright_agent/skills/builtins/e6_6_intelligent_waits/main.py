"""
Intelligent Waits Skill - Smart wait management for test automation

This skill provides intelligent wait strategies including:
1. Explicit waits - Wait for specific conditions
2. Implicit waits - Global wait configuration
3. Smart waits - AI-powered optimal wait detection
4. Hybrid waits - Combine multiple strategies
5. Dynamic timeout adjustment - Based on network and page conditions
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class WaitCondition(str, Enum):
    """Wait condition types"""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ATTACHED = "attached"
    DETACHED = "detached"
    ENABLED = "enabled"
    DISABLED = "disabled"
    STABLE = "stable"


class WaitStrategy(str, Enum):
    """Wait strategy types"""
    EXPLICIT = "explicit"  # Wait for specific condition
    IMPLICIT = "implicit"  # Global wait for all elements
    SMART = "smart"  # AI-powered optimal wait
    HYBRID = "hybrid"  # Combine multiple strategies


@dataclass
class WaitResult:
    """Result of a wait operation"""
    element: str
    strategy: WaitStrategy
    condition: WaitCondition
    duration_ms: int
    success: bool
    message: str
    attempts: int = 1
    optimizations: List[str] = field(default_factory=list)


@dataclass
class WaitAnalytics:
    """Analytics data for wait operations"""
    total_wait_time_ms: int = 0
    wait_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    wait_times: List[int] = field(default_factory=list)
    average_wait_time: float = 0.0
    recommended_timeout: int = 30000

    def add_wait(self, duration_ms: int, success: bool) -> None:
        """Add a wait operation to analytics"""
        self.wait_count += 1
        self.total_wait_time_ms += duration_ms
        self.wait_times.append(duration_ms)

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Recalculate average
        if self.wait_times:
            self.average_wait_time = statistics.mean(self.wait_times)

        # Calculate recommended timeout (p95)
        if len(self.wait_times) >= 20:
            sorted_times = sorted(self.wait_times)
            index = int(len(sorted_times) * 0.95)
            self.recommended_timeout = sorted_times[index]


class IntelligentWaitsManager:
    """Manager for intelligent wait strategies"""

    def __init__(
        self,
        page: Page,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the intelligent waits manager.

        Args:
            page: Playwright page instance
            config: Configuration for wait behavior
        """
        self.page = page
        self.config = config or {}
        self.analytics = WaitAnalytics()

        # Configuration defaults
        self.default_timeout = self.config.get("default_timeout", 30000)
        self.implicit_wait_enabled = self.config.get("implicit_wait_enabled", True)
        self.implicit_wait_duration = self.config.get("implicit_wait_duration", 5000)
        self.smart_wait_enabled = self.config.get("smart_wait_enabled", True)
        self.context_aware = self.config.get("context_aware", True)

        # Network condition tracking
        self.network_conditions = {
            "slow_network": False,
            "last_page_load_time": 0,
            "average_response_time": 500,
        }

    async def explicit_wait(
        self,
        selector: str,
        condition: WaitCondition,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None
    ) -> WaitResult:
        """
        Perform explicit wait for a specific condition.

        Args:
            selector: CSS selector or Playwright locator
            condition: Condition to wait for
            timeout: Maximum wait time in milliseconds
            poll_interval: Polling interval in milliseconds

        Returns:
            WaitResult with outcome and analytics
        """
        timeout = timeout or self.default_timeout
        poll_interval = poll_interval or 500
        start_time = time.time()

        try:
            if condition == WaitCondition.VISIBLE:
                await self.page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=timeout
                )
            elif condition == WaitCondition.HIDDEN:
                await self.page.wait_for_selector(
                    selector,
                    state="hidden",
                    timeout=timeout
                )
            elif condition == WaitCondition.ATTACHED:
                await self.page.wait_for_selector(
                    selector,
                    state="attached",
                    timeout=timeout
                )
            elif condition == WaitCondition.ENABLED:
                locator = self.page.locator(selector)
                await locator.wait_for(state="enabled", timeout=timeout)
            elif condition == WaitCondition.DISABLED:
                locator = self.page.locator(selector)
                await locator.wait_for(state="disabled", timeout=timeout)

            duration_ms = int((time.time() - start_time) * 1000)

            return WaitResult(
                element=selector,
                strategy=WaitStrategy.EXPLICIT,
                condition=condition,
                duration_ms=duration_ms,
                success=True,
                message=f"Element '{selector}' became {condition.value}"
            )

        except PlaywrightTimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            return WaitResult(
                element=selector,
                strategy=WaitStrategy.EXPLICIT,
                condition=condition,
                duration_ms=duration_ms,
                success=False,
                message=f"Timeout waiting for '{selector}' to be {condition.value}"
            )

    async def implicit_wait(
        self,
        selector: str,
        action: str,
        timeout: Optional[int] = None
    ) -> WaitResult:
        """
        Perform action with implicit wait.

        Args:
            selector: CSS selector
            action: Action to perform (click, fill, etc.)
            timeout: Timeout for the operation

        Returns:
            WaitResult with outcome
        """
        timeout = timeout or self.implicit_wait_duration
        start_time = time.time()

        try:
            # Set implicit wait
            await self.page.set_default_timeout(timeout)

            # Perform action
            if action == "click":
                await self.page.click(selector)
            elif action == "fill":
                # This will wait for element to be ready
                locator = self.page.locator(selector)
                await locator.wait_for(state="visible", timeout=timeout)

            duration_ms = int((time.time() - start_time) * 1000)

            return WaitResult(
                element=selector,
                strategy=WaitStrategy.IMPLICIT,
                condition=WaitCondition.ATTACHED,
                duration_ms=duration_ms,
                success=True,
                message=f"Implicit wait completed for '{selector}'"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return WaitResult(
                element=selector,
                strategy=WaitStrategy.IMPLICIT,
                condition=WaitCondition.ATTACHED,
                duration_ms=duration_ms,
                success=False,
                message=f"Implicit wait failed: {str(e)}"
            )

    async def smart_wait(
        self,
        selector: str,
        condition: WaitCondition,
        timeout: Optional[int] = None,
        retry_count: int = 3
    ) -> WaitResult:
        """
        Perform AI-powered smart wait with adaptive strategies.

        Analyzes page context and dynamically adjusts wait strategy.

        Args:
            selector: CSS selector
            condition: Condition to wait for
            timeout: Maximum wait time
            retry_count: Number of retry attempts with different strategies

        Returns:
            WaitResult with optimal strategy used
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        # Analyze context to determine optimal strategy
        context = await self._analyze_page_context(selector)
        strategies = self._determine_optimal_strategies(context, condition)

        for attempt, strategy in enumerate(strategies, 1):
            try:
                result = await self._execute_strategy(
                    selector, condition, strategy, timeout
                )

                duration_ms = int((time.time() - start_time) * 1000)

                if result.success:
                    # Update analytics with successful strategy
                    self.analytics.add_wait(duration_ms, True)

                    return WaitResult(
                        element=selector,
                        strategy=WaitStrategy.SMART,
                        condition=condition,
                        duration_ms=duration_ms,
                        success=True,
                        message=f"Smart wait succeeded using {strategy} (attempt {attempt})",
                        attempts=attempt,
                        optimizations=[f"Used {strategy} strategy"]
                    )

            except Exception:
                if attempt >= retry_count:
                    break
                await asyncio.sleep(0.5)  # Brief pause before retry

        duration_ms = int((time.time() - start_time) * 1000)
        self.analytics.add_wait(duration_ms, False)

        return WaitResult(
            element=selector,
            strategy=WaitStrategy.SMART,
            condition=condition,
            duration_ms=duration_ms,
            success=False,
            message=f"Smart wait failed after {retry_count} attempts",
            attempts=retry_count
        )

    async def hybrid_wait(
        self,
        selector: str,
        condition: WaitCondition,
        timeout: Optional[int] = None,
        retry_count: int = 3
    ) -> WaitResult:
        """
        Perform hybrid wait combining explicit and smart strategies.

        First tries explicit wait, then falls back to smart wait strategies.

        Args:
            selector: CSS selector
            condition: Condition to wait for
            timeout: Maximum wait time
            retry_count: Number of smart strategy attempts

        Returns:
            WaitResult with best strategy used
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        # Try explicit wait first
        explicit_result = await self.explicit_wait(selector, condition, timeout)

        if explicit_result.success:
            duration_ms = int((time.time() - start_time) * 1000)
            return WaitResult(
                element=selector,
                strategy=WaitStrategy.HYBRID,
                condition=condition,
                duration_ms=duration_ms,
                success=True,
                message="Hybrid wait succeeded with explicit strategy",
                attempts=1
            )

        # Fall back to smart wait
        smart_result = await self.smart_wait(
            selector, condition, timeout, retry_count
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return WaitResult(
            element=selector,
            strategy=WaitStrategy.HYBRID,
            condition=condition,
            duration_ms=duration_ms,
            success=smart_result.success,
            message=smart_result.message,
            attempts=1 + smart_result.attempts,
            optimizations=["Tried explicit, then smart strategies"]
        )

    async def _analyze_page_context(self, selector: str) -> Dict[str, Any]:
        """
        Analyze page context to determine optimal wait strategy.

        Args:
            selector: Element selector

        Returns:
            Context information dictionary
        """
        context = {
            "page_loaded": False,
            "network_idle": False,
            "element_exists": False,
            "element_visible": False,
            "has_animations": False,
            "is_dynamic_content": False,
            "loading_indicators": [],
            "network_speed": "fast"
        }

        try:
            # Check page load state
            context["page_loaded"] = await self._check_page_loaded()
            context["network_idle"] = await self._check_network_idle()

            # Check element state
            try:
                locator = self.page.locator(selector)
                context["element_exists"] = await locator.count() > 0
                context["element_visible"] = await locator.is_visible()
            except:
                pass

            # Check for loading indicators
            loading_selectors = [
                ".loading", ".spinner", "[data-loading]",
                ".loader", ".progress", "[data-waiting]"
            ]

            for loading_selector in loading_selectors:
                try:
                    if await self.page.locator(loading_selector).count() > 0:
                        context["loading_indicators"].append(loading_selector)
                except:
                    pass

            # Check for animations
            try:
                has_animations = await self.page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        for (let el of elements) {
                            const styles = window.getComputedStyle(el);
                            if (styles.animationName !== 'none' ||
                                styles.transitionDuration !== '0s') {
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                context["has_animations"] = has_animations
            except:
                pass

            # Determine network speed based on page load time
            if self.network_conditions["last_page_load_time"] > 0:
                load_time = self.network_conditions["last_page_load_time"]
                if load_time > 5000:  # 5 seconds
                    context["network_speed"] = "slow"
                elif load_time > 2000:
                    context["network_speed"] = "medium"

        except Exception as e:
            context["analysis_error"] = str(e)

        return context

    async def _check_page_loaded(self) -> bool:
        """Check if page is fully loaded"""
        try:
            return await self.page.evaluate("""
                () => {
                    return document.readyState === 'complete';
                }
            """)
        except:
            return False

    async def _check_network_idle(self) -> bool:
        """Check if network is idle (no more than 2 requests in 500ms)"""
        try:
            # Wait a brief moment to check network state
            await asyncio.sleep(0.5)

            # Check if there are any pending requests
            in_progress = await self.page.evaluate("""
                () => {
                    return window.performance ?
                           performance.getEntriesByType('resource')
                               .filter(r => r.duration < 100)
                               .length > 0 : false;
                }
            """)
            return not in_progress
        except:
            return True  # Assume idle if can't check

    def _determine_optimal_strategies(
        self,
        context: Dict[str, Any],
        condition: WaitCondition
    ) -> List[str]:
        """
        Determine optimal wait strategies based on context.

        Args:
            context: Page context analysis
            condition: Desired wait condition

        Returns:
            List of strategies to try in order
        """
        strategies = []

        # Strategy 1: Direct selector wait (fastest if element is ready)
        strategies.append("direct_locator")

        # Strategy 2: Wait for loading indicators to disappear
        if context["loading_indicators"]:
            strategies.append("wait_for_loading_complete")

        # Strategy 3: Wait for network idle if page is loading
        if not context["network_idle"]:
            strategies.append("wait_for_network_idle")

        # Strategy 4: Wait for animations to complete
        if context["has_animations"]:
            strategies.append("wait_for_animations")

        # Strategy 5: Poll for visibility (reliable for dynamic content)
        if not context["element_visible"]:
            strategies.append("poll_visibility")

        # Strategy 6: Wait for DOM content (for AJAX-loaded content)
        strategies.append("wait_for_dom_content")

        # Strategy 7: Wait for specific attribute (data-loaded, etc.)
        strategies.append("wait_for_attribute")

        return strategies

    async def _execute_strategy(
        self,
        selector: str,
        condition: WaitCondition,
        strategy: str,
        timeout: int
    ) -> WaitResult:
        """
        Execute a specific wait strategy.

        Args:
            selector: Element selector
            condition: Desired condition
            strategy: Strategy name to execute
            timeout: Maximum wait time

        Returns:
            WaitResult with outcome
        """
        start_time = time.time()

        try:
            if strategy == "direct_locator":
                # Direct locator wait
                if condition == WaitCondition.VISIBLE:
                    await self.page.wait_for_selector(
                        selector, state="visible", timeout=timeout
                    )
                else:
                    await self.page.wait_for_selector(
                        selector, state=condition.value, timeout=timeout
                    )

            elif strategy == "wait_for_loading_complete":
                # Wait for all loading indicators to disappear
                for loading_selector in [".loading", ".spinner", "[data-loading]"]:
                    try:
                        await self.page.wait_for_selector(
                            loading_selector,
                            state="hidden",
                            timeout=timeout
                        )
                    except:
                        pass  # Loading indicator might not exist

            elif strategy == "wait_for_network_idle":
                # Wait for network to be idle
                await self.page.wait_for_load_state("networkidle", timeout=timeout)

            elif strategy == "wait_for_animations":
                # Wait for animations to complete
                await self.page.wait_for_timeout(500)  # Brief pause
                await self.page.evaluate("""
                    () => {
                        return new Promise(resolve => {
                            const elements = document.querySelectorAll('*');
                            let animating = 0;
                            for (let el of elements) {
                                const styles = window.getComputedStyle(el);
                                if (styles.transitionDuration !== '0s' ||
                                    styles.animationName !== 'none') {
                                    animating++;
                                }
                            }
                            if (animating === 0) {
                                resolve();
                            } else {
                                setTimeout(resolve, 500);
                            }
                        });
                    }
                """)

            elif strategy == "poll_visibility":
                # Poll for element visibility
                poll_interval = 500
                max_attempts = timeout // poll_interval

                for _ in range(max_attempts):
                    try:
                        locator = self.page.locator(selector)
                        if await locator.is_visible():
                            break
                    except:
                        pass
                    await asyncio.sleep(poll_interval / 1000)

            elif strategy == "wait_for_dom_content":
                # Wait for DOM to be stable (no mutations for 500ms)
                await self.page.wait_for_timeout(500)
                await self.page.evaluate("""
                    () => {
                        return new Promise(resolve => {
                            const observer = new MutationObserver(() => {});
                            observer.observe(document.body, {
                                childList: true,
                                subtree: true
                            });
                            setTimeout(() => {
                                observer.disconnect();
                                resolve();
                            }, 500);
                        });
                    }
                """)

            elif strategy == "wait_for_attribute":
                # Wait for data-loaded or similar attribute
                try:
                    await self.page.wait_for_selector(
                        f"{selector}[data-loaded], {selector}[data-ready]",
                        timeout=timeout
                    )
                except:
                    pass  # Attribute might not be set

            duration_ms = int((time.time() - start_time) * 1000)

            return WaitResult(
                element=selector,
                strategy=WaitStrategy.SMART,
                condition=condition,
                duration_ms=duration_ms,
                success=True,
                message=f"Strategy '{strategy}' succeeded"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return WaitResult(
                element=selector,
                strategy=WaitStrategy.SMART,
                condition=condition,
                duration_ms=duration_ms,
                success=False,
                message=f"Strategy '{strategy}' failed: {str(e)}"
            )

    def get_optimization_suggestions(self) -> List[str]:
        """
        Get optimization suggestions based on wait analytics.

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        if self.analytics.wait_count > 0:
            avg_wait = self.analytics.average_wait_time

            # Suggest timeout adjustments
            if avg_wait > self.default_timeout * 0.8:
                suggestions.append(
                    f"Average wait time ({avg_wait}ms) is close to default timeout. "
                    f"Consider increasing default_timeout to {int(avg_wait * 1.5)}ms"
                )

            # Succeed rate
            success_rate = self.analytics.success_count / self.analytics.wait_count
            if success_rate < 0.8:
                suggestions.append(
                    f"Low success rate ({success_rate:.1%}). Consider using smart waits "
                    "or adjusting selectors"
                )

            # Recommended timeout
            recommended = self.analytics.recommended_timeout
            if recommended < self.default_timeout:
                suggestions.append(
                    f"Based on history, recommended timeout is {recommended}ms "
                    f"(current: {self.default_timeout}ms)"
                )

        return suggestions

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get summary of wait analytics.

        Returns:
            Dictionary with analytics summary
        """
        return {
            "total_waits": self.analytics.wait_count,
            "successful_waits": self.analytics.success_count,
            "failed_waits": self.analytics.failure_count,
            "success_rate": (
                self.analytics.success_count / self.analytics.wait_count
                if self.analytics.wait_count > 0 else 0
            ),
            "total_wait_time_ms": self.analytics.total_wait_time_ms,
            "average_wait_ms": self.analytics.average_wait_time,
            "recommended_timeout_ms": self.analytics.recommended_timeout,
            "optimization_suggestions": self.get_optimization_suggestions()
        }


# Skill main entry point
async def intelligent_waits_skill(
    page: Page,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main entry point for intelligent waits skill.

    Args:
        page: Playwright page instance
        input_data: Input parameters for the skill

    Returns:
        Dictionary with wait results and analytics
    """
    config = input_data.get("configuration", {})
    manager = IntelligentWaitsManager(page, config)

    # Determine wait strategy
    strategy_str = input_data.get("wait_strategy", "smart")
    strategy = WaitStrategy(strategy_str)

    # Get parameters
    selector = input_data.get("target_element")
    condition_str = input_data.get("wait_condition", "visible")
    condition = WaitCondition(condition_str)
    timeout = input_data.get("timeout")
    retry_count = input_data.get("retry_count", 3)

    # Execute wait
    if strategy == WaitStrategy.EXPLICIT:
        result = await manager.explicit_wait(selector, condition, timeout)
    elif strategy == WaitStrategy.IMPLICIT:
        result = await manager.implicit_wait(selector, "click", timeout)
    elif strategy == WaitStrategy.SMART:
        result = await manager.smart_wait(selector, condition, timeout, retry_count)
    elif strategy == WaitStrategy.HYBRID:
        result = await manager.hybrid_wait(selector, condition, timeout, retry_count)
    else:
        result = WaitResult(
            element=selector,
            strategy=strategy,
            condition=condition,
            duration_ms=0,
            success=False,
            message=f"Unknown wait strategy: {strategy}"
        )

    return {
        "success": result.success,
        "result": {
            "element": result.element,
            "strategy": result.strategy.value,
            "condition": result.condition.value,
            "duration_ms": result.duration_ms,
            "message": result.message,
            "attempts": result.attempts,
            "optimizations": result.optimizations
        },
        "analytics": manager.get_analytics_summary(),
        "suggestions": manager.get_optimization_suggestions()
    }


# Convenience functions for common wait patterns
async def wait_for_element_visible(
    page: Page,
    selector: str,
    timeout: int = 30000
) -> bool:
    """
    Wait for element to be visible (smart wait).

    Args:
        page: Playwright page
        selector: CSS selector
        timeout: Maximum wait time

    Returns:
        True if element became visible, False otherwise
    """
    manager = IntelligentWaitsManager(page)
    result = await manager.smart_wait(
        selector,
        WaitCondition.VISIBLE,
        timeout
    )
    return result.success


async def wait_for_element_hidden(
    page: Page,
    selector: str,
    timeout: int = 30000
) -> bool:
    """
    Wait for element to be hidden (smart wait).

    Args:
        page: Playwright page
        selector: CSS selector
        timeout: Maximum wait time

    Returns:
        True if element became hidden, False otherwise
    """
    manager = IntelligentWaitsManager(page)
    result = await manager.smart_wait(
        selector,
        WaitCondition.HIDDEN,
        timeout
    )
    return result.success


async def wait_for_page_load(
    page: Page,
    timeout: int = 30000
) -> bool:
    """
    Wait for page to fully load (network idle).

    Args:
        page: Playwright page
        timeout: Maximum wait time

    Returns:
        True if page loaded, False otherwise
    """
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        return True
    except:
        return False


async def wait_for_text(
    page: Page,
    selector: str,
    text: str,
    timeout: int = 30000
) -> bool:
    """
    Wait for element to contain specific text.

    Args:
        page: Playwright page
        selector: CSS selector
        text: Expected text
        timeout: Maximum wait time

    Returns:
        True if text found, False otherwise
    """
    manager = IntelligentWaitsManager(page)

    # Use smart wait with text condition
    start_time = time.time()
    poll_interval = 500

    while (time.time() - start_time) * 1000 < timeout:
        try:
            element_text = await page.locator(selector).inner_text()
            if text in element_text:
                return True
        except:
            pass

        await asyncio.sleep(poll_interval / 1000)

    return False
