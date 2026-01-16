"""
Test Runner CLI Commands

Commands for discovering and running tests.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click


@click.group()
def test():
    """Test discovery and execution commands."""
    pass


@test.command()
@click.option("--project", "-p", default=".", help="Project root directory")
@click.option("--features", "-f", default="features", help="Features directory")
@click.option("--tests", "-t", default="tests", help="Tests directory")
@click.option("--pages", "-p", default="pages", help="Page objects directory")
def discover(project: str, features: str, tests: str, pages: str):
    """
    Discover all tests in the project.

    Example:
        cpa test discover --project .
    """
    from ...agents.test_discovery import TestDiscovery

    discovery = TestDiscovery(project_path=project)

    click.echo("Discovering tests...")
    results = discovery.discover_all(
        features_dir=features,
        tests_dir=tests,
        pages_dir=pages,
    )

    click.echo(f"\nFound {results['total_tests']} test files")
    click.echo(f"  - {len(results['features'])} feature files")
    click.echo(f"  - {len(results['scenarios'])} scenarios")
    click.echo(f"  - {len(results['step_definitions'])} step definitions")
    click.echo(f"  - {len(results['page_objects'])} page objects")

    # Show detailed report
    click.echo("\n" + discovery.generate_test_report())


@test.command()
@click.argument("feature_files", nargs=-1, type=click.Path(exists=True))
@click.option("--framework", "-f", default="behave", type=click.Choice(["behave", "pytest-bdd"]))
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--parallel/--no-parallel", default=False)
@click.option("--workers", "-w", default=1, help="Number of parallel workers")
@click.option("--retries", "-r", default=0, help="Number of retries for failed tests")
@click.option("--output", "-o", help="Output report file")
def run(
    feature_files: tuple,
    framework: str,
    tags: Optional[str],
    parallel: bool,
    workers: int,
    retries: int,
    output: Optional[str],
):
    """
    Run BDD tests.

    Example:
        cpa test run features/login.feature --tags smoke
        cpa test run features/ --parallel --workers 4
    """
    async def _run():
        from ...agents.execution import TestExecutionEngine, TestFramework, RetryConfig

        engine = TestExecutionEngine()

        # Parse tags
        tag_list = tags.split(",") if tags else None

        # Configure retries
        retry_config = None
        if retries > 0:
            retry_config = RetryConfig(max_retries=retries)

        click.echo(f"Running tests with {framework}...")

        result = await engine.execute_tests(
            framework=TestFramework(framework),
            feature_files=list(feature_files) if feature_files else None,
            tags=tag_list,
            parallel=parallel,
            workers=workers,
            retry_config=retry_config,
        )

        # Display results
        click.echo(f"\nTest Results:")
        click.echo(f"  Total: {result.total_tests}")
        click.echo(f"  Passed: {result.passed}")
        click.echo(f"  Failed: {result.failed}")
        click.echo(f"  Skipped: {result.skipped}")
        click.echo(f"  Duration: {result.duration:.2f}s")

        # Show failures
        if result.failed_tests:
            click.echo(f"\nFailed Tests:")
            for test_result in result.failed_tests:
                click.echo(f"  - {test_result.name}")
                if test_result.error_message:
                    click.echo(f"    Error: {test_result.error_message[:100]}")

        # Save report
        if output:
            from ...agents.execution import ExecutionResult

            report_path = Path(output)
            report_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate JSON report
            import json
            report_data = {
                "summary": {
                    "total": result.total_tests,
                    "passed": result.passed,
                    "failed": result.failed,
                    "skipped": result.skipped,
                    "duration": result.duration,
                },
                "tests": [t.to_dict() for t in result.tests],
            }

            report_path.write_text(json.dumps(report_data, indent=2))
            click.echo(f"\nReport saved to: {report_path}")

    asyncio.run(_run())


@test.command()
@click.argument("pattern")
@click.option("--project", "-p", default=".", help="Project root directory")
def find(pattern: str, project: str):
    """
    Find tests matching a pattern.

    Example:
        cpa test find "login"
        cpa test find "^smoke_"
    """
    from ...agents.test_discovery import TestDiscovery

    discovery = TestDiscovery(project_path=project)
    discovery.discover_all()

    # Filter by pattern
    matches = discovery.filter_by_name(pattern)

    click.echo(f"Found {len(matches)} tests matching '{pattern}':\n")

    for test_file in matches:
        click.echo(f"  - {test_file.path}")
        if test_file.scenarios:
            for scenario in test_file.scenarios:
                click.echo(f"      Scenario: {scenario.name}")
        if test_file.tags:
            click.echo(f"      Tags: {', '.join(test_file.tags)}")


@test.command()
@click.argument("tags")
@click.option("--project", "-p", default=".", help="Project root directory")
def filter_by_tag(tags: str, project: str):
    """
    Find tests with specific tags.

    Example:
        cpa test filter-by-tag smoke,regression
    """
    from ...agents.test_discovery import TestDiscovery

    discovery = TestDiscovery(project_path=project)
    discovery.discover_all()

    # Filter by tags
    tag_list = tags.split(",")
    matches = discovery.filter_by_tags(tag_list)

    click.echo(f"Found {len(matches)} tests with tags {', '.join(tag_list)}:\n")

    for test_file in matches:
        click.echo(f"  - {test_file.path}")
        click.echo(f"    Tags: {', '.join(test_file.tags)}")
        if test_file.scenarios:
            click.echo(f"    Scenarios: {len(test_file.scenarios)}")


@test.command()
@click.option("--framework", "-f", default="behave", type=click.Choice(["behave", "pytest-bdd"]))
def validate(framework: str):
    """
    Validate test configuration and dependencies.

    Example:
        cpa test validate
    """
    from ...agents.test_discovery import TestDiscovery

    click.echo("Validating test configuration...\n")

    project_path = Path(".")
    discovery = TestDiscovery(project_path=".")
    results = discovery.discover_all()

    # Check for required directories
    checks = []

    # Features directory
    features_dir = project_path / "features"
    if features_dir.exists():
        checks.append(("✓", "Features directory exists"))
        feature_count = len([f for f in features_dir.rglob("*.feature")])
        checks.append(("✓", f"  Found {feature_count} feature files"))
    else:
        checks.append(("✗", "Features directory missing"))

    # Steps directory
    steps_dir = features_dir / "steps"
    if steps_dir.exists():
        checks.append(("✓", "Steps directory exists"))
        step_count = len([f for f in steps_dir.rglob("*.py") if not f.name.startswith("_")])
        checks.append(("✓", f"  Found {step_count} step definition files"))
    else:
        checks.append(("✗", "Steps directory missing"))

    # Page objects
    pages_dir = project_path / "pages"
    if pages_dir.exists():
        checks.append(("✓", "Pages directory exists"))
        checks.append(("✓", f"  Found {results['total_page_objects']} page objects"))
    else:
        checks.append(("✗", "Pages directory missing"))

    # Framework installation
    try:
        if framework == "behave":
            import behave
            checks.append(("✓", f"{framework} is installed"))
        else:
            import pytest_bdd
            checks.append(("✓", f"{framework} is installed"))
    except ImportError:
        checks.append(("✗", f"{framework} is NOT installed"))

    # Print results
    for status, message in checks:
        click.echo(f"{status} {message}")

    # Summary
    passed = sum(1 for s, _ in checks if s == "✓")
    total = len(checks)

    click.echo(f"\nValidation: {passed}/{total} checks passed")

    if passed == total:
        click.echo("✓ All checks passed!")
        return 0
    else:
        click.echo("✗ Some checks failed. Please fix the issues above.")
        return 1
