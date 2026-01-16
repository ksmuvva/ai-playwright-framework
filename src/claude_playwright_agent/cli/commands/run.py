"""
Run command - Execute BDD tests with workflow triggering.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.state import StateManager
from claude_playwright_agent.agents.execution import (
    TestExecutionEngine,
    TestFramework,
    execute_tests,
)

console = Console()


def print_timestamp(message: str, style: str = "") -> None:
    """Print a message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"[{timestamp}] {message}", style=style)


@click.command()
@click.argument(
    "workflow",
    type=click.Choice(["full", "ingest", "convert", "test"]),
    default="test",
)
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--tags", "-t",
    multiple=True,
    help="Filter scenarios by tags",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable detailed output",
)
def run(
    workflow: str,
    project_path: str,
    tags: tuple,
    verbose: bool,
) -> None:
    """
    Run BDD tests or workflows.

    Workflows:
    - full: Complete pipeline (ingest → dedup → BDD → test)
    - ingest: Ingest all pending recordings
    - convert: Run BDD conversion on ingested data
    - test: Execute BDD scenarios (default)

    Examples:
        cpa run test                    # Run all tests
        cpa run test --tags @smoke     # Run smoke tests
        cpa run convert                 # Convert to BDD
        cpa run full                    # Run full pipeline
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    print_timestamp(f"🚀 Starting workflow: {workflow}", "bold blue")

    if workflow == "test":
        _run_tests(project_path, tags, verbose)
    elif workflow == "convert":
        _run_conversion(project_path, verbose)
    elif workflow == "ingest":
        _run_ingestion(project_path, verbose)
    elif workflow == "full":
        _run_full_pipeline(project_path, verbose)


def _run_tests(project_path: Path, tags: tuple, verbose: bool) -> None:
    """Run BDD test scenarios."""
    print_timestamp("📊 Executing BDD scenarios...", "bold yellow")

    # Load configuration
    try:
        config = ConfigManager(project_path)
        framework_str = config.framework.bdd_framework.value
    except Exception:
        framework_str = "behave"  # Default

    state = StateManager(project_path)
    scenarios = state.get_all_scenarios()

    # Filter by tags if specified
    if tags:
        tag_set = set(tags)
        scenarios = [s for s in scenarios if any(tag in s.tags for tag in tag_set)]
        print_timestamp(f"   Filtering by tags: {', '.join(tags)}", "cyan")

    print_timestamp(f"   Found {len(scenarios)} scenario(s)", "green")

    if not scenarios:
        print_timestamp("   ⚠️  No scenarios to run. Run 'cpa ingest' first.", "yellow")
        return

    # Get framework type and execute tests
    framework = TestFramework(framework_str)

    print_timestamp(f"   Using framework: {framework.value}", "cyan")
    console.print("")

    # Execute tests
    try:
        result = asyncio.run(execute_tests(
            framework=framework.value,
            tags=list(tags) if tags else None,
            project_path=project_path,
        ))

        # Display results
        _display_test_results(result, verbose)

        # Save results to state
        state.add_test_run(
            run_id=f"run_{result.timestamp}",
            total=result.total_tests,
            passed=result.passed,
            failed=result.failed,
            skipped=result.skipped,
            duration=result.duration,
        )
        state.save()

        # Check for flaky tests
        _check_and_display_flaky_tests(project_path, result, verbose)

    except Exception as e:
        print_timestamp(f"   ❌ Test execution failed: {e}", "red")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_test_results(result, verbose: bool) -> None:
    """Display test results in a formatted table."""
    from claude_playwright_agent.agents.execution import TestStatus

    console.print("")

    # Summary table
    table = Table(title="Test Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Framework", result.framework.value)
    table.add_row("Total Tests", str(result.total_tests))
    table.add_row("Passed", str(result.passed))
    table.add_row("Failed", str(result.failed))
    table.add_row("Skipped", str(result.skipped))
    table.add_row("Errors", str(result.errors))
    table.add_row("Duration", f"{result.duration:.2f}s")

    console.print(table)

    # Individual test results if verbose
    if verbose and result.test_results:
        console.print("")
        details_table = Table(title="Test Details", show_header=True)
        details_table.add_column("Test", style="cyan")
        details_table.add_column("Status", style="bold")
        details_table.add_column("Duration", style="dim")

        for test_result in result.test_results:
            status_style = {
                TestStatus.PASSED: "green",
                TestStatus.FAILED: "red",
                TestStatus.SKIPPED: "yellow",
                TestStatus.ERROR: "bold red",
            }.get(test_result.status, "dim")

            status_symbol = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.SKIPPED: "○",
                TestStatus.ERROR: "!",
            }.get(test_result.status, "?")

            details_table.add_row(
                test_result.name[:40],
                f"[{status_style}]{status_symbol} {test_result.status.value}[/]",
                f"{test_result.duration:.2f}s",
            )

        console.print(details_table)

    # Show errors if any
    if result.failed > 0 or result.errors > 0:
        console.print("")
        for test_result in result.test_results:
            if test_result.status in (TestStatus.FAILED, TestStatus.ERROR):
                console.print(f"[red]✗ {test_result.name}[/red]")
                if test_result.error_message:
                    console.print(f"   {test_result.error_message}", style="dim")
                if test_result.stack_trace and verbose:
                    console.print(f"   {test_result.stack_trace[:200]}...", style="dim")


def _check_and_display_flaky_tests(project_path: Path, result, verbose: bool) -> None:
    """Check for and display flaky tests."""
    from claude_playwright_agent.agents.failure_analysis import FailureAnalyzer

    # Get historical test runs from state
    state = StateManager(project_path)
    test_runs = state.get_test_runs(limit=50)

    if not test_runs:
        return  # Not enough history yet

    # Build history for failure analyzer
    analyzer = FailureAnalyzer()
    for run in test_runs:
        # Convert execution run to test results format
        for _ in range(run.total):
            # Simplified: we'd need detailed per-test results here
            # For now, just use aggregate data
            pass

    # Update analyzer with current test results
    test_results_for_history = []
    for test_result in result.test_results:
        test_results_for_history.append({
            "name": test_result.name,
            "status": test_result.status.value,
            "retry_count": getattr(test_result, "retry_count", 0),
            "previous_attempts": getattr(test_result, "previous_attempts", []),
            "duration": test_result.duration,
        })

    analyzer.update_history(test_results_for_history)

    # Detect flaky tests
    flaky_tests = analyzer.detect_flaky_tests(min_runs=3, flaky_threshold=0.5)

    if not flaky_tests:
        return  # No flaky tests detected

    # Display flaky tests
    console.print("")
    flaky_table = Table(title="⚠️  Potentially Flaky Tests Detected", show_header=True)
    flaky_table.add_column("Test", style="cyan")
    flaky_table.add_column("Pass Rate", style="yellow")
    flaky_table.add_column("Confidence", style="bold")
    flaky_table.add_column("Inconsistency", style="red")
    flaky_table.add_column("Retry Pass Rate", style="green")

    for flaky in flaky_tests[:5]:  # Show top 5
        pass_rate_style = "green" if flaky.pass_rate > 0.7 else "yellow" if flaky.pass_rate > 0.5 else "red"
        confidence_style = "bold red" if flaky.flaky_confidence > 0.7 else "yellow" if flaky.flaky_confidence > 0.4 else "dim"

        flaky_table.add_row(
            flaky.test_name[:35],
            f"[{pass_rate_style}]{flaky.pass_rate:.1%}[/]",
            f"[{confidence_style}]{flaky.flaky_confidence:.0%}[/]",
            f"{flaky.inconsistency_score:.0%}",
            f"{flaky.passes_on_retry_rate:.0%}",
        )

    console.print(flaky_table)

    if verbose:
        console.print("")
        for flaky in flaky_tests[:3]:
            console.print(f"[cyan]{flaky.test_name}[/cyan]")
            console.print(f"  Cause: {flaky.likely_cause}", style="dim")
            console.print(f"  Total runs: {flaky.total_runs}, Failed: {flaky.failed_runs}", style="dim")


def _run_conversion(project_path: Path, verbose: bool) -> None:
    """Run BDD conversion on ingested data."""
    print_timestamp("🔄 Running BDD conversion...", "bold yellow")

    from claude_playwright_agent.bdd import BDDConversionAgent, BDDConversionConfig

    state = StateManager(project_path)
    recordings = state.get_recordings()

    if not recordings:
        print_timestamp("   ⚠️  No recordings found. Run 'cpa ingest' first.", "yellow")
        return

    print_timestamp(f"   Processing {len(recordings)} recording(s)...", "cyan")

    config = BDDConversionConfig(
        extract_backgrounds=True,
        auto_tag_scenarios=True,
    )
    agent = BDDConversionAgent(project_path, config)
    result = agent.run()

    if result.success:
        print_timestamp(f"   ✅ Generated {result.total_scenarios} scenarios", "green")
        print_timestamp(f"   ✅ Created {result.total_features} feature file(s)", "green")
    else:
        print_timestamp("   ❌ BDD conversion failed", "red")


def _run_ingestion(project_path: Path, verbose: bool) -> None:
    """Ingest all pending recordings."""
    print_timestamp("📦 Checking for recordings to ingest...", "bold yellow")

    recordings_dir = project_path / "recordings"
    if not recordings_dir.exists():
        print_timestamp("   ⚠️  No recordings directory found.", "yellow")
        return

    recording_files = list(recordings_dir.glob("*.js"))
    print_timestamp(f"   Found {len(recording_files)} recording file(s)", "cyan")

    if not recording_files:
        print_timestamp("   ⚠️  No recording files found.", "yellow")
        return

    # TODO: Auto-ingest all files (will use ingest command)
    print_timestamp("   ℹ️  Use 'cpa ingest <file>' to ingest each recording", "cyan")


def _run_full_pipeline(project_path: Path, verbose: bool) -> None:
    """Run complete pipeline."""
    print_timestamp("🔄 Running full pipeline...", "bold blue")

    # Step 1: Ingest
    print_timestamp("   Step 1: Ingest recordings", "cyan")
    _run_ingestion(project_path, verbose)

    # Step 2: Convert
    print_timestamp("   Step 2: Convert to BDD", "cyan")
    _run_conversion(project_path, verbose)

    # Step 3: Test
    print_timestamp("   Step 3: Execute tests", "cyan")
    _run_tests(project_path, (), verbose)

    print_timestamp("✅ Full pipeline complete!", "bold green")
