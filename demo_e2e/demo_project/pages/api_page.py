"""
API Page for demo.playwright.dev
"""

from playwright.async_api import Page
from .base_page import BasePage


class APIPage(BasePage):
    """API Page object for demo.playwright.dev."""

    def __init__(self, page: Page):
        """Initialize API Page."""
        super().__init__(page)
        self.url = "/docs/api/class-playwright"

        # Selectors
        self.api_title = "h1"
        self.search_box = "input.DocSearch-Input"
        class_api_link = "a[href*='api/class-playwright']"

    async def navigate_to_api(self):
        """Navigate to API documentation."""
        await self.navigate(self.url)

    async def get_api_title(self) -> str:
        """Get the API page title."""
        return await self.get_text(self.api_title)

    async def search_api(self, query: str):
        """Search in API documentation."""
        if await self.is_visible(self.search_box):
            await self.fill_text(self.search_box, query)
            await asyncio.sleep(1)
