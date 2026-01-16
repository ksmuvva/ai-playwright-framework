"""
Page Objects Module

This module contains all Page Object classes for the application.
Page Objects encapsulate web page interactions and provide a clean,
maintainable way to interact with application UI.

Example:
    >>> from pages import LoginPage, DashboardPage
    >>>
    >>> login_page = LoginPage(page)
    >>> login_page.navigate()
    >>> login_page.login("user", "pass")
    >>>
    >>> dashboard = DashboardPage(page)
    >>> dashboard.assert_is_loaded()
"""

from pages.base_page import BasePage

__all__ = [
    "BasePage",
]
