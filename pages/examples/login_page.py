"""
Login Page Object Model.

This page object represents a standard login page with username/password
authentication. It demonstrates best practices for Page Object Model implementation.

Auto-generated example showing best practices for page objects.

Example:
    >>> from pages.login_page import LoginPage
    >>>
    >>> login_page = LoginPage(page, base_url="https://example.com")
    >>> login_page.navigate()
    >>> login_page.login("testuser", "password123")
"""

from typing import TYPE_CHECKING

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class LoginPage(BasePage):
    """
    Page object for login functionality.

    This class encapsulates all interactions with the login page including:
    - Navigation
    - Form filling
    - Form submission
    - Error validation
    - Success navigation

    Attributes:
        page: Playwright Page instance
        base_url: Base URL for the application
        url_path: Path to the login page

    Example:
        >>> page = LoginPage(page, "https://example.com")
        >>> page.navigate()
        >>> page.login("user@example.com", "secret123")
    """

    def __init__(self, page: "Page", base_url: str = "") -> None:
        """
        Initialize the LoginPage.

        Args:
            page: Playwright Page instance
            base_url: Base URL for the application
        """
        super().__init__(page, base_url, "LoginPage")
        self.url_path = "/login"

    # ========================================================================
    # ELEMENT LOCATORS (using Playwright best practices)
    # ========================================================================

    @property
    def username_input(self):
        """Username/email input field."""
        return self.page.locator("input[name='username'], input[type='email'], input[id*='username'], input[id*='email']")

    @property
    def password_input(self):
        """Password input field."""
        return self.page.locator("input[name='password'], input[type='password']")

    @property
    def login_button(self):
        """Login/submit button."""
        return self.page.locator("button[type='submit'], button:has-text('Log In'), button:has-text('Sign In'), input[type='submit']")

    @property
    def error_message(self):
        """Error message container."""
        return self.page.locator(".error-message, .alert-error, [role='alert']")

    @property
    def remember_me_checkbox(self):
        """Remember me checkbox."""
        return self.page.locator("input[name='remember'], input[id*='remember']")

    @property
    def forgot_password_link(self):
        """Forgot password link."""
        return self.page.locator("a:has-text('Forgot Password')")

    # ========================================================================
    # PAGE ACTIONS
    # ========================================================================

    def navigate(self) -> None:
        """
        Navigate to the login page.

        Example:
            >>> login_page = LoginPage(page)
            >>> login_page.navigate()
        """
        self.goto(self.url_path)
        self.wait_for_load_state()

    def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> None:
        """
        Perform login action with username and password.

        Args:
            username: User's username or email
            password: User's password
            remember_me: Whether to check "remember me" checkbox

        Example:
            >>> login_page.login("testuser@example.com", "secret123")
            >>> login_page.login("user", "pass", remember_me=True)
        """
        # Fill username
        self.username_input.fill(username)

        # Fill password
        self.password_input.fill(password)

        # Check remember me if requested
        if remember_me:
            if self.is_visible("input[name='remember']"):
                self.check("input[name='remember']")

        # Submit form
        self.login_button.click()

    def login_successfully(
        self,
        username: str,
        password: str,
    ) -> "DashboardPage":
        """
        Login and return DashboardPage on success.

        This method demonstrates page navigation flow in POM.
        After successful login, it returns the next page object.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            DashboardPage instance after successful login

        Example:
            >>> from pages.dashboard_page import DashboardPage
            >>>
            >>> login_page = LoginPage(page)
            >>> dashboard = login_page.login_successfully("user", "pass")
            >>> dashboard.assert_welcome_message_shown()
        """
        self.login(username, password)

        # Import here to avoid circular dependency
        from pages.examples.dashboard_page import DashboardPage

        return DashboardPage(self.page, self.base_url)

    def click_forgot_password(self) -> None:
        """
        Click the forgot password link.

        Example:
            >>> login_page.click_forgot_password()
        """
        self.forgot_password_link.click()

    # ========================================================================
    # ASSERTIONS
    # ========================================================================

    def assert_is_loaded(self) -> None:
        """
        Assert login page is loaded and visible.

        Raises:
            AssertionError: If page is not loaded

        Example:
            >>> login_page.navigate()
            >>> login_page.assert_is_loaded()
        """
        self.wait_for_load_state()
        self.assert_visible("[name='username'], [type='email']")

    def assert_error_shown(self, expected_error: str = None) -> None:
        """
        Assert error message is displayed.

        Args:
            expected_error: Expected error text (optional)

        Raises:
            AssertionError: If error not shown or text doesn't match

        Example:
            >>> login_page.login("invalid", "wrong")
            >>> login_page.assert_error_shown("Invalid credentials")
        """
        self.assert_visible(".error-message, .alert-error, [role='alert']")
        if expected_error:
            self.assert_text(".error-message, .alert-error, [role='alert']", expected_error)

    def assert_login_button_enabled(self) -> None:
        """
        Assert login button is enabled.

        Example:
            >>> login_page.assert_login_button_enabled()
        """
        self.assert_enabled("button[type='submit'], input[type='submit']")

    def assert_login_button_disabled(self) -> None:
        """
        Assert login button is disabled (e.g., form validation).

        Example:
            >>> login_page.assert_login_button_disabled()
        """
        self.assert_disabled("button[type='submit'], input[type='submit']")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_username_value(self) -> str:
        """
        Get current value of username field.

        Returns:
            Current username field value

        Example:
            >>> username = login_page.get_username_value()
        """
        return self.username_input.input_value() or ""

    def get_password_value(self) -> str:
        """
        Get current value of password field.

        Returns:
            Current password field value

        Example:
            >>> password = login_page.get_password_value()
        """
        return self.password_input.input_value() or ""

    def is_remember_me_visible(self) -> bool:
        """
        Check if remember me checkbox is visible.

        Returns:
            True if visible, False otherwise

        Example:
            >>> if login_page.is_remember_me_visible():
            ...     login_page.check("input[name='remember']")
        """
        return self.remember_me_checkbox.is_visible()

    def clear_form(self) -> None:
        """
        Clear all form fields.

        Example:
            >>> login_page.clear_form()
        """
        self.username_input.fill("")
        self.password_input.fill("")
