"""
CLI - Main command-line interface for Claude Playwright Agent.

This module provides the Click-based CLI with commands for:
- Project initialization
- Recording ingestion
- Test execution
- Configuration management
- Status reporting
- Skill management
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_playwright_agent.config import ConfigManager, PROFILES
from claude_playwright_agent.scaffold import ScaffoldOptions, TemplateManager
from claude_playwright_agent.skills import load_skills
from claude_playwright_agent.state import StateManager, NotInitializedError

# Import skill commands
from claude_playwright_agent.cli.commands.skill_commands import (
    register_skills_commands,
)

# Import workflow commands
from claude_playwright_agent.cli.commands.ingest import ingest
from claude_playwright_agent.cli.commands.run import run
from claude_playwright_agent.cli.commands.report import report
from claude_playwright_agent.cli.commands.deps import deps
from claude_playwright_agent.cli.commands.cicd import cicd_command
from claude_playwright_agent.cli.commands.profile import profile
from claude_playwright_agent.cli.commands.provider import provider
from claude_playwright_agent.cli.commands.state_cmd import state
from claude_playwright_agent.cli.commands.flaky import flaky
from claude_playwright_agent.cli.commands.template import template
from claude_playwright_agent.cli.commands.environment import environment
from claude_playwright_agent.cli.commands.validation import validate

# =============================================================================
# Constants
# =============================================================================

VERSION = "0.1.0"
DEFAULT_PROJECT_NAME = "my-test-project"
DEFAULT_FRAMEWORK = "behave"

# Rich console for styled output
console = Console()


# =============================================================================
# Utility Functions
# =============================================================================


def print_banner() -> None:
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║        Claude Playwright Agent - AI Test Automation          ║
║                     Version {version:36}                 ║
╚═══════════════════════════════════════════════════════════════╝
""".format(version=VERSION)
    console.print(banner, style="bold blue")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[OK] {message}", style="bold green")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[ERROR] {message}", style="bold red")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[INFO] {message}", style="bold cyan")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[WARN] {message}", style="bold yellow")


# =============================================================================
# CLI Group
# =============================================================================


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, version: bool, verbose: bool) -> None:
    """
    Claude Playwright Agent - AI-powered test automation framework.

    \b
    QUICK START:
        1. Initialize a project:
           cpa init my-test-project

        2. Ingest a Playwright recording:
           cpa ingest recordings/login.js

        3. Run the generated tests:
           cpa run test

        4. View reports:
           cpa report

    \b
    COMMON COMMANDS:
        cpa init           Create a new test project
        cpa ingest          Convert Playwright recordings to BDD tests
        cpa run             Execute BDD scenarios
        cpa report          View test reports and statistics
        cpa status          Show project status
        cpa deps            Manage dependencies (check, install)
        cpa provider        Manage LLM providers (list, test, set)

    \b
    GETTING HELP:
        cpa --help          Show this help message
        cpa <command> --help Show help for a specific command
        cpa help            Show all available commands

    \b
    EXAMPLES:
        # Create a new project with Behave framework
        cpa init --name my-tests --framework behave

        # Ingest a recording with detailed output
        cpa ingest recordings/login.js --verbose

        # Run only smoke tests
        cpa run test --tags @smoke

        # Check if all dependencies are installed
        cpa deps check

        # List available LLM providers
        cpa provider list

        # Switch to OpenAI provider
        cpa provider set openai

    \b
    DOCUMENTATION:
        For more information, visit:
        https://github.com/anthropics/claude-playwright-agent
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if version:
        console.print(f"Claude Playwright Agent v{VERSION}")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(Panel.fit(
            "Use --help to see available commands",
            title="Welcome",
            border_style="blue"
        ))


# =============================================================================
# Init Command
# =============================================================================


@cli.command()
@click.option(
    "--name", "-n",
    default=DEFAULT_PROJECT_NAME,
    help="Project name",
)
@click.option(
    "--framework", "-F",
    type=click.Choice(["behave", "pytest-bdd"]),
    default=DEFAULT_FRAMEWORK,
    help="BDD framework to use",
)
@click.option(
    "--template", "-t",
    type=click.Choice(["basic", "advanced", "ecommerce"]),
    default="basic",
    help="Project template",
)
@click.option(
    "--profile", "-p",
    type=click.Choice(PROFILES),
    default="default",
    help="Configuration profile",
)
@click.option(
    "--force",
    is_flag=True,
    help="Initialize in existing directory",
)
def init(name: str, framework: str, template: str, profile: str, force: bool) -> None:
    """
    Initialize a new Claude Playwright Agent project.

    \b
    USAGE:
        cpa init [OPTIONS]

    \b
    PROJECT STRUCTURE CREATED:
        .cpa/               Configuration and state
        features/           BDD feature files
        features/steps/     Step definitions
        pages/              Page objects
        recordings/         Playwright recordings
        reports/            Test reports
        requirements.txt    Python dependencies
        .gitignore          Git ignore file

    \b
    EXAMPLES:
        # Create a basic project (default)
        cpa init

        # Create a project with custom name
        cpa init --name my-test-suite

        # Use pytest-bdd framework
        cpa init --framework pytest-bdd

        # Use advanced template with more features
        cpa init --template advanced

        # Combine multiple options
        cpa init --name ecommerce-tests --framework behave --template advanced

        # Re-initialize in existing directory
        cpa init --force

    \b
    TEMPLATES:
        basic        Simple project structure
        advanced     Includes parallel execution, reporting
        ecommerce    Pre-configured for e-commerce testing

    \b
    FRAMEWORKS:
        behave       Python BDD framework (recommended)
        pytest-bdd   BDD for pytest (lighter alternative)

    \b
    NEXT STEPS:
        After initialization:
        1. pip install -r requirements.txt
        2. playwright install chromium
        3. cpa ingest recordings/recording.js
        4. cpa run
    """
    project_path = Path.cwd()

    # Check if already initialized
    cpa_dir = project_path / ".cpa"
    if cpa_dir.exists() and not force:
        print_error("Project already initialized. Use --force to re-initialize.")
        sys.exit(1)

    print_info(f"Initializing project: {name}")
    print_info(f"Framework: {framework}")
    print_info(f"Template: {template}")
    print_info(f"Profile: {profile}")

    # Create scaffold options
    options = ScaffoldOptions(
        project_name=name,
        framework=framework,
        template=template,
        base_url="http://localhost:8000",
        with_screenshots=True,
        with_videos=False,
        with_reports=True,
        self_healing=True,
    )

    # Scaffold project structure
    template_manager = TemplateManager()
    try:
        created_files = template_manager.scaffold_project(project_path, options)
        print_info(f"Created {len(created_files)} files and directories")
    except Exception as e:
        print_error(f"Failed to scaffold project: {e}")
        sys.exit(1)

    # Initialize configuration
    config_manager = ConfigManager(project_path, profile=profile)
    config_manager.update(
        framework_bdd_framework=framework,
        framework_template=template,
        framework_base_url=options.base_url,
    )
    config_manager.save()

    # Initialize state
    state_manager = StateManager(project_path)
    state_manager.update_project_metadata(
        name=name,
        framework_type=framework,
    )

    print_success(f"Project '{name}' initialized successfully!")
    print_info("\nNext steps:")
    console.print("  1. Install dependencies: pip install -r requirements.txt")
    console.print("  2. Install browsers: playwright install chromium")
    console.print("  3. Place Playwright recordings in recordings/")
    console.print("  4. Run: cpa ingest recordings/<recording>.js")
    console.print("  5. Run: cpa run to execute your BDD scenarios")


# =============================================================================
# Status Command
# =============================================================================


@cli.command()
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def status(project_path: str) -> None:
    """
    Show project status and statistics.

    \b
    USAGE:
        cpa status [OPTIONS]

    \b
    DISPLAYS:
        • Project metadata (name, framework, version)
        • Recordings status (count, ingestion status)
        • Scenarios generated (count, tags)
        • Test runs summary (total, passed, failed, pass rate)
        • Available skills (enabled count)

    \b
    EXAMPLES:
        # Show status of current project
        cpa status

        # Show status of specific project
        cpa status --project-path /path/to/project

    \b
    STATUS INFORMATION:
        The status command provides a quick overview of:
        - How many recordings have been ingested
        - How many BDD scenarios have been generated
        - Test execution history and results
        - Which skills are available and enabled
        - Overall project health
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        print_error("Failed to load project: Not initialized. Run 'cpa init' first.")
        sys.exit(1)

    try:
        state = StateManager(project_path)
        config = ConfigManager(project_path)
    except Exception as e:
        print_error(f"Failed to load project: {e}")
        sys.exit(1)

    # Auto-load skills
    from claude_playwright_agent.skills import get_registry
    skill_count = load_project_skills(project_path)
    skills = get_registry().list_skills(include_disabled=False)

    # Project metadata table
    metadata_table = Table(title="Project Metadata", show_header=True)
    metadata_table.add_column("Property", style="cyan")
    metadata_table.add_column("Value", style="green")

    project_meta = state.get_project_metadata()
    metadata_table.add_row("Name", project_meta.name)
    metadata_table.add_row("Framework", project_meta.framework_type.value)
    metadata_table.add_row("Version", project_meta.version)
    metadata_table.add_row("Created", project_meta.created_at[:19])

    console.print(metadata_table)

    # Statistics table
    stats_table = Table(title="Statistics", show_header=True)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Count", style="green")

    recordings = state.get_recordings()
    scenarios = state.get_all_scenarios()
    test_runs = state.get_test_runs(limit=100)

    stats_table.add_row("Recordings", str(len(recordings)))
    stats_table.add_row("Scenarios", str(len(scenarios)))
    stats_table.add_row("Test Runs", str(len(test_runs)))
    stats_table.add_row("Skills (enabled)", str(len(skills)))

    # Calculate totals
    total_tests = sum(run.total for run in test_runs)
    total_passed = sum(run.passed for run in test_runs)
    total_failed = sum(run.failed for run in test_runs)

    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        stats_table.add_row("Total Tests", str(total_tests))
        stats_table.add_row("Passed", str(total_passed))
        stats_table.add_row("Failed", str(total_failed))
        stats_table.add_row("Pass Rate", f"{pass_rate:.1f}%")

    console.print(stats_table)


# =============================================================================
# Config Commands
# =============================================================================


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command(name="show")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def config_show(project_path: str) -> None:
    """Show current configuration."""
    project_path = Path(project_path)

    try:
        config_manager = ConfigManager(project_path)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    console.print(f"[bold cyan]Configuration Profile:[/bold cyan] {config_manager.get_profile()}")
    console.print("")

    # Framework settings
    console.print("[bold]Framework:[/bold]")
    console.print(f"  BDD Framework: {config_manager.framework.bdd_framework.value}")
    console.print(f"  Template: {config_manager.framework.template}")
    console.print(f"  Base URL: {config_manager.framework.base_url}")
    console.print(f"  Timeout: {config_manager.framework.default_timeout}ms")
    console.print("")

    # Browser settings
    console.print("[bold]Browser:[/bold]")
    console.print(f"  Browser: {config_manager.browser.browser.value}")
    console.print(f"  Headless: {config_manager.browser.headless}")
    console.print(f"  Viewport: {config_manager.browser.viewport_width}x{config_manager.browser.viewport_height}")
    console.print("")

    # Execution settings
    console.print("[bold]Execution:[/bold]")
    console.print(f"  Parallel Workers: {config_manager.execution.parallel_workers}")
    console.print(f"  Retry Failed: {config_manager.execution.retry_failed}")
    console.print(f"  Self-Healing: {config_manager.execution.self_healing}")


@config.command(name="set")
@click.argument("key_value", nargs=-1, required=True)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def config_set(key_value: tuple, project_path: str) -> None:
    """
    Set configuration values.

    KEY_VALUE format: section.key=value

    Examples:
        cpa config set browser.headless=false
        cpa config set execution.parallel_workers=4
        cpa config set logging.level=DEBUG
    """
    project_path = Path(project_path)

    try:
        config_manager = ConfigManager(project_path)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    updates = {}
    for kv in key_value:
        if "=" not in kv:
            print_error(f"Invalid key=value pair: {kv}")
            sys.exit(1)

        key, value = kv.split("=", 1)
        updates[key.replace(".", "_")] = value

    try:
        config_manager.update(**updates)
        config_manager.save()
        print_success(f"Configuration updated: {', '.join(updates.keys())}")
    except Exception as e:
        print_error(f"Failed to update configuration: {e}")
        sys.exit(1)


@config.command(name="validate")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def config_validate(project_path: str) -> None:
    """Validate configuration file."""
    project_path = Path(project_path)

    try:
        ConfigManager(project_path)
        print_success("Configuration is valid!")
    except Exception as e:
        print_error(f"Configuration validation failed: {e}")
        sys.exit(1)


@config.command(name="profile")
@click.argument("profile", type=click.Choice(PROFILES))
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def config_profile(profile: str, project_path: str) -> None:
    """Switch configuration profile."""
    project_path = Path(project_path)

    try:
        config_manager = ConfigManager(project_path)
        config_manager.set_profile(profile)
        print_success(f"Switched to profile: {profile}")
    except Exception as e:
        print_error(f"Failed to switch profile: {e}")
        sys.exit(1)


# =============================================================================
# Skill Discovery Commands
# =============================================================================


def load_project_skills(project_path: Path) -> int:
    """
    Auto-discover and load skills from the project.

    Args:
        project_path: Path to the project directory

    Returns:
        Number of skills loaded
    """
    try:
        skills = load_skills(project_path=project_path, include_builtins=True)
        return len(skills)
    except Exception:
        # Silently fail if skills cannot be loaded
        return 0


@cli.command()
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def refresh_skills(project_path: str) -> None:
    """
    Refresh skills by re-scanning the project directory.

    This command reloads all skills from:
    - Built-in skills directory
    - Project skills directory (.cpa/skills or skills)
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        print_warning("Project not initialized. Skills from built-in directory only.")

    print_info("Scanning for skills...")

    skills = load_skills(project_path=project_path, include_builtins=True)

    print_success(f"Loaded {len(skills)} skill(s):")
    for skill in skills:
        status = "enabled" if skill.enabled else "disabled"
        console.print(f"  - {skill.name} v{skill.version} [{status}]")


# =============================================================================
# Main Entry Point
# =============================================================================


# Register commands at module import time
# This ensures commands are available when using CliRunner or importing the module
register_skills_commands(cli)
cli.add_command(ingest)
cli.add_command(run)
cli.add_command(report)
cli.add_command(deps)
cli.add_command(cicd_command)
cli.add_command(profile)
cli.add_command(provider)  # NEW: Provider management commands
cli.add_command(state)
cli.add_command(flaky)
cli.add_command(template)
cli.add_command(environment)
cli.add_command(validate)


def main() -> None:
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
