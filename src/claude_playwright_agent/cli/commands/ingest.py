"""
Ingest command - Ingest Playwright recordings with full pipeline.

This command:
1. Parses Playwright recording files
2. Runs deduplication on extracted selectors
3. Generates BDD scenarios using deduplicated data
4. Updates state with all results

Full pipeline: parse → deduplicate → BDD conversion
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from claude_playwright_agent.bdd import BDDConversionAgent, BDDConversionConfig
from claude_playwright_agent.deduplication import DeduplicationAgent, DeduplicationConfig
from claude_playwright_agent.state import StateManager, NotInitializedError

# Rich console
console = Console()


def print_timestamp(message: str, style: str = "") -> None:
    """Print a message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"[{timestamp}] {message}", style=style)


@click.command()
@click.argument(
    "recording_path",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--no-dedup",
    is_flag=True,
    help="Skip deduplication step",
)
@click.option(
    "--no-bdd",
    is_flag=True,
    help="Skip BDD conversion step",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable detailed output",
)
def ingest(
    recording_path: str,
    project_path: str,
    no_dedup: bool,
    no_bdd: bool,
    verbose: bool,
) -> None:
    """
    Ingest a Playwright recording with full pipeline.

    This command runs the complete ingestion pipeline:
    1. Parse the Playwright recording
    2. Deduplicate selectors across recordings
    3. Generate BDD scenarios with context

    Example:
        cpa ingest recordings/login.js
        cpa ingest recordings/login.js --verbose
        cpa ingest recordings/login.js --no-dedup  # Skip deduplication
        cpa ingest recordings/login.js --no-bdd     # Skip BDD conversion
    """
    project_path = Path(project_path)
    recording_file = Path(recording_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    # Load state
    try:
        state = StateManager(project_path)
    except Exception as e:
        console.print(f"[ERROR] Failed to load state: {e}", style="bold red")
        sys.exit(1)

    # Generate recording ID
    recording_id = f"rec_{hashlib.md5(str(recording_file).encode()).hexdigest()[:12]}"

    print_timestamp("🚀 Starting ingestion pipeline...", "bold blue")
    print_timestamp(f"   Recording: {recording_file.name}", "cyan")
    print_timestamp(f"   Project: {state.get_project_metadata().name}", "cyan")
    console.print("")

    # ========================================================================
    # Step 1: Parse Recording
    # ========================================================================

    print_timestamp("📦 Step 1: Parsing Playwright recording...", "bold yellow")

    try:
        actions, urls = _parse_playwright_recording(recording_file)
        print_timestamp(f"   ✅ Parsed {len(actions)} actions", "green")
        print_timestamp(f"   ✅ Found {len(urls)} URL(s)", "green")

        # Store recording data in state
        state._state.recordings_data[recording_id] = {
            "actions": actions,
            "urls_visited": urls,
        }

        # Add recording to state
        state.add_recording(
            recording_id=recording_id,
            file_path=str(recording_file),
        )
        state.update_recording_status(
            recording_id,
            "completed",
            actions_count=len(actions),
        )
        state.save()

        console.print("")

    except Exception as e:
        print_timestamp(f"   ❌ Failed to parse recording: {e}", "red")
        sys.exit(1)

    # ========================================================================
    # Step 2: Deduplication (if not skipped)
    # ========================================================================

    dedup_result = None
    if not no_dedup:
        print_timestamp("📦 Step 2: Running deduplication...", "bold yellow")

        try:
            dedup_agent = DeduplicationAgent(project_path)
            dedup_result = dedup_agent.run()

            if dedup_result.success:
                print_timestamp(f"   ✅ Found {dedup_result.total_groups} element groups", "green")
                print_timestamp(f"   ✅ Extracted {dedup_result.components_extracted} components", "green")
                print_timestamp(f"   ✅ Generated {dedup_result.page_objects_generated} page objects", "green")
                print_timestamp(f"   ✅ Cataloged {dedup_result.selectors_cataloged} selectors", "green")

                if verbose and dedup_result.total_groups > 0:
                    print_timestamp("   📊 Element groups:", "cyan")
                    for group in dedup_result.groups:
                        name = group.name_suggestion or group.canonical_selector.value
                        print_timestamp(f"      - {name} ({group.usage_count} usages)", "dim")
            else:
                print_timestamp("   ⚠️  Deduplication completed with warnings", "yellow")
                if dedup_result.stats.get("error"):
                    print_timestamp(f"      Error: {dedup_result.stats['error']}", "dim")

            console.print("")

        except Exception as e:
            print_timestamp(f"   ❌ Deduplication failed: {e}", "red")
            if not verbose:
                print_timestamp("   Continuing with BDD conversion...", "yellow")
            console.print("")
    else:
        print_timestamp("⏭️  Skipping deduplication (--no-dedup)", "yellow")
        console.print("")

    # ========================================================================
    # Step 3: BDD Conversion (if not skipped)
    # ========================================================================

    bdd_result = None
    if not no_bdd:
        print_timestamp("📦 Step 3: Generating BDD scenarios...", "bold yellow")

        try:
            bdd_config = BDDConversionConfig(
                extract_backgrounds=True,
                auto_tag_scenarios=True,
            )
            bdd_agent = BDDConversionAgent(project_path, bdd_config)
            bdd_result = bdd_agent.run()

            if bdd_result.success:
                print_timestamp(f"   ✅ Generated {bdd_result.total_scenarios} scenarios", "green")
                print_timestamp(f"   ✅ Created {bdd_result.total_features} feature file(s)", "green")
                print_timestamp(f"   ✅ Generated {bdd_result.total_steps} step definitions", "green")
                print_timestamp(f"   ✅ Extracted {bdd_result.backgrounds_extracted} background(s)", "green")
                print_timestamp(f"   ✅ Added {bdd_result.tags_added} tag(s)", "green")

                if verbose:
                    print_timestamp("   📊 Scenarios by recording:", "cyan")
                    for rec_id, count in bdd_result.scenarios_by_recording.items():
                        print_timestamp(f"      - {rec_id}: {count} scenarios", "dim")
            else:
                print_timestamp("   ❌ BDD conversion failed", "red")
                if bdd_result.stats.get("error"):
                    print_timestamp(f"      Error: {bdd_result.stats['error']}", "dim")
                sys.exit(1)

            console.print("")

        except Exception as e:
            print_timestamp(f"   ❌ BDD conversion failed: {e}", "red")
            sys.exit(1)
    else:
        print_timestamp("⏭️  Skipping BDD conversion (--no-bdd)", "yellow")
        console.print("")

    # ========================================================================
    # Summary
    # ========================================================================

    print_timestamp("💾 Saving state...", "bold yellow")
    state.save()
    print_timestamp("   ✅ State saved", "green")
    console.print("")

    console.print(Panel.fit(
        f"✅ Ingestion complete!\n\n"
        f"Recording ID: {recording_id}\n"
        f"Actions: {len(actions)}\n"
        f"Element Groups: {dedup_result.total_groups if dedup_result else 0}\n"
        f"Scenarios: {bdd_result.total_scenarios if bdd_result else 0}",
        title="Pipeline Summary",
        border_style="green"
    ))

    console.print("")
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print("  1. Review generated scenarios in features/")
    console.print("  2. Review step definitions in features/steps/")
    console.print("  3. Run tests: cpa run")


# =============================================================================
# Recording Parser (Simplified - will be enhanced in E3)
# =============================================================================


def _parse_playwright_recording(recording_file: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Parse a Playwright recording file.

    Args:
        recording_file: Path to the recording file

    Returns:
        Tuple of (actions list, URLs list)

    Note: This is a simplified parser. Full parser will be implemented in E3.
    """
    import re

    content = recording_file.read_text(encoding="utf-8")

    actions = []
    urls_visited = []

    # Extract goto actions
    goto_pattern = r'await page\.goto\([\'"]([^\'"]+)[\'"]'
    for match in re.finditer(goto_pattern, content):
        url = match.group(1)
        urls_visited.append(url)
        actions.append({
            "action_type": "goto",
            "value": url,
            "page_url": "",
            "line_number": match.start(),
        })

    # Extract click actions
    click_pattern = r'await\s+(?:page\.|locator\(.+\)\.)click\(\)'
    for match in re.finditer(click_pattern, content):
        # Find the locator before the click
        locator_match = _find_locator_before(content, match.start())
        selector = _parse_locator(locator_match) if locator_match else {}
        actions.append({
            "action_type": "click",
            "selector": selector,
            "page_url": urls_visited[-1] if urls_visited else "",
            "line_number": match.start(),
        })

    # Extract fill actions
    fill_pattern = r'await\s+(?:page\.|locator\(.+\)\.)fill\([\'"]?([^\'")\)]+'
    for match in re.finditer(fill_pattern, content):
        locator_match = _find_locator_before(content, match.start())
        selector = _parse_locator(locator_match) if locator_match else {}
        actions.append({
            "action_type": "fill",
            "selector": selector,
            "value": match.group(1),
            "page_url": urls_visited[-1] if urls_visited else "",
            "line_number": match.start(),
        })

    # Remove duplicates and sort by line number
    seen = set()
    unique_actions = []
    for action in sorted(actions, key=lambda x: x["line_number"]):
        key = (action["action_type"], action.get("selector", {}).get("raw", ""), action.get("value", ""))
        if key not in seen:
            seen.add(key)
            unique_actions.append(action)

    return unique_actions, list(set(urls_visited))


def _find_locator_before(content: str, pos: int) -> str | None:
    """Find the locator expression before a position."""
    # Look back for locator pattern
    pattern = r'locator\((.+?)\)\.'
    match = None
    for m in re.finditer(pattern, content[:pos]):
        match = m
    if match:
        return match.group(1)
    return None


def _parse_locator(locator_str: str) -> dict[str, Any]:
    """Parse a locator string into selector data."""
    import re

    selector_str = locator_str.strip()

    # getByRole
    match = re.search(r'getByRole\([\'"]?([\w-]+)[\'"]?\s*(?:,\s*\{[^}]*name:\s*[\'"]([^\'"]+)[\'"]', selector_str)
    if match:
        return {
            "raw": f"getByRole(\"{match.group(1)}\", {{ name: \"{match.group(2)}\" }})",
            "type": "getByRole",
            "value": match.group(2),
            "attributes": {"name": match.group(2)},
        }

    # getByLabel
    match = re.search(r'getByLabel\([\'"]([^\'"]+)[\'"]', selector_str)
    if match:
        return {
            "raw": f'getByLabel("{match.group(1)}")',
            "type": "getByLabel",
            "value": match.group(1),
            "attributes": {},
        }

    # getByText
    match = re.search(r'getByText\([\'"]([^\'"]+)[\'"]', selector_str)
    if match:
        return {
            "raw": f'getByText("{match.group(1)}")',
            "type": "getByText",
            "value": match.group(1),
            "attributes": {},
        }

    # getByPlaceholder
    match = re.search(r'getByPlaceholder\([\'"]([^\'"]+)[\'"]', selector_str)
    if match:
        return {
            "raw": f'getByPlaceholder("{match.group(1)}")',
            "type": "getByPlaceholder",
            "value": match.group(1),
            "attributes": {},
        }

    # CSS selector
    match = re.search(r'[\'"]([.#][\w-]+)[\'"]', selector_str)
    if match:
        return {
            "raw": f'locator("{match.group(1)}")',
            "type": "css",
            "value": match.group(1),
            "attributes": {},
        }

    # Fallback
    return {
        "raw": selector_str,
        "type": "unknown",
        "value": "",
        "attributes": {},
    }
