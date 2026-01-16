"""
Dashboard Page Object Model.

This page object represents a post-login dashboard page.
It demonstrates how to model pages with dynamic content and user-specific data.

Example:
    >>> from pages.dashboard_page import DashboardPage
    >>>
    >>> dashboard = DashboardPage(page, base_url="https://example.com")
    >>> dashboard.assert_welcome_message_shown()
    >>> dashboard.logout()
"""

from typing import TYPE_CHECKING, List

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class DashboardPage(BasePage):
    """
    Page object for the user dashboard.

    This class encapsulates dashboard functionality including:
    - Welcome message display
    - User profile information
    - Navigation menu
    - Logout functionality
    - Quick actions

    Attributes:
        page: Playwright Page instance
        base_url: Base URL for the application

    Example:
        >>> dashboard = DashboardPage(page, "https://example.com")
        >>> dashboard.assert_is_loaded()
        >>> username = dashboard.get_username()
        >>> print(f"Logged in as: {username}")
    """

    def __init__(self, page: "Page", base_url: str = "") -> None:
        """
        Initialize the DashboardPage.

        Args:
            page: Playwright Page instance
            base_url: Base URL for the application
        """
        super().__init__(page, base_url, "DashboardPage")
        self.url_path = "/dashboard"

    # ========================================================================
    # ELEMENT LOCATORS
    # ========================================================================

    @property
    def welcome_message(self):
        """Welcome message element."""
        return self.page.locator("h1, h2, .welcome, .greeting")

    @property
    def username_display(self):
        """Username/user display element."""
        return self.page.locator(".username, .user-name, [data-testid='username']")

    @property
    def logout_button(self):
        """Logout button/link."""
        return self.page.locator("button:has-text('Logout'), a:has-text('Logout'), button:has-text('Sign Out')")

    @property
    def navigation_menu(self):
        """Main navigation menu."""
        return self.page.locator("nav, .navigation, .menu")

    @property
    def profile_link(self):
        """Profile/settings link."""
        return self.page.locator("a:has-text('Profile'), a:has-text('Settings')")

    @property
    def notification_bell(self):
        """Notification bell icon."""
        return self.page.locator(".notification, .bell-icon, [aria-label='Notifications']")

    # ========================================================================
    # PAGE ACTIONS
    # ========================================================================

    def navigate(self) -> None:
        """
        Navigate to the dashboard.

        Example:
            >>> dashboard = DashboardPage(page)
            >>> dashboard.navigate()
        """
        self.goto(self.url_path)
        self.wait_for_load_state()

    def logout(self) -> "LoginPage":
        """
        Logout and return to LoginPage.

        Returns:
            LoginPage instance after logout

        Example:
            >>> from pages.login_page import LoginPage
            >>>
            >>> dashboard = DashboardPage(page)
            >>> login_page = dashboard.logout()
            >>> login_page.assert_is_loaded()
        """
        self.logout_button.click()

        # Import here to avoid circular dependency
        from pages.examples.login_page import LoginPage

        return LoginPage(self.page, self.base_url)

    def navigate_to_profile(self) -> None:
        """
        Navigate to user profile page.

        Example:
            >>> dashboard.navigate_to_profile()
        """
        self.profile_link.click()

    def click_notifications(self) -> None:
        """
        Click on notification bell to view notifications.

        Example:
            >>> dashboard.click_notifications()
        """
        self.notification_bell.click()

    def get_navigation_items(self) -> List[str]:
        """
        Get list of navigation menu items.

        Returns:
            List of navigation item texts

        Example:
            >>> items = dashboard.get_navigation_items()
            >>> print(f"Menu items: {items}")
        """
        items = self.navigation_menu.locator("a, button").all()
        return [item.inner_text() for item in items]

    def navigate_to_menu_item(self, item_text: str) -> None:
        """
        Navigate to a specific menu item.

        Args:
            item_text: Text of the menu item to click

        Example:
            >>> dashboard.navigate_to_menu_item("Reports")
        """
        self.navigation_menu.locator(f"a:has-text('{item_text}'), button:has-text('{item_text}')").click()

    # ========================================================================
    # ASSERTIONS
    # ========================================================================

    def assert_is_loaded(self) -> None:
        """
        Assert dashboard is loaded.

        Raises:
            AssertionError: If dashboard is not loaded

        Example:
            >>> dashboard.navigate()
            >>> dashboard.assert_is_loaded()
        """
        self.wait_for_load_state()
        # Check for common dashboard elements
        self.assert_visible("h1, h2, .welcome, nav")

    def assert_welcome_message_shown(self) -> None:
        """
        Assert welcome message is displayed.

        Raises:
            AssertionError: If welcome message not shown

        Example:
            >>> dashboard.assert_welcome_message_shown()
        """
        self.assert_visible("h1, h2, .welcome, .greeting")

    def assert_username_displayed(self, expected_username: str) -> None:
        """
        Assert specific username is displayed.

        Args:
            expected_username: Expected username to be displayed

        Raises:
            AssertionError: If username not displayed correctly

        Example:
            >>> dashboard.assert_username_displayed("testuser@example.com")
        """
        self.assert_text(".username, .user-name, [data-testid='username']", expected_username)

    def assert_logout_button_visible(self) -> None:
        """
        Assert logout button is visible.

        Example:
            >>> dashboard.assert_logout_button_visible()
        """
        self.assert_visible("button:has-text('Logout'), a:has-text('Logout')")

    def assert_notification_count(self, count: int) -> None:
        """
        Assert notification count badge shows specific number.

        Args:
            count: Expected notification count

        Raises:
            AssertionError: If count doesn't match

        Example:
            >>> dashboard.assert_notification_count(3)
        """
        badge = self.page.locator(".notification-badge, .badge")
        self.assert_text(".notification-badge, .badge", str(count))

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_welcome_message(self) -> str:
        """
        Get the welcome message text.

        Returns:
            Welcome message text

        Example:
            >>> message = dashboard.get_welcome_message()
            >>> print(f"Welcome: {message}")
        """
        return self.welcome_message.inner_text() or ""

    def get_username(self) -> str:
        """
        Get displayed username.

        Returns:
            Username text

        Example:
            >>> username = dashboard.get_username()
        """
        return self.username_display.inner_text() or ""

    def get_notification_count(self) -> int:
        """
        Get notification count from badge.

        Returns:
            Number of notifications (0 if no badge)

        Example:
            >>> count = dashboard.get_notification_count()
            >>> print(f"You have {count} notifications")
        """
        badge = self.page.locator(".notification-badge, .badge")
        if badge.is_visible():
            text = badge.inner_text()
            try:
                return int(text)
            except ValueError:
                return 0
        return 0

    def has_notification(self) -> bool:
        """
        Check if user has any notifications.

        Returns:
            True if notification badge is visible with count > 0

        Example:
            >>> if dashboard.has_notification():
            ...     dashboard.click_notifications()
        """
        badge = self.page.locator(".notification-badge, .badge")
        return badge.is_visible() and self.get_notification_count() > 0

    def take_screenshot(self) -> str:
        """
        Take screenshot of dashboard.

        Returns:
            Path to screenshot file

        Example:
            >>> path = dashboard.take_screenshot()
            >>> print(f"Dashboard screenshot: {path}")
        """
        return super().screenshot(name=f"dashboard_{self.get_username()}")
