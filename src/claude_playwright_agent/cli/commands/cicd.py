"""
CI/CD command - Generate CI/CD pipeline configurations.

Generates CI/CD configuration files for:
- GitHub Actions
- GitLab CI/CD
- Jenkins
- Azure DevOps
- CircleCI
"""

import sys
from pathlib import Path

import click
from rich.console import Console

from claude_playwright_agent.scaffold.cicd import (
    CICDTemplateGenerator,
    CIConfig,
    CIPlatform,
    TestFramework as CICTestFramework,
)

console = Console()


@click.group()
def cicd() -> None:
    """Generate CI/CD pipeline configurations."""
    pass


@cicd.command(name="generate")
@click.option(
    "--platform", "-p",
    type=click.Choice(["github", "gitlab", "jenkins", "azure", "circleci", "all"]),
    default="all",
    help="CI/CD platform",
)
@click.option(
    "--framework", "-f",
    type=click.Choice(["behave", "pytest-bdd"]),
    default="behave",
    help="BDD framework",
)
@click.option(
    "--python-version",
    default="3.12",
    help="Python version",
)
@click.option(
    "--node-version",
    default="20",
    help="Node.js version",
)
@click.option(
    "--parallel-jobs",
    type=int,
    default=4,
    help="Number of parallel test jobs",
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True, path_type=Path),
    default=Path("."),
    help="Output directory",
)
@click.option(
    "--slack-webhook",
    default="",
    help="Slack webhook URL for notifications",
)
@click.option(
    "--enable-notifications",
    is_flag=True,
    help="Enable Slack notifications",
)
@click.option(
    "--enable-cache",
    is_flag=True,
    default=True,
    help="Enable dependency caching",
)
def generate_ci(
    platform: str,
    framework: str,
    python_version: str,
    node_version: str,
    parallel_jobs: int,
    output_dir: Path,
    slack_webhook: str,
    enable_notifications: bool,
    enable_cache: bool,
) -> None:
    """
    Generate CI/CD pipeline configuration files.

    \b
    USAGE:
        cpa cicd generate                    # Generate all configurations
        cpa cicd generate -p github          # Generate GitHub Actions only
        cpa cicd generate -f pytest-bdd      # Use pytest-bdd framework

    \b
    EXAMPLES:
        # Generate GitHub Actions workflow
        cpa cicd generate --platform github

        # Generate all with custom Python version
        cpa cicd generate --python-version 3.11

        # Generate with Slack notifications
        cpa cicd generate --enable-notifications --slack-webhook $SLACK_WEBHOOK

        # Generate to specific directory
        cpa cicd generate --output-dir .github/workflows
    """
    console.print(f"[bold cyan]Generating CI/CD configuration for: {platform}[/bold cyan]")
    console.print(f"  Framework: {framework}")
    console.print(f"  Python: {python_version}, Node.js: {node_version}")
    console.print(f"  Parallel jobs: {parallel_jobs}")
    console.print("")

    generator = CICDTemplateGenerator()

    if platform == "all":
        # Generate all configurations
        config = CIConfig(
            platform=CIPlatform.GITHUB_ACTIONS,
            framework=CICTestFramework(framework),
            python_version=python_version,
            node_version=node_version,
            parallel_jobs=parallel_jobs,
            enable_cache=enable_cache,
            enable_notifications=enable_notifications,
            slack_webhook=slack_webhook,
        )

        generated = generator.generate_all(config, output_dir)

        console.print(f"[bold green]Generated {len(generated)} CI/CD configuration(s):[/bold green]")
        for plat, path in generated.items():
            console.print(f"  - {plat.value}: {path}")

    else:
        # Generate specific platform
        platform_enum = CIPlatform(platform)
        config = CIConfig(
            platform=platform_enum,
            framework=CICTestFramework(framework),
            python_version=python_version,
            node_version=node_version,
            parallel_jobs=parallel_jobs,
            enable_cache=enable_cache,
            enable_notifications=enable_notifications,
            slack_webhook=slack_webhook,
        )

        # Determine output filename based on platform
        filename = {
            "github": ".github/workflows/bdd-tests.yml",
            "gitlab": ".gitlab-ci.yml",
            "jenkins": "Jenkinsfile",
            "azure": "azure-pipelines.yml",
            "circleci": ".circleci/config.yml",
        }[platform]

        output_path = output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator.generate(config, output_path)

        console.print(f"[bold green]Generated {platform_enum.value} configuration:[/bold green]")
        console.print(f"  {output_path}")

    console.print("")
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print("  1. Review the generated configuration file(s)")
    console.print("  2. Commit and push to your repository")
    console.print("  3. Configure any required secrets (e.g., SLACK_WEBHOOK)")
    console.print("  4. Monitor your CI/CD pipeline runs")


@cicd.command(name="validate")
@click.argument(
    "config-file",
    type=click.Path(exists=True, path_type=Path),
)
def validate_ci(config_file: Path) -> None:
    """
    Validate a CI/CD configuration file.

    \b
    USAGE:
        cpa cicd validate .github/workflows/bdd-tests.yml
        cpa cicd validate .gitlab-ci.yml
        cpa cicd validate Jenkinsfile

    \b
    EXAMPLES:
        # Validate GitHub Actions workflow
        cpa cicd validate .github/workflows/bdd-tests.yml

        # Validate GitLab CI config
        cpa cicd validate .gitlab-ci.yml
    """
    console.print(f"[bold cyan]Validating: {config_file}[/bold cyan]")

    filename = config_file.name
    errors = []
    warnings = []

    # Check file extension/name
    if filename.endswith(".yml") or filename.endswith(".yaml"):
        # YAML file
        try:
            import yaml

            with open(config_file) as f:
                content = yaml.safe_load(f)

            if content is None:
                errors.append("File is empty")
            else:
                console.print("[green]✓ Valid YAML syntax[/green]")

        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
        except ImportError:
            warnings.append("PyYAML not installed, skipping YAML validation")

    elif filename == "Jenkinsfile":
        # Groovy file (basic validation)
        content = config_file.read_text()

        if "pipeline" in content:
            console.print("[green]✓ Contains pipeline definition[/green]")
        else:
            errors.append("Missing pipeline definition")

        if "stage(" in content or "stages {" in content:
            console.print("[green]✓ Contains stages[/green]")
        else:
            warnings.append("No stages found")

    else:
        warnings.append(f"Unknown configuration type: {filename}")

    # Report results
    console.print("")

    if errors:
        console.print("[bold red]Errors:[/bold red]")
        for error in errors:
            console.print(f"  ✗ {error}")
        console.print("")
        sys.exit(1)

    if warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  ⚠ {warning}")
        console.print("")

    if not errors and not warnings:
        console.print("[bold green]✓ Configuration is valid![/bold green]")


@cicd.command(name="list")
def list_platforms() -> None:
    """
    List all supported CI/CD platforms.

    \b
    USAGE:
        cpa cicd list

    \b
    Displays:
        - Platform name
        - Configuration file location
        - Supported features
    """
    from rich.table import Table

    table = Table(title="Supported CI/CD Platforms", show_header=True)
    table.add_column("Platform", style="cyan")
    table.add_column("Config File", style="green")
    table.add_column("Features", style="yellow")

    platforms = [
        (
            "GitHub Actions",
            ".github/workflows/*.yml",
            "Caching, Artifacts, Matrix builds, Secrets",
        ),
        (
            "GitLab CI/CD",
            ".gitlab-ci.yml",
            "Docker executors, Caching, Artifacts, Environments",
        ),
        (
            "Jenkins",
            "Jenkinsfile",
            "Pipeline as Code, Stages, Parallel execution, Plugins",
        ),
        (
            "Azure DevOps",
            "azure-pipelines.yml",
            "Multi-stage pipelines, Templates, Environments",
        ),
        (
            "CircleCI",
            ".circleci/config.yml",
            "Docker executors, Workflows, Caching, Orbs",
        ),
    ]

    for name, config, features in platforms:
        table.add_row(name, config, features)

    console.print(table)
    console.print("")
    console.print("[bold cyan]Generate a configuration:[/bold cyan]")
    console.print("  cpa cicd generate --platform <platform>")


# Export the command group
cicd_command = cicd
