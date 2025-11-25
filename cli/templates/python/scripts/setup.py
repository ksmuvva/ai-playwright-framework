#!/usr/bin/env python3
"""
AI-Playwright-Framework: Complete Setup Script

Usage:
    uv run python -m scripts.setup

Or directly:
    python -m scripts.setup
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ{Colors.END}  {msg}")


def log_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.END}  {msg}")


def log_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.END}  {msg}")


def log_error(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.END}  {msg}")


def get_playwright_version() -> Optional[str]:
    """Get installed Playwright version."""
    try:
        import playwright
        return playwright.__version__
    except ImportError:
        return None


def check_browsers_installed() -> dict:
    """Check which Playwright browsers are installed."""
    cache_dir = Path.home() / ".cache" / "ms-playwright"

    if not cache_dir.exists():
        return {"chromium": False, "firefox": False, "webkit": False}

    browsers = {}
    for browser in ["chromium", "firefox", "webkit"]:
        browser_dirs = list(cache_dir.glob(f"{browser}-*"))
        browsers[browser] = len(browser_dirs) > 0

    return browsers


def install_browsers(browsers: List[str] = None) -> bool:
    """Install Playwright browsers."""
    if browsers is None:
        browsers = ["chromium"]

    print(f"\n{'─' * 60}")
    print(f"Installing browsers: {', '.join(browsers)}")
    print(f"{'─' * 60}")

    success = True
    for browser in browsers:
        log_info(f"Installing {browser}... (this may take a few minutes)")

        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", browser],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            log_success(f"{browser} installed successfully")
        else:
            log_error(f"Failed to install {browser}")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            success = False

    return success


def install_system_deps(browsers: List[str] = None) -> bool:
    """Install system dependencies (Linux only)."""
    if sys.platform != "linux":
        log_info("System dependencies: Not required (non-Linux)")
        return True

    if browsers is None:
        browsers = ["chromium"]

    print(f"\n{'─' * 60}")
    print("Installing system dependencies (Linux)")
    print(f"{'─' * 60}")
    log_warning("This may require sudo password")

    for browser in browsers:
        log_info(f"Installing dependencies for {browser}...")

        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install-deps", browser],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            log_warning(f"Could not auto-install deps for {browser}")
            log_info("Run manually: sudo playwright install-deps")

    return True


def verify_browser_launch() -> bool:
    """Verify browser can launch."""
    print(f"\n{'─' * 60}")
    print("Verifying browser launch")
    print(f"{'─' * 60}")

    test_script = '''
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com")
        title = page.title()
        browser.close()
        print(f"SUCCESS: {title}")
        exit(0)
except Exception as e:
    print(f"FAILED: {e}")
    exit(1)
'''

    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and "SUCCESS" in result.stdout:
        log_success("Browser verification passed!")
        return True
    else:
        log_error("Browser verification failed")
        if result.stderr:
            print(f"   Error: {result.stderr.strip()}")
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("  AI-Playwright-Framework: Complete Setup")
    print("=" * 70)

    # Check Playwright package
    version = get_playwright_version()
    if not version:
        log_error("Playwright Python package not installed!")
        log_info("Run: uv sync")
        sys.exit(1)

    log_success(f"Playwright package: v{version}")

    # Check browser status
    browsers = check_browsers_installed()
    needs_install = []

    for browser, installed in browsers.items():
        if installed:
            log_success(f"{browser}: Already installed")
        else:
            log_info(f"{browser}: Not installed")
            if browser == "chromium":
                needs_install.append(browser)

    # Install if needed
    if needs_install:
        if not install_browsers(needs_install):
            log_error("Browser installation failed!")
            sys.exit(1)
        install_system_deps(needs_install)
    else:
        log_info("All required browsers already installed")

    # Verify
    if not verify_browser_launch():
        log_error("Setup completed with errors!")
        sys.exit(1)

    print("\n" + "=" * 70)
    log_success("Setup completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Configure .env with API keys")
    print("  2. Record: playwright-ai record --url https://app.com")
    print("  3. Convert: playwright-ai convert recordings/test.json")
    print("  4. Run: uv run behave")
    print()


if __name__ == "__main__":
    main()
