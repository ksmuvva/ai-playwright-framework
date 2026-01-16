"""
E1.3 - Project Initialization Skill.

This skill provides project scaffolding:
- Project directory structure creation
- BDD framework setup (Behave, pytest-bdd)
- Template-based file generation
- Configuration file creation
- Initial state and config setup
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ProjectInitializationAgent(BaseAgent):
    """
    Agent for project initialization and scaffolding.

    This agent provides:
    1. Project directory structure creation
    2. BDD framework setup (Behave, pytest-bdd)
    3. Template-based file generation
    4. Configuration file creation
    5. Initial state and config setup
    """

    name = "e1_3_project_initialization"
    version = "1.0.0"
    description = "E1.3 - Project Initialization"

    def __init__(self, **kwargs) -> None:
        """Initialize the project initialization agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a E1.3 - Project Initialization agent for the Playwright test automation framework. You help users with e1.3 - project initialization tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []

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
        Execute project initialization task.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Result of the initialization operation
        """
        task_type = context.get("task_type", task)

        if task_type == "initialize_project":
            return await self._initialize_project(context)
        elif task_type == "create_directory_structure":
            return await self._create_directory_structure(context)
        elif task_type == "generate_framework_files":
            return await self._generate_framework_files(context)
        elif task_type == "create_config_files":
            return await self._create_config_files(context)
        elif task_type == "setup_state":
            return await self._setup_state(context)
        elif task_type == "validate_project":
            return await self._validate_project(context)
        else:
            return f"Unknown task type: {task_type}"

    async def _initialize_project(self, context: dict[str, Any]) -> str:
        """Initialize a new project."""
        project_name = context.get("project_name", "my-test-project")
        framework = context.get("framework", "behave")
        template = context.get("template", "basic")
        project_path = Path(context.get("project_path", "."))

        # Check if already initialized
        cpa_dir = project_path / ".cpa"
        if cpa_dir.exists():
            return f"Project already initialized at {project_path}"

        # Create directory structure
        await self._create_directory_structure(context)

        # Generate framework files
        await self._generate_framework_files(context)

        # Create config files
        await self._create_config_files(context)

        # Setup state
        await self._setup_state(context)

        return f"Project '{project_name}' initialized successfully with {framework} framework"

    async def _create_directory_structure(self, context: dict[str, Any]) -> str:
        """Create project directory structure."""
        project_path = Path(context.get("project_path", "."))
        framework = context.get("framework", "behave")

        directories = [
            ".cpa",
            "features",
            "features/steps",
            "pages",
            "recordings",
            "reports",
            "tests" if framework == "pytest-bdd" else None,
        ]

        # Filter out None values and create directories
        for directory in filter(None, directories):
            dir_path = project_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        return f"Directory structure created at {project_path}"

    async def _generate_framework_files(self, context: dict[str, Any]) -> str:
        """Generate framework-specific files."""
        project_path = Path(context.get("project_path", "."))
        framework = context.get("framework", "behave")

        if framework == "behave":
            # Create conftest.py for Behave
            conftest_content = '''"""
Behave environment configuration.
"""

from behave import use_fixture
from playwright.sync_api import Page, BrowserContext


def before_scenario(context, scenario):
    """Setup before each scenario."""
    # Initialize Playwright page
    context.page = context.browser.new_page()


def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    # Close page if exists
    if hasattr(context, "page"):
        context.page.close()
'''
            (project_path / "features" / "conftest.py").write_text(conftest_content)

            # Create example feature file
            feature_content = '''Feature: Example Feature
  As a user
  I want to perform actions
  So that I can test the application

  Scenario: Example scenario
    Given I navigate to the homepage
    When I perform an action
    Then I should see the result
'''
            (project_path / "features" / "example.feature").write_text(feature_content)

        elif framework == "pytest-bdd":
            # Create conftest.py for pytest-bdd
            conftest_content = '''"""
Pytest-bdd configuration.
"""

import pytest
from playwright.sync_api import Page, BrowserContext


@pytest.fixture
def browser_context_args(browser_context_args):
    """Playwright browser context args."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture
def page(browser):
    """Playwright page fixture."""
    page = browser.new_page()
    yield page
    page.close()
'''
            (project_path / "conftest.py").write_text(conftest_content)

        return f"Framework files generated for {framework}"

    async def _create_config_files(self, context: dict[str, Any]) -> str:
        """Create configuration files."""
        from claude_playwright_agent.config import ConfigManager

        project_path = Path(context.get("project_path", "."))
        profile = context.get("profile", "default")

        config_manager = ConfigManager(project_path, profile=profile)
        config_manager.update(
            framework_bdd_framework=context.get("framework", "behave"),
            framework_template=context.get("template", "basic"),
            framework_base_url=context.get("base_url", "http://localhost:8000"),
        )
        config_manager.save()

        # Create requirements.txt
        requirements = '''# Playwright
playwright>=1.40.0

# BDD Framework
behave>=1.2.6

# Testing
pytest>=7.4.0
pytest-bdd>=7.0.0

# Reporting
allure-pytest>=2.13.2
'''
        (project_path / "requirements.txt").write_text(requirements)

        # Create .gitignore
        gitignore = '''.cpa/
__pycache__/
*.pyc
.pytest_cache/
.playwright/
reports/
screenshots/
videos/
*.log
'''
        (project_path / ".gitignore").write_text(gitignore)

        return "Configuration files created"

    async def _setup_state(self, context: dict[str, Any]) -> str:
        """Setup initial state."""
        from claude_playwright_agent.state import StateManager

        project_path = Path(context.get("project_path", "."))
        project_name = context.get("project_name", "my-test-project")
        framework = context.get("framework", "behave")

        state_manager = StateManager(project_path)
        state_manager.update_project_metadata(
            name=project_name,
            framework_type=framework,
        )

        return "Initial state setup completed"

    async def _validate_project(self, context: dict[str, Any]) -> str:
        """Validate project structure."""
        project_path = Path(context.get("project_path", "."))

        required_dirs = ["features", "pages"]
        missing_dirs = []

        for directory in required_dirs:
            if not (project_path / directory).exists():
                missing_dirs.append(directory)

        if missing_dirs:
            return f"Validation failed: Missing directories: {', '.join(missing_dirs)}"

        return "Project structure is valid"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

