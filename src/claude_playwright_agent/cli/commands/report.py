"""
Report command - View test reports and project statistics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from claude_playwright_agent.state import StateManager

console = Console()


def print_timestamp(message: str, style: str = "") -> None:
    """Print a message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"[{timestamp}] {message}", style=style)


@click.command()
@click.option(
    "--project-path", "-p",
    default=".",
    help="Path to project directory",
)
@click.option(
    "--type", "-t",
    type=click.Choice(["summary", "recordings", "scenarios", "test-runs", "components", "trends"]),
    default="summary",
    help="Report type to display",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json", "html", "pdf"]),
    default="table",
    help="Output format",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Output file path (for html/pdf formats)",
)
@click.option(
    "--limit", "-l",
    type=int,
    default=100,
    help="Limit number of results",
)
def report(
    project_path: str,
    type: str,
    format: str,
    output: Path | None,
    limit: int,
) -> None:
    """
    View test reports and project statistics.

    Report types:
    - summary: Overall project statistics
    - recordings: Detailed recording information
    - scenarios: BDD scenario information
    - test-runs: Test execution history
    - components: UI component inventory
    - trends: Historical trends and analysis

    Formats:
    - table: Rich terminal table (default)
    - json: Machine-readable JSON
    - html: Interactive HTML report
    - pdf: PDF document

    Examples:
        cpa report                        # Show summary
        cpa report --type scenarios        # List scenarios
        cpa report --type recordings -f json  # Recordings as JSON
        cpa report --type test-runs -f html -o report.html  # HTML report
        cpa report --type trends          # Show historical trends
    """
    project_path = Path(project_path)

    # Check if project is initialized
    if not StateManager.is_initialized(project_path):
        console.print("[ERROR] Project not initialized. Run 'cpa init' first.", style="bold red")
        sys.exit(1)

    try:
        state = StateManager(project_path)
    except Exception as e:
        console.print(f"[ERROR] Failed to load state: {e}", style="bold red")
        sys.exit(1)

    print_timestamp(f"📊 Generating report: {type}", "bold blue")

    if type == "summary":
        _show_summary(state, format, output, project_path)
    elif type == "recordings":
        _show_recordings(state, format, output, project_path, limit)
    elif type == "scenarios":
        _show_scenarios(state, format, output, project_path, limit)
    elif type == "test-runs":
        _show_test_runs(state, format, output, project_path, limit)
    elif type == "components":
        _show_components(state, format, output, project_path)
    elif type == "trends":
        _show_trends(state, format, output, project_path, limit)


def _generate_html_report(data: dict[str, Any], title: str) -> str:
    """Generate HTML report from data."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Claude Playwright Agent</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .timestamp {{
            color: #666;
            font-size: 14px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .card h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }}

        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}

        tr:hover {{
            background: #f9fafb;
        }}

        .metric {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}

        .metric-card {{
            background: #f9fafb;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}

        .metric-card .label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}

        .metric-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}

        .status-pass {{
            color: #10b981;
        }}

        .status-fail {{
            color: #ef4444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="card">
            <h2>Summary</h2>
            <div class="metric">
                {_render_html_metrics(data.get('summary', {}))}
            </div>
        </div>

        <div class="card">
            <h2>Details</h2>
            {_render_html_table(data.get('details', []))}
        </div>
    </div>
</body>
</html>"""


def _render_html_metrics(summary: dict[str, Any]) -> str:
    """Render metrics cards for HTML."""
    html = ""
    for key, value in summary.items():
        html += f"""
                <div class="metric-card">
                    <div class="label">{key}</div>
                    <div class="value">{value}</div>
                </div>"""
    return html


def _render_html_table(items: list[dict[str, Any]]) -> str:
    """Render HTML table from data."""
    if not items:
        return "<p>No data available</p>"

    # Get headers from first item
    headers = list(items[0].keys())

    html = "<table><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"

    for item in items:
        html += "<tr>"
        for header in headers:
            value = item.get(header, "")
            # Handle status highlighting
            if header.lower() == "status":
                status_class = "status-pass" if str(value).lower() in ("pass", "passed", "success") else "status-fail"
                html += f'<td class="{status_class}">{value}</td>'
            else:
                html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html


def _save_output(content: str, output: Path | None, default_name: str, project_path: Path) -> Path:
    """Save output to file."""
    if output is None:
        output = project_path / "reports" / default_name
        output.parent.mkdir(parents=True, exist_ok=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output


def _show_summary(state: StateManager, format: str, output: Path | None, project_path: Path) -> None:
    """Show project summary."""
    project_meta = state.get_project_metadata()
    recordings = state.get_recordings()
    scenarios = state.get_all_scenarios()
    test_runs = state.get_test_runs(limit=100)
    components = state._state.components

    total_tests = sum(run.total for run in test_runs)
    total_passed = sum(run.passed for run in test_runs)
    total_failed = sum(run.failed for run in test_runs)
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0

    summary_data = {
        "summary": {
            "Project Name": project_meta.name,
            "Framework": project_meta.framework_type.value,
            "Version": project_meta.version,
            "Recordings": len(recordings),
            "Scenarios": len(scenarios),
            "Test Runs": len(test_runs),
            "Components": len(components),
            "Total Tests": total_tests,
            "Passed": total_passed,
            "Failed": total_failed,
            "Pass Rate": f"{pass_rate:.1f}%",
        },
        "details": [],
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "summary.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "Project Summary")
        output_path = _save_output(html, output, "summary.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        # Summary table
        table = Table(title="Project Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project Name", project_meta.name)
        table.add_row("Framework", project_meta.framework_type.value)
        table.add_row("Version", project_meta.version)
        table.add_row("Created", project_meta.created_at[:19])
        table.add_row("", "")
        table.add_row("Recordings", str(len(recordings)))
        table.add_row("Scenarios", str(len(scenarios)))
        table.add_row("Test Runs", str(len(test_runs)))
        table.add_row("Components", str(len(components)))

        console.print(table)

        # Test statistics
        if test_runs:
            console.print("")
            stats_table = Table(title="Test Statistics", show_header=True)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")

            if total_tests > 0:
                stats_table.add_row("Total Tests", str(total_tests))
                stats_table.add_row("Passed", str(total_passed))
                stats_table.add_row("Failed", str(total_failed))
                stats_table.add_row("Skipped", str(sum(run.skipped for run in test_runs)))
                stats_table.add_row("Pass Rate", f"{pass_rate:.1f}%")

            console.print(stats_table)


def _show_recordings(state: StateManager, format: str, output: Path | None, project_path: Path, limit: int) -> None:
    """Show recordings information."""
    recordings = state.get_recordings()[:limit]

    summary_data = {
        "summary": {"Total Recordings": len(recordings)},
        "details": [
            {
                "ID": rec.recording_id[:20],
                "File": rec.file_path,
                "Status": rec.status.value,
                "Actions": rec.actions_count,
                "Scenarios": rec.scenarios_count,
                "Ingested": rec.ingested_at[:19],
            }
            for rec in recordings
        ],
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "recordings.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "Recordings Report")
        output_path = _save_output(html, output, "recordings.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        table = Table(title="Recordings", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Actions", style="blue")
        table.add_column("Scenarios", style="blue")
        table.add_column("Ingested", style="dim")

        for rec in recordings:
            status_style = "green" if rec.status == "completed" else "yellow"
            table.add_row(
                rec.recording_id[:20],
                rec.file_path,
                f"[{status_style}]{rec.status.value}[/]",
                str(rec.actions_count),
                str(rec.scenarios_count),
                rec.ingested_at[:19],
            )

        console.print(table)


def _show_scenarios(state: StateManager, format: str, output: Path | None, project_path: Path, limit: int) -> None:
    """Show scenarios information."""
    scenarios = state.get_all_scenarios()[:limit]

    summary_data = {
        "summary": {"Total Scenarios": len(scenarios)},
        "details": [
            {
                "ID": scen.scenario_id[:20],
                "Name": scen.scenario_name[:50],
                "Feature": scen.feature_file[:50],
                "Tags": ", ".join(scen.tags[:5]),
                "Steps": scen.steps_count,
                "Created": scen.created_at[:19],
            }
            for scen in scenarios
        ],
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "scenarios.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "BDD Scenarios Report")
        output_path = _save_output(html, output, "scenarios.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        table = Table(title="BDD Scenarios", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Feature", style="blue")
        table.add_column("Tags", style="yellow")
        table.add_column("Steps", style="blue")
        table.add_column("Created", style="dim")

        for scen in scenarios:
            tags_str = ", ".join(scen.tags[:3])
            if len(scen.tags) > 3:
                tags_str += "..."
            table.add_row(
                scen.scenario_id[:20],
                scen.scenario_name[:30],
                scen.feature_file[:30],
                tags_str,
                str(scen.steps_count),
                scen.created_at[:19],
            )

        console.print(table)


def _show_test_runs(state: StateManager, format: str, output: Path | None, project_path: Path, limit: int) -> None:
    """Show test run history."""
    test_runs = state.get_test_runs(limit=limit)

    total_tests = sum(run.total for run in test_runs)
    total_passed = sum(run.passed for run in test_runs)
    avg_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0

    summary_data = {
        "summary": {
            "Total Runs": len(test_runs),
            "Total Tests": total_tests,
            "Average Pass Rate": f"{avg_pass_rate:.1f}%",
        },
        "details": [
            {
                "Run ID": run.run_id[:20],
                "Date": run.timestamp[:19],
                "Total": run.total,
                "Passed": run.passed,
                "Failed": run.failed,
                "Skipped": run.skipped,
                "Duration": f"{run.duration:.1f}s",
            }
            for run in test_runs
        ],
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "test-runs.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "Test Runs Report")
        output_path = _save_output(html, output, "test-runs.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        table = Table(title="Test Runs", show_header=True)
        table.add_column("Run ID", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Total", style="blue")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Skipped", style="yellow")
        table.add_column("Duration", style="dim")

        for run in test_runs:
            table.add_row(
                run.run_id[:20],
                run.timestamp[:19],
                str(run.total),
                str(run.passed),
                str(run.failed),
                str(run.skipped),
                f"{run.duration:.1f}s",
            )

        console.print(table)


def _show_components(state: StateManager, format: str, output: Path | None, project_path: Path) -> None:
    """Show UI components inventory."""
    components = state._state.components

    details = []
    for comp_id, comp in components.items():
        pages_str = ", ".join(comp.pages[:2])
        if len(comp.pages) > 2:
            pages_str += "..."
        details.append({
            "ID": comp_id[:20],
            "Name": comp.name[:50],
            "Type": comp.component_type,
            "Elements": len(comp.elements),
            "Pages": pages_str,
        })

    summary_data = {
        "summary": {"Total Components": len(components)},
        "details": details,
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "components.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "UI Components Report")
        output_path = _save_output(html, output, "components.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        table = Table(title="UI Components", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Elements", style="blue")
        table.add_column("Pages", style="dim")

        for comp_id, comp in components.items():
            pages_str = ", ".join(comp.pages[:2])
            if len(comp.pages) > 2:
                pages_str += "..."
            table.add_row(
                comp_id[:20],
                comp.name[:30],
                comp.component_type,
                str(len(comp.elements)),
                pages_str,
            )

        console.print(table)


def _show_trends(state: StateManager, format: str, output: Path | None, project_path: Path, limit: int) -> None:
    """Show historical trends and analysis."""
    test_runs = state.get_test_runs(limit=limit)

    if not test_runs:
        console.print("[yellow]No test run data available for trends analysis[/yellow]")
        return

    # Calculate trends
    runs_by_date = {}
    for run in test_runs:
        date = run.timestamp[:10]
        if date not in runs_by_date:
            runs_by_date[date] = {"total": 0, "passed": 0, "failed": 0, "count": 0}
        runs_by_date[date]["total"] += run.total
        runs_by_date[date]["passed"] += run.passed
        runs_by_date[date]["failed"] += run.failed
        runs_by_date[date]["count"] += 1

    # Sort by date
    sorted_dates = sorted(runs_by_date.keys())

    # Calculate overall trend
    if len(sorted_dates) >= 2:
        first_date = sorted_dates[0]
        last_date = sorted_dates[-1]
        first_pass_rate = (
            runs_by_date[first_date]["passed"] / runs_by_date[first_date]["total"] * 100
            if runs_by_date[first_date]["total"] > 0 else 0
        )
        last_pass_rate = (
            runs_by_date[last_date]["passed"] / runs_by_date[last_date]["total"] * 100
            if runs_by_date[last_date]["total"] > 0 else 0
        )
        trend = last_pass_rate - first_pass_rate
        trend_direction = "↑" if trend > 0 else "↓" if trend < 0 else "→"
    else:
        trend = 0
        trend_direction = "→"
        first_date = ""
        last_date = ""

    summary_data = {
        "summary": {
            "Total Runs Analyzed": len(test_runs),
            "Date Range": f"{first_date} to {last_date}" if first_date else "N/A",
            "Pass Rate Trend": f"{trend_direction} {trend:+.1f}%",
        },
        "details": [
            {
                "Date": date,
                "Runs": data["count"],
                "Total Tests": data["total"],
                "Passed": data["passed"],
                "Failed": data["failed"],
                "Pass Rate": f"{(data['passed'] / data['total'] * 100):.1f}%" if data["total"] > 0 else "N/A",
            }
            for date in sorted_dates
        ],
    }

    if format == "json":
        content = json.dumps(summary_data, indent=2)
        if output:
            output_path = _save_output(content, output, "trends.json", project_path)
            print_timestamp(f"✓ Report saved: {output_path}", "green")
        else:
            console.print_json(content)

    elif format == "html":
        html = _generate_html_report(summary_data, "Historical Trends Report")
        output_path = _save_output(html, output, "trends.html", project_path)
        print_timestamp(f"✓ Report saved: {output_path}", "green")

    else:  # table format
        console.print("")
        summary_table = Table(title="Trends Summary", show_header=True)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Runs Analyzed", str(len(test_runs)))
        summary_table.add_row("Date Range", f"{first_date} to {last_date}" if first_date else "N/A")
        trend_style = "green" if trend > 0 else "red" if trend < 0 else "yellow"
        summary_table.add_row("Pass Rate Trend", f"[{trend_style}]{trend_direction} {trend:+.1f}%[/]")

        console.print(summary_table)

        console.print("")
        details_table = Table(title="Test Runs by Date", show_header=True)
        details_table.add_column("Date", style="cyan")
        details_table.add_column("Runs", style="blue")
        details_table.add_column("Total", style="blue")
        details_table.add_column("Passed", style="green")
        details_table.add_column("Failed", style="red")
        details_table.add_column("Pass Rate", style="yellow")

        for date in sorted_dates:
            data = runs_by_date[date]
            pass_rate = (data["passed"] / data["total"] * 100) if data["total"] > 0 else 0
            details_table.add_row(
                date,
                str(data["count"]),
                str(data["total"]),
                str(data["passed"]),
                str(data["failed"]),
                f"{pass_rate:.1f}%",
            )

        console.print(details_table)
