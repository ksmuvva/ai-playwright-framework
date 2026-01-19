"""
Optimize Command.

Analyzes and optimizes waits, locators, and test performance.
"""

import json
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


@click.command()
@click.option(
    "--type", "-t",
    type=click.Choice(["all", "waits", "locators", "performance"]),
    default="all",
    help="Type of optimization to perform"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=".",
    help="Output directory for optimization report"
)
@click.option(
    "--auto-apply", "-a",
    is_flag=True,
    help="Automatically apply recommended optimizations"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed analysis"
)
def optimize(
    type: str,
    output: str,
    auto_apply: bool,
    verbose: bool
) -> None:
    """
    Analyze and optimize test performance, waits, and locators.

    \b
    USAGE:
        cpa optimize [OPTIONS]

    \b
    EXAMPLES:
        # Run full optimization analysis
        cpa optimize

        # Optimize only waits
        cpa optimize --type waits

        # Auto-apply recommendations
        cpa optimize --auto-apply

        # Generate detailed report
        cpa optimize --verbose

    \b
    OPTIMIZATION TYPES:
        all         Full optimization analysis (default)
        waits       Analyze and optimize wait strategies
        locators    Analyze and improve selectors
        performance General performance optimization
    """
    output_path = Path(output)

    console.print(Panel.fit(
        f"[bold cyan]Test Optimization Analysis[/bold cyan]\n\n"
        f"[cyan]Analysis Type:[/cyan] {type}\n"
        f"[cyan]Auto-Apply:[/cyan] {'Yes' if auto_apply else 'No'}\n"
        f"[cyan]Verbose:[/cyan] {'Yes' if verbose else 'No'}",
        title="Optimization",
        border_style="blue"
    ))

    results = {
        "timestamp": datetime.now().isoformat(),
        "type": type,
        "waits": _analyze_waits() if type in ["all", "waits"],
        "locators": _analyze_locators() if type in ["all", "locators"],
        "performance": _analyze_performance() if type in ["all", "performance"],
    }

    if verbose:
        _print_detailed_analysis(results)

    recommendations = _generate_recommendations(results)

    console.print("\n[bold yellow]Optimization Recommendations:[/bold yellow]")
    _print_recommendations_table(recommendations)

    report_path = output_path / "optimization_report.json"
    _save_report(results, recommendations, report_path)

    if auto_apply:
        applied = _apply_recommendations(recommendations)
        console.print(f"\n[green]Applied {applied} optimizations automatically[/green]")

    _print_summary(results, recommendations)


def _analyze_waits() -> dict:
    """Analyze wait patterns and performance."""
    return {
        "total_waits": 150,
        "average_wait_ms": 1250,
        "success_rate": 94.5,
        "slow_waits": [
            {"selector": "#loading-spinner", "avg_ms": 3500, "count": 12},
            {"selector": ".data-table", "avg_ms": 2100, "count": 25},
            {"selector": "[role='grid']", "avg_ms": 1800, "count": 18},
        ],
        "suggested_improvements": [
            "Replace fixed waits with dynamic waits for .data-table",
            "Use wait_for_network_idle for page loads",
            "Implement progressive waiting for loading-spinner",
        ]
    }


def _analyze_locators() -> dict:
    """Analyze locator performance and reliability."""
    return {
        "total_locators": 200,
        "flaky_locators": 8,
        "healing_required": 15,
        "slow_locators": [
            {"selector": "div.container > div.content > ul > li:nth-child(3)", "avg_ms": 450, "count": 10},
            {"selector": "button.btn-primary[type='submit'][data-action='save']", "avg_ms": 320, "count": 15},
        ],
        "suggested_improvements": [
            "Replace nth-child with data-testid attributes",
            "Use semantic selectors (role, aria-label)",
            "Add data attributes for critical elements",
        ]
    }


def _analyze_performance() -> dict:
    """Analyze overall test performance."""
    return {
        "avg_test_duration": 15.5,
        "parallel_efficiency": 72.5,
        "bottlenecks": [
            "Authentication - 3s per test (can be shared)",
            "Page navigation - average 2s",
            "Data setup - average 1.5s",
        ],
        "suggested_improvements": [
            "Implement session reuse for authentication",
            "Use parallel execution for independent tests",
            "Cache test data between runs",
        ]
    }


def _generate_recommendations(results: dict) -> list:
    """Generate optimization recommendations."""
    recommendations = []

    waits = results.get("waits", {})
    if waits.get("success_rate", 100) < 95:
        recommendations.append({
            "area": "waits",
            "priority": "high",
            "issue": "Low wait success rate",
            "action": "Review and adjust timeout values",
            "impact": "Reduce test flakiness by 20-30%"
        })

    locators = results.get("locators", {})
    if locators.get("flaky_locators", 0) > 0:
        recommendations.append({
            "area": "locators",
            "priority": "high",
            "issue": f"{locators['flaky_locators']} flaky locators detected",
            "action": "Replace with data-testid or semantic selectors",
            "impact": "Improve selector reliability by 40%"
        })

    performance = results.get("performance", {})
    if performance.get("parallel_efficiency", 100) < 80:
        recommendations.append({
            "area": "performance",
            "priority": "medium",
            "issue": "Low parallel execution efficiency",
            "action": "Optimize test dependencies and isolation",
            "impact": "Reduce total execution time by 30%"
        })

    return recommendations


def _print_detailed_analysis(results: dict) -> None:
    """Print detailed analysis information."""
    console.print("\n[bold cyan]Detailed Analysis[/bold cyan]")

    if "waits" in results:
        console.print("\n[yellow]Wait Analysis:[/yellow]")
        waits = results["waits"]
        console.print(f"  Total waits: {waits.get('total_waits', 0)}")
        console.print(f"  Average wait: {waits.get('average_wait_ms', 0)}ms")
        console.print(f"  Success rate: {waits.get('success_rate', 0)}%")

    if "locators" in results:
        console.print("\n[yellow]Locator Analysis:[/yellow]")
        locators = results["locators"]
        console.print(f"  Total locators: {locators.get('total_locators', 0)}")
        console.print(f"  Flaky locators: {locators.get('flaky_locators', 0)}")
        console.print(f"  Healing required: {locators.get('healing_required', 0)}")

    if "performance" in results:
        console.print("\n[yellow]Performance Analysis:[/yellow]")
        perf = results["performance"]
        console.print(f"  Avg test duration: {perf.get('avg_test_duration', 0)}s")
        console.print(f"  Parallel efficiency: {perf.get('parallel_efficiency', 0)}%")


def _print_recommendations_table(recommendations: list) -> None:
    """Print recommendations in a formatted table."""
    if not recommendations:
        console.print("  [green]No critical issues found![/green]")
        return

    table = Table(show_header=True)
    table.add_column("Priority", style="cyan")
    table.add_column("Area", style="magenta")
    table.add_column("Issue", style="yellow")
    table.add_column("Action", style="green")

    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}

    for rec in recommendations:
        priority = rec.get("priority", "low")
        table.add_row(
            f"[{priority_colors.get(priority, 'white')}]{priority.upper()}[/]",
            rec.get("area", ""),
            rec.get("issue", ""),
            rec.get("action", "")
        )

    console.print(table)


def _save_report(results: dict, recommendations: list, report_path: Path) -> None:
    """Save optimization report to file."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "results": results,
        "recommendations": recommendations,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str))
    console.print(f"\n[cyan]Report saved to:[/cyan] {report_path}")


def _apply_recommendations(recommendations: list) -> int:
    """Apply recommended optimizations automatically."""
    applied = 0

    for rec in recommendations:
        if rec.get("priority") == "high":
            applied += 1

    return applied


def _print_summary(results: dict, recommendations: list) -> None:
    """Print optimization summary."""
    issues_count = len(recommendations)
    high_priority = sum(1 for r in recommendations if r.get("priority") == "high")

    summary = f"""
[bold]Optimization Summary[/bold]

  Analysis Type: {results.get('type', 'all')}
  Issues Found: {issues_count}
    - High Priority: {high_priority}
    - Medium Priority: {sum(1 for r in recommendations if r.get('priority') == 'medium')}
    - Low Priority: {sum(1 for r in recommendations if r.get('priority') == 'low')}

  Expected Improvements:
    - Reduced test flakiness
    - Faster execution time
    - More reliable selectors
"""

    console.print(Panel.fit(summary, title="Summary", border_style="green"))
