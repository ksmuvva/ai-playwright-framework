"""
Login Page Object
Encapsulates all login page interactions
"""

from playwright.sync_api import Page
from pages.base_page import BasePage
import os


class LoginPage(BasePage):
    """
    Login page object
    Handles all login-related interactions
    """

    def __init__(self, page: Page):
        """Initialize login page"""
        super().__init__(page)

        # Page URL
        self.page_url = f"{os.getenv('APP_URL', 'http://localhost:3000')}/login"

        # Define page-specific locators
        self.locators = {
            'email_input': 'input[name="email"], input[type="email"], #email',
            'password_input': 'input[name="password"], input[type="password"], #password',
            'login_button': 'button:has-text("Login"), button:has-text("Sign In"), button[type="submit"]',
            'error_message': '.error-message, .alert-error, [role="alert"]',
            'forgot_password_link': 'a:has-text("Forgot Password"), a:has-text("Reset Password")',
            'signup_link': 'a:has-text("Sign Up"), a:has-text("Register")',
            'remember_me_checkbox': 'input[type="checkbox"][name="remember"], #remember-me'
        }

    def go_to_login(self):
        """Navigate to login page"""
        self.navigate()

    def enter_email(self, email: str):
        """
        Enter email address

        Args:
            email: Email address to enter
        """
        self.fill('email_input', email, "Email input field")

    def enter_password(self, password: str):
        """
        Enter password

        Args:
            password: Password to enter
        """
        self.fill('password_input', password, "Password input field")

    def click_login(self):
        """Click login button"""
        self.click('login_button', "Login button")
        self.wait_for_page_load()

    def login(self, email: str, password: str):
        """
        Perform complete login action

        Args:
            email: User email
            password: User password
        """
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()

    def is_error_displayed(self) -> bool:
        """
        Check if error message is displayed

        Returns:
            True if error visible, False otherwise
        """
        return self.is_visible('error_message')

    def get_error_message(self) -> str:
        """
        Get error message text

        Returns:
            Error message text
        """
        return self.get_text('error_message')

    def click_forgot_password(self):
        """Click forgot password link"""
        self.click('forgot_password_link', "Forgot password link")

    def click_signup(self):
        """Click signup link"""
        self.click('signup_link', "Sign up link")

    def check_remember_me(self):
        """Check remember me checkbox"""
        self.check('remember_me_checkbox', "Remember me checkbox")
