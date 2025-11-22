"""
Authentication helper - Reusable authentication functions
Executes login once per session to improve test performance
"""

from playwright.sync_api import Page, BrowserContext
from typing import Optional
import os
from .screenshot_manager import ScreenshotManager

class AuthHelper:
    """Reusable authentication helper"""

    _authenticated_context: Optional[BrowserContext] = None
    _session_storage: dict = {}

    @staticmethod
    def authenticate(page: Page, username: str = None, password: str = None) -> bool:
        """
        Authenticate user and store session

        Args:
            page: Playwright page object
            username: Username (defaults to env var TEST_USER)
            password: Password (defaults to env var TEST_PASSWORD)

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication fails
        """
        username = username or os.getenv('TEST_USER')
        password = password or os.getenv('TEST_PASSWORD')

        if not username or not password:
            raise ValueError("Username and password must be provided or set in environment")

        try:
            # Navigate to login page
            app_url = os.getenv('APP_URL', 'http://localhost:3000')
            page.goto(f"{app_url}/login", wait_until='networkidle')

            # Fill credentials
            # Adjust selectors based on your application
            page.fill('input[name="username"], input[type="email"], #username', username)
            page.fill('input[name="password"], input[type="password"], #password', password)

            # Click login button
            page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')

            # Wait for successful login (adjust based on your app)
            page.wait_for_url('**/home', timeout=10000)

            ScreenshotManager.capture_screenshot(page, 'login_success')
            return True

        except Exception as e:
            ScreenshotManager.capture_screenshot(page, 'login_failed')
            raise Exception(f"Authentication failed: {str(e)}")

    @staticmethod
    def is_authenticated(page: Page) -> bool:
        """
        Check if user is already authenticated

        Args:
            page: Playwright page object

        Returns:
            bool: True if authenticated
        """
        try:
            # Check for common authentication indicators
            # Adjust based on your application

            # Method 1: Check current URL
            current_url = page.url
            if '/login' in current_url or '/signin' in current_url:
                return False

            # Method 2: Check for auth token in cookies
            cookies = page.context.cookies()
            auth_cookies = [c for c in cookies if 'auth' in c['name'].lower() or 'session' in c['name'].lower()]
            if auth_cookies:
                return True

            # Method 3: Check for user menu or profile element
            user_menu = page.locator('[data-testid="user-menu"], .user-profile, #user-dropdown').count()
            if user_menu > 0:
                return True

            return False

        except:
            return False

    @staticmethod
    def logout(page: Page) -> None:
        """
        Logout current user

        Args:
            page: Playwright page object
        """
        try:
            # Click logout button (adjust selector based on your app)
            page.click('[data-testid="logout"], button:has-text("Logout"), button:has-text("Sign out")')

            # Wait for redirect to login
            page.wait_for_url('**/login', timeout=5000)

            ScreenshotManager.capture_screenshot(page, 'logout_success')

        except Exception as e:
            ScreenshotManager.capture_screenshot(page, 'logout_failed')
            raise Exception(f"Logout failed: {str(e)}")

    @staticmethod
    def save_session_state(context: BrowserContext, name: str = 'default') -> None:
        """
        Save authentication state for reuse

        Args:
            context: Browser context
            name: Session name
        """
        state_path = f"./auth_states/{name}_state.json"
        os.makedirs('./auth_states', exist_ok=True)
        context.storage_state(path=state_path)

    @staticmethod
    def load_session_state(context: BrowserContext, name: str = 'default') -> bool:
        """
        Load saved authentication state

        Args:
            context: Browser context
            name: Session name

        Returns:
            bool: True if state loaded successfully
        """
        state_path = f"./auth_states/{name}_state.json"

        if os.path.exists(state_path):
            # State is loaded when creating new context
            return True

        return False

    @staticmethod
    def authenticate_with_sso(page: Page, provider: str = 'microsoft') -> bool:
        """
        Authenticate using SSO provider

        Args:
            page: Playwright page object
            provider: SSO provider (microsoft, google, okta)

        Returns:
            bool: True if authentication successful
        """
        try:
            # Navigate to login
            app_url = os.getenv('APP_URL')
            page.goto(f"{app_url}/login")

            # Click SSO button
            sso_selectors = {
                'microsoft': 'button:has-text("Microsoft"), button:has-text("Sign in with Microsoft")',
                'google': 'button:has-text("Google"), button:has-text("Sign in with Google")',
                'okta': 'button:has-text("Okta"), button:has-text("Sign in with Okta")'
            }

            page.click(sso_selectors.get(provider, sso_selectors['microsoft']))

            # Handle SSO provider login
            # This varies by provider - implement based on your SSO setup

            # Wait for redirect back to app
            page.wait_for_url('**/home', timeout=30000)

            ScreenshotManager.capture_screenshot(page, f'sso_{provider}_success')
            return True

        except Exception as e:
            ScreenshotManager.capture_screenshot(page, f'sso_{provider}_failed')
            raise Exception(f"SSO authentication failed: {str(e)}")
