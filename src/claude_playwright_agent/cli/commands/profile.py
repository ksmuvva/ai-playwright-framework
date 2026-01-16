"""
Profile Management Commands for Claude Playwright Agent.

This module provides advanced profile management:
- List all available profiles (built-in and custom)
- Create custom profiles
- Compare profiles
- Export/import profiles
- Validate profile configuration
- Profile inheritance
"""

import json
import sys
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from claude_playwright_agent.config import (
    ConfigManager,
    PROFILES,
    CONFIG_PROFILES_DIR,
    CONFIG_DIR_NAME,
    ConfigError,
    ProfileConfig,
)

console = Console()


# =============================================================================
# Utility Functions
# =============================================================================


def get_profiles_dir(project_path: Path) -> Path:
    """Get the profiles directory for a project."""
    return project_path / CONFIG_DIR_NAME / CONFIG_PROFILES_DIR


def get_custom_profiles(project_path: Path) -> list[str]:
    """Get list of custom profile names."""
    profiles_dir = get_profiles_dir(project_path)
    if not profiles_dir.exists():
        return []

    custom_profiles = []
    for profile_file in profiles_dir.glob("*.yaml"):
        custom_profiles.append(profile_file.stem)

    return sorted(custom_profiles)


def load_profile_config(
    profile_name: str,
    project_path: Path,
) -> dict[str, Any] | None:
    """
    Load configuration for a profile.

    Args:
        profile_name: Name of the profile
        project_path: Project path

    Returns:
        Profile configuration dict or None if not found
    """
    # Check if it's a built-in profile
    if profile_name in PROFILES:
        return ProfileConfig.get_profile_config(profile_name)

    # Check if it's a custom profile
    profile_file = get_profiles_dir(project_path) / f"{profile_name}.yaml"
    if profile_file.exists():
        try:
            with open(profile_file, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    return None


def validate_profile_config(config: dict[str, Any]) -> list[str]:
    """
    Validate a profile configuration.

    Args:
        config: Profile configuration dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for required sections
    required_sections = ["framework", "browser", "execution"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    # Validate framework section
    if "framework" in config:
        framework = config["framework"]
        if "bdd_framework" not in framework:
            errors.append("framework.bdd_framework is required")
        elif framework["bdd_framework"] not in ["behave", "pytest-bdd"]:
            errors.append(f"Invalid framework.bdd_framework: {framework.get('bdd_framework')}")

    # Validate browser section
    if "browser" in config:
        browser = config["browser"]
        if "browser" not in browser:
            errors.append("browser.browser is required")
        elif browser["browser"] not in ["chromium", "firefox", "webkit"]:
            errors.append(f"Invalid browser.browser: {browser.get('browser')}")

        if "headless" in browser and not isinstance(browser["headless"], bool):
            errors.append("browser.headless must be a boolean")

    # Validate execution section
    if "execution" in config:
        execution = config["execution"]
        if "parallel_workers" in execution:
            if not isinstance(execution["parallel_workers"], int):
                errors.append("execution.parallel_workers must be an integer")
            elif execution["parallel_workers"] < 1:
                errors.append("execution.parallel_workers must be at least 1")

        if "retry_failed" in execution:
            if not isinstance(execution["retry_failed"], int):
                errors.append("execution.retry_failed must be an integer")
            elif execution["retry_failed"] < 0:
                errors.append("execution.retry_failed must be non-negative")

    # Validate logging section
    if "logging" in config:
        logging = config["logging"]
        if "level" in logging:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if logging["level"].upper() not in valid_levels:
                errors.append(f"Invalid logging.level: {logging['level']}")

    return errors


# =============================================================================
# Profile Commands
# =============================================================================


@click.group()
def profile() -> None:
    """Advanced profile management commands."""
    pass


@profile.command(name="list")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def profile_list(project_path: str, output_json: bool) -> None:
    """
    List all available profiles.

    Shows both built-in profiles (default, dev, test, prod, ci)
    and any custom profiles created for the project.
    """
    project_path = Path(project_path)

    custom_profiles = get_custom_profiles(project_path)

    if output_json:
        data = {
            "built_in": PROFILES,
            "custom": custom_profiles,
            "total": len(PROFILES) + len(custom_profiles),
        }
        console.print_json(json.dumps(data, indent=2))
        return

    # Create table
    table = Table(title="Available Profiles", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    # Built-in profiles
    descriptions = {
        "default": "Basic settings for new projects",
        "dev": "Development with debug output and visible browser",
        "test": "Testing with parallel execution and retries",
        "prod": "Production with optimized settings",
        "ci": "CI/CD with JSON logging and no artifacts",
    }

    for p in PROFILES:
        table.add_row(
            "Built-in",
            p,
            descriptions.get(p, ""),
        )

    # Custom profiles
    for p in custom_profiles:
        config = load_profile_config(p, project_path)
        desc = config.get("description", "") if config else ""
        table.add_row("Custom", p, desc)

    console.print(table)
    console.print(f"\nTotal: {len(PROFILES)} built-in, {len(custom_profiles)} custom")


@profile.command(name="create")
@click.argument("name")
@click.option(
    "--extends", "-e",
    help="Base profile to extend (default, dev, test, prod, ci, or custom)",
)
@click.option(
    "--description", "-d",
    default="",
    help="Profile description",
)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def profile_create(
    name: str,
    extends: str | None,
    description: str,
    project_path: str,
) -> None:
    """
    Create a new custom profile.

    Examples:
        cpa profile create my-profile --extends dev
        cpa profile create staging --extends prod --description "Staging environment"
    """
    project_path = Path(project_path)

    # Validate profile name
    if name in PROFILES:
        console.print(
            f"[error]Cannot create profile '{name}': "
            f"conflicts with built-in profile[/error]"
        )
        sys.exit(1)

    # Check if profile already exists
    profiles_dir = get_profiles_dir(project_path)
    profile_file = profiles_dir / f"{name}.yaml"
    if profile_file.exists():
        console.print(f"[error]Profile '{name}' already exists[/error]")
        sys.exit(1)

    # Start with base profile if specified, otherwise use default
    if extends:
        base_config = load_profile_config(extends, project_path)
        if base_config is None:
            console.print(f"[error]Base profile '{extends}' not found[/error]")
            sys.exit(1)
        config = base_config.copy()
    else:
        # Use default profile as base
        config = ProfileConfig.get_profile_config("default")

    # Add metadata
    config["name"] = name
    if description:
        config["description"] = description
    if extends:
        config["extends"] = extends

    # Add creation timestamp
    config["created_at"] = datetime.now().isoformat()

    # Validate configuration
    errors = validate_profile_config(config)
    if errors:
        console.print("[error]Profile validation failed:[/error]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    # Ensure profiles directory exists
    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Write profile file
    with open(profile_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[success]Profile '{name}' created successfully![/success]")
    if extends:
        console.print(f"  Extends: {extends}")
    if description:
        console.print(f"  Description: {description}")
    console.print(f"  Location: {profile_file}")


@profile.command(name="show")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--resolved",
    is_flag=True,
    help="Show resolved config with inheritance applied",
)
def profile_show(name: str, project_path: str, resolved: bool) -> None:
    """
    Show profile configuration.

    Examples:
        cpa profile show dev
        cpa profile show my-custom-profile --resolved
    """
    project_path = Path(project_path)

    config = load_profile_config(name, project_path)
    if config is None:
        console.print(f"[error]Profile '{name}' not found[/error]")
        sys.exit(1)

    # Resolve inheritance if requested
    if resolved and "extends" in config:
        base_name = config["extends"]
        base_config = load_profile_config(base_name, project_path)
        if base_config:
            # Merge configs (base -> custom)
            resolved_config = base_config.copy()
            resolved_config.update(config)
            config = resolved_config
            console.print(f"[dim]Resolving inheritance from: {base_name}[/dim]\n")

    # Display as formatted YAML
    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Profile: {name}", expand=False))


@profile.command(name="diff")
@click.argument("profile1")
@click.argument("profile2")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def profile_diff(profile1: str, profile2: str, project_path: str) -> None:
    """
    Compare two profiles.

    Shows the differences between two profile configurations.

    Examples:
        cpa profile diff dev test
        cpa profile diff prod my-custom-profile
    """
    project_path = Path(project_path)

    config1 = load_profile_config(profile1, project_path)
    config2 = load_profile_config(profile2, project_path)

    if config1 is None:
        console.print(f"[error]Profile '{profile1}' not found[/error]")
        sys.exit(1)
    if config2 is None:
        console.print(f"[error]Profile '{profile2}' not found[/error]")
        sys.exit(1)

    # Convert to YAML for comparison
    yaml1 = yaml.dump(config1, default_flow_style=False, sort_keys=True)
    yaml2 = yaml.dump(config2, default_flow_style=False, sort_keys=True)

    # Generate diff
    diff_lines = list(unified_diff(
        yaml1.splitlines(keepends=True),
        yaml2.splitlines(keepends=True),
        fromfile=profile1,
        tofile=profile2,
        lineterm="",
    ))

    if not diff_lines:
        console.print(f"[success]Profiles '{profile1}' and '{profile2}' are identical[/success]")
    else:
        console.print(Panel(
            "".join(diff_lines),
            title=f"Diff: {profile1} vs {profile2}",
            border_style="yellow",
        ))


@profile.command(name="validate")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def profile_validate(name: str, project_path: str) -> None:
    """
    Validate a profile configuration.

    Checks for:
    - Required sections
    - Valid values for all settings
    - Type correctness
    - Referenced profile (extends) exists

    Examples:
        cpa profile validate my-profile
    """
    project_path = Path(project_path)

    config = load_profile_config(name, project_path)
    if config is None:
        console.print(f"[error]Profile '{name}' not found[/error]")
        sys.exit(1)

    # Validate extends reference
    if "extends" in config:
        base_name = config["extends"]
        base_config = load_profile_config(base_name, project_path)
        if base_config is None:
            console.print(f"[error]Invalid 'extends': profile '{base_name}' not found[/error]")
            sys.exit(1)

    # Run validation
    errors = validate_profile_config(config)

    if errors:
        console.print(f"[error]Profile '{name}' validation failed:[/error]")
        for error in errors:
            console.print(f"  [red]-[/red] {error}")
        sys.exit(1)
    else:
        console.print(f"[success]Profile '{name}' is valid![/success]")


@profile.command(name="delete")
@click.argument("name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Delete without confirmation",
)
def profile_delete(name: str, project_path: str, force: bool) -> None:
    """
    Delete a custom profile.

    Cannot delete built-in profiles.

    Examples:
        cpa profile delete my-profile
        cpa profile delete old-profile --force
    """
    project_path = Path(project_path)

    # Check if it's a built-in profile
    if name in PROFILES:
        console.print(f"[error]Cannot delete built-in profile '{name}'[/error]")
        sys.exit(1)

    # Check if profile exists
    profile_file = get_profiles_dir(project_path) / f"{name}.yaml"
    if not profile_file.exists():
        console.print(f"[error]Profile '{name}' not found[/error]")
        sys.exit(1)

    # Confirm deletion
    if not force:
        click.confirm(f"Delete profile '{name}'?", abort=True)

    # Delete the profile file
    profile_file.unlink()

    console.print(f"[success]Profile '{name}' deleted[/success]")


@profile.command(name="export")
@click.argument("name")
@click.argument("output_file", type=click.Path())
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Export format",
)
def profile_export(name: str, output_file: str, project_path: str, format: str) -> None:
    """
    Export a profile to a file.

    Examples:
        cpa profile export dev my-dev-profile.yaml
        cpa profile export my-profile custom-profile.json --format json
    """
    project_path = Path(project_path)

    config = load_profile_config(name, project_path)
    if config is None:
        console.print(f"[error]Profile '{name}' not found[/error]")
        sys.exit(1)

    output_path = Path(output_file)

    try:
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"[success]Profile '{name}' exported to {output_path}[/success]")
    except Exception as e:
        console.print(f"[error]Failed to export profile: {e}[/error]")
        sys.exit(1)


@profile.command(name="import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--name", "-n",
    required=True,
    help="Name for the imported profile",
)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing profile",
)
def profile_import(
    input_file: str,
    name: str,
    project_path: str,
    force: bool,
) -> None:
    """
    Import a profile from a file.

    Examples:
        cpa profile import custom-profile.yaml --name my-profile
        cpa profile import profile.json --name production-copy --force
    """
    project_path = Path(project_path)
    input_path = Path(input_file)

    # Load the profile file
    try:
        if input_path.suffix == ".json":
            with open(input_path, encoding="utf-8") as f:
                config = json.load(f)
        else:
            with open(input_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[error]Failed to load profile file: {e}[/error]")
        sys.exit(1)

    # Validate profile name
    if name in PROFILES:
        console.print(
            f"[error]Cannot import as '{name}': "
            f"conflicts with built-in profile[/error]"
        )
        sys.exit(1)

    # Check if profile already exists
    profiles_dir = get_profiles_dir(project_path)
    profile_file = profiles_dir / f"{name}.yaml"
    if profile_file.exists() and not force:
        console.print(f"[error]Profile '{name}' already exists. Use --force to overwrite[/error]")
        sys.exit(1)

    # Update profile name
    config["name"] = name

    # Validate
    errors = validate_profile_config(config)
    if errors:
        console.print("[error]Profile validation failed:[/error]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    # Ensure profiles directory exists
    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Write profile file
    with open(profile_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[success]Profile imported as '{name}'[/success]")


__all__ = ["profile"]
