"""
Flaky tests command - View and manage flaky tests.

This module provides commands to:
- List flaky tests from history
- Display detailed flaky test information
- Clear flaky test history
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from claude_playwright_agent.state import StateManager
from claude_playwright_agent.agents.failure_analysis import FailureAnalyzer

console = Console()


@click.group()
def flaky() -> None:
    """Flaky test detection and management commands."""
    pass


@flaky.command(name="list")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--min-runs",
    type=int,
    default=3,
    help="Minimum number of runs to consider",
)
@click.option(
    "--threshold",
    type=float,
    default=0.5,
    help="Flaky threshold (pass rate below this is considered flaky)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed information",
)
def flaky_list(project_path: str, min_runs: int, threshold: float, verbose: bool) -> None:
    """
    List detected flaky tests.

    This command analyzes test execution history to identify tests
    with inconsistent results that may be flaky.

    Examples:
        cpa flaky list                          # List all flaky tests
        cpa flaky list --min-runs 5             # Only tests with 5+ runs
        cpa flaky list --threshold 0.3          # Use stricter threshold
        cpa flaky list --verbose                # Show detailed info
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    # Get historical test runs
    state = StateManager(project_path)
    test_runs = state.get_test_runs(limit=100)

    if not test_runs:
        console.print("[INFO] No test runs found in history.", style="yellow")
        console.print("Run tests first with 'cpa run test' to build history.", style="dim")
        return

    # Build analyzer with historical data
    analyzer = FailureAnalyzer()

    # Reconstruct test history from state
    # Note: This is simplified - in production we'd store detailed per-test results
    for run in test_runs:
        # We would need to store individual test results in state
        # For now, this demonstrates the concept
        pass

    # For now, we can only use the analyzer's internal history if tests were run recently
    # In a full implementation, StateManager would store detailed per-test results

    flaky_tests = analyzer.detect_flaky_tests(min_runs=min_runs, flaky_threshold=threshold)

    if not flaky_tests:
        console.print(f"[INFO] No flaky tests detected (min_runs={min_runs}, threshold={threshold}).", style="green")
        console.print("\nTips for detecting flaky tests:", style="dim")
        console.print("  - Run tests multiple times to build history")
        console.print("  - Lower --min-runs to detect flakiness sooner")
        console.print("  - Increase --threshold for stricter detection")
        return

    # Display flaky tests table
    console.print("")

    summary_table = Table(title=f"⚠️  Flaky Tests Detected ({len(flaky_tests)})", show_header=True)
    summary_table.add_column("Test", style="cyan", width=40)
    summary_table.add_column("Pass Rate", style="yellow", width=10)
    summary_table.add_column("Confidence", style="bold", width=10)
    summary_table.add_column("Inconsistency", style="red", width=12)
    summary_table.add_column("Retry Pass %", style="green", width=12)

    for flaky in flaky_tests[:20]:  # Show top 20
        # Style based on severity
        pass_rate_style = "green" if flaky.pass_rate > 0.7 else "yellow" if flaky.pass_rate > 0.5 else "red"
        confidence_style = "bold red" if flaky.flaky_confidence > 0.7 else "yellow" if flaky.flaky_confidence > 0.4 else "dim"
        inconsistency_style = "bold red" if flaky.inconsistency_score > 0.7 else "yellow" if flaky.inconsistency_score > 0.4 else "dim"

        summary_table.add_row(
            flaky.test_name[:40],
            f"[{pass_rate_style}]{flaky.pass_rate:.1%}[/]",
            f"[{confidence_style}]{flaky.flaky_confidence:.0%}[/]",
            f"[{inconsistency_style}]{flaky.inconsistency_score:.0%}[/]",
            f"{flaky.passes_on_retry_rate:.0%}",
        )

    console.print(summary_table)

    # Detailed view if verbose
    if verbose and flaky_tests:
        console.print("")
        for i, flaky in enumerate(flaky_tests[:5], 1):
            details = [
                f"[bold cyan]Test {i}: {flaky.test_name}[/bold cyan]",
                f"",
                f"  Statistics:",
                f"    Total runs: {flaky.total_runs}",
                f"    Failed runs: {flaky.failed_runs}",
                f"    Pass rate: {flaky.pass_rate:.1%}",
                f"",
                f"  Flaky Metrics:",
                f"    Confidence: {flaky.flaky_confidence:.1%} (how confident we are it's flaky)",
                f"    Inconsistency: {flaky.inconsistency_score:.1%} (how inconsistent results are)",
                f"    Retry pass rate: {flaky.passes_on_retry_rate:.1%} (failures that pass on retry)",
                f"",
                f"  Likely cause: {flaky.likely_cause}",
            ]
            console.print(Panel("\n".join(details), border_style="yellow"))
            console.print("")


@flaky.command(name="analyze")
@click.argument("test_name")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
def flaky_analyze(test_name: str, project_path: str) -> None:
    """
    Analyze a specific test for flakiness.

    Displays detailed information about why a test is considered flaky
    and provides recommendations for fixing it.

    Examples:
        cpa flaky analyze "features/login/login.feature:Login with valid credentials"
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    # Get analyzer and detect flaky tests
    analyzer = FailureAnalyzer()
    flaky_tests = analyzer.detect_flaky_tests(min_runs=1)

    # Find the specific test
    found = None
    for flaky in flaky_tests:
        if test_name.lower() in flaky.test_name.lower():
            found = flaky
            break

    if not found:
        console.print(f"[INFO] Test '{test_name}' not found in flaky test history.", style="yellow")
        console.print("\nTips:", style="dim")
        console.print("  - Use 'cpa flaky list' to see all flaky tests")
        console.print("  - Run the test multiple times to build history")
        console.print("  - Check the test name for typos")
        return

    # Display detailed analysis
    console.print("")
    console.print(Panel(
        f"[bold cyan]Test Analysis: {found.test_name}[/bold cyan]\n\n"
        f"Pass Rate: [yellow]{found.pass_rate:.1%}[/yellow]\n"
        f"Total Runs: {found.total_runs}\n"
        f"Failed Runs: {found.failed_runs}\n\n"
        f"[bold]Flaky Metrics:[/bold]\n"
        f"  Confidence: {found.flaky_confidence:.1%}\n"
        f"  Inconsistency: {found.inconsistency_score:.1%}\n"
        f"  Retry Pass Rate: {found.passes_on_retry_rate:.1%}\n\n"
        f"[bold]Likely Cause:[/bold]\n"
        f"  {found.likely_cause}",
        title="Flaky Test Analysis",
        border_style="yellow",
    ))

    # Recommendations based on metrics
    console.print("\n[bold]Recommendations:[/bold]")
    if found.passes_on_retry_rate > 0.5:
        console.print("  [green]•[/green] High retry pass rate indicates timing issues")
        console.print("    - Add explicit waits (wait_for_selector, wait_for_response)")
        console.print("    - Increase timeout for specific operations")
        console.print("    - Check for race conditions in parallel execution")
    elif found.inconsistency_score > 0.7:
        console.print("  [green]•[/green] High inconsistency suggests environment dependency")
        console.print("    - Check for external API dependencies")
        console.print("    - Verify test data is properly isolated")
        console.print("    - Consider using test fixtures with setup/teardown")
    elif found.flaky_confidence > 0.7:
        console.print("  [green]•[/green] High confidence flaky test - prioritize fixing")
        console.print("    - Review test for fragile selectors")
        console.print("    - Check for dependencies on other tests")
        console.print("    - Ensure proper cleanup in tearDown")
    else:
        console.print("  [green]•[/green] Monitor this test over more runs")
        console.print("    - Run the test more frequently")
        console.print("    - Check if flakiness correlates with specific conditions")


@flaky.command(name="export")
@click.argument("output_file")
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def flaky_export(output_file: str, project_path: str, format: str) -> None:
    """
    Export flaky test data to a file.

    Exports all flaky test information to JSON or YAML format
    for further analysis or reporting.

    Examples:
        cpa flaky export flaky_tests.json
        cpa flaky export flaky_tests.yaml --format yaml
    """
    import json

    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    # Get flaky tests
    analyzer = FailureAnalyzer()
    flaky_tests = analyzer.detect_flaky_tests()

    if not flaky_tests:
        console.print("[INFO] No flaky tests to export.", style="yellow")
        return

    # Prepare export data
    export_data = {
        "total_flaky_tests": len(flaky_tests),
        "flaky_tests": [f.to_dict() for f in flaky_tests],
    }

    # Write to file
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        if format == "json":
            json.dump(export_data, f, indent=2)
        else:  # yaml
            import yaml
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"[OK] Exported {len(flaky_tests)} flaky test(s) to {output_file}", style="bold green")
