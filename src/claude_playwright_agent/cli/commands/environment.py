"""
Environment commands - Manage environment-specific configurations.

This module provides commands to:
- List configured environments
- Add new environments
- Switch between environments
- Remove environments
- View environment details
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.state import StateManager

console = Console()


@click.group()
def environment() -> None:
    """Environment configuration management commands."""
    pass


@environment.command(name="list")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed environment information",
)
def environment_list(project_path: str, verbose: bool) -> None:
    """
    List all configured environments.

    Shows all environments defined in the project configuration
    along with their settings.

    Examples:
        cpa environment list
        cpa environment list --verbose
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    try:
        config_manager = ConfigManager(project_path)
        environments = config_manager.list_environments()
        active_env = config_manager.get_active_environment()
    except Exception as e:
        console.print(f"[ERROR] Failed to load configuration: {e}", style="bold red")
        sys.exit(1)

    if not environments:
        console.print("[INFO] No environments configured.", style="yellow")
        console.print("\nUse 'cpa environment add' to create an environment.")
        return

    # Display environments table
    console.print("")
    env_table = Table(title="Configured Environments", show_header=True)
    env_table.add_column("Environment", style="cyan")
    env_table.add_column("Base URL", style="green")
    env_table.add_column("Browser", style="yellow")
    env_table.add_column("Headless", style="dim")
    env_table.add_column("Status", style="bold")

    for env_name in sorted(environments):
        env_config = config_manager.config.get_environment(env_name)
        if env_config:
            status = " [ACTIVE]" if env_name == active_env else ""

            env_table.add_row(
                env_name,
                env_config.base_url or "-",
                env_config.browser.value if env_config.browser else "-",
                str(env_config.headless) if env_config.headless is not None else "-",
                status,
            )

    console.print(env_table)

    if verbose:
        console.print("")
        for env_name in sorted(environments):
            env_config = config_manager.config.get_environment(env_name)
            if env_config:
                details = [
                    f"[bold cyan]Environment: {env_name}[/bold cyan]",
                    f"",
                ]
                if env_config.base_url:
                    details.append(f"  Base URL: {env_config.base_url}")
                if env_config.browser:
                    details.append(f"  Browser: {env_config.browser.value}")
                if env_config.headless is not None:
                    details.append(f"  Headless: {env_config.headless}")
                if env_config.parallel_workers:
                    details.append(f"  Parallel Workers: {env_config.parallel_workers}")
                if env_config.timeout:
                    details.append(f"  Timeout: {env_config.timeout}ms")
                if env_config.screenshots:
                    details.append(f"  Screenshots: {env_config.screenshots}")
                if env_config.video is not None:
                    details.append(f"  Video: {env_config.video}")
                if env_config.log_level:
                    details.append(f"  Log Level: {env_config.log_level}")
                if env_config.env_vars:
                    details.append(f"  Environment Variables:")
                    for key, value in env_config.env_vars.items():
                        details.append(f"    {key}={value}")

                console.print(Panel("\n".join(details), border_style="cyan"))


@environment.command(name="add")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--base-url", "-u",
    help="Override base URL for this environment",
)
@click.option(
    "--browser", "-b",
    type=click.Choice(["chromium", "firefox", "webkit"]),
    help="Override browser for this environment",
)
@click.option(
    "--headless/--no-headless",
    default=None,
    help="Override headless mode for this environment",
)
@click.option(
    "--parallel-workers", "-w",
    type=int,
    help="Override parallel workers for this environment",
)
@click.option(
    "--timeout", "-t",
    type=int,
    help="Override default timeout (ms) for this environment",
)
@click.option(
    "--screenshots",
    type=click.Choice(["always", "on-failure", "never"]),
    help="Override screenshot setting for this environment",
)
@click.option(
    "--video/--no-video",
    default=None,
    help="Override video recording for this environment",
)
@click.option(
    "--log-level", "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Override log level for this environment",
)
@click.option(
    "--env-var", "-e",
    multiple=True,
    help="Environment variables to set (KEY=VALUE)",
)
def environment_add(
    name: str,
    project_path: str,
    base_url: str | None,
    browser: str | None,
    headless: bool | None,
    parallel_workers: int | None,
    timeout: int | None,
    screenshots: str | None,
    video: bool | None,
    log_level: str | None,
    env_var: tuple,
) -> None:
    """
    Add or update an environment configuration.

    Creates a new environment or updates an existing one with
    the specified configuration overrides.

    Examples:
        cpa environment add prod --base-url https://example.com
        cpa environment add staging --base-url https://staging.example.com --headless
        cpa environment add dev --base-url http://localhost:3000 --parallel-workers 4
        cpa environment add test -u http://test.example.com -e API_KEY=secret
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    # Parse environment variables
    env_vars = {}
    for var in env_var:
        if "=" not in var:
            console.print(f"[ERROR] Invalid environment variable format: {var}", style="bold red")
            console.print("Expected format: KEY=VALUE")
            sys.exit(1)
        key, value = var.split("=", 1)
        env_vars[key] = value

    try:
        config_manager = ConfigManager(project_path)

        # Check if environment already exists
        existing = name in config_manager.list_environments()
        action = "Updated" if existing else "Created"

        config_manager.add_environment(
            env_name=name,
            base_url=base_url,
            browser=browser,
            headless=headless,
            parallel_workers=parallel_workers,
            timeout=timeout,
            screenshots=screenshots,
            video=video,
            log_level=log_level,
            env_vars=env_vars if env_vars else None,
        )

        # Save configuration
        config_manager.save()

        console.print(f"[OK] {action} environment: {name}", style="bold green")

    except Exception as e:
        console.print(f"[ERROR] Failed to add environment: {e}", style="bold red")
        sys.exit(1)


@environment.command(name="remove")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force removal without confirmation",
)
def environment_remove(name: str, project_path: str, force: bool) -> None:
    """
    Remove an environment configuration.

    Permanently removes an environment from the project configuration.

    Examples:
        cpa environment remove old-env
        cpa environment remove test --force
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    try:
        config_manager = ConfigManager(project_path)

        if name not in config_manager.list_environments():
            console.print(f"[ERROR] Environment '{name}' not found.", style="bold red")
            console.print(f"Available environments: {', '.join(config_manager.list_environments())}")
            sys.exit(1)

        if not force:
            click.confirm(f"Are you sure you want to remove environment '{name}'?", abort=True)

        config_manager.remove_environment(name)
        config_manager.save()

        console.print(f"[OK] Removed environment: {name}", style="bold green")

    except click.Abort:
        console.print("Aborted.", style="yellow")
    except Exception as e:
        console.print(f"[ERROR] Failed to remove environment: {e}", style="bold red")
        sys.exit(1)


@environment.command(name="use")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--show", "-s",
    is_flag=True,
    help="Show the environment configuration without saving",
)
def environment_use(name: str, project_path: str, show: bool) -> None:
    """
    Switch to or preview an environment configuration.

    Applies the environment overrides to show what the configuration
    would look like with that environment active.

    Examples:
        cpa environment use prod
        cpa environment use dev --show
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    try:
        config_manager = ConfigManager(project_path)

        if name not in config_manager.list_environments():
            console.print(f"[ERROR] Environment '{name}' not found.", style="bold red")
            console.print(f"Available environments: {', '.join(config_manager.list_environments())}")
            sys.exit(1)

        # Get environment configuration
        env_config = config_manager.use_environment(name)

        if show:
            # Preview mode - just show the config
            console.print("")
            console.print(Panel(
                f"[bold cyan]Environment Preview: {name}[/bold cyan]\n\n"
                f"[bold]Base Configuration:[/bold]\n"
                f"  Framework: {env_config.framework.bdd_framework.value}\n"
                f"  Base URL: {env_config.framework.base_url}\n"
                f"  Timeout: {env_config.framework.default_timeout}ms\n\n"
                f"[bold]Browser:[/bold]\n"
                f"  Type: {env_config.browser.browser.value}\n"
                f"  Headless: {env_config.browser.headless}\n"
                f"  Viewport: {env_config.browser.viewport_width}x{env_config.browser.viewport_height}\n\n"
                f"[bold]Execution:[/bold]\n"
                f"  Parallel Workers: {env_config.execution.parallel_workers}\n"
                f"  Retry Failed: {env_config.execution.retry_failed}\n"
                f"  Self-Healing: {env_config.execution.self_healing}\n"
                f"  Screenshots: {env_config.execution.screenshots}\n"
                f"  Video: {env_config.execution.video}\n\n"
                f"[bold]Logging:[/bold]\n"
                f"  Level: {env_config.logging.level}\n"
                f"  Format: {env_config.logging.format}\n",
                title=f"Environment: {name}",
                border_style="cyan",
            ))
            console.print("\n[yellow]Preview mode - configuration not applied[/yellow]")
        else:
            # Apply the environment
            console.print(f"[OK] Switched to environment: {name}", style="bold green")
            console.print(f"\nActive Environment Configuration:")
            console.print(f"  Base URL: {env_config.framework.base_url}")
            console.print(f"  Browser: {env_config.browser.browser.value}")
            console.print(f"  Headless: {env_config.browser.headless}")

    except Exception as e:
        console.print(f"[ERROR] Failed to switch environment: {e}", style="bold red")
        sys.exit(1)


@environment.command(name="show")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def environment_show(name: str, project_path: str) -> None:
    """
    Show detailed information about an environment.

    Displays all configuration overrides for the specified environment.

    Examples:
        cpa environment show prod
        cpa environment show dev
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    try:
        config_manager = ConfigManager(project_path)

        if name not in config_manager.list_environments():
            console.print(f"[ERROR] Environment '{name}' not found.", style="bold red")
            console.print(f"Available environments: {', '.join(config_manager.list_environments())}")
            sys.exit(1)

        env_config = config_manager.config.get_environment(name)

        console.print("")
        console.print(Panel(
            f"[bold cyan]Environment: {name}[/bold cyan]\n\n"
            f"[bold]Configuration Overrides:[/bold]\n",
            title="Environment Details",
            border_style="cyan",
        ))

        # Show overrides
        overrides = [
            ("Base URL", env_config.base_url),
            ("Browser", env_config.browser.value if env_config.browser else None),
            ("Headless", str(env_config.headless) if env_config.headless is not None else None),
            ("Parallel Workers", env_config.parallel_workers),
            ("Timeout", f"{env_config.timeout}ms" if env_config.timeout else None),
            ("Screenshots", env_config.screenshots),
            ("Video", str(env_config.video) if env_config.video is not None else None),
            ("Log Level", env_config.log_level),
        ]

        for key, value in overrides:
            if value is not None:
                console.print(f"  [cyan]{key}:[/cyan] {value}")

        if env_config.env_vars:
            console.print("\n[bold]Environment Variables:[/bold]")
            for key, value in env_config.env_vars.items():
                console.print(f"  {key}={value}")

    except Exception as e:
        console.print(f"[ERROR] Failed to show environment: {e}", style="bold red")
        sys.exit(1)
