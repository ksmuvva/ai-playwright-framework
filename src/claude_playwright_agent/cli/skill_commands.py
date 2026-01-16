"""
CLI commands for skill management.

This module provides commands for:
- Adding custom skills to a project
- Listing available skills
- Enabling/disabling skills
- Validating skill manifests
"""

import json as json_lib
from pathlib import Path
from typing import Any

import click

from claude_playwright_agent.skills import (
    Skill,
    SkillRegistry,
    get_registry,
    list_skills,
    register_skill,
)
from claude_playwright_agent.skills.manifest import (
    ManifestParser,
    ManifestValidationError,
    SkillManifest,
    parse_manifest,
)


# =============================================================================
# Skill Management Commands
# =============================================================================


@click.group(name="skills")
def skills_group() -> None:
    """Manage custom skills for the project."""
    pass


@skills_group.command(name="list")
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Include disabled skills",
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON",
)
def list_skills_command(all: bool, json: bool) -> None:
    """List all available skills."""
    skills = list_skills(include_disabled=all)

    if json:
        output = {
            "skills": [s.to_dict() for s in skills],
            "total": len(skills),
        }
        click.echo(json_lib.dumps(output, indent=2))
    else:
        if not skills:
            click.echo("No skills found.")
            return

        click.echo(f"Found {len(skills)} skill(s):\n")

        for skill in skills:
            status = click.style("enabled", fg="green") if skill.enabled else click.style("disabled", fg="red")
            click.echo(f"  {click.style(skill.name, bold=True)} ({skill.version}) [{status}]")
            if skill.description:
                click.echo(f"    {skill.description}")

            if skill.path:
                click.echo(f"    Path: {skill.path}")


@skills_group.command(name="add")
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--name",
    "-n",
    help="Override skill name (default: from manifest)",
)
@click.option(
    "--enabled/--disabled",
    is_flag=True,
    default=True,
    help="Enable the skill after adding (default: enabled)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing skill with same name",
)
def add_skill_command(source: str, name: str | None, enabled: bool, force: bool) -> None:
    """Add a custom skill from a manifest file or directory.

    SOURCE can be:
    - A skill.yaml manifest file
    - A directory containing a skill.yaml file
    - A zip file containing a skill
    """
    source_path = Path(source)

    # Determine manifest path
    if source_path.is_file():
        if source_path.suffix == ".yaml" or source_path.suffix == ".yml":
            manifest_path = source_path
        else:
            click.echo(f"Error: Source file must be a YAML manifest")
            raise click.Abort()
    elif source_path.is_dir():
        # Look for skill.yaml in directory
        manifest_path = source_path / "skill.yaml"
        if not manifest_path.exists():
            manifest_path = source_path / "skill.yml"
        if not manifest_path.exists():
            click.echo(f"Error: No skill.yaml found in {source_path}")
            raise click.Abort()
    else:
        click.echo(f"Error: Source not found: {source}")
        raise click.Abort()

    # Parse manifest
    try:
        manifest = parse_manifest(manifest_path)
    except ManifestValidationError as e:
        click.echo(f"Error: Invalid manifest: {e}")
        if e.errors:
            click.echo("\nValidation errors:")
            for error in e.errors:
                click.echo(f"  - {error}")
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: Failed to parse manifest: {e}")
        raise click.Abort()

    # Override name if specified
    skill_name = name or manifest.name
    skill_version = manifest.version

    # Check if skill already exists
    registry = get_registry()
    existing = registry.get(skill_name)

    if existing and not force:
        click.echo(f"Error: Skill '{skill_name}' is already registered.")
        click.echo(f"Use --force to overwrite.")
        raise click.Abort()

    # Create skill
    skill = Skill(
        name=skill_name,
        version=skill_version,
        description=manifest.description,
        enabled=enabled,
        path=manifest.path,
    )

    # Register skill
    if existing:
        registry.unregister(skill_name)

    registry.register(skill)

    # Note: Config update skipped for now - skills are managed via registry
    # To persist skills across sessions, we would need to save to a skills.yaml file

    click.echo(f"✓ Added skill: {click.style(skill_name, bold=True)} v{skill_version}")
    click.echo(f"  Description: {manifest.description}")
    if manifest.author:
        click.echo(f"  Author: {manifest.author}")
    click.echo(f"  Status: {click.style('enabled', fg='green') if enabled else click.style('disabled', fg='red')}")


@skills_group.command(name="remove")
@click.argument("name")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Remove without confirmation",
)
def remove_skill_command(name: str, force: bool) -> None:
    """Remove a registered skill."""
    registry = get_registry()
    skill = registry.get(name)

    if not skill:
        click.echo(f"Error: Skill '{name}' is not registered.")
        raise click.Abort()

    if not force:
        click.confirm(f"Remove skill '{name}'?", abort=True)

    registry.unregister(name)

    click.echo(f"✓ Removed skill: {click.style(name, bold=True)}")


@skills_group.command(name="enable")
@click.argument("name")
def enable_skill_command(name: str) -> None:
    """Enable a skill."""
    registry = get_registry()

    if not registry.get(name):
        click.echo(f"Error: Skill '{name}' is not registered.")
        raise click.Abort()

    registry.enable(name)

    click.echo(f"✓ Enabled skill: {click.style(name, bold=True)}")


@skills_group.command(name="disable")
@click.argument("name")
def disable_skill_command(name: str) -> None:
    """Disable a skill."""
    registry = get_registry()

    if not registry.get(name):
        click.echo(f"Error: Skill '{name}' is not registered.")
        raise click.Abort()

    registry.disable(name)

    click.echo(f"✓ Disabled skill: {click.style(name, bold=True)}")


@skills_group.command(name="info")
@click.argument("name")
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON",
)
def skill_info_command(name: str, json: bool) -> None:
    """Show detailed information about a skill."""
    registry = get_registry()
    skill = registry.get(name)

    if not skill:
        click.echo(f"Error: Skill '{name}' is not registered.")
        raise click.Abort()

    if json:
        click.echo(json_lib.dumps(skill.to_dict(), indent=2))
    else:
        click.echo(f"Name: {click.style(skill.name, bold=True)}")
        click.echo(f"Version: {skill.version}")
        click.echo(f"Description: {skill.description}")

        status = click.style("enabled", fg="green") if skill.enabled else click.style("disabled", fg="red")
        click.echo(f"Status: {status}")

        if skill.path:
            click.echo(f"Path: {skill.path}")


@skills_group.command(name="validate")
@click.argument("source", type=click.Path(exists=True))
def validate_skill_command(source: str) -> None:
    """Validate a skill manifest file."""
    source_path = Path(source)

    # Determine manifest path
    if source_path.is_file():
        if source_path.suffix in [".yaml", ".yml"]:
            manifest_path = source_path
        else:
            click.echo(f"Error: Source file must be a YAML manifest")
            raise click.Abort()
    elif source_path.is_dir():
        manifest_path = source_path / "skill.yaml"
        if not manifest_path.exists():
            manifest_path = source_path / "skill.yml"
        if not manifest_path.exists():
            click.echo(f"Error: No skill.yaml found in {source_path}")
            raise click.Abort()
    else:
        click.echo(f"Error: Source not found: {source}")
        raise click.Abort()

    parser = ManifestParser()
    errors = parser.validate(manifest_path)

    if errors:
        click.echo(f"❌ Validation failed for {manifest_path}")
        click.echo("\nErrors:")
        for error in errors:
            click.echo(f"  - {error}")
        raise click.Abort()
    else:
        click.echo(f"✓ Manifest is valid: {manifest_path}")

        # Parse and show summary
        manifest = parse_manifest(manifest_path)
        click.echo(f"\n  Name: {manifest.name}")
        click.echo(f"  Version: {manifest.version}")
        click.echo(f"  Description: {manifest.description}")


# =============================================================================
# Register commands with CLI
# =============================================================================


def register_skill_commands(cli: click.Group) -> None:
    """
    Register skill management commands with the CLI.

    Args:
        cli: The CLI group to add commands to
    """
    cli.add_command(skills_group)
    cli.add_command(list_skills_command, name="list-skills")
    cli.add_command(add_skill_command, name="add-skill")
    cli.add_command(remove_skill_command, name="remove-skill")
    cli.add_command(enable_skill_command, name="enable-skill")
    cli.add_command(disable_skill_command, name="disable-skill")
    cli.add_command(skill_info_command, name="skill-info")
    cli.add_command(validate_skill_command, name="validate-skill")
