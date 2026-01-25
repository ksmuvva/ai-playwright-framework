"""
Base Page class for the demo project.
Provides common functionality for all page objects.
"""

from playwright.async_api import Page, Locator, expect
import asyncio


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        """Initialize base page with Playwright page instance."""
        self.page = page
        self.base_url = "https://demo.playwright.dev"

    async def navigate(self, url: str = ""):
        """Navigate to a URL."""
        full_url = f"{self.base_url}{url}"
        await self.page.goto(full_url)
        await self.page.wait_for_load_state("networkidle")

    async def wait_for_element(self, selector: str, timeout: int = 5000):
        """Wait for an element to be visible."""
        await self.page.wait_for_selector(selector, timeout=timeout)

    async def click_element(self, selector: str):
        """Click an element with wait."""
        await self.wait_for_element(selector)
        await self.page.click(selector)

    async def fill_text(self, selector: str, text: str):
        """Fill text into an input field."""
        await self.wait_for_element(selector)
        await self.page.fill(selector, text)

    async def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        await self.wait_for_element(selector)
        return await self.page.inner_text(selector)

    async def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        try:
            await self.wait_for_element(selector, timeout=2000)
            return True
        except:
            return False

    async def take_screenshot(self, name: str):
        """Take a screenshot."""
        await self.page.screenshot(path=f"reports/{name}.png")

    async def wait_for_navigation(self):
        """Wait for navigation to complete."""
        await self.page.wait_for_load_state("networkidle")
