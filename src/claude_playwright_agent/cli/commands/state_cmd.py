"""
State Export/Import Commands for Claude Playwright Agent.

This module provides commands for:
- Exporting state to files (JSON/YAML)
- Importing state from files
- Selective state export
- Merge strategies for import
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from claude_playwright_agent.state import StateManager, NotInitializedError

console = Console()


@click.group()
def state() -> None:
    """State management commands."""
    pass


@state.command(name="export")
@click.argument("output_file", type=click.Path())
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Export format",
)
@click.option(
    "--sections", "-s",
    multiple=True,
    help="Sections to export (e.g., recordings, scenarios, test_runs)",
)
def state_export(
    output_file: str,
    project_path: str,
    format: str,
    sections: tuple,
) -> None:
    """
    Export project state to a file.

    \b
    USAGE:
        cpa state export <output_file> [OPTIONS]

    \b
    SECTIONS:
        recordings      Export recordings data
        scenarios       Export BDD scenarios
        test_runs       Export test execution runs
        page_objects    Export page objects
        ui_components   Export UI components

    \b
    EXAMPLES:
        # Export full state as JSON
        cpa state export backup.json

        # Export full state as YAML
        cpa state export backup.yaml --format yaml

        # Export only recordings and scenarios
        cpa state export partial.json --sections recordings --sections scenarios

        # Export from specific project
        cpa state export ../backup.json --project-path /path/to/project
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[error]Project not initialized. Run 'cpa init' first.[/error]")
        sys.exit(1)

    try:
        state = StateManager(project_path)
    except Exception as e:
        console.print(f"[error]Failed to load state: {e}[/error]")
        sys.exit(1)

    # Convert sections tuple to list
    sections_list = list(sections) if sections else None

    try:
        state.export_state(output_file, format=format, sections=sections_list)
        console.print(f"[success]State exported to {output_file}[/success]")

        if sections_list:
            console.print(f"  Sections: {', '.join(sections_list)}")
        console.print(f"  Format: {format}")

    except Exception as e:
        console.print(f"[error]Failed to export state: {e}[/error]")
        sys.exit(1)


@state.command(name="import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--merge", "-m",
    is_flag=True,
    help="Merge with existing state instead of replacing",
)
@click.option(
    "--merge-strategy",
    type=click.Choice(["replace", "append", "update"]),
    default="replace",
    help="Merge strategy (used with --merge)",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Skip confirmation",
)
def state_import(
    input_file: str,
    project_path: str,
    merge: bool,
    merge_strategy: str,
    force: bool,
) -> None:
    """
    Import project state from a file.

    \b
    USAGE:
        cpa state import <input_file> [OPTIONS]

    \b
    MERGE STRATEGIES:
        replace    Keep existing project metadata, replace everything else
        append     Add new items without overwriting existing ones
        update     Update existing items by ID, add new ones

    \b
    EXAMPLES:
        # Import state (replaces existing)
        cpa state import backup.json

        # Import with merge (keeps project metadata)
        cpa state import backup.json --merge

        # Import and append new items only
        cpa state import backup.json --merge --merge-strategy append

        # Import and update existing items
        cpa state import backup.json --merge --merge-strategy update
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[error]Project not initialized. Run 'cpa init' first.[/error]")
        sys.exit(1)

    # Confirm import if not forced
    if not force:
        if merge:
            msg = f"Merge state from '{input_file}' using '{merge_strategy}' strategy?"
        else:
            msg = f"Replace current state with '{input_file}'?"

        click.confirm(msg, abort=True)

    try:
        state = StateManager(project_path)
    except Exception as e:
        console.print(f"[error]Failed to load state: {e}[/error]")
        sys.exit(1)

    try:
        state.import_state(input_file, merge=merge, merge_strategy=merge_strategy)
        console.print(f"[success]State imported from {input_file}[/success]")

        if merge:
            console.print(f"  Strategy: {merge_strategy}")

    except Exception as e:
        console.print(f"[error]Failed to import state: {e}[/error]")
        sys.exit(1)


@state.command(name="info")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def state_info(project_path: str) -> None:
    """
    Show state file information.

    Displays statistics about the current state including:
    - State file location and size
    - Counts of recordings, scenarios, test runs
    - Project metadata

    \b
    EXAMPLES:
        cpa state info
        cpa state info --project-path /path/to/project
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[error]Project not initialized. Run 'cpa init' first.[/error]")
        sys.exit(1)

    try:
        state = StateManager(project_path)
    except Exception as e:
        console.print(f"[error]Failed to load state: {e}[/error]")
        sys.exit(1)

    # State file info
    state_file = state._state_file
    if state_file.exists():
        file_size = state_file.stat().st_size
        console.print(f"[bold]State File:[/bold] {state_file}")
        console.print(f"[bold]Size:[/bold] {file_size:,} bytes")

    # Statistics table
    table = Table(title="State Statistics", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")

    state_dict = state._state.model_dump()
    table.add_row("Recordings", str(len(state_dict.get("recordings_data", []))))
    table.add_row("Scenarios", str(len(state_dict.get("scenarios", []))))
    table.add_row("Test Runs", str(len(state_dict.get("test_runs", []))))
    table.add_row("Page Objects", str(len(state_dict.get("page_objects", []))))
    table.add_row("UI Components", str(len(state_dict.get("ui_components", []))))

    console.print(table)

    # Project metadata
    metadata = state.get_project_metadata()
    console.print(f"\n[bold]Project:[/bold] {metadata.name}")
    console.print(f"[bold]Framework:[/bold] {metadata.framework_type.value}")
    console.print(f"[bold]Version:[/bold] {metadata.version}")
    console.print(f"[bold]Created:[/bold] {metadata.created_at[:19]}")


__all__ = ["state"]
