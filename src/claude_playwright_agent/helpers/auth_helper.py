"""
Authentication Helper Module.

Provides reusable authentication utilities for test automation.
Supports username/password, SSO, and session management.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from playwright.async_api import Page, BrowserContext


@dataclass
class UserCredentials:
    """User credentials dataclass."""

    username: str
    password: str
    domain: Optional[str] = None
    tenant_id: Optional[str] = None


class AuthHelper:
    """
    Authentication helper for managing user logins and sessions.

    Features:
    - Username/password authentication
    - SSO support (to be extended with MSAL)
    - Session persistence
    - Logout functionality
    - Authentication state checking
    """

    def __init__(self, credentials_file: Optional[str] = None):
        """
        Initialize the authentication helper.

        Args:
            credentials_file: Path to encrypted credentials JSON file
        """
        self.credentials_file = credentials_file or self._default_credentials_file()
        self._session_data: Optional[Dict[str, Any]] = None

    def _default_credentials_file(self) -> str:
        """Get default credentials file path."""
        return str(Path.cwd() / "fixtures" / "user_credentials.json")

    def load_credentials(self, username: str) -> Optional[UserCredentials]:
        """
        Load credentials for a specific user.

        Args:
            username: The username to load credentials for

        Returns:
            UserCredentials object or None if not found
        """
        try:
            if Path(self.credentials_file).exists():
                with open(self.credentials_file, "r") as f:
                    credentials = json.load(f)
                    user_data = credentials.get(username, {})
                    if user_data:
                        return UserCredentials(
                            username=username,
                            password=user_data.get("password", ""),
                            domain=user_data.get("domain"),
                            tenant_id=user_data.get("tenant_id"),
                        )
        except Exception:
            pass
        return None

    async def authenticate_user(
        self,
        page: Page,
        base_url: str,
        username: str,
        password: str,
        login_url: Optional[str] = None,
    ) -> bool:
        """
        Authenticate a user with username and password.

        Args:
            page: Playwright page object
            base_url: Base URL of the application
            username: Username for login
            password: Password for login
            login_url: Specific login URL (optional)

        Returns:
            True if authentication successful, False otherwise
        """
        login_page = login_url or f"{base_url}/login"
        await page.goto(login_page)

        try:
            await page.fill(
                'input[name="username"], input[id="email"], input[name="email"]', username
            )
            await page.fill('input[name="password"], input[type="password"]', password)
            await page.click('button[type="submit"], input[type="submit"]')

            await page.wait_for_load_state("networkidle")
            return await self.check_authentication_state(page)

        except Exception:
            return False

    async def authenticate_with_sso(
        self,
        context: BrowserContext,
        base_url: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> bool:
        """
        Authenticate using SSO (Microsoft/Azure AD).

        Note: Requires MSAL library for full implementation.
        This is a placeholder for future MSAL integration.

        Args:
            context: Playwright browser context
            base_url: Base URL of the application
            tenant_id: Azure AD tenant ID
            client_id: Application client ID

        Returns:
            True if SSO authentication successful
        """
        sso_url = f"https://login.microsoftonline.com/{tenant_id or 'common'}"
        await context.add_init_script(f"""
            // MSAL initialization placeholder
            if (typeof msal !== 'undefined') {{
                console.log('MSAL is available');
            }}
        """)
        return True

    async def logout(self, page: Page, base_url: str) -> bool:
        """
        Log out the current user.

        Args:
            page: Playwright page object
            base_url: Base URL of the application

        Returns:
            True if logout successful
        """
        try:
            await page.goto(f"{base_url}/logout")
            await page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False

    async def check_authentication_state(self, page: Page) -> bool:
        """
        Check if user is currently authenticated.

        Args:
            page: Playwright page object

        Returns:
            True if authenticated, False otherwise
        """
        try:
            await page.wait_for_load_state("networkidle")

            auth_indicators = [
                "text=Welcome",
                "text=Log out",
                "text=Logout",
                '[aria-label*="User"]',
                ".user-menu",
                ".logged-in",
            ]

            for indicator in auth_indicators:
                try:
                    element = page.locator(indicator).first
                    if await element.is_visible(timeout=2000):
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    async def refresh_session(self, page: Page) -> bool:
        """
        Refresh the current user session.

        Args:
            page: Playwright page object

        Returns:
            True if session refreshed successfully
        """
        try:
            await page.reload()
            await page.wait_for_load_state("networkidle")
            return await self.check_authentication_state(page)
        except Exception:
            return False

    def save_session(self, session_data: Dict[str, Any]) -> None:
        """
        Save session data for later use.

        Args:
            session_data: Dictionary containing session information
        """
        self._session_data = session_data

    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get the current session data."""
        return self._session_data
