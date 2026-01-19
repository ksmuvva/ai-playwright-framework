"""
Add Scenario Command.

Adds a new scenario to the test framework.
"""

import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
@click.argument("scenario_name", type=str)
@click.option(
    "--feature", "-f", type=str, default="general", help="Feature file to add scenario to"
)
@click.option("--description", "-d", type=str, default=None, help="Scenario description")
@click.option(
    "--tags", "-t", type=str, default=None, help="Tags for the scenario (comma-separated)"
)
@click.option(
    "--template",
    "-T",
    type=click.Choice(["basic", "login", "form", "search", "custom"]),
    default="basic",
    help="Scenario template to use",
)
@click.option(
    "--output", "-o", type=click.Path(), default=".", help="Output directory for feature files"
)
def add_scenario(
    scenario_name: str, feature: str, description: str, tags: str, template: str, output: str
) -> None:
    """
    Add a new BDD scenario to the test framework.

    \b
    USAGE:
        cpa add-scenario <scenario-name> [OPTIONS]

    \b
    EXAMPLES:
        # Add a basic scenario to general.feature
        cpa add-scenario "User Login"

        # Add a login scenario with tags
        cpa add-scenario "User Login" --feature auth --tags @smoke,@auth

        # Add a form scenario with description
        cpa add-scenario "Submit Contact Form" --template form --description "Test contact form submission"

    \b
    TEMPLATES:
        basic   Generic scenario template
        login   Login/authentication scenario
        form    Form submission scenario
        search  Search/filter scenario
    """
    output_path = Path(output)
    feature_file = output_path / f"{feature.lower().replace(' ', '_')}.feature"

    scenario_id = f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tag_list = []
    if tags:
        tag_list = [f"@{t.strip()}" for t in tags.split(",")]

    scenario_content = _generate_scenario(
        scenario_name=scenario_name,
        description=description,
        tags=tag_list,
        template=template,
        scenario_id=scenario_id,
    )

    feature_content = _update_feature_file(
        feature_file=feature_file, feature_name=feature.title(), new_scenario=scenario_content
    )

    console.print(
        Panel.fit(
            f"[bold green]Scenario '{scenario_name}' created successfully![/bold green]\n\n"
            f"[cyan]File:[/cyan] {feature_file}\n"
            f"[cyan]Template:[/cyan] {template}\n"
            f"[cyan]Tags:[/cyan] {', '.join(tag_list) if tag_list else 'None'}",
            title="Scenario Added",
            border_style="green",
        )
    )

    _print_next_steps(scenario_name, feature_file)


def _generate_scenario(
    scenario_name: str, description: str, tags: list, template: str, scenario_id: str
) -> str:
    """Generate scenario content based on template."""
    lines = []

    for tag in tags:
        lines.append(tag)

    lines.append(f"  Scenario: {scenario_name}")

    if description:
        lines.append(f"    # {description}")
        lines.append("")

    templates = {
        "basic": [
            ("Given ", "I am on the homepage"),
            ("When ", "I perform an action"),
            ("Then ", "I should see the expected result"),
        ],
        "login": [
            ("Given ", "I am on the login page"),
            ("When ", "I enter valid credentials"),
            ("And ", "I click the login button"),
            ("Then ", "I should be logged in successfully"),
            ("And ", "I should see my dashboard"),
        ],
        "form": [
            ("Given ", "I am on the form page"),
            ("When ", "I fill in the required fields"),
            ("And ", "I submit the form"),
            ("Then ", "I should see a success message"),
        ],
        "search": [
            ("Given ", "I am on the search page"),
            ("When ", "I enter a search query"),
            ("And ", "I click the search button"),
            ("Then ", "I should see search results"),
        ],
        "custom": [
            ("Given ", ""),
            ("When ", ""),
            ("Then ", ""),
        ],
    }

    template_steps = templates.get(template, templates["basic"])

    for prefix, default_step in template_steps:
        lines.append(f"    {prefix}")

    return "\n".join(lines)


def _update_feature_file(feature_file: Path, feature_name: str, new_scenario: str) -> str:
    """Update or create feature file with new scenario."""
    if feature_file.exists():
        content = feature_file.read_text()

        if "Feature:" in content:
            return content + "\n\n" + new_scenario + "\n"

    header = f"""@wip
Feature: {feature_name}
  As a user
  I want to perform actions
  So that I can achieve my goals

"""
    return header + new_scenario + "\n"


def _print_next_steps(scenario_name: str, feature_file: Path) -> None:
    """Print next steps for the user."""
    console.print("\n[bold yellow]Next Steps:[/bold yellow]")
    console.print("  1. Implement the step definitions in steps/")
    console.print("  2. Run: cpa run test --tags @wip")
    console.print("  3. Remove @wip tag when ready")
