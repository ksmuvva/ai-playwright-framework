"""
Page Objects Module
Import all page objects here for easy access
"""

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

__all__ = [
    'BasePage',
    'LoginPage',
    'DashboardPage'
]
