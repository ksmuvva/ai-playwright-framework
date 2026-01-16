"""
Intelligent Waits Skill Package

This skill provides comprehensive wait strategies for test automation:
- Explicit waits: Wait for specific conditions
- Implicit waits: Global wait configuration
- Smart waits: AI-powered optimal wait detection
- Hybrid waits: Combine multiple strategies
- Dynamic timeout adjustment: Based on network conditions

Example usage:
    from playwright.async_api import async_playwright
    from skills.builtins.e6_6_intelligent_waits import (
        IntelligentWaitsManager,
        wait_for_element_visible,
        wait_for_page_load
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Use convenience functions
        await wait_for_page_load(page)
        await wait_for_element_visible(page, "#submit-button")

        # Or use the manager directly
        manager = IntelligentWaitsManager(page)
        result = await manager.smart_wait("#modal", WaitCondition.VISIBLE)
"""

from .main import (
    WaitCondition,
    WaitStrategy,
    WaitResult,
    WaitAnalytics,
    IntelligentWaitsManager,
    intelligent_waits_skill,
    wait_for_element_visible,
    wait_for_element_hidden,
    wait_for_page_load,
    wait_for_text,
)

__all__ = [
    "WaitCondition",
    "WaitStrategy",
    "WaitResult",
    "WaitAnalytics",
    "IntelligentWaitsManager",
    "intelligent_waits_skill",
    "wait_for_element_visible",
    "wait_for_element_hidden",
    "wait_for_page_load",
    "wait_for_text",
]

__version__ = "1.0.0"
__author__ = "Claude Playwright Agent"
