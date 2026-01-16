"""
E1.5 - Dependency Management Skill.

This skill provides dependency management:
- Python package dependency checking
- Package installation
- Playwright browser installation
- Version tracking and updates
- Requirements file generation
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class DependencyManagementAgent(BaseAgent):
    """
    Agent for dependency management.

    This agent provides:
    1. Python package dependency checking
    2. Package installation
    3. Playwright browser installation
    4. Version tracking and updates
    5. Requirements file generation
    """

    name = "e1_5_dependency_management"
    version = "1.0.0"
    description = "E1.5 - Dependency Management"

    # Core dependencies
    CORE_DEPENDENCIES = {
        "playwright": "1.40.0",
        "click": "8.0.0",
        "rich": "13.0.0",
        "pydantic": "2.0.0",
    }

    # Optional framework dependencies
    FRAMEWORK_DEPENDENCIES = {
        "behave": ["behave>=1.2.6"],
        "pytest-bdd": ["pytest-bdd>=7.0.0", "pytest>=7.4.0"],
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the dependency management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E1.5 - Dependency Management agent for the Playwright test automation framework. You help users with e1.5 - dependency management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._installed_packages: dict[str, str] = {}
        self._installed_browsers: dict[str, bool] = {}

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute dependency management task.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Result of the dependency operation
        """
        task_type = context.get("task_type", task)

        if task_type == "check_dependencies":
            return await self._check_dependencies(context)
        elif task_type == "install_dependencies":
            return await self._install_dependencies(context)
        elif task_type == "check_browsers":
            return await self._check_browsers(context)
        elif task_type == "install_browsers":
            return await self._install_browsers(context)
        elif task_type == "generate_requirements":
            return await self._generate_requirements(context)
        elif task_type == "update_dependencies":
            return await self._update_dependencies(context)
        elif task_type == "get_dependency_status":
            return await self._get_dependency_status(context)
        else:
            return f"Unknown task type: {task_type}"

    async def _check_dependencies(self, context: dict[str, Any]) -> str:
        """Check if all required dependencies are installed."""
        missing = []
        outdated = []

        # Check core dependencies
        for package, min_version in self.CORE_DEPENDENCIES.items():
            installed_version = self._get_installed_version(package)
            if installed_version is None:
                missing.append(package)
            elif self._compare_versions(installed_version, min_version) < 0:
                outdated.append(f"{package} (installed: {installed_version}, required: {min_version})")

        # Check framework dependencies
        framework = context.get("framework", "behave")
        if framework in self.FRAMEWORK_DEPENDENCIES:
            for dep_spec in self.FRAMEWORK_DEPENDENCIES[framework]:
                package = dep_spec.split(">=")[0].split("==")[0]
                installed_version = self._get_installed_version(package)
                if installed_version is None:
                    missing.append(package)

        if missing or outdated:
            result = []
            if missing:
                result.append(f"Missing packages: {', '.join(missing)}")
            if outdated:
                result.append(f"Outdated packages: {', '.join(outdated)}")
            return "\n".join(result)

        return "All dependencies are installed and up-to-date"

    async def _install_dependencies(self, context: dict[str, Any]) -> str:
        """Install missing dependencies."""
        framework = context.get("framework", "behave")
        auto_install = context.get("auto_install", False)

        packages_to_install = []

        # Check core dependencies
        for package, min_version in self.CORE_DEPENDENCIES.items():
            installed_version = self._get_installed_version(package)
            if installed_version is None:
                packages_to_install.append(f"{package}>={min_version}")

        # Check framework dependencies
        if framework in self.FRAMEWORK_DEPENDENCIES:
            for dep_spec in self.FRAMEWORK_DEPENDENCIES[framework]:
                package = dep_spec.split(">=")[0].split("==")[0]
                installed_version = self._get_installed_version(package)
                if installed_version is None:
                    packages_to_install.append(dep_spec)

        if not packages_to_install:
            return "All dependencies are already installed"

        if not auto_install:
            return f"Would install: {', '.join(packages_to_install)}"

        # Install packages
        for package in packages_to_install:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                return f"Failed to install: {package}"

        return f"Installed: {', '.join(packages_to_install)}"

    async def _check_browsers(self, context: dict[str, Any]) -> str:
        """Check if Playwright browsers are installed."""
        browsers = context.get("browsers", ["chromium"])
        missing = []

        for browser in browsers:
            installed = self._check_browser_installed(browser)
            self._installed_browsers[browser] = installed
            if not installed:
                missing.append(browser)

        if missing:
            return f"Missing browsers: {', '.join(missing)}"

        return f"All browsers installed: {', '.join(browsers)}"

    async def _install_browsers(self, context: dict[str, Any]) -> str:
        """Install Playwright browsers."""
        browsers = context.get("browsers", ["chromium"])
        auto_install = context.get("auto_install", False)

        missing = []
        for browser in browsers:
            if not self._check_browser_installed(browser):
                missing.append(browser)

        if not missing:
            return f"All browsers already installed: {', '.join(browsers)}"

        if not auto_install:
            return f"Would install browsers: {', '.join(missing)}"

        # Install browsers
        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install"] + missing,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Installed browsers: {', '.join(missing)}"
        except subprocess.CalledProcessError:
            return f"Failed to install browsers: {', '.join(missing)}"

    async def _generate_requirements(self, context: dict[str, Any]) -> str:
        """Generate requirements.txt file."""
        framework = context.get("framework", "behave")
        output_path = context.get("output_path", "requirements.txt")

        requirements = []

        # Add core dependencies
        for package, min_version in self.CORE_DEPENDENCIES.items():
            requirements.append(f"{package}>={min_version}")

        # Add framework dependencies
        if framework in self.FRAMEWORK_DEPENDENCIES:
            requirements.extend(self.FRAMEWORK_DEPENDENCIES[framework])

        # Write requirements file
        output_file = Path(output_path)
        output_file.write_text("\n".join(requirements) + "\n")

        return f"Requirements file generated: {output_path}"

    async def _update_dependencies(self, context: dict[str, Any]) -> str:
        """Update all dependencies to latest versions."""
        updated = []

        for package in self.CORE_DEPENDENCIES.keys():
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--upgrade", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                updated.append(package)
            except subprocess.CalledProcessError:
                pass

        if updated:
            return f"Updated packages: {', '.join(updated)}"
        else:
            return "No packages were updated"

    async def _get_dependency_status(self, context: dict[str, Any]) -> str:
        """Get comprehensive dependency status."""
        status_lines = ["Dependency Status:", ""]

        # Python packages
        status_lines.append("Python Packages:")
        for package, min_version in self.CORE_DEPENDENCIES.items():
            installed_version = self._get_installed_version(package)
            if installed_version:
                status = "✓" if self._compare_versions(installed_version, min_version) >= 0 else "⚠"
                status_lines.append(f"  {status} {package}: {installed_version}")
            else:
                status_lines.append(f"  ✗ {package}: Not installed")

        # Browsers
        status_lines.append("\nPlaywright Browsers:")
        for browser in ["chromium", "firefox", "webkit"]:
            installed = self._check_browser_installed(browser)
            status = "✓" if installed else "✗"
            status_lines.append(f"  {status} {browser}: {'Installed' if installed else 'Not installed'}")

        return "\n".join(status_lines)

    def _get_installed_version(self, package: str) -> str | None:
        """Get installed version of a package."""
        if package in self._installed_packages:
            return self._installed_packages[package]

        try:
            result = subprocess.check_output(
                [sys.executable, "-m", "pip", "show", package],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in result.split("\n"):
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    self._installed_packages[package] = version
                    return version
        except subprocess.CalledProcessError:
            pass

        return None

    def _check_browser_installed(self, browser: str) -> bool:
        """Check if a Playwright browser is installed."""
        try:
            result = subprocess.check_output(
                [sys.executable, "-m", "playwright", "install", "--dry-run", browser],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            # If the output doesn't contain "Download", it's already installed
            return "Download" not in result
        except subprocess.CalledProcessError:
            return False

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings."""
        def parse_version(v):
            return [int(x) for x in v.split(".")]

        v1_parts = parse_version(v1)
        v2_parts = parse_version(v2)

        for a, b in zip(v1_parts, v2_parts):
            if a < b:
                return -1
            elif a > b:
                return 1

        if len(v1_parts) < len(v2_parts):
            return -1
        elif len(v1_parts) > len(v2_parts):
            return 1

        return 0

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

