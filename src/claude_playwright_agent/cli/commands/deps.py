"""
Dependency management commands.

This module provides commands for:
- Checking if all dependencies are installed
- Installing missing dependencies
- Verifying Playwright browsers
- Checking Python packages
"""

import sys
import subprocess
from pathlib import Path
from typing import Any

import click
from packaging import version
from rich.console import Console
from rich.table import Table

from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.state import StateManager

console = Console()


def print_timestamp(message: str, style: str = "") -> None:
    """Print a message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"[{timestamp}] {message}", style=style)


# =============================================================================
# Required Dependencies
# =============================================================================

# Minimum required versions
REQUIRED_PYTHON_VERSION = "3.9"
REQUIRED_PYTHON_PACKAGES = {
    "playwright": "1.40.0",
    "pydantic": "2.0.0",
    "click": "8.1.0",
    "rich": "13.0.0",
    "jinja2": "3.1.0",
}

# Optional but recommended packages
OPTIONAL_PYTHON_PACKAGES = {
    "behave": "1.2.0",
    "pytest-bdd": "7.0.0",
    "pytest": "8.0.0",
    "allure-behave": "2.12.0",
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_python_version() -> str:
    """Get current Python version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_python_version() -> tuple[bool, str]:
    """
    Check if Python version meets minimum requirements.

    Returns:
        Tuple of (is_satisfied, current_version)
    """
    current = get_python_version()
    try:
        return version.parse(current) >= version.parse(REQUIRED_PYTHON_VERSION), current
    except version.InvalidVersion:
        return True, current


def get_installed_packages() -> dict[str, str]:
    """
    Get all installed packages and their versions.

    Returns:
        Dict mapping package name to version
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
        import json
        packages = json.loads(result.stdout)
        return {pkg["name"].lower(): pkg["version"] for pkg in packages}
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def check_package_installed(
    package_name: str,
    min_version: str,
    installed: dict[str, str],
) -> tuple[bool, str, str]:
    """
    Check if a package is installed and meets minimum version.

    Args:
        package_name: Name of the package
        min_version: Minimum required version
        installed: Dict of installed packages

    Returns:
        Tuple of (is_installed, installed_version, status)
    """
    installed_version = installed.get(package_name.lower(), "")

    if not installed_version:
        return False, "", "NOT_INSTALLED"

    try:
        if version.parse(installed_version) >= version.parse(min_version):
            return True, installed_version, "OK"
        else:
            return False, installed_version, "OUTDATED"
    except version.InvalidVersion:
        # If we can't parse version, assume it's OK
        return True, installed_version, "UNKNOWN"


def check_playwright_browsers() -> dict[str, Any]:
    """
    Check which Playwright browsers are installed.

    Returns:
        Dict with browser installation status
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
        )
        # Check if browsers are already installed
        is_installed = result.returncode == 0 or "already installed" in result.stderr.lower()
        return {
            "chromium": is_installed,
            "firefox": False,  # Simplified check
            "webkit": False,
            "any_installed": is_installed,
        }
    except Exception:
        return {
            "chromium": False,
            "firefox": False,
            "webkit": False,
            "any_installed": False,
        }


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def deps() -> None:
    """
    Manage project dependencies.

    Check and install required dependencies for the Claude Playwright Agent.
    """
    pass


@deps.command(name="check")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed information",
)
def check_deps(project_path: str, verbose: bool) -> None:
    """
    Check if all dependencies are installed.

    Checks:
    - Python version
    - Required Python packages
    - Optional Python packages
    - Playwright browsers

    Example:
        cpa deps check
        cpa deps check --verbose
    """
    project_path = Path(project_path)

    print_timestamp("🔍 Checking dependencies...", "bold blue")

    # Check if project is initialized
    is_initialized = StateManager.is_initialized(project_path)
    if is_initialized:
        try:
            config = ConfigManager(project_path)
            console.print(f"   Project: {config.framework.project_name}")
            console.print(f"   Framework: {config.framework.bdd_framework.value}")
        except Exception:
            pass
    console.print("")

    all_ok = True
    issues = []

    # ========================================================================
    # Check Python version
    # ========================================================================

    print_timestamp("📦 Checking Python version...", "cyan")

    python_ok, python_version = check_python_version()
    if python_ok:
        console.print(f"   ✅ Python {python_version} (>= {REQUIRED_PYTHON_VERSION})", style="green")
    else:
        console.print(
            f"   ❌ Python {python_version} (< {REQUIRED_PYTHON_VERSION})",
            style="bold red"
        )
        issues.append(f"Python version must be >= {REQUIRED_PYTHON_VERSION}")
        all_ok = False

    console.print("")

    # ========================================================================
    # Check required packages
    # ========================================================================

    print_timestamp("📦 Checking required Python packages...", "cyan")

    installed = get_installed_packages()
    required_table = Table(show_header=True)
    required_table.add_column("Package", style="cyan")
    required_table.add_column("Required", style="yellow")
    required_table.add_column("Installed", style="blue")
    required_table.add_column("Status", style="bold")

    for package, min_ver in REQUIRED_PYTHON_PACKAGES.items():
        is_ok, installed_ver, status = check_package_installed(package, min_ver, installed)

        if status == "OK":
            required_table.add_row(
                package,
                f">= {min_ver}",
                installed_ver,
                "[green]✓ OK[/green]"
            )
        elif status == "OUTDATED":
            required_table.add_row(
                package,
                f">= {min_ver}",
                installed_ver,
                "[yellow]⚠ OUTDATED[/yellow]"
            )
            issues.append(f"{package}: version {installed_ver} < {min_ver}")
            all_ok = False
        else:  # NOT_INSTALLED
            required_table.add_row(
                package,
                f">= {min_ver}",
                "-",
                "[red]✗ MISSING[/red]"
            )
            issues.append(f"{package}: not installed")
            all_ok = False

    console.print(required_table)
    console.print("")

    # ========================================================================
    # Check optional packages
    # ========================================================================

    if verbose:
        print_timestamp("📦 Checking optional Python packages...", "cyan")

        optional_table = Table(show_header=True)
        optional_table.add_column("Package", style="cyan")
        optional_table.add_column("Minimum", style="dim")
        optional_table.add_column("Installed", style="blue")
        optional_table.add_column("Status", style="dim")

        for package, min_ver in OPTIONAL_PYTHON_PACKAGES.items():
            is_ok, installed_ver, status = check_package_installed(package, min_ver, installed)

            if status == "OK":
                optional_table.add_row(
                    package,
                    f">= {min_ver}",
                    installed_ver,
                    "[green]✓ Installed[/green]"
                )
            elif status == "OUTDATED":
                optional_table.add_row(
                    package,
                    f">= {min_ver}",
                    installed_ver,
                    "[yellow]⚠ Outdated[/yellow]"
                )
            else:
                optional_table.add_row(
                    package,
                    f">= {min_ver}",
                    "-",
                    "[dim]✗ Not installed[/dim]"
                )

        console.print(optional_table)
        console.print("")

    # ========================================================================
    # Check Playwright browsers
    # ========================================================================

    print_timestamp("🌐 Checking Playwright browsers...", "cyan")

    browsers = check_playwright_browsers()

    browser_table = Table(show_header=True)
    browser_table.add_column("Browser", style="cyan")
    browser_table.add_column("Status", style="bold")

    for browser_name, is_installed in [
        ("Chromium", browsers["chromium"]),
        ("Firefox", browsers["firefox"]),
        ("WebKit", browsers["webkit"]),
    ]:
        if is_installed:
            browser_table.add_row(browser_name, "[green]✓ Installed[/green]")
        else:
            browser_table.add_row(browser_name, "[red]✗ Not installed[/red]")
            if browser_name == "Chromium":  # Chromium is recommended
                issues.append(f"{browser_name} browser not installed")
                all_ok = False

    console.print(browser_table)
    console.print("")

    # ========================================================================
    # Summary
    # ========================================================================

    if all_ok:
        print_timestamp("✅ All dependencies are satisfied!", "bold green")
        console.print("")
        console.print("   You're ready to:")
        console.print("   - cpa ingest <recording.js>")
        console.print("   - cpa run")
    else:
        print_timestamp("⚠️  Some dependencies are missing or outdated.", "bold yellow")
        console.print("")
        if issues:
            console.print("   Issues found:", style="yellow")
            for issue in issues:
                console.print(f"   • {issue}", style="dim")
        console.print("")
        console.print("   Run to fix:", style="cyan")
        console.print("   cpa deps install")


@deps.command(name="install")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--include-optional",
    is_flag=True,
    help="Also install optional packages",
)
@click.option(
    "--browsers",
    type=click.Choice(["chromium", "firefox", "webkit", "all"]),
    default="chromium",
    help="Which Playwright browsers to install",
)
def install_deps(project_path: str, include_optional: bool, browsers: str) -> None:
    """
    Install missing dependencies.

    Installs:
    - Required Python packages
    - Optional Python packages (if --include-optional)
    - Playwright browsers

    Example:
        cpa deps install
        cpa deps install --include-optional
        cpa deps install --browsers all
    """
    project_path = Path(project_path)

    print_timestamp("📦 Installing dependencies...", "bold blue")

    # ========================================================================
    # Install required packages
    # ========================================================================

    print_timestamp("📦 Installing required Python packages...", "cyan")

    required_packages = " ".join(
        f"{pkg}>={ver}"
        for pkg, ver in REQUIRED_PYTHON_PACKAGES.items()
    )

    console.print(f"   Installing: {required_packages}")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", *REQUIRED_PYTHON_PACKAGES.keys()],
            check=True,
        )
        console.print("   ✅ Required packages installed", style="green")
    except subprocess.CalledProcessError as e:
        console.print(f"   ❌ Failed to install packages: {e}", style="bold red")
        sys.exit(1)

    console.print("")

    # ========================================================================
    # Install optional packages
    # ========================================================================

    if include_optional:
        print_timestamp("📦 Installing optional Python packages...", "cyan")

        optional_names = list(OPTIONAL_PYTHON_PACKAGES.keys())
        console.print(f"   Installing: {', '.join(optional_names)}")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", *optional_names],
                check=False,  # Don't fail if optional packages fail
            )
            console.print("   ✅ Optional packages installed (or already present)", style="green")
        except Exception:
            console.print("   ⚠️  Some optional packages failed to install", style="yellow")

        console.print("")

    # ========================================================================
    # Install Playwright browsers
    # ========================================================================

    print_timestamp(f"🌐 Installing Playwright browser(s)...", "cyan")

    browser_targets = []
    if browsers == "all":
        browser_targets = ["chromium", "firefox", "webkit"]
    else:
        browser_targets = [browsers]

    console.print(f"   Installing: {', '.join(browser_targets)}")

    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", *browser_targets],
            check=True,
        )
        console.print("   ✅ Playwright browsers installed", style="green")
    except subprocess.CalledProcessError as e:
        console.print(f"   ❌ Failed to install browsers: {e}", style="bold red")
        sys.exit(1)

    console.print("")

    # ========================================================================
    # Summary
    # ========================================================================

    print_timestamp("✅ Dependency installation complete!", "bold green")
    console.print("")
    console.print("   Next steps:")
    console.print("   1. Verify installation: cpa deps check")
    console.print("   2. Start testing: cpa ingest <recording.js>")


@deps.command(name="verify")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def verify_deps(project_path: str) -> None:
    """
    Quick verification that critical dependencies are present.

    Exits with code 1 if any critical dependency is missing.

    Example:
        cpa deps verify && cpa run
    """
    project_path = Path(project_path)

    # Quick checks
    installed = get_installed_packages()
    all_ok = True

    # Check required packages
    for package, min_ver in REQUIRED_PYTHON_PACKAGES.items():
        is_ok, _, status = check_package_installed(package, min_ver, installed)
        if status != "OK":
            console.print(f"❌ {package} is missing or outdated", style="red")
            all_ok = False

    # Check Playwright
    browsers = check_playwright_browsers()
    if not browsers.get("chromium", False):
        console.print("❌ Playwright Chromium not installed", style="red")
        all_ok = False

    if all_ok:
        console.print("✅ All critical dependencies verified", style="green")
    else:
        console.print("❌ Dependencies missing. Run: cpa deps install", style="red")
        sys.exit(1)
