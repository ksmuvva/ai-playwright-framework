"""
Step Definition Generation CLI Command

Generates Python step definitions from Gherkin feature files.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click


@click.command()
@click.argument("feature_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path", default="steps/steps.py")
@click.option("--framework", "-f", default="behave", type=click.Choice(["behave", "pytest-bdd"]), help="BDD framework")
@click.option("--pages-dir", "-p", default="pages", help="Page objects directory")
@click.option("--async", "use_async", is_flag=True, default=True, help="Use async/await")
@click.option("--overwrite", is_flag=True, help="Overwrite existing file")
def generate_steps(feature_file: str, output: str, framework: str, pages_dir: str, use_async: bool, overwrite: bool):
    """
    Generate Python step definitions from a Gherkin feature file.

    Example:
        cpa generate-steps features/login.feature --output steps/login_steps.py
    """
    async def _generate():
        from ...bdd.steps import StepDefinitionGenerator, StepGenConfig
        from ...bdd.gherkin import GherkinParser
        from ...bdd.features import FeatureFileParser

        # Parse feature file
        feature_path = Path(feature_file)
        parser = FeatureFileParser()
        feature = parser.parse(feature_path)

        click.echo(f"Parsed feature: {feature.name}")
        click.echo(f"  Scenarios: {len(feature.scenarios)}")

        # Count steps
        total_steps = sum(len(scenario.steps) for scenario in feature.scenarios)
        click.echo(f"  Total steps: {total_steps}")

        # Configure generator
        config = StepGenConfig(
            framework=framework,
            use_async=use_async,
            include_type_hints=True,
            include_docstrings=True,
            page_object_import=pages_dir,
        )

        generator = StepDefinitionGenerator(config)

        # Generate step definitions for all scenarios
        all_definitions = []
        for scenario in feature.scenarios:
            click.echo(f"\nGenerating steps for scenario: {scenario.name}")

            for step in scenario.steps:
                # Generate function name from step text
                function_name = generator._generate_function_name(step)

                # Generate step code
                step_def = StepDefinition(
                    step_text=step.text,
                    function_name=function_name,
                    code=generator.generate_step_code(step, function_name),
                    parameters=[p["name"] for p in generator.extract_parameters(step.text)],
                )

                all_definitions.append(step_def)
                click.echo(f"  ✓ {step.keyword} {step.text[:50]}...")

        # Generate complete steps file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if output_path.exists() and not overwrite:
            click.echo(f"\n⚠️  Output file already exists: {output_path}")
            click.echo("   Use --overwrite to overwrite it")
            return

        # Write generated steps
        steps_content = generator._generate_steps_file(
            all_definitions,
            feature_name=feature.name,
            pages_dir=pages_dir,
        )

        output_path.write_text(steps_content, encoding="utf-8")

        click.echo(f"\n✅ Generated {len(all_definitions)} step definitions")
        click.echo(f"   Output: {output_path}")

    asyncio.run(_generate())


def _generate_function_name_from_text(step_text: str) -> str:
    """Generate a function name from step text."""
    import re

    # Remove special characters and convert to snake_case
    clean = re.sub(r'[^\w\s]', ' ', step_text.lower())
    words = clean.split()
    return "_".join(words) if words else "step_definition"


# Add the method to StepDefinitionGenerator if it doesn't exist
def monkey_patch_generator():
    """Add helper methods to StepDefinitionGenerator."""
    from ...bdd.steps import StepDefinitionGenerator

    if not hasattr(StepDefinitionGenerator, "_generate_function_name"):
        def _generate_function_name(self, step):
            """Generate function name from step."""
            return _generate_function_name_from_text(step.text)

        StepDefinitionGenerator._generate_function_name = _generate_function_name

    if not hasattr(StepDefinitionGenerator, "_generate_steps_file"):
        def _generate_steps_file(self, definitions, feature_name, pages_dir):
            """Generate complete steps file content."""
            lines = [
                '"""',
                f'Auto-generated step definitions for {feature_name}',
                '"""',
                '',
                'from behave import given, when, then',
                'from playwright.sync_api import Page, expect',
                '',
            ]

            # Import page objects
            pages_imported = set()
            for step_def in definitions:
                # Extract page references from code (naive approach)
                import re
                page_refs = re.findall(r'(\w+Page)', step_def.code)
                pages_imported.update(page_refs)

            if pages_imported:
                lines.append(f'from {pages_dir} import (')
                for page in sorted(pages_imported):
                    lines.append(f'    {page},')
                lines.append(')')
                lines.append('')

            # Add step definitions
            lines.append('')
            lines.append('# Step Definitions')
            lines.append('')

            for step_def in definitions:
                lines.append(step_def.code)
                lines.append('')

            return "\n".join(lines)

        StepDefinitionGenerator._generate_steps_file = _generate_steps_file


# Apply monkey patch
monkey_patch_generator()
