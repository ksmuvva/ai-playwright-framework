"""
Wait Manager Module (AI-Powered).

Provides intelligent wait management for test automation.
Uses AI to determine optimal wait strategies and Power Apps loading detection.
"""

import asyncio
from typing import Any, Callable, Dict, Optional, Union
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass, field
from enum import Enum


class WaitType(Enum):
    """Types of waits available."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    ATTACHED = "attached"
    DETACHED = "detached"
    ENABLED = "enabled"
    DISABLED = "disabled"
    TEXT_PRESENT = "text_present"
    NETWORK_IDLE = "networkidle"


@dataclass
class WaitConfig:
    """Configuration for wait operations."""

    timeout: int = 30000
    interval: int = 500
    retry_on_timeout: bool = False
    max_retries: int = 3
    power_apps_mode: bool = False


@dataclass
class WaitMetrics:
    """Metrics for wait performance tracking."""

    total_waits: int = 0
    successful_waits: int = 0
    failed_waits: int = 0
    average_wait_time: float = 0.0
    wait_times: list = field(default_factory=list)


class WaitManager:
    """
    AI-powered wait manager for intelligent element waiting.

    Features:
    - Smart wait type selection
    - Power Apps loading detection
    - Adaptive wait times
    - Performance metrics tracking
    - Context-aware wait strategies
    """

    DEFAULT_TIMEOUT = 30000  # milliseconds
    POWER_APPS_TIMEOUT = 60000  # milliseconds for Power Apps

    def __init__(self, config: Optional[WaitConfig] = None):
        """
        Initialize the wait manager.

        Args:
            config: Wait configuration
        """
        self.config = config or WaitConfig()
        self.metrics = WaitMetrics()

    async def smart_wait(
        self,
        page: Page,
        condition: Callable[[], Any],
        timeout: Optional[int] = None,
        retry_on_timeout: bool = None,
    ) -> bool:
        """
        Wait for a condition to be true with smart timeout handling.

        Args:
            page: Playwright page object
            condition: Callable that returns truthy value when condition met
            timeout: Maximum time to wait in milliseconds
            retry_on_timeout: Whether to retry with different strategies

        Returns:
            True if condition met within timeout
        """
        timeout = timeout or self.config.timeout
        retry_on_timeout = (
            retry_on_timeout if retry_on_timeout is not None else self.config.retry_on_timeout
        )

        self.metrics.total_waits += 1
        start_time = asyncio.get_event_loop().time()

        try:
            await asyncio.wait_for(
                self._wait_for_condition(page, condition), timeout=timeout / 1000
            )
            self._record_success(timeout)
            return True

        except PlaywrightTimeoutError:
            self.metrics.failed_waits += 1
            if retry_on_timeout:
                return await self._retry_with_adaptive_wait(page, condition, timeout)
            return False

        except Exception:
            self.metrics.failed_waits += 1
            return False

    async def _wait_for_condition(self, page: Page, condition: Callable[[], Any]) -> None:
        """Wait for condition to be truthy."""
        while not condition():
            await asyncio.sleep(0.1)

    async def _retry_with_adaptive_wait(
        self, page: Page, condition: Callable[[], Any], original_timeout: int
    ) -> bool:
        """Retry with adaptive wait strategies."""
        strategies = [
            ("Checking with extended timeout", original_timeout * 2),
            ("Trying with shorter polling interval", original_timeout),
            ("Checking element state", original_timeout // 2),
        ]

        for strategy_name, strategy_timeout in strategies:
            try:
                await asyncio.wait_for(
                    self._wait_for_condition(page, condition), timeout=strategy_timeout / 1000
                )
                self._record_success(strategy_timeout)
                return True
            except Exception:
                continue

        return False

    async def wait_for_element(
        self,
        page: Page,
        selector: str,
        wait_type: WaitType = WaitType.VISIBLE,
        timeout: Optional[int] = None,
        state: Optional[str] = None,
    ) -> bool:
        """
        Wait for an element to be in a specific state.

        Args:
            page: Playwright page object
            selector: CSS selector or locator string
            wait_type: Type of wait to perform
            timeout: Maximum time to wait
            state: Element state (for compatibility)

        Returns:
            True if element found in desired state
        """
        timeout = timeout or self._get_timeout_for_type(wait_type)

        if state:
            wait_type = WaitType(state)

        self.metrics.total_waits += 1

        try:
            state_value = wait_type.value
            await page.wait_for_selector(selector, state=state_value, timeout=timeout)
            self._record_success(timeout)
            return True

        except PlaywrightTimeoutError:
            self.metrics.failed_waits += 1
            return False

    def _get_timeout_for_type(self, wait_type: WaitType) -> int:
        """Get appropriate timeout based on wait type."""
        timeouts = {
            WaitType.VISIBLE: 30000,
            WaitType.HIDDEN: 10000,
            WaitType.ATTACHED: 15000,
            WaitType.DETACHED: 10000,
            WaitType.ENABLED: 20000,
            WaitType.DISABLED: 10000,
            WaitType.TEXT_PRESENT: 30000,
            WaitType.NETWORK_IDLE: 60000,
        }
        return timeouts.get(wait_type, self.DEFAULT_TIMEOUT)

    async def wait_for_network_idle(self, page: Page, timeout: int = 30000) -> bool:
        """
        Wait for network to be idle (no pending requests).

        Args:
            page: Playwright page object
            timeout: Maximum time to wait

        Returns:
            True if network idle within timeout
        """
        self.metrics.total_waits += 1

        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            self._record_success(timeout)
            return True
        except PlaywrightTimeoutError:
            self.metrics.failed_waits += 1
            return False

    async def wait_for_power_apps_load(self, page: Page, timeout: Optional[int] = None) -> bool:
        """
        Wait for Power Apps to fully load.

        Uses multiple indicators to determine if Power Apps is ready:
        - No active spinners/loading indicators
        - Main canvas is visible
        - No pending network requests

        Args:
            page: Playwright page object
            timeout: Maximum time to wait

        Returns:
            True if Power Apps loaded successfully
        """
        timeout = timeout or self.POWER_APPS_TIMEOUT

        self.metrics.total_waits += 1

        power_apps_indicators = [
            "[role='application']",
            ".canvas-app",
            "[data-powerapps]",
            ".powerapps-canvas",
        ]

        loading_indicators = [
            ".spinner",
            ".loading",
            "[aria-busy='true']",
            ".powerapps-loader",
        ]

        try:
            for indicator in power_apps_indicators:
                try:
                    element = page.locator(indicator).first
                    if await element.is_visible(timeout=5000):
                        break
                except Exception:
                    continue
            else:
                return False

            for loading in loading_indicators:
                try:
                    if await page.locator(loading).first.is_visible(timeout=1000):
                        await page.wait_for_selector(loading, state="hidden", timeout=timeout)
                except Exception:
                    pass

            await page.wait_for_load_state("networkidle", timeout=timeout)
            self._record_success(timeout)
            return True

        except PlaywrightTimeoutError:
            self.metrics.failed_waits += 1
            return False

    async def adaptive_wait(
        self, page: Page, selector: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        AI decides optimal wait type based on context.

        Args:
            page: Playwright page object
            selector: Element selector
            context: Context information about the element

        Returns:
            True if wait successful
        """
        context = context or {}

        element_type = context.get("element_type", "")
        is_critical = context.get("critical", False)
        has_dynamic_content = context.get("dynamic", False)

        if is_critical:
            wait_type = WaitType.VISIBLE
            timeout = (
                self.POWER_APPS_TIMEOUT if context.get("power_apps") else self.DEFAULT_TIMEOUT * 2
            )
        elif has_dynamic_content:
            wait_type = WaitType.ATTACHED
            timeout = self.DEFAULT_TIMEOUT
        elif "button" in element_type.lower() or "input" in element_type.lower():
            wait_type = WaitType.ENABLED
            timeout = self.DEFAULT_TIMEOUT
        else:
            wait_type = WaitType.VISIBLE
            timeout = self.DEFAULT_TIMEOUT

        return await self.wait_for_element(page, selector, wait_type, timeout)

    def _record_success(self, time_taken: int) -> None:
        """Record a successful wait."""
        self.metrics.successful_waits += 1
        self.metrics.wait_times.append(time_taken)
        if self.metrics.wait_times:
            self.metrics.average_wait_time = sum(self.metrics.wait_times) / len(
                self.metrics.wait_times
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get wait performance metrics."""
        return {
            "total_waits": self.metrics.total_waits,
            "successful_waits": self.metrics.successful_waits,
            "failed_waits": self.metrics.failed_waits,
            "success_rate": (
                self.metrics.successful_waits / self.metrics.total_waits * 100
                if self.metrics.total_waits > 0
                else 0
            ),
            "average_wait_time_ms": self.metrics.average_wait_time,
        }

    def reset_metrics(self) -> None:
        """Reset wait metrics."""
        self.metrics = WaitMetrics()
