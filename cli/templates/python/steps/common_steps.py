"""
Common step definitions
Reusable steps that can be used across all scenarios
"""

from behave import given, when, then, step
from helpers.wait_manager import WaitManager
from helpers.healing_locator import HealingLocator
from helpers.screenshot_manager import ScreenshotManager
from helpers.data_generator import TestDataGenerator
import os


# Navigation steps

@given('I am on the "{page_name}" page')
@given('I navigate to the "{page_name}" page')
def step_navigate_to_page(context, page_name):
    """Navigate to a specific page"""
    # You can configure page URLs in a config file or environment variables
    page_urls = {
        'home': f"{context.app_url}/home",
        'login': f"{context.app_url}/login",
        'dashboard': f"{context.app_url}/dashboard",
        # Add more page mappings as needed
    }

    url = page_urls.get(page_name.lower(), f"{context.app_url}/{page_name.lower()}")

    context.page.goto(url, wait_until='networkidle')
    WaitManager.wait_for_power_apps_load(context.page)


@given('I am on the homepage')
def step_navigate_to_homepage(context):
    """Navigate to homepage"""
    context.page.goto(context.app_url, wait_until='networkidle')
    WaitManager.wait_for_power_apps_load(context.page)


@when('I navigate to "{url}"')
def step_navigate_to_url(context, url):
    """Navigate to specific URL"""
    full_url = url if url.startswith('http') else f"{context.app_url}{url}"
    context.page.goto(full_url, wait_until='networkidle')


# Click actions

@when('I click on "{element_description}"')
@when('I click the "{element_description}"')
@when('I click "{element_description}"')
def step_click_element(context, element_description):
    """Click an element using healing locator"""

    # Try to find locator in context (if defined in scenario or loaded from config)
    locator = None

    if hasattr(context, 'locators') and element_description in context.locators:
        locator = context.locators[element_description]
    else:
        # Try common patterns based on description
        locator = f'button:has-text("{element_description}"), a:has-text("{element_description}"), [aria-label="{element_description}"]'

    # Use healing locator for reliability
    element = context.healing_locator.find_element(
        context.page,
        locator,
        element_description
    )

    element.click()
    WaitManager.smart_wait(context.page, locator, 'visible', timeout=2000)


@when('I click the button with text "{text}"')
def step_click_button_with_text(context, text):
    """Click button with specific text"""
    locator = f'button:has-text("{text}")'
    context.page.click(locator)


# Form filling

@when('I fill "{field_name}" with "{value}"')
@when('I enter "{value}" in "{field_name}"')
@when('I type "{value}" in "{field_name}"')
def step_fill_field(context, field_name, value):
    """Fill a form field"""

    # Try to find locator in context
    if hasattr(context, 'locators') and field_name in context.locators:
        locator = context.locators[field_name]
    else:
        # Try common patterns
        locator = f'input[name="{field_name}"], input[id="{field_name}"], [aria-label="{field_name}"], [data-testid="{field_name}"]'

    element = context.healing_locator.find_element(
        context.page,
        locator,
        f"input field: {field_name}"
    )

    element.fill(value)


@when('I fill "{field_name}" with random "{data_type}"')
def step_fill_field_with_random_data(context, field_name, data_type):
    """Fill field with randomly generated data"""

    generator = context.data_generator

    # Generate data based on type
    value = generator._generate_field_value(field_name, {'type': data_type})

    # Store generated value in context for later verification
    if not hasattr(context, 'generated_data'):
        context.generated_data = {}
    context.generated_data[field_name] = value

    # Fill the field
    step_fill_field(context, field_name, str(value))


# Selection

@when('I select "{option}" from "{dropdown_name}"')
def step_select_from_dropdown(context, option, dropdown_name):
    """Select option from dropdown"""

    locator = f'select[name="{dropdown_name}"], select[id="{dropdown_name}"]'

    element = context.healing_locator.find_element(
        context.page,
        locator,
        f"dropdown: {dropdown_name}"
    )

    element.select_option(label=option)


@when('I check the "{checkbox_name}" checkbox')
def step_check_checkbox(context, checkbox_name):
    """Check a checkbox"""
    locator = f'input[type="checkbox"][name="{checkbox_name}"], input[type="checkbox"][id="{checkbox_name}"]'
    context.page.check(locator)


@when('I uncheck the "{checkbox_name}" checkbox')
def step_uncheck_checkbox(context, checkbox_name):
    """Uncheck a checkbox"""
    locator = f'input[type="checkbox"][name="{checkbox_name}"], input[type="checkbox"][id="{checkbox_name}"]'
    context.page.uncheck(locator)


# Verification steps

@then('I should see "{text}"')
@then('I should see the text "{text}"')
def step_verify_text_visible(context, text):
    """Verify text is visible on page"""
    WaitManager.wait_for_text(context.page, text)
    assert context.page.locator(f'text={text}').is_visible(), f"Text '{text}' is not visible"


@then('I should not see "{text}"')
def step_verify_text_not_visible(context, text):
    """Verify text is not visible"""
    assert not context.page.locator(f'text={text}').is_visible(), f"Text '{text}' should not be visible"


@then('I should be on the "{page_name}" page')
def step_verify_on_page(context, page_name):
    """Verify current page"""
    # Check if URL contains page name
    current_url = context.page.url.lower()
    assert page_name.lower() in current_url, f"Expected to be on {page_name} page, but current URL is {current_url}"


@then('the "{element}" should be visible')
def step_verify_element_visible(context, element):
    """Verify element is visible"""
    locator = f'[data-testid="{element}"], #{element}, .{element}'
    WaitManager.smart_wait(context.page, locator, 'visible')
    assert context.page.locator(locator).is_visible(), f"Element '{element}' is not visible"


@then('the "{element}" should not be visible')
def step_verify_element_not_visible(context, element):
    """Verify element is not visible"""
    locator = f'[data-testid="{element}"], #{element}, .{element}'
    assert not context.page.locator(locator).is_visible(), f"Element '{element}' should not be visible"


@then('the "{element}" should contain text "{text}"')
def step_verify_element_contains_text(context, element, text):
    """Verify element contains specific text"""
    locator = f'[data-testid="{element}"], #{element}, .{element}'
    element_obj = context.page.locator(locator)
    actual_text = element_obj.text_content()
    assert text in actual_text, f"Element does not contain text '{text}'. Actual: '{actual_text}'"


# Wait steps

@step('I wait for {seconds:d} seconds')
def step_wait_seconds(context, seconds):
    """Wait for specified seconds"""
    context.page.wait_for_timeout(seconds * 1000)


@step('I wait for the page to load')
def step_wait_for_page_load(context):
    """Wait for page to fully load"""
    WaitManager.wait_for_power_apps_load(context.page)


@step('I wait for "{element}" to be visible')
def step_wait_for_element(context, element):
    """Wait for element to become visible"""
    locator = f'[data-testid="{element}"], #{element}, .{element}, text={element}'
    WaitManager.smart_wait(context.page, locator, 'visible')


# Authentication steps (using AuthHelper)

@given('I am logged in')
@given('I am authenticated')
def step_user_is_logged_in(context):
    """Ensure user is logged in"""
    from helpers.auth_helper import AuthHelper

    if not AuthHelper.is_authenticated(context.page):
        test_user = os.getenv('TEST_USER')
        test_password = os.getenv('TEST_PASSWORD')
        AuthHelper.authenticate(context.page, test_user, test_password)


@when('I log out')
@when('I sign out')
def step_logout(context):
    """Logout current user"""
    from helpers.auth_helper import AuthHelper
    AuthHelper.logout(context.page)


# Screenshot steps

@step('I take a screenshot named "{name}"')
def step_take_screenshot(context, name):
    """Manually capture screenshot"""
    ScreenshotManager.capture_screenshot(context.page, name)


# Power Apps specific steps

@step('I wait for Power Apps to load')
def step_wait_for_power_apps(context):
    """Wait for Power Apps specific loading"""
    WaitManager.wait_for_power_apps_load(context.page)


@when('I create a new "{entity_type}" record')
def step_create_power_apps_record(context, entity_type):
    """Create new Power Apps entity record"""
    # This is a placeholder - customize based on your Power Apps UI
    context.page.click('button:has-text("New")')
    WaitManager.wait_for_power_apps_load(context.page)


# Debug steps

@step('I print the current URL')
def step_print_url(context):
    """Print current page URL"""
    print(f"Current URL: {context.page.url}")


@step('I print the page title')
def step_print_title(context):
    """Print page title"""
    print(f"Page title: {context.page.title()}")


@step('I pause')
def step_pause(context):
    """Pause execution for debugging"""
    context.page.pause()
