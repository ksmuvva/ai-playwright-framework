"""
Generate Helpers Command.

Generates helper functions based on project patterns and requirements.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="helpers",
    help="Output directory for generated helpers",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["all", "auth", "navigation", "data", "wait", "screenshot", "power-apps"]),
    default="all",
    help="Type of helpers to generate",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@click.option(
    "--analyze", "-a", is_flag=True, help="Analyze existing code for patterns before generating"
)
def generate_helpers(output: str, type: str, force: bool, analyze: bool) -> None:
    """
    Generate helper functions for test automation.

    \b
    USAGE:
        cpa generate-helpers [OPTIONS]

    \b
    EXAMPLES:
        # Generate all helper functions
        cpa generate-helpers

        # Generate only authentication helpers
        cpa generate-helpers --type auth

        # Analyze existing code first
        cpa generate-helpers --analyze

        # Output to specific directory
        cpa generate-helpers --output custom_helpers

    \b
    HELPER TYPES:
        all        Generate all helper modules (default)
        auth       Authentication helpers
        navigation Navigation helpers
        data       Data generation helpers
        wait       Wait management helpers
        screenshot Screenshot helpers
        power-apps Power Apps specific helpers
    """
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel.fit(
            f"[bold cyan]Generating Helper Functions[/bold cyan]\n\n"
            f"[cyan]Output:[/cyan] {output_path.absolute()}\n"
            f"[cyan]Type:[/cyan] {type}\n"
            f"[cyan]Analyze:[/cyan] {'Yes' if analyze else 'No'}",
            title="Generate Helpers",
            border_style="blue",
        )
    )

    if analyze:
        patterns = _analyze_existing_code()
        console.print("\n[bold yellow]Detected Patterns:[/bold yellow]")
        for pattern in patterns:
            console.print(f"  - {pattern}")

    generated_files = []

    helper_templates = {
        "auth": ("auth_helper.py", _generate_auth_helper),
        "navigation": ("navigation_helper.py", _generate_navigation_helper),
        "data": ("data_generator.py", _generate_data_helper),
        "wait": ("wait_manager.py", _generate_wait_helper),
        "screenshot": ("screenshot_manager.py", _generate_screenshot_helper),
    }

    if type == "all":
        types_to_generate = list(helper_templates.keys())
        if analyze:
            types_to_generate.append("power-apps")
    else:
        types_to_generate = [type] if type in helper_templates else []

    for helper_type in types_to_generate:
        if helper_type in helper_templates:
            filename, generator = helper_templates[helper_type]
            file_path = output_path / filename

            if file_path.exists() and not force:
                console.print(
                    f"[yellow]Skipping {filename} (exists, use --force to overwrite)[/yellow]"
                )
                continue

            content = generator()
            file_path.write_text(content)
            generated_files.append(str(file_path))
            console.print(f"[green]Generated:[/green] {filename}")

    if "power-apps" in types_to_generate or (analyze and "power-apps" in types_to_generate):
        power_apps_file = output_path / "power_apps_helper.py"
        content = _generate_power_apps_helper()
        power_apps_file.write_text(content)
        generated_files.append(str(power_apps_file))
        console.print(f"[green]Generated:[/green] power_apps_helper.py")

    if generated_files:
        console.print("\n[bold green]Summary:[/bold green]")
        table = Table(show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")

        for file in generated_files:
            table.add_row(file, "Created")

        console.print(table)
        _print_usage_instructions(output_path)
    else:
        console.print("\n[yellow]No files generated.[/yellow]")


def _analyze_existing_code() -> List[str]:
    """Analyze existing code for patterns."""
    patterns = []

    feature_files = list(Path("features").glob("*.feature"))
    step_files = list(Path("steps").glob("*.py"))

    if any("login" in f.name.lower() for f in feature_files):
        patterns.append("Login/Authentication flows detected")
    if any("navigate" in f.name.lower() or "go to" in f.name.lower() for f in step_files):
        patterns.append("Navigation patterns detected")
    if any("form" in f.name.lower() or "fill" in f.name.lower() for f in step_files):
        patterns.append("Form handling detected")
    if any("wait" in f.name.lower() or "sleep" in f.name.lower() for f in step_files):
        patterns.append("Wait/sleep patterns detected - consider using wait_manager")

    if not patterns:
        patterns.append("No specific patterns detected - generating standard helpers")

    return patterns


def _generate_auth_helper() -> str:
    """Generate authentication helper template."""
    return '''"""Authentication Helper Module."""

from typing import Optional
from playwright.async_api import Page


class AuthHelper:
    """Authentication helper for managing user logins and sessions."""

    def __init__(self, credentials_file: Optional[str] = None):
        """Initialize the authentication helper."""
        self.credentials_file = credentials_file

    async def authenticate_user(
        self,
        page: Page,
        base_url: str,
        username: str,
        password: str,
        login_url: Optional[str] = None
    ) -> bool:
        """Authenticate a user with username and password."""
        login_page = login_url or f"{base_url}/login"
        await page.goto(login_page)
        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')
        return await self.check_authentication_state(page)

    async def logout(self, page: Page, base_url: str) -> bool:
        """Log out the current user."""
        await page.goto(f"{base_url}/logout")
        return True

    async def check_authentication_state(self, page: Page) -> bool:
        """Check if user is currently authenticated."""
        try:
            await page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False
'''


def _generate_navigation_helper() -> str:
    """Generate navigation helper template."""
    return '''"""Navigation Helper Module."""

from typing import Optional
from playwright.async_api import Page


class NavigationHelper:
    """Navigation helper for managing page navigation."""

    DEFAULT_TIMEOUT = 30000

    def __init__(self, default_timeout: int = None):
        """Initialize the navigation helper."""
        self.default_timeout = default_timeout or self.DEFAULT_TIMEOUT

    async def navigate_to(
        self,
        page: Page,
        url: str,
        timeout: Optional[int] = None
    ) -> bool:
        """Navigate to a specific URL."""
        timeout = timeout or self.default_timeout
        try:
            await page.goto(url, timeout=timeout)
            return True
        except Exception:
            return False

    async def navigate_back(self, page: Page) -> bool:
        """Navigate back to the previous page."""
        try:
            await page.go_back()
            return True
        except Exception:
            return False

    async def wait_for_page_load(self, page: Page, timeout: int = None) -> bool:
        """Wait for the page to fully load."""
        timeout = timeout or self.default_timeout
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception:
            return False
'''


def _generate_data_helper() -> str:
    """Generate data generation helper template."""
    return '''"""Data Generator Module (AI-Powered)."""

import random
import string
from typing import Any, Dict, List, Optional


class DataGenerator:
    """AI-powered data generator for test automation."""

    FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Michael", "Linda"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]

    def generate_random_email(self, first_name: str = None, last_name: str = None) -> str:
        """Generate a random email address."""
        first = (first_name or random.choice(self.FIRST_NAMES)).lower()
        last = (last_name or random.choice(self.LAST_NAMES)).lower()
        return f"{first}.{last}@test.com"

    def generate_phone_number(self, country_code: str = "+1") -> str:
        """Generate a random phone number."""
        area = str(random.randint(200, 999))
        exchange = str(random.randint(200, 999))
        subscriber = str(random.randint(1000, 9999))
        return f"({area}) {exchange}-{subscriber}"

    def generate_company_data(self) -> Dict[str, str]:
        """Generate company information."""
        return {
            "name": f"Test Company {random.randint(1, 1000)}",
            "email": self.generate_random_email(),
            "phone": self.generate_phone_number(),
        }

    def generate_address(self) -> Dict[str, str]:
        """Generate a random address."""
        return {
            "street": f"{random.randint(100, 9999)} Test Street",
            "city": "Test City",
            "state": "TS",
            "zip_code": str(random.randint(10000, 99999)),
        }
'''


def _generate_wait_helper() -> str:
    """Generate wait management helper template."""
    return '''"""Wait Manager Module (AI-Powered)."""

from typing import Callable, Optional
from playwright.async_api import Page
from enum import Enum


class WaitType(Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ATTACHED = "attached"
    DETACHED = "detached"


class WaitManager:
    """AI-powered wait manager for intelligent element waiting."""

    DEFAULT_TIMEOUT = 30000

    def __init__(self, default_timeout: int = None):
        """Initialize the wait manager."""
        self.default_timeout = default_timeout or self.DEFAULT_TIMEOUT

    async def wait_for_element(
        self,
        page: Page,
        selector: str,
        wait_type: WaitType = WaitType.VISIBLE,
        timeout: int = None
    ) -> bool:
        """Wait for an element to be in a specific state."""
        timeout = timeout or self.default_timeout
        try:
            await page.wait_for_selector(selector, state=wait_type.value, timeout=timeout)
            return True
        except Exception:
            return False

    async def wait_for_network_idle(self, page: Page, timeout: int = None) -> bool:
        """Wait for network to be idle."""
        timeout = timeout or self.default_timeout
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception:
            return False
'''


def _generate_screenshot_helper() -> str:
    """Generate screenshot manager helper template."""
    return '''"""Screenshot Manager Module."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.async_api import Page


class ScreenshotManager:
    """Screenshot manager for capturing and managing test evidence."""

    def __init__(self, output_dir: str = "reports/screenshots"):
        """Initialize the screenshot manager."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def capture_screenshot(
        self,
        page: Page,
        name: str,
        full_page: bool = True
    ) -> str:
        """Capture a screenshot with a given name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.output_dir / filename
        await page.screenshot(path=str(filepath), full_page=full_page)
        return str(filepath)

    async def capture_on_failure(self, page: Page, test_name: str) -> str:
        """Capture screenshot when a test fails."""
        return await self.capture_screenshot(page, f"FAILURE_{test_name}")
'''


def _generate_power_apps_helper() -> str:
    """Generate Power Apps specific helper."""
    return '''"""Power Apps Helper Module.

Power Apps specific utilities for model-driven application testing.
"""

from typing import Optional
from playwright.async_api import Page


class PowerAppsHelper:
    """Helper for Power Apps model-driven application testing."""

    POWER_APPS_SELECTORS = {
        "canvas": "[role='application'], .canvas-app",
        "navigation": "[data-powerapps-navigate]",
        "command_bar": ".commandBar, [role='toolbar']",
        "form": "[role='form'], .powerapps-form",
        "grid": "[role='grid'], .data-grid",
        "dialog": "[role='dialog'], .dialog",
    }

    async def wait_for_power_apps_load(self, page: Page, timeout: int = 60000) -> bool:
        """Wait for Power Apps to fully load."""
        try:
            await page.wait_for_selector(
                self.POWER_APPS_SELECTORS["canvas"],
                state="visible",
                timeout=timeout
            )
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception:
            return False

    async def navigate_to_entity(self, page: Page, entity_name: str) -> bool:
        """Navigate to a specific Power Apps entity."""
        try:
            nav_item = page.locator(
                f"text={entity_name}, [aria-label*='{entity_name}']"
            ).first
            await nav_item.click()
            return True
        except Exception:
            return False

    async def open_record(self, page: Page, record_id: str) -> bool:
        """Open a specific record by ID."""
        try:
            record = page.locator(f"[data-id='{record_id}']").first
            await record.dblclick()
            return True
        except Exception:
            return False

    async def save_record(self, page: Page) -> bool:
        """Save the current record."""
        try:
            save_button = page.locator(
                "button[aria-label*='Save'], [data-command='save']"
            ).first
            await save_button.click()
            return True
        except Exception:
            return False
'''


def _print_usage_instructions(output_path: Path) -> None:
    """Print instructions for using generated helpers."""
    console.print("\n[bold yellow]Usage Instructions:[/bold yellow]")
    console.print(f"""
  1. Import the helpers in your step definitions:

     from helpers.auth_helper import AuthHelper
     from helpers.navigation_helper import NavigationHelper
     from helpers.data_generator import DataGenerator

  2. Initialize helpers:

     auth = AuthHelper()
     nav = NavigationHelper()
     data = DataGenerator()

  3. Use in your tests:

     await auth.authenticate_user(page, "https://app.com", "user", "pass")
     email = data.generate_random_email()
""")
