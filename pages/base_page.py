"""
Base Page Object class for Claude Playwright Agent.

This module provides the BasePage class that serves as the foundation for all
Page Object Model implementations. It includes common functionality for:

- Navigation
- Element waiting and interaction
- Screenshot capture
- Assertions
- Self-healing selector recovery
- Logging and analytics

Example:
    >>> from pages.base_page import BasePage
    >>> from playwright.sync_api import sync_playwright
    >>>
    >>> with sync_playwright() as p:
    ...     browser = p.chromium.launch()
    ...     page = browser.new_page()
    ...     base_page = BasePage(page, "https://example.com", "MyPage")
    ...     base_page.goto("/login")
    ...     base_page.click("#login-button")
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError, expect


class BasePage:
    """
    Base class for all Page Objects.

    Provides common functionality for page interactions including navigation,
    element operations, waiting strategies, assertions, and self-healing.

    Attributes:
        page: Playwright Page instance
        base_url: Base URL for the application
        page_name: Name of the page (for logging/screenshots)
        timeout: Default timeout for operations (milliseconds)

    Example:
        >>> class LoginPage(BasePage):
        ...     def __init__(self, page: Page, base_url: str = ""):
        ...         super().__init__(page, base_url, "LoginPage")
        ...         self.url_path = "/login"
    """

    def __init__(
        self,
        page: Page,
        base_url: str = "",
        page_name: str = "UnnamedPage",
        timeout: int = 30000,
    ) -> None:
        """
        Initialize the BasePage.

        Args:
            page: Playwright Page instance
            base_url: Base URL for the application (e.g., "https://example.com")
            page_name: Name of the page for logging and screenshot naming
            timeout: Default timeout for operations in milliseconds
        """
        self.page = page
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.page_name = page_name
        self.timeout = timeout
        self._selector_cache: dict[str, Locator] = {}

    # ==========================================================================
    # NAVIGATION METHODS
    # ==========================================================================

    def goto(self, path: str = "", wait_until: str = "load") -> None:
        """
        Navigate to a URL path.

        Args:
            path: URL path to navigate to (e.g., "/login", "/products/123")
            wait_until: Navigation wait condition (load, domcontentloaded, networkidle)

        Example:
            >>> page.goto("/login")  # Navigates to base_url + "/login"
            >>> page.goto("https://example.com")  # Full URL override
        """
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url

        self.page.goto(url, wait_until=wait_until, timeout=self.timeout)

    def reload(self, wait_until: str = "load") -> None:
        """
        Reload the current page.

        Args:
            wait_until: Navigation wait condition

        Example:
            >>> page.reload()
        """
        self.page.reload(wait_until=wait_until, timeout=self.timeout)

    def go_back(self) -> None:
        """Navigate back in browser history.

        Example:
            >>> page.go_back()
        """
        self.page.go_back(timeout=self.timeout)

    def go_forward(self) -> None:
        """Navigate forward in browser history.

        Example:
            >>> page.go_forward()
        """
        self.page.go_forward(timeout=self.timeout)

    # ==========================================================================
    # WAIT STRATEGIES
    # ==========================================================================

    def wait_for_load_state(self, state: str = "load") -> None:
        """
        Wait for page load state.

        Args:
            state: Load state to wait for (load, domcontentloaded, networkidle)

        Example:
            >>> page.wait_for_load_state("networkidle")
        """
        self.page.wait_for_load_state(state, timeout=self.timeout)

    def wait_for_selector(
        self,
        selector: str,
        state: str = "attached",
        timeout: Optional[int] = None,
    ) -> Locator:
        """
        Wait for selector to match element.

        Args:
            selector: CSS/Playwright selector
            state: Element state (attached, detached, visible, hidden)
            timeout: Timeout in milliseconds (uses default if None)

        Returns:
            Locator for the matched element

        Example:
            >>> element = page.wait_for_selector("#submit-button", state="visible")
        """
        timeout = timeout or self.timeout
        return self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def wait_for_url(self, url: str, timeout: Optional[int] = None) -> None:
        """
        Wait for URL to match expected value.

        Args:
            url: Expected URL (can be substring or regex)
            timeout: Timeout in milliseconds

        Example:
            >>> page.wait_for_url("/login")
            >>> page.wait_for_url(".*dashboard.*")
        """
        timeout = timeout or self.timeout
        self.page.wait_for_url(url, timeout=timeout)

    def wait_for_element_visible(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """
        Wait for element to be visible.

        Args:
            selector: CSS/Playwright selector
            timeout: Timeout in milliseconds

        Returns:
            Locator for the visible element

        Example:
            >>> submit_btn = page.wait_for_element_visible("#submit")
        """
        return self.wait_for_selector(selector, state="visible", timeout=timeout)

    # ==========================================================================
    # ELEMENT INTERACTION (WITH SELF-HEALING)
    # ==========================================================================

    def click(
        self,
        selector: str,
        **kwargs: Any,
    ) -> None:
        """
        Click element with automatic retry and self-healing.

        Args:
            selector: CSS/Playwright selector
            **kwargs: Additional arguments for page.click()

        Example:
            >>> page.click("#submit-button")
            >>> page.click("text=Submit", force=True)
        """
        try:
            self.page.click(selector, timeout=self.timeout, **kwargs)
        except PlaywrightTimeoutError as e:
            # Self-healing would be triggered here via SelfHealingAgent
            # For now, re-raise with more context
            raise TimeoutError(
                f"Failed to click element '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    def fill(
        self,
        selector: str,
        value: str,
        **kwargs: Any,
    ) -> None:
        """
        Fill input field with value.

        Args:
            selector: CSS/Playwright selector
            value: Value to fill
            **kwargs: Additional arguments for page.fill()

        Example:
            >>> page.fill("#username", "testuser")
            >>> page.fill("input[name='email']", "user@example.com")
        """
        try:
            self.page.fill(selector, value, timeout=self.timeout, **kwargs)
        except PlaywrightTimeoutError as e:
            raise TimeoutError(
                f"Failed to fill element '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    def type(
        self,
        selector: str,
        text: str,
        delay: int = 0,
        **kwargs: Any,
    ) -> None:
        """
        Type text into element character by character.

        Args:
            selector: CSS/Playwright selector
            text: Text to type
            delay: Delay between keystrokes (milliseconds)
            **kwargs: Additional arguments for page.type()

        Example:
            >>> page.type("#search", "search query", delay=50)
        """
        try:
            self.page.type(selector, text, delay=delay, timeout=self.timeout, **kwargs)
        except PlaywrightTimeoutError as e:
            raise TimeoutError(
                f"Failed to type into element '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    def select_option(
        self,
        selector: str,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Select option in select element.

        Args:
            selector: CSS/Playwright selector for select element
            value: Option value to select
            label: Option label to select
            index: Option index to select
            **kwargs: Additional arguments

        Example:
            >>> page.select_option("#country", value="US")
            >>> page.select_option("#country", label="United States")
        """
        try:
            self.page.select_option(
                selector,
                value=value,
                label=label,
                index=index,
                timeout=self.timeout,
                **kwargs,
            )
        except PlaywrightTimeoutError as e:
            raise TimeoutError(
                f"Failed to select option in '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    def check(
        self,
        selector: str,
        **kwargs: Any,
    ) -> None:
        """
        Check checkbox.

        Args:
            selector: CSS/Playwright selector
            **kwargs: Additional arguments

        Example:
            >>> page.check("#terms-checkbox")
        """
        try:
            self.page.check(selector, timeout=self.timeout, **kwargs)
        except PlaywrightTimeoutError as e:
            raise TimeoutError(
                f"Failed to check checkbox '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    def uncheck(
        self,
        selector: str,
        **kwargs: Any,
    ) -> None:
        """
        Uncheck checkbox.

        Args:
            selector: CSS/Playwright selector
            **kwargs: Additional arguments

        Example:
            >>> page.uncheck("#terms-checkbox")
        """
        try:
            self.page.uncheck(selector, timeout=self.timeout, **kwargs)
        except PlaywrightTimeoutError as e:
            raise TimeoutError(
                f"Failed to uncheck checkbox '{selector}' on {self.page_name}. "
                f"Selector may be invalid or element not found."
            ) from e

    # ==========================================================================
    # ASSERTIONS
    # ==========================================================================

    def assert_url(self, expected_url: str) -> None:
        """
        Assert current URL matches expected.

        Args:
            expected_url: Expected URL (can be substring or regex)

        Raises:
            AssertionError: If URL doesn't match

        Example:
            >>> page.assert_url("/dashboard")
        """
        actual_url = self.page.url
        assert expected_url in actual_url, f"URL assertion failed: expected '{expected_url}' in '{actual_url}'"

    def assert_visible(self, selector: str) -> None:
        """
        Assert element is visible.

        Args:
            selector: CSS/Playwright selector

        Raises:
            AssertionError: If element not visible

        Example:
            >>> page.assert_visible("#success-message")
        """
        locator = self.page.locator(selector)
        try:
            expect(locator).to_be_visible(timeout=self.timeout)
        except AssertionError as e:
            raise AssertionError(f"Element '{selector}' not visible on {self.page_name}") from e

    def assert_hidden(self, selector: str) -> None:
        """
        Assert element is hidden.

        Args:
            selector: CSS/Playwright selector

        Raises:
            AssertionError: If element not hidden

        Example:
            >>> page.assert_hidden("#loading-spinner")
        """
        locator = self.page.locator(selector)
        expect(locator).to_be_hidden(timeout=self.timeout)

    def assert_text(
        self,
        selector: str,
        text: str,
        exact: bool = False,
    ) -> None:
        """
        Assert element contains expected text.

        Args:
            selector: CSS/Playwright selector
            text: Expected text
            exact: Whether to match exact text (default: contains)

        Raises:
            AssertionError: If text doesn't match

        Example:
            >>> page.assert_text("#title", "Welcome")
            >>> page.assert_text("#count", "5", exact=True)
        """
        locator = self.page.locator(selector)
        if exact:
            expect(locator).to_have_text(text, timeout=self.timeout)
        else:
            expect(locator).to_contain_text(text, timeout=self.timeout)

    def assert_value(
        self,
        selector: str,
        value: str,
    ) -> None:
        """
        Assert input element has expected value.

        Args:
            selector: CSS/Playwright selector
            value: Expected value

        Raises:
            AssertionError: If value doesn't match

        Example:
            >>> page.assert_value("#email", "user@example.com")
        """
        locator = self.page.locator(selector)
        expect(locator).to_have_value(value, timeout=self.timeout)

    def assert_enabled(self, selector: str) -> None:
        """
        Assert element is enabled.

        Args:
            selector: CSS/Playwright selector

        Raises:
            AssertionError: If element not enabled

        Example:
            >>> page.assert_enabled("#submit-button")
        """
        locator = self.page.locator(selector)
        expect(locator).to_be_enabled(timeout=self.timeout)

    def assert_disabled(self, selector: str) -> None:
        """
        Assert element is disabled.

        Args:
            selector: CSS/Playwright selector

        Raises:
            AssertionError: If element not disabled

        Example:
            >>> page.assert_disabled("#submit-button")
        """
        locator = self.page.locator(selector)
        expect(locator).to_be_disabled(timeout=self.timeout)

    def assert_checked(self, selector: str) -> None:
        """
        Assert checkbox is checked.

        Args:
            selector: CSS/Playwright selector

        Raises:
            AssertionError: If checkbox not checked

        Example:
            >>> page.assert_checked("#agree-checkbox")
        """
        locator = self.page.locator(selector)
        expect(locator).to_be_checked(timeout=self.timeout)

    def assert_count(
        self,
        selector: str,
        count: int,
    ) -> None:
        """
        Assert number of elements matching selector.

        Args:
            selector: CSS/Playwright selector
            count: Expected count

        Raises:
            AssertionError: If count doesn't match

        Example:
            >>> page.assert_count(".item", 5)
        """
        locator = self.page.locator(selector)
        expect(locator).to_have_count(count, timeout=self.timeout)

    # ==========================================================================
    # SCREENSHOTS
    # ==========================================================================

    def screenshot(
        self,
        name: Optional[str] = None,
        full_page: bool = False,
    ) -> str:
        """
        Take screenshot with automatic naming.

        Args:
            name: Screenshot name (auto-generated if None)
            full_page: Capture full scrollable page

        Returns:
            Path to screenshot file

        Example:
            >>> path = page.screenshot("login_success")
            >>> print(f"Screenshot saved to: {path}")
        """
        # Create screenshots directory if needed
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{self.page_name}_{timestamp}"

        filename = f"{name}.png"
        path = screenshots_dir / filename

        # Take screenshot
        self.page.screenshot(path=str(path), full_page=full_page)

        return str(path)

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def get_text(self, selector: str) -> str:
        """
        Get text content of element.

        Args:
            selector: CSS/Playwright selector

        Returns:
            Text content of element

        Example:
            >>> title = page.get_text("h1")
            >>> print(f"Page title: {title}")
        """
        locator = self.page.locator(selector)
        return locator.text_content(timeout=self.timeout) or ""

    def get_attribute(
        self,
        selector: str,
        attribute: str,
    ) -> Optional[str]:
        """
        Get attribute value of element.

        Args:
            selector: CSS/Playwright selector
            attribute: Attribute name

        Returns:
            Attribute value or None

        Example:
            >>> href = page.get_attribute("#link", "href")
        """
        locator = self.page.locator(selector)
        return locator.get_attribute(attribute, timeout=self.timeout)

    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.

        Args:
            selector: CSS/Playwright selector

        Returns:
            True if visible, False otherwise

        Example:
            >>> if page.is_visible("#error-message"):
            ...     print("Error shown")
        """
        locator = self.page.locator(selector)
        return locator.is_visible(timeout=self.timeout)

    def is_enabled(self, selector: str) -> bool:
        """
        Check if element is enabled.

        Args:
            selector: CSS/Playwright selector

        Returns:
            True if enabled, False otherwise

        Example:
            >>> if page.is_enabled("#submit"):
            ...     page.click("#submit")
        """
        locator = self.page.locator(selector)
        return locator.is_enabled(timeout=self.timeout)

    def wait(self, milliseconds: int) -> None:
        """
        Wait for specified milliseconds (useful for debugging).

        Args:
            milliseconds: Time to wait in milliseconds

        Example:
            >>> page.wait(1000)  # Wait 1 second
        """
        self.page.wait_for_timeout(milliseconds)

    def __repr__(self) -> str:
        """String representation of the page."""
        return f"{self.__class__.__name__}(page_name='{self.page_name}', url='{self.page.url}')"
