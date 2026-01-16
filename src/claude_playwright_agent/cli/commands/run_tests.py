"""
Test Execution CLI Command

Discovers and executes tests with parallel execution and retry logic.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
from tabulate import tabulate


@click.command()
@click.option("--tags", "-t", help="Tags to filter tests by (comma-separated)")
@click.option("--parallel", "-p", default=3, help="Number of parallel workers")
@click.option("--retries", "-r", default=2, help="Maximum number of retries")
@click.option("--timeout", default=300, help="Test timeout in seconds")
@click.option("--headed", is_flag=True, help="Run tests in headed mode (non-headless)")
@click.option("--video", is_flag=True, help="Enable video recording")
@click.option("--output", "-o", help="Output JSON file for results")
def run_tests(tags: Optional[str], parallel: int, retries: int, timeout: bool, headed: bool, video: bool, output: Optional[str]):
    """
    Discover and run tests with parallel execution.

    Example:
        cpa run-tests --tags @smoke --parallel 5 --retries 3
    """
    async def _run():
        from ...execution import TestDiscovery, TestExecutionEngine, ExecutionConfig

        # Discover tests
        click.echo("🔍 Discovering tests...")
        discovery = TestDiscovery(project_path=".")
        tests = discovery.discover_all()

        click.echo(f"✅ Found {len(tests)} tests")

        # Show statistics
        stats = discovery.get_test_statistics()
        click.echo("\n📊 Test Statistics:")
        click.echo(f"  By Type: {stats['by_type']}")
        click.echo(f"  By Framework: {stats['by_framework']}")
        click.echo(f"  Top Tags: {stats['top_tags'][:5]}")

        # Filter by tags
        if tags:
            tag_list = tags.split(",")
            click.echo(f"\n🏷️  Filtering by tags: {tag_list}")

            filtered_tests = []
            for test in tests:
                if any(tag in test.tags for tag in tag_list):
                    filtered_tests.append(test)

            tests = filtered_tests
            click.echo(f"✅ {len(tests)} tests after filtering")

        if not tests:
            click.echo("\n⚠️  No tests to run!")
            return

        # Configure execution
        config = ExecutionConfig(
            max_parallel=parallel,
            max_retries=retries,
            timeout=timeout,
            enable_video=video,
            headless=not headed,
        )

        # Create execution engine
        click.echo(f"\n🚀 Starting test execution...")
        click.echo(f"   Parallel workers: {parallel}")
        click.echo(f"   Max retries: {retries}")
        click.echo(f"   Timeout: {timeout}s")
        click.echo()

        engine = TestExecutionEngine(project_path=".", config=config)

        # Run tests
        results = await engine.run_tests(tests)

        # Display results
        click.echo("\n" + "="*80)
        click.echo("📋 TEST RESULTS")
        click.echo("="*80 + "\n")

        # Summary table
        summary = engine.get_execution_summary()

        table_data = [
            ["Total Tests", summary["total_tests"]],
            ["✅ Passed", summary["passed"]],
            ["❌ Failed", summary["failed"]],
            ["⚠️  Errors", summary["errors"]],
            ["⏭️  Skipped", summary["skipped"]],
            ["🔄 Retried", summary["retried_tests"]],
            ["📈 Success Rate", f"{summary['success_rate']:.1f}%"],
            ["⏱️  Total Duration", f"{summary['total_duration']:.2f}s"],
            ["⏱️  Avg Duration", f"{summary['average_duration']:.2f}s"],
        ]

        click.echo(tabulate(table_data, tablefmt="plain"))
        click.echo()

        # Failed tests details
        failed = [r for r in results if r.status in ["failed", "error"]]
        if failed:
            click.echo("❌ FAILED TESTS:")
            click.echo()
            for result in failed[:10]:  # Show first 10
                click.echo(f"  {result.test_name}")
                click.echo(f"    Status: {result.status.value}")
                if result.error_message:
                    click.echo(f"    Error: {result.error_message[:100]}...")
                click.echo()

            if len(failed) > 10:
                click.echo(f"  ... and {len(failed) - 10} more failed tests")

        # Save results to file
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            results_data = {
                "summary": summary,
                "results": [r.to_dict() for r in results],
            }

            import json
            output_path.write_text(json.dumps(results_data, indent=2, default=str))
            click.echo(f"💾 Results saved to {output}")

        # Exit with appropriate code
        if summary["failed"] > 0 or summary["errors"] > 0:
            raise click.ClickException(1)

    asyncio.run(_run())
