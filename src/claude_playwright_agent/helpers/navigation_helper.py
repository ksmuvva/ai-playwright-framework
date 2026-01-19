"""
Navigation Helper Module.

Provides reusable navigation utilities for test automation.
Supports URL navigation, app switching, and page load management.
"""

from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class NavigationHelper:
    """
    Navigation helper for managing page navigation and app switching.

    Features:
    - URL navigation
    - Back/forward navigation
    - App switching
    - Page load waiting
    - Navigation timeout handling
    """

    DEFAULT_TIMEOUT = 30000  # milliseconds

    def __init__(self, default_timeout: int = None):
        """
        Initialize the navigation helper.

        Args:
            default_timeout: Default timeout for navigation operations
        """
        self.default_timeout = default_timeout or self.DEFAULT_TIMEOUT

    async def navigate_to(
        self, page: Page, url: str, wait_until: str = "networkidle", timeout: Optional[int] = None
    ) -> bool:
        """
        Navigate to a specific URL.

        Args:
            page: Playwright page object
            url: URL to navigate to
            wait_until: Load state to wait for
            timeout: Timeout in milliseconds

        Returns:
            True if navigation successful
        """
        timeout = timeout or self.default_timeout
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    async def navigate_back(self, page: Page) -> bool:
        """
        Navigate back to the previous page.

        Args:
            page: Playwright page object

        Returns:
            True if navigation successful
        """
        try:
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False

    async def navigate_forward(self, page: Page) -> bool:
        """
        Navigate forward to the next page.

        Args:
            page: Playwright page object

        Returns:
            True if navigation successful
        """
        try:
            await page.go_forward()
            await page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False

    async def navigate_to_app(
        self, page: Page, base_url: str, app_name: str, app_path: Optional[str] = None
    ) -> bool:
        """
        Navigate to a specific application or module.

        Args:
            page: Playwright page object
            base_url: Base URL of the application
            app_name: Name of the application/module
            app_path: Specific path for the app (optional)

        Returns:
            True if navigation successful
        """
        if app_path:
            app_url = f"{base_url}/{app_path}"
        else:
            app_url = f"{base_url}/{app_name.lower().replace(' ', '-')}"

        return await self.navigate_to(page, app_url)

    async def wait_for_page_load(self, page: Page, timeout: Optional[int] = None) -> bool:
        """
        Wait for the page to fully load.

        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds

        Returns:
            True if page loaded successfully
        """
        timeout = timeout or self.default_timeout
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    async def wait_for_element(
        self, page: Page, selector: str, state: str = "visible", timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for a specific element to be available.

        Args:
            page: Playwright page object
            selector: CSS selector or locator
            state: Element state to wait for (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds

        Returns:
            True if element found within timeout
        """
        timeout = timeout or self.default_timeout
        try:
            await page.wait_for_selector(selector, state=state, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    async def get_current_url(self, page: Page) -> str:
        """
        Get the current page URL.

        Args:
            page: Playwright page object

        Returns:
            Current URL string
        """
        return page.url

    async def is_url_matches(self, page: Page, pattern: str) -> bool:
        """
        Check if current URL matches a pattern.

        Args:
            page: Playwright page object
            pattern: URL pattern to match (supports wildcards)

        Returns:
            True if URL matches pattern
        """
        current_url = await self.get_current_url(page)
        if "*" in pattern:
            import fnmatch

            return fnmatch.fnmatch(current_url, pattern)
        return pattern in current_url

    async def reload_page(self, page: Page) -> bool:
        """
        Reload the current page.

        Args:
            page: Playwright page object

        Returns:
            True if reload successful
        """
        try:
            await page.reload()
            await page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False
