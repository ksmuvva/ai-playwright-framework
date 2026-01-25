"""
Home Page for demo.playwright.dev
"""

from playwright.async_api import Page
from .base_page import BasePage


class HomePage(BasePage):
    """Home Page object for demo.playwright.dev."""

    def __init__(self, page: Page):
        """Initialize Home Page."""
        super().__init__(page)
        self.url = "/"

        # Selectors
        self.heading_selector = "h1"
        self.get_started_button = "a[href='/docs/intro']"
        self.search_input = "input[placeholder*='Search']"
        self.github_link = "a[href*='github']"
        self.menu_button = "button[aria-label*='Menu']"

    async def navigate_home(self):
        """Navigate to the home page."""
        await self.navigate(self.url)

    async def get_heading_text(self) -> str:
        """Get the main heading text."""
        return await self.get_text(self.heading_selector)

    async def click_get_started(self):
        """Click the Get Started button."""
        await self.click_element(self.get_started_button)

    async def search(self, query: str):
        """Search in the documentation."""
        await self.fill_text(self.search_input, query)
        await self.page.keyboard.press("Enter")

    async def go_to_github(self):
        """Navigate to GitHub repository."""
        await self.click_element(self.github_link)

    async def is_menu_visible(self) -> bool:
        """Check if menu button is visible."""
        return await self.is_visible(self.menu_button)
