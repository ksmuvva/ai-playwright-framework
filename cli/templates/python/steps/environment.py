"""
Behave environment configuration
Hooks for setup and teardown at different levels
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from helpers.screenshot_manager import ScreenshotManager
from helpers.auth_helper import AuthHelper
from helpers.wait_manager import WaitManager
from helpers.healing_locator import HealingLocator
from helpers.data_generator import TestDataGenerator


def before_all(context):
    """Setup before all tests"""

    print("\n🚀 Initializing test framework...\n")

    # Initialize Playwright
    context.playwright = sync_playwright().start()

    # Launch browser
    browser_type = os.getenv('BROWSER', 'chromium')
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'

    if browser_type == 'chromium':
        context.browser = context.playwright.chromium.launch(headless=headless)
    elif browser_type == 'firefox':
        context.browser = context.playwright.firefox.launch(headless=headless)
    elif browser_type == 'webkit':
        context.browser = context.playwright.webkit.launch(headless=headless)
    else:
        context.browser = context.playwright.chromium.launch(headless=headless)

    # Setup screenshot directory
    ScreenshotManager.setup()

    # Initialize helpers
    context.healing_locator = HealingLocator()
    context.data_generator = TestDataGenerator()

    # Load configuration
    context.app_url = os.getenv('APP_URL', 'http://localhost:3000')
    context.timeout = int(os.getenv('DEFAULT_TIMEOUT', '10000'))

    print(f"✅ Browser: {browser_type} (headless: {headless})")
    print(f"✅ App URL: {context.app_url}")
    print(f"✅ Default timeout: {context.timeout}ms\n")


def before_scenario(context, scenario):
    """Setup before each scenario"""

    print(f"\n📝 Scenario: {scenario.name}\n")

    # Create new page with viewport settings
    viewport_width = int(os.getenv('VIEWPORT_WIDTH', '1920'))
    viewport_height = int(os.getenv('VIEWPORT_HEIGHT', '1080'))

    context.page = context.browser.new_page(
        viewport={'width': viewport_width, 'height': viewport_height}
    )

    # Set default timeout
    context.page.set_default_timeout(context.timeout)

    # Setup screenshot manager for this scenario
    ScreenshotManager.setup(scenario.name)

    # Reset screenshot counter
    ScreenshotManager.reset_counter()

    # Authenticate if scenario doesn't have @skip_auth tag
    if 'skip_auth' not in scenario.tags and 'no_auth' not in scenario.tags:
        try:
            test_user = os.getenv('TEST_USER')
            test_password = os.getenv('TEST_PASSWORD')

            if test_user and test_password:
                print("🔐 Authenticating user...")
                AuthHelper.authenticate(context.page, test_user, test_password)
                print("✅ Authentication successful\n")
        except (TimeoutError, ValueError, RuntimeError) as e:
            print(f"⚠️  Authentication failed: {type(e).__name__}: {e}")
            # Continue without auth for scenarios that might handle it differently


def after_step(context, step):
    """Capture screenshot after every step"""

    if os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true':
        step_name = step.name.replace(' ', '_')[:50]
        status = '✓' if step.status == 'passed' else '✗'

        print(f"{status} {step.keyword}{step.name}")

        ScreenshotManager.capture_screenshot(context.page, step_name)


def after_scenario(context, scenario):
    """Cleanup after scenario"""

    # Capture failure screenshot
    if scenario.status == 'failed':
        print(f"\n❌ Scenario failed: {scenario.name}")
        ScreenshotManager.capture_on_failure(context.page, scenario.name)

        # Print page URL and title for debugging
        try:
            print(f"  URL: {context.page.url}")
            print(f"  Title: {context.page.title()}")
        except (AttributeError, RuntimeError) as e:
            print(f"  ⚠️  Could not retrieve page info: {e}")

    elif scenario.status == 'passed':
        print(f"\n✅ Scenario passed: {scenario.name}")

    # Print screenshot count
    screenshot_count = ScreenshotManager.get_screenshot_count()
    print(f"📸 Screenshots captured: {screenshot_count}")

    # Close page
    context.page.close()

    print("\n" + "="*70 + "\n")


def after_all(context):
    """Cleanup after all tests"""

    print("\n🏁 Test execution completed\n")

    # Print healing statistics
    if hasattr(context, 'healing_locator'):
        stats = context.healing_locator.get_healing_stats()
        if stats['total_failed_locators'] > 0:
            print(f"🔧 Self-healing statistics:")
            print(f"  Failed locators: {stats['total_failed_locators']}")
            print(f"  Healing attempts: {stats['total_healing_attempts']}")
            print()

    # Print wait optimization suggestions
    wait_stats = WaitManager.get_wait_stats()
    if wait_stats['total_waits'] > 0:
        print(f"⏱️  Wait statistics:")
        print(f"  Total waits: {wait_stats['total_waits']}")
        print(f"  Success rate: {wait_stats['success_rate']:.1%}")
        print()

    # Save wait patterns for next run
    WaitManager._save_patterns()

    # Close browser
    context.browser.close()

    # Stop Playwright
    context.playwright.stop()

    print("✅ Framework shutdown complete\n")
