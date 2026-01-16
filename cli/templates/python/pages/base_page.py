"""
Base Page Object
All page objects should inherit from this base class
"""

from playwright.sync_api import Page, Locator
from typing import Optional
from helpers.healing_locator import HealingLocator
from helpers.wait_manager import WaitManager
from helpers.screenshot_manager import ScreenshotManager


class BasePage:
    """
    Base page object that all page objects inherit from
    Provides common functionality for all pages
    """

    def __init__(self, page: Page):
        """
        Initialize base page

        Args:
            page: Playwright page object
        """
        self.page = page
        self.healing_locator = HealingLocator()
        self.locators = {}

    def navigate(self, url: str = None):
        """
        Navigate to the page

        Args:
            url: URL to navigate to (optional, uses page_url if not provided)
        """
        target_url = url or getattr(self, 'page_url', None)
        if not target_url:
            raise ValueError("No URL provided and no page_url defined")

        self.page.goto(target_url, wait_until='networkidle')
        WaitManager.wait_for_power_apps_load(self.page)

    def find_element(
        self,
        locator_key: str,
        description: str = "",
        timeout: int = 5000
    ) -> Locator:
        """
        Find element using healing locator

        Args:
            locator_key: Key in self.locators dictionary
            description: Human-readable element description
            timeout: Wait timeout in milliseconds

        Returns:
            Playwright Locator object
        """
        if locator_key not in self.locators:
            raise ValueError(f"Locator '{locator_key}' not found in page object")

        locator = self.locators[locator_key]
        return self.healing_locator.find_element(
            self.page,
            locator,
            description or locator_key,
            timeout
        )

    def click(self, locator_key: str, description: str = ""):
        """
        Click an element

        Args:
            locator_key: Key in self.locators dictionary
            description: Element description for healing
        """
        element = self.find_element(locator_key, description)
        element.click()
        ScreenshotManager.capture_screenshot(self.page, f"clicked_{locator_key}")

    def fill(self, locator_key: str, value: str, description: str = ""):
        """
        Fill a text input

        Args:
            locator_key: Key in self.locators dictionary
            value: Value to fill
            description: Element description
        """
        element = self.find_element(locator_key, description)
        element.fill(value)
        ScreenshotManager.capture_screenshot(self.page, f"filled_{locator_key}")

    def select_option(self, locator_key: str, option: str, description: str = ""):
        """
        Select dropdown option

        Args:
            locator_key: Key in self.locators dictionary
            option: Option to select
            description: Element description
        """
        element = self.find_element(locator_key, description)
        element.select_option(label=option)

    def check(self, locator_key: str, description: str = ""):
        """
        Check a checkbox

        Args:
            locator_key: Key in self.locators dictionary
            description: Element description
        """
        element = self.find_element(locator_key, description)
        element.check()

    def uncheck(self, locator_key: str, description: str = ""):
        """
        Uncheck a checkbox

        Args:
            locator_key: Key in self.locators dictionary
            description: Element description
        """
        element = self.find_element(locator_key, description)
        element.uncheck()

    def get_text(self, locator_key: str) -> str:
        """
        Get element text content

        Args:
            locator_key: Key in self.locators dictionary

        Returns:
            Element text content
        """
        element = self.find_element(locator_key)
        return element.text_content()

    def is_visible(self, locator_key: str) -> bool:
        """
        Check if element is visible

        Args:
            locator_key: Key in self.locators dictionary

        Returns:
            True if visible, False otherwise
        """
        try:
            element = self.find_element(locator_key, timeout=2000)
            return element.is_visible()
        except (TimeoutError, LookupError, ValueError, Exception) as e:
            # Element not found or not visible - this is expected behavior
            return False

    def wait_for_element(
        self,
        locator_key: str,
        state: str = 'visible',
        timeout: int = 10000
    ):
        """
        Wait for element to reach a specific state

        Args:
            locator_key: Key in self.locators dictionary
            state: Element state (visible, hidden, attached, detached)
            timeout: Wait timeout in milliseconds
        """
        element = self.find_element(locator_key, timeout=timeout)
        element.wait_for(state=state, timeout=timeout)

    def wait_for_page_load(self):
        """Wait for page to fully load"""
        WaitManager.wait_for_power_apps_load(self.page)

    def take_screenshot(self, name: str):
        """
        Take a screenshot

        Args:
            name: Screenshot name
        """
        ScreenshotManager.capture_screenshot(self.page, name)

    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url

    def get_title(self) -> str:
        """Get page title"""
        return self.page.title()
