"""
BDD Step Definitions for Login Feature

This file contains step implementations for the complete_login.feature file.
These steps integrate with the LoginPage and SecurePage page objects.
"""

from behave import given, when, then
from pages.login_page import LoginPage
from pages.secure_page import SecurePage
import asyncio


# GIVEN steps


@given('I am on the login page')
def step_impl_given_on_login_page(context):
    """Navigate to the login page."""
    context.login_page = LoginPage(context.page)
    context.login_page.navigate()
    context.login_page.wait_for_page_load()


@given('I am logged in as "{username}" with password "{password}"')
def step_impl_given_logged_in(context, username, password):
    """Login with given credentials."""
    context.login_page = LoginPage(context.page)
    context.login_page.navigate()
    context.login_page.login(username, password)
    context.secure_page = SecurePage(context.page)
    context.secure_page.wait_for_page_load()


# WHEN steps


@when('I enter username "{username}"')
def step_impl_when_enter_username(context, username):
    """Enter username in the username field."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    context.login_page.enter_username(username)


@when('I enter password "{password}"')
def step_impl_when_enter_password(context, password):
    """Enter password in the password field."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    context.login_page.enter_password(password)


@when('I click the login button')
def step_impl_when_click_login(context):
    """Click the login button."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    context.login_page.click_login()


@when('I click the logout button')
def step_impl_when_click_logout(context):
    """Click the logout button."""
    if not hasattr(context, 'secure_page'):
        context.secure_page = SecurePage(context.page)
    context.secure_page.click_logout()


# THEN steps


@then('I should see a success message "{message}"')
def step_impl_then_see_success_message(context, message):
    """Verify success message is displayed."""
    if not hasattr(context, 'secure_page'):
        context.secure_page = SecurePage(context.page)
    assert context.secure_page.is_success_message_displayed(message), \
        f"Expected success message containing '{message}' but got '{context.secure_page.get_flash_message()}'"


@then('I should see an error message "{message}"')
def step_impl_then_see_error_message(context, message):
    """Verify error message is displayed."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    assert context.login_page.is_error_message_displayed(message), \
        f"Expected error message containing '{message}' but got '{context.login_page.get_flash_message()}'"


@then('I should be redirected to the secure area')
def step_impl_then_on_secure_page(context):
    """Verify we are on the secure page."""
    if not hasattr(context, 'secure_page'):
        context.secure_page = SecurePage(context.page)
    assert context.secure_page.is_on_page(), "Expected to be on secure page but URL is different"


@then('I should remain on the login page')
def step_impl_then_on_login_page(context):
    """Verify we are still on the login page."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    assert context.login_page.is_on_page(), "Expected to be on login page but URL is different"


@then('I should see a logout button')
def step_impl_then_see_logout_button(context):
    """Verify logout button is visible."""
    if not hasattr(context, 'secure_page'):
        context.secure_page = SecurePage(context.page)
    assert context.secure_page.is_logout_button_visible(), "Logout button is not visible"


@then('I should be redirected to the login page')
def step_impl_then_redirected_to_login(context):
    """Verify redirected back to login page."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    assert context.login_page.is_on_page(), "Expected to be on login page after logout"


@then('I should see the login heading')
def step_impl_then_see_login_heading(context):
    """Verify login page heading is displayed."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page)
    assert context.login_page.is_heading_visible(), "Login page heading is not visible"


@then('I should see result "{result}"')
def step_impl_then_see_result(context, result):
    """Verify the login result."""
    if result == "success":
        # Verify on secure page with success message
        step_impl_then_on_secure_page(context)
        step_impl_then_see_success_message(context, "You logged into a secure area!")
    elif "username invalid" in result:
        # Verify on login page with username error
        step_impl_then_on_login_page(context)
        step_impl_then_see_error_message(context, "Your username is invalid!")
    elif "password invalid" in result:
        # Verify on login page with password error
        step_impl_then_on_login_page(context)
        step_impl_then_see_error_message(context, "Your password is invalid!")
    else:
        raise AssertionError(f"Unknown result type: {result}")


# BEFORE and AFTER hooks


def before_scenario(context, scenario):
    """Setup before each scenario."""
    # Create a new browser context for each scenario
    context.browser = context.browser_type.launch(headless=context.config.userdata.get('headless', True))
    context.page = context.browser.new_page()


def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    # Close browser and cleanup
    if hasattr(context, 'page'):
        context.page.close()
    if hasattr(context, 'browser'):
        context.browser.close()
