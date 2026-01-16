"""
Login Page Object

Page object for the login page at the-internet.herokuapp.com/login
Demonstrates best practices for Page Object Model.
"""

from playwright.async_api import Page, Locator
import sys
from pathlib import Path

# Add framework root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pages.base_page import BasePage


class LoginPage(BasePage):
    """
    Page object for the login page.

    This page object encapsulates all interactions with the login page,
    following the Page Object Model design pattern.
    """

    def __init__(self, page: Page, base_url: str = "https://the-internet.herokuapp.com"):
        """
        Initialize the login page object.

        Args:
            page: Playwright page instance
            base_url: Base URL for the application
        """
        super().__init__(page, base_url, "LoginPage")

        # Selectors
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "button[type='submit']"
        self.logout_button = ".button.secondary"
        self.flash_message = "#flash"
        self.page_header = "h2"

    def navigate(self) -> None:
        """Navigate to the login page."""
        self.page.goto(f"{self.base_url}/login")
        self.wait_for_page_load()

    def login(self, username: str, password: str) -> None:
        """
        Perform login with the given credentials.

        Args:
            username: Username to enter
            password: Password to enter
        """
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)

    def logout(self) -> None:
        """Click the logout button."""
        self.click(self.logout_button)

    def get_flash_message(self) -> str:
        """
        Get the flash message text.

        Returns:
            The flash message text (stripped of whitespace and × character)
        """
        self.assert_visible(self.flash_message)
        text = self.page.locator(self.flash_message).text_content()
        # Remove the × character and extra whitespace
        return text.replace("×", "").strip()

    def is_flash_message_success(self) -> bool:
        """
        Check if flash message indicates success.

        Returns:
            True if success message, False otherwise
        """
        self.assert_visible(self.flash_message)
        flash_element = self.page.locator(self.flash_message)
        class_list = flash_element.get_attribute("class") or ""
        return "success" in class_list

    def is_flash_message_error(self) -> bool:
        """
        Check if flash message indicates error.

        Returns:
            True if error message, False otherwise
        """
        self.assert_visible(self.flash_message)
        flash_element = self.page.locator(self.flash_message)
        class_list = flash_element.get_attribute("class") or ""
        return "error" in class_list

    def is_logout_button_visible(self) -> bool:
        """
        Check if logout button is visible.

        Returns:
            True if logout button is visible, False otherwise
        """
        return self.is_visible(self.logout_button)

    def get_page_title(self) -> str:
        """
        Get the page header title.

        Returns:
            The page title text
        """
        self.assert_visible(self.page_header)
        return self.page.locator(self.page_header).text_content()

    def is_on_login_page(self) -> bool:
        """
        Check if currently on the login page.

        Returns:
            True if on login page, False otherwise
        """
        return self.is_visible(self.login_button) and self.is_visible(self.username_input)
