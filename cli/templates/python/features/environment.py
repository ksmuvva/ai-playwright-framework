"""
Behave environment configuration
Hooks for setup and teardown at different levels
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from helpers.screenshot_manager import ScreenshotManager
from helpers.auth_helper import AuthHelper
from helpers.wait_manager import WaitManager
from helpers.healing_locator import HealingLocator
from helpers.data_generator import TestDataGenerator
from helpers.phoenix_tracer import PhoenixTracer
from helpers.logger import (
    configure_logging,
    get_logger,
    log_framework_info,
    log_phoenix_status,
    log_ai_config,
    log_browser_config,
    log_scenario_start,
    log_scenario_end,
)

# Initialize logging first
configure_logging()
logger = get_logger("environment")


def before_all(context):
    """Setup before all tests"""

    logger.info("="*70)
    logger.info("framework_initialization_started", message="🚀 Initializing AI Playwright Test Framework...")
    logger.info("="*70)

    # Log framework information
    log_framework_info()

    # Initialize Phoenix tracing FIRST (before any AI operations)
    # This ensures all LLM calls are captured from the start
    enable_phoenix = os.getenv('ENABLE_PHOENIX_TRACING', 'true').lower() != 'false'
    if enable_phoenix:
        try:
            logger.info("phoenix_init", message="Initializing Phoenix tracing for LLM observability...")
            PhoenixTracer.initialize()
            log_phoenix_status(
                enabled=True,
                endpoint=os.getenv('PHOENIX_COLLECTOR_ENDPOINT', 'http://localhost:6006/v1/traces'),
                ui_launched=os.getenv('PHOENIX_LAUNCH_UI', 'true').lower() != 'false'
            )
        except Exception as e:
            logger.error(
                "phoenix_init_error",
                error=str(e),
                message="⚠️ Phoenix initialization failed - continuing without tracing"
            )
    else:
        log_phoenix_status(enabled=False)

    # Log AI configuration
    ai_provider = os.getenv('AI_PROVIDER', 'anthropic')
    ai_model = os.getenv('AI_MODEL', 'claude-sonnet-4-5-20250929')
    ai_features = {
        'reasoning_enabled': os.getenv('ENABLE_REASONING', 'true').lower() == 'true',
        'prompt_caching': os.getenv('ENABLE_PROMPT_CACHING', 'true').lower() == 'true',
        'streaming': os.getenv('ENABLE_STREAMING', 'false').lower() == 'true',
        'ai_cache': os.getenv('ENABLE_AI_CACHE', 'true').lower() == 'true',
        'healing': os.getenv('ENABLE_HEALING', 'true').lower() == 'true',
    }
    log_ai_config(ai_provider, ai_model, ai_features)

    # Initialize Playwright
    logger.info("playwright_init", message="Starting Playwright...")
    context.playwright = sync_playwright().start()
    logger.debug("playwright_started", message="Playwright started successfully")

    # Launch browser
    browser_type = os.getenv('BROWSER', 'chromium')
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'

    logger.info("browser_launch", browser=browser_type, headless=headless, message="Launching browser...")

    if browser_type == 'chromium':
        context.browser = context.playwright.chromium.launch(headless=headless)
    elif browser_type == 'firefox':
        context.browser = context.playwright.firefox.launch(headless=headless)
    elif browser_type == 'webkit':
        context.browser = context.playwright.webkit.launch(headless=headless)
    else:
        logger.warning("browser_fallback", browser=browser_type, message="Unknown browser, falling back to chromium")
        context.browser = context.playwright.chromium.launch(headless=headless)

    # Setup screenshot directory
    logger.debug("screenshot_setup", message="Setting up screenshot directory...")
    ScreenshotManager.setup()

    # Initialize helpers
    logger.debug("helpers_init", message="Initializing helper modules...")
    context.healing_locator = HealingLocator()
    context.data_generator = TestDataGenerator()

    # Load configuration
    context.app_url = os.getenv('APP_URL', 'http://localhost:3000')
    context.timeout = int(os.getenv('DEFAULT_TIMEOUT', '10000'))

    viewport_width = int(os.getenv('VIEWPORT_WIDTH', '1920'))
    viewport_height = int(os.getenv('VIEWPORT_HEIGHT', '1080'))

    # Log browser configuration
    log_browser_config(
        browser=browser_type,
        headless=headless,
        viewport={'width': viewport_width, 'height': viewport_height}
    )

    logger.info(
        "framework_ready",
        app_url=context.app_url,
        timeout_ms=context.timeout,
        message="✅ Framework initialization complete - Ready to run tests!"
    )
    logger.info("="*70)
    print()  # Add blank line for readability


def before_scenario(context, scenario):
    """Setup before each scenario"""

    # Track scenario start time
    context.scenario_start_time = time.time()

    print()  # Blank line for readability
    logger.info("="*70)
    log_scenario_start(scenario.name, scenario.tags)

    # Create new page with viewport settings
    viewport_width = int(os.getenv('VIEWPORT_WIDTH', '1920'))
    viewport_height = int(os.getenv('VIEWPORT_HEIGHT', '1080'))

    logger.debug(
        "page_creation",
        viewport={'width': viewport_width, 'height': viewport_height},
        message="Creating new browser page..."
    )

    context.page = context.browser.new_page(
        viewport={'width': viewport_width, 'height': viewport_height}
    )

    # Set default timeout
    context.page.set_default_timeout(context.timeout)
    logger.debug("timeout_set", timeout_ms=context.timeout, message="Default timeout configured")

    # Setup screenshot manager for this scenario
    ScreenshotManager.setup(scenario.name)
    ScreenshotManager.reset_counter()
    logger.debug("screenshots_ready", message="Screenshot manager configured")

    # Authenticate if scenario doesn't have @skip_auth tag
    if 'skip_auth' not in scenario.tags and 'no_auth' not in scenario.tags:
        try:
            test_user = os.getenv('TEST_USER')
            test_password = os.getenv('TEST_PASSWORD')

            if test_user and test_password:
                logger.info("auth_start", user=test_user, message="🔐 Authenticating user...")
                AuthHelper.authenticate(context.page, test_user, test_password)
                logger.info("auth_success", message="✅ Authentication successful")
            else:
                logger.warning("auth_skipped", message="No credentials provided - skipping authentication")
        except (TimeoutError, ValueError, RuntimeError) as e:
            logger.error(
                "auth_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                message="⚠️ Authentication failed - continuing without auth"
            )
            # Continue without auth for scenarios that might handle it differently
    else:
        logger.info("auth_skipped", tags=scenario.tags, message="Authentication skipped due to scenario tags")


def after_step(context, step):
    """Capture screenshot after every step"""

    status = '✓' if step.status == 'passed' else '✗'
    step_display = f"{status} {step.keyword}{step.name}"

    # Log step execution
    if step.status == 'passed':
        logger.debug("step_passed", step=step.name, message=step_display)
    else:
        logger.error("step_failed", step=step.name, status=step.status, message=step_display)

    # Capture screenshot if enabled
    # Note: ScreenshotManager now handles filename sanitization internally
    if os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true':
        ScreenshotManager.capture_screenshot(context.page, step.name)
        logger.debug("screenshot_captured", step=step.name, message="Screenshot saved")


def after_scenario(context, scenario):
    """Cleanup after scenario"""

    # Calculate scenario duration
    duration = None
    if hasattr(context, 'scenario_start_time'):
        duration = (time.time() - context.scenario_start_time) * 1000  # Convert to ms

    # Capture failure screenshot and log details
    if scenario.status == 'failed':
        logger.error("scenario_failed", scenario=scenario.name, message="❌ Scenario failed")
        ScreenshotManager.capture_on_failure(context.page, scenario.name)

        # Log page URL and title for debugging
        try:
            page_url = context.page.url
            page_title = context.page.title()
            logger.error(
                "failure_context",
                url=page_url,
                title=page_title,
                message="Page state at failure"
            )
        except (AttributeError, RuntimeError) as e:
            logger.warning(
                "failure_context_unavailable",
                error=str(e),
                message="Could not retrieve page info"
            )

    elif scenario.status == 'passed':
        logger.info("scenario_passed", scenario=scenario.name, message="✅ Scenario passed")

    # Log screenshot count
    screenshot_count = ScreenshotManager.get_screenshot_count()
    logger.info("screenshots_captured", count=screenshot_count, message=f"📸 Screenshots: {screenshot_count}")

    # Log scenario completion with duration
    log_scenario_end(scenario.name, scenario.status, duration)

    # Close page
    logger.debug("page_cleanup", message="Closing browser page...")
    context.page.close()

    logger.info("="*70)
    print()  # Blank line for readability


def after_all(context):
    """Cleanup after all tests"""

    print()  # Blank line
    logger.info("="*70)
    logger.info("framework_shutdown", message="🏁 Test execution completed - Starting cleanup...")
    logger.info("="*70)

    # Print healing statistics
    if hasattr(context, 'healing_locator'):
        stats = context.healing_locator.get_healing_stats()
        if stats['total_failed_locators'] > 0:
            logger.info(
                "healing_statistics",
                failed_locators=stats['total_failed_locators'],
                healing_attempts=stats['total_healing_attempts'],
                message="🔧 Self-healing statistics"
            )

    # Print wait optimization suggestions
    wait_stats = WaitManager.get_wait_stats()
    if wait_stats['total_waits'] > 0:
        logger.info(
            "wait_statistics",
            total_waits=wait_stats['total_waits'],
            success_rate=f"{wait_stats['success_rate']:.1%}",
            message="⏱️ Wait optimization statistics"
        )

    # Save wait patterns for next run
    logger.debug("wait_patterns_save", message="Saving wait patterns...")
    WaitManager._save_patterns()

    # Shutdown Phoenix tracing
    if PhoenixTracer.is_initialized():
        logger.info("phoenix_shutdown", message="Shutting down Phoenix tracing...")
        PhoenixTracer.shutdown()

    # Close browser
    logger.info("browser_close", message="Closing browser...")
    context.browser.close()

    # Stop Playwright
    logger.info("playwright_stop", message="Stopping Playwright...")
    context.playwright.stop()

    logger.info("="*70)
    logger.info("framework_complete", message="✅ Framework shutdown complete!")
    logger.info("="*70)
    print()  # Blank line
