"""
Screenshot Manager - Auto-capture screenshots for every step
"""

from playwright.sync_api import Page
from pathlib import Path
from datetime import datetime
import os
import re

class ScreenshotManager:
    """Auto-capture screenshots for debugging and reporting"""

    screenshot_dir = Path("reports/screenshots")
    step_counter = 0
    current_scenario = ""

    @classmethod
    def _sanitize_filename(cls, name: str) -> str:
        """
        Sanitize filename to be cross-platform compatible

        Removes/replaces characters that are invalid in Windows filenames:
        < > : " / \ | ? * and control characters

        Args:
            name: Original filename

        Returns:
            str: Sanitized filename safe for all platforms
        """
        # Replace Windows-invalid characters with underscores
        # This includes: < > : " / \ | ? * and control characters (0-31)
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)

        # Replace multiple consecutive underscores with single underscore
        sanitized = re.sub(r'_+', '_', sanitized)

        # Remove leading/trailing underscores and whitespace
        sanitized = sanitized.strip('_ ')

        # Limit length to 50 characters
        return sanitized[:50]

    @classmethod
    def setup(cls, scenario_name: str = "test"):
        """
        Initialize screenshot directory

        Args:
            scenario_name: Name of current scenario
        """
        cls.current_scenario = cls._sanitize_filename(scenario_name)
        cls.screenshot_dir.mkdir(parents=True, exist_ok=True)
        cls.step_counter = 0

    @classmethod
    def capture_screenshot(
        cls,
        page: Page,
        name: str,
        full_page: bool = True
    ) -> str:
        """
        Capture screenshot with automatic naming

        Args:
            page: Playwright page object
            name: Screenshot name/description
            full_page: Capture full page or just viewport

        Returns:
            str: Path to saved screenshot
        """
        if not os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true':
            return ""

        try:
            cls.step_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = cls._sanitize_filename(name)

            filename = f"{cls.step_counter:03d}_{timestamp}_{clean_name}.png"

            if cls.current_scenario:
                scenario_dir = cls.screenshot_dir / cls.current_scenario
                scenario_dir.mkdir(exist_ok=True)
                filepath = scenario_dir / filename
            else:
                filepath = cls.screenshot_dir / filename

            page.screenshot(path=str(filepath), full_page=full_page)

            print(f"📸 Screenshot saved: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"⚠️  Failed to capture screenshot: {e}")
            return ""

    @classmethod
    def capture_on_failure(cls, page: Page, test_name: str) -> str:
        """
        Capture screenshot when test fails

        Args:
            page: Playwright page object
            test_name: Name of failed test

        Returns:
            str: Path to saved screenshot
        """
        return cls.capture_screenshot(page, f"FAILURE_{test_name}", full_page=True)

    @classmethod
    def reset_counter(cls):
        """Reset step counter for new test"""
        cls.step_counter = 0

    @classmethod
    def capture_element(
        cls,
        page: Page,
        selector: str,
        name: str
    ) -> str:
        """
        Capture screenshot of specific element

        Args:
            page: Playwright page object
            selector: Element selector
            name: Screenshot name

        Returns:
            str: Path to saved screenshot
        """
        if not os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true':
            return ""

        try:
            element = page.locator(selector)

            if element.count() > 0:
                cls.step_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_name = cls._sanitize_filename(name)

                filename = f"{cls.step_counter:03d}_{timestamp}_{clean_name}_element.png"
                filepath = cls.screenshot_dir / filename

                element.first.screenshot(path=str(filepath))

                print(f"📸 Element screenshot saved: {filepath}")
                return str(filepath)

        except Exception as e:
            print(f"⚠️  Failed to capture element screenshot: {e}")
            return ""

    @classmethod
    def get_screenshot_count(cls) -> int:
        """Get total number of screenshots captured in current scenario"""
        return cls.step_counter

    @classmethod
    def cleanup_old_screenshots(cls, days: int = 7):
        """
        Delete screenshots older than specified days

        Args:
            days: Number of days to keep screenshots
        """
        import time

        if not cls.screenshot_dir.exists():
            return

        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)

        for screenshot in cls.screenshot_dir.rglob('*.png'):
            if screenshot.stat().st_mtime < cutoff_time:
                screenshot.unlink()
                print(f"🗑️  Deleted old screenshot: {screenshot}")
