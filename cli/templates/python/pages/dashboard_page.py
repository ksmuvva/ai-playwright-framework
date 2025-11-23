"""
Dashboard Page Object
Encapsulates dashboard page interactions
"""

from playwright.sync_api import Page
from pages.base_page import BasePage
import os


class DashboardPage(BasePage):
    """
    Dashboard page object
    Handles all dashboard-related interactions
    """

    def __init__(self, page: Page):
        """Initialize dashboard page"""
        super().__init__(page)

        # Page URL
        self.page_url = f"{os.getenv('APP_URL', 'http://localhost:3000')}/dashboard"

        # Define page-specific locators
        self.locators = {
            'welcome_message': '.welcome-message, h1:has-text("Welcome"), [data-testid="welcome"]',
            'user_menu': '.user-menu, [data-testid="user-menu"], #user-dropdown',
            'logout_button': 'button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout")',
            'new_button': 'button:has-text("New"), button:has-text("Create"), [data-testid="new-button"]',
            'search_input': 'input[type="search"], input[placeholder*="Search"], [data-testid="search"]',
            'notifications_icon': '.notifications, [data-testid="notifications"], i.fa-bell',
            'settings_link': 'a:has-text("Settings"), [data-testid="settings"]'
        }

    def go_to_dashboard(self):
        """Navigate to dashboard page"""
        self.navigate()

    def is_welcome_message_visible(self) -> bool:
        """
        Check if welcome message is displayed

        Returns:
            True if welcome message visible
        """
        return self.is_visible('welcome_message')

    def get_welcome_message(self) -> str:
        """
        Get welcome message text

        Returns:
            Welcome message text
        """
        return self.get_text('welcome_message')

    def open_user_menu(self):
        """Open user menu dropdown"""
        self.click('user_menu', "User menu")

    def logout(self):
        """Logout current user"""
        self.open_user_menu()
        self.click('logout_button', "Logout button")

    def click_new(self):
        """Click new/create button"""
        self.click('new_button', "New button")
        self.wait_for_page_load()

    def search(self, query: str):
        """
        Perform search

        Args:
            query: Search query
        """
        self.fill('search_input', query, "Search input")
        self.page.keyboard.press('Enter')
        self.wait_for_page_load()

    def open_notifications(self):
        """Open notifications panel"""
        self.click('notifications_icon', "Notifications icon")

    def go_to_settings(self):
        """Navigate to settings"""
        self.click('settings_link', "Settings link")
        self.wait_for_page_load()
