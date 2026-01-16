"""
Skills Management CLI Commands for Claude Playwright Agent.

This module provides CLI commands for managing skills:
- List available skills
- Install/uninstall skills
- Enable/disable skills
- View skill information
- Validate skills
"""

import click
from pathlib import Path
from typing import Any

from ...state import StateManager
from ...skills import (
    get_registry,
    list_skills,
    get_skill,
    enable_skill,
    disable_skill,
    Skill,
    discover_skills,
    load_skills,
    SkillLoader,
    parse_manifest,
    SkillManifest,
    validate_manifest,
    SkillLoadError,
    DependencyError,
)


# =============================================================================
# Skills Commands
# =============================================================================


@click.group()
def skills() -> None:
    """Manage skills for the agent framework."""
    pass


@skills.command("list")
@click.option("--include-disabled", is_flag=True, help="Include disabled skills")
@click.option("--format", type=click.Choice(["table", "json", "compact"]), default="table", help="Output format")
@click.option("--project-path", default=".", help="Project directory")
def list_skills_command(include_disabled: bool, format: str, project_path: str) -> None:
    """List all available skills."""
    project_path = Path(project_path)

    # Discover and load skills
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Load skills
    loaded_skills = []
    for manifest_path in discovered:
        try:
            skill = loader.load_skill(manifest_path)
            loaded_skills.append(skill)
        except SkillLoadError as e:
            click.echo(f"Warning: Failed to load skill from {manifest_path}: {e}", err=True)

    # Get skills from registry
    skills = list_skills(include_disabled=include_disabled)

    if format == "json":
        import json
        output = {
            "total": len(skills),
            "enabled": sum(1 for s in skills if s.enabled),
            "skills": [s.to_dict() for s in skills],
        }
        click.echo(json.dumps(output, indent=2))

    elif format == "compact":
        for skill in skills:
            status = "✓" if skill.enabled else "✗"
            click.echo(f"{status} {skill.name} v{skill.version}")

    else:  # table format
        if not skills:
            click.echo("No skills found.")
            return

        click.echo("\nAvailable Skills:\n")
        click.echo("-" * 60)

        for skill in skills:
            status = "enabled" if skill.enabled else "disabled"
            click.echo(f"Name:       {skill.name}")
            click.echo(f"Version:    {skill.version}")
            click.echo(f"Status:     {status}")
            click.echo(f"Description: {skill.description}")
            if skill.path:
                click.echo(f"Path:       {skill.path}")
            click.echo("-" * 60)


@skills.command("info")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
def skill_info(skill_name: str, project_path: str) -> None:
    """Show detailed information about a skill."""
    project_path = Path(project_path)

    # Load skills first
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    loader.load_all()

    # Get skill from registry
    skill = get_skill(skill_name)

    if not skill:
        click.echo(f"Skill '{skill_name}' not found.", err=True)
        return

    # Display skill info
    click.echo(f"\nSkill: {skill.name}")
    click.echo("=" * 50)
    click.echo(f"Version:     {skill.version}")
    click.echo(f"Description: {skill.description}")
    click.echo(f"Enabled:     {'Yes' if skill.enabled else 'No'}")
    click.echo(f"Path:        {skill.path}")

    # Show manifest info if available
    if skill.path:
        manifest_path = Path(skill.path) / "skill.yaml"
        if not manifest_path.exists():
            manifest_path = Path(skill.path) / "skill.yml"

        if manifest_path.exists():
            try:
                manifest = parse_manifest(manifest_path)
                click.echo(f"\nAuthor:      {manifest.author}")
                click.echo(f"License:     {manifest.license}")
                click.echo(f"Homepage:    {manifest.homepage}")
                click.echo(f"Repository:  {manifest.repository}")

                if manifest.dependencies:
                    click.echo(f"\nDependencies:")
                    for dep in manifest.dependencies:
                        click.echo(f"  - {dep}")

                if manifest.python_dependencies:
                    click.echo(f"\nPython Dependencies:")
                    for dep in manifest.python_dependencies:
                        click.echo(f"  - {dep}")

                if manifest.tags:
                    click.echo(f"\nTags: {', '.join(manifest.tags)}")

            except Exception:
                pass

    click.echo()


@skills.command("enable")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
def enable_skill_command(skill_name: str, project_path: str) -> None:
    """Enable a skill."""
    project_path = Path(project_path)

    # Load skills first
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    loader.load_all()

    if enable_skill(skill_name):
        click.echo(f"✓ Skill '{skill_name}' enabled successfully.")
    else:
        click.echo(f"✗ Skill '{skill_name}' not found.", err=True)
        return


@skills.command("disable")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
def disable_skill_command(skill_name: str, project_path: str) -> None:
    """Disable a skill."""
    project_path = Path(project_path)

    # Load skills first
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    loader.load_all()

    if disable_skill(skill_name):
        click.echo(f"✓ Skill '{skill_name}' disabled successfully.")
    else:
        click.echo(f"✗ Skill '{skill_name}' not found.", err=True)
        return


@skills.command("install")
@click.argument("source", type=click.Path(exists=True))
@click.option("--project-path", default=".", help="Project directory")
@click.option("--name", help="Custom name for the skill")
@click.option("--enable", is_flag=True, help="Enable after installation")
def install_skill(source: str, project_path: str, name: str, enable: bool) -> None:
    """Install a skill from a directory or file."""
    import shutil
    import uuid

    project_path = Path(project_path)
    source_path = Path(source)

    # Load state to get skills directory
    state = StateManager(project_path)
    skills_dir = project_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Determine skill name
    if name:
        skill_name = name
    else:
        # Try to get name from manifest
        manifest_path = source_path / "skill.yaml"
        if not manifest_path.exists():
            manifest_path = source_path / "skill.yml"

        if manifest_path.exists():
            try:
                manifest = parse_manifest(manifest_path)
                skill_name = manifest.name
            except Exception:
                skill_name = f"skill_{uuid.uuid4().hex[:8]}"
        else:
            skill_name = source_path.name

    # Destination directory
    dest_dir = skills_dir / skill_name

    if dest_dir.exists():
        click.echo(f"✗ Skill '{skill_name}' already exists.", err=True)
        return

    # Copy skill files
    if source_path.is_file():
        # Source is a file - likely a compressed archive
        click.echo(f"Extracting skill from {source_path}...")
        # For now, just copy the file
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_dir / source_path.name)
    else:
        # Source is a directory
        click.echo(f"Installing skill from {source_path}...")
        shutil.copytree(source_path, dest_dir)

    # Validate the skill
    manifest_path = dest_dir / "skill.yaml"
    if not manifest_path.exists():
        manifest_path = dest_dir / "skill.yml"

    if manifest_path.exists():
        errors = validate_manifest(manifest_path)
        if errors:
            click.echo(f"⚠ Manifest validation warnings:")
            for error in errors:
                click.echo(f"  - {error}")

    # Load the skill
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    try:
        loaded_skill = loader.load_skill(manifest_path)
        click.echo(f"✓ Skill '{loaded_skill.name}' v{loaded_skill.version} installed successfully.")

        if enable:
            enable_skill(loaded_skill.name)
            click.echo(f"✓ Skill '{loaded_skill.name}' enabled.")

    except SkillLoadError as e:
        click.echo(f"✗ Failed to load skill: {e}", err=True)
        # Cleanup on failure
        if dest_dir.exists():
            shutil.rmtree(dest_dir)


@skills.command("uninstall")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
@click.option("--force", is_flag=True, help="Force removal without confirmation")
def uninstall_skill(skill_name: str, project_path: str, force: bool) -> None:
    """Uninstall a skill."""
    import shutil

    project_path = Path(project_path)

    # Load skills first
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    loader.load_all()

    # Check if skill exists
    skill = get_skill(skill_name)

    if not skill or not skill.path:
        click.echo(f"✗ Skill '{skill_name}' not found or is a built-in skill.", err=True)
        return

    # Check if it's a built-in skill
    skill_path = Path(skill.path)
    if not skill_path.is_relative_to(project_path / "skills"):
        click.echo(f"✗ Cannot uninstall built-in skill '{skill_name}'.", err=True)
        return

    # Confirm deletion
    if not force:
        if not click.confirm(f"Are you sure you want to uninstall skill '{skill_name}'?"):
            click.echo("Uninstall cancelled.")
            return

    # Remove skill directory
    try:
        shutil.rmtree(skill_path)
        click.echo(f"✓ Skill '{skill_name}' uninstalled successfully.")

        # Unregister from registry
        registry = get_registry()
        registry.unregister(skill_name)

    except Exception as e:
        click.echo(f"✗ Failed to uninstall skill: {e}", err=True)


@skills.command("validate")
@click.argument("path", type=click.Path(exists=True))
def validate_skill_command(path: str) -> None:
    """Validate a skill manifest."""
    path = Path(path)

    try:
        # Check if it's a manifest file or directory
        if path.is_file():
            manifest_path = path
        else:
            manifest_path = path / "skill.yaml"
            if not manifest_path.exists():
                manifest_path = path / "skill.yml"

        if not manifest_path.exists():
            click.echo(f"✗ No manifest file found in {path}", err=True)
            return

        # Parse and validate manifest
        errors = validate_manifest(manifest_path)

        if not errors:
            click.echo(f"✓ Skill manifest is valid: {manifest_path}")
            return

        # Show validation results
        click.echo(f"\nValidation results for {manifest_path}:")

        if errors:
            click.echo("\nErrors found:")
            for error in errors:
                click.echo(f"  ✗ {error}")
        else:
            click.echo("  ✓ No errors found")

    except Exception as e:
        click.echo(f"✗ Validation failed: {e}", err=True)


@skills.command("check-dependencies")
@click.argument("skill_name", required=False)
@click.option("--project-path", default=".", help="Project directory")
def check_dependencies(skill_name: str | None, project_path: str) -> None:
    """Check skill dependencies."""
    project_path = Path(project_path)

    # Load skills first
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    loader.load_all()

    if skill_name:
        # Check specific skill
        skill = get_skill(skill_name)

        if not skill:
            click.echo(f"✗ Skill '{skill_name}' not found.", err=True)
            return

        # Get manifest to check dependencies
        if skill.path:
            manifest_path = Path(skill.path) / "skill.yaml"
            if not manifest_path.exists():
                manifest_path = Path(skill.path) / "skill.yml"

            if manifest_path.exists():
                try:
                    manifest = parse_manifest(manifest_path)

                    if not manifest.dependencies:
                        click.echo(f"Skill '{skill_name}' has no dependencies.")
                        return

                    click.echo(f"\nDependencies for '{skill_name}':")
                    for dep in manifest.dependencies:
                        dep_skill = get_skill(dep)
                        status = "✓" if dep_skill and dep_skill.enabled else "✗"
                        click.echo(f"  {status} {dep}")

                except Exception as e:
                    click.echo(f"✗ Failed to check dependencies: {e}", err=True)
    else:
        # Check all skills
        skills = list_skills(include_disabled=True)

        for skill in skills:
            if skill.path:
                manifest_path = Path(skill.path) / "skill.yaml"
                if not manifest_path.exists():
                    manifest_path = Path(skill.path) / "skill.yml"

                if manifest_path.exists():
                    try:
                        manifest = parse_manifest(manifest_path)

                        if manifest.dependencies:
                            click.echo(f"\n{skill.name}:")
                            for dep in manifest.dependencies:
                                dep_skill = get_skill(dep)
                                status = "✓" if dep_skill and dep_skill.enabled else "✗"
                                click.echo(f"  {status} {dep}")

                    except Exception:
                        pass


@skills.command("create")
@click.argument("name")
@click.option("--project-path", default=".", help="Project directory")
@click.option("--description", help="Skill description")
@click.option("--author", help="Skill author")
@click.option("--version", default="0.1.0", help="Initial version")
def create_skill(name: str, project_path: str, description: str, author: str, version: str) -> None:
    """Create a new skill scaffold."""
    from datetime import datetime

    project_path = Path(project_path)
    skills_dir = project_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_dir = skills_dir / name
    if skill_dir.exists():
        click.echo(f"✗ Skill '{name}' already exists.", err=True)
        return

    # Create skill directory structure
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create manifest
    manifest_content = f"""name: {name}
version: {version}
description: {description or "A skill for " + name}
author: {author or ""}
license: MIT

# Python dependencies
python_dependencies: []

# Skill dependencies
dependencies: []

# Tags for categorization
tags: []
"""

    (skill_dir / "skill.yaml").write_text(manifest_content)

    # Create main module
    main_content = f'''"""
{name.replace("-", " ").title()} Skill.

This skill provides custom functionality for the agent.
"""

from typing import Any
from claude_playwright_agent.agents.base import BaseAgent


class {name.replace("-", "").replace(" ", "").title()}Agent(BaseAgent):
    """Agent for {name} skill."""

    def __init__(self, **kwargs) -> None:
        \"""Initialize the agent.\""\"
        super().__init__(**kwargs)

    async def run(self, task: str, context: dict[str, Any]) -> str:
        \"""
        Run the agent.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Agent response
        \"\"\"
        return f"{{self.__class__.__name__}} completed task: {{task}}"
'''

    (skill_dir / "main.py").write_text(main_content)

    # Create __init__.py
    init_content = f'''"""
{name} skill.
"""

from .main import {name.replace("-", "").replace(" ", "").title()}Agent

__all__ = ["{name.replace("-", "").replace(" ", "").title()}Agent"]
'''

    (skill_dir / "__init__.py").write_text(init_content)

    click.echo(f"✓ Skill '{name}' created at {skill_dir}")
    click.echo(f"  - Edit {skill_dir / 'skill.yaml'} to configure the skill")
    click.echo(f"  - Implement your agent in {skill_dir / 'main.py'}")
    click.echo(f"  - Run 'cpa skills install {skill_dir}' to install the skill")


# =============================================================================
# Register Commands
# =============================================================================


@skills.command("execute")
@click.argument("skill_name")
@click.argument("task", required=False)
@click.option("--context", help="JSON context for the task")
@click.option("--workflow-id", help="Workflow ID for tracking")
@click.option("--project-path", default=".", help="Project directory")
def execute_skill(skill_name: str, task: str | None, context: str, workflow_id: str, project_path: str) -> None:
    """Execute a skill task."""
    import asyncio
    import json

    project_path = Path(project_path)

    # Load skills
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Find the skill
    skill = None
    for manifest_path in discovered:
        try:
            loaded_skill = loader.load_skill(manifest_path)
            if loaded_skill.name == skill_name:
                skill = loaded_skill
                break
        except SkillLoadError:
            continue

    if not skill or not skill.agent_class:
        click.echo(f"✗ Skill '{skill_name}' not found or has no agent class.", err=True)
        return

    # Default task if not specified
    if not task:
        task = "test"

    # Prepare context
    exec_context = {}
    if context:
        try:
            exec_context = json.loads(context)
        except json.JSONDecodeError:
            click.echo(f"✗ Invalid JSON context: {context}", err=True)
            return

    if workflow_id:
        exec_context["workflow_id"] = workflow_id

    # Execute the skill
    try:
        click.echo(f"Executing skill '{skill_name}' with task '{task}'...")
        agent = skill.agent_class()

        # Run async
        result = asyncio.run(agent.run(task, exec_context))

        click.echo(f"\nResult:\n{result}")

        # Show context history if available
        history = agent.get_context_history()
        if history:
            click.echo(f"\nContext history: {len(history)} operations")

    except Exception as e:
        click.echo(f"✗ Execution failed: {e}", err=True)


@skills.command("describe")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
@click.option("--format", type=click.Choice(["text", "markdown", "json"]), default="text", help="Output format")
def describe_skill(skill_name: str, project_path: str, format: str) -> None:
    """Show detailed description of a skill."""
    import json

    project_path = Path(project_path)

    # Load skills
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Find the skill
    skill = None
    for manifest_path in discovered:
        try:
            loaded_skill = loader.load_skill(manifest_path)
            if loaded_skill.name == skill_name:
                skill = loaded_skill
                break
        except SkillLoadError:
            continue

    if not skill:
        click.echo(f"✗ Skill '{skill_name}' not found.", err=True)
        return

    # Get manifest for additional details
    manifest_details = {}
    manifest_path = None
    if skill.path:
        for ext in ["skill.yaml", "skill.yml"]:
            potential_path = Path(skill.path) / ext
            if potential_path.exists():
                manifest_path = potential_path
                break

    if manifest_path and manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                import yaml
                manifest_data = yaml.safe_load(f)
                manifest_details = manifest_data
        except Exception:
            pass

    # Output based on format
    if format == "json":
        output = {
            "name": skill.name,
            "version": skill.version,
            "description": skill.description,
            "enabled": skill.enabled,
            "path": str(skill.path) if skill.path else None,
            "manifest": manifest_details
        }
        click.echo(json.dumps(output, indent=2))

    elif format == "markdown":
        click.echo(f"# {skill.name}\n")
        click.echo(f"**Version:** {skill.version}")
        click.echo(f"**Description:** {skill.description}")
        click.echo(f"**Status:** {'Enabled' if skill.enabled else 'Disabled'}")
        click.echo(f"**Path:** `{skill.path}`\n")

        if manifest_details:
            if manifest_details.get("author"):
                click.echo(f"**Author:** {manifest_details['author']}")
            if manifest_details.get("dependencies"):
                click.echo(f"\n## Dependencies\n")
                for dep in manifest_details["dependencies"]:
                    click.echo(f"- {dep}")
            if manifest_details.get("tags"):
                tags = ", ".join(manifest_details["tags"])
                click.echo(f"\n**Tags:** {tags}")

        if skill.agent_class:
            click.echo(f"\n## Agent Class\n")
            click.echo(f"`{skill.agent_class.__name__}`")
            click.echo(f"\n**Methods:**")
            for method_name in dir(skill.agent_class):
                if not method_name.startswith("_"):
                    click.echo(f"- `{method_name}()`")

    else:  # text format
        click.echo(f"\nSkill: {skill.name}")
        click.echo("=" * 60)
        click.echo(f"Version:     {skill.version}")
        click.echo(f"Description: {skill.description}")
        click.echo(f"Status:      {'Enabled' if skill.enabled else 'Disabled'}")
        click.echo(f"Path:        {skill.path}")

        if manifest_details:
            if manifest_details.get("author"):
                click.echo(f"Author:      {manifest_details['author']}")
            if manifest_details.get("dependencies"):
                click.echo(f"\nDependencies:")
                for dep in manifest_details["dependencies"]:
                    click.echo(f"  - {dep}")

        if skill.agent_class:
            click.echo(f"\nAgent Class: {skill.agent_class.__name__}")
            click.echo(f"Module:      {skill.agent_class.__module__}")

        click.echo()


@skills.command("tree")
@click.argument("skill_name", required=False)
@click.option("--project-path", default=".", help="Project directory")
@click.option("--format", type=click.Choice(["text", "dot", "json"]), default="text", help="Output format")
@click.option("--include-all", is_flag=True, help="Include all skills in tree")
def show_dependency_tree(skill_name: str | None, project_path: str, format: str, include_all: bool) -> None:
    """Show skill dependency tree."""
    import json

    project_path = Path(project_path)

    # Load skills
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Build dependency graph
    from ...skills.dependencies import DependencyGraph

    graph = DependencyGraph()
    skills_info = {}

    for manifest_path in discovered:
        try:
            import yaml
            with open(manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)

            name = manifest_data.get("name", "")
            version = manifest_data.get("version", "1.0.0")
            deps = manifest_data.get("dependencies", [])

            graph.add_skill(name, version, deps)
            skills_info[name] = {
                "version": version,
                "dependencies": deps,
                "description": manifest_data.get("description", "")
            }
        except Exception:
            continue

    # Output based on format
    if format == "json":
        output = {
            "skills": skills_info,
            "load_order": graph.get_load_order(),
            "has_circular": graph.has_circular_dependency()
        }
        click.echo(json.dumps(output, indent=2))

    elif format == "dot":
        click.echo(graph.to_dot())

    else:  # text format
        if skill_name:
            # Show specific skill dependencies
            if skill_name not in skills_info:
                click.echo(f"✗ Skill '{skill_name}' not found.", err=True)
                return

            click.echo(f"\nDependency tree for '{skill_name}':\n")
            _print_dependency_tree(skill_name, skills_info, level=0)

        elif include_all:
            # Show full dependency tree
            click.echo("\nFull dependency tree:\n")
            load_order = graph.get_load_order()
            for skill in load_order:
                _print_dependency_tree(skill, skills_info, level=0)
                click.echo()

        else:
            # Show summary
            click.echo("\nSkill Dependencies:\n")
            click.echo(f"Total skills: {len(skills_info)}")
            click.echo(f"Load order: {' → '.join(graph.get_load_order()[:5])}")
            if len(graph.get_load_order()) > 5:
                click.echo(f"            → ... → {graph.get_load_order()[-1]}")
            click.echo(f"Circular dependencies: {'Yes' if graph.has_circular_dependency() else 'No'}")


def _print_dependency_tree(skill_name: str, skills_info: dict, level: int = 0) -> None:
    """Helper to print dependency tree."""
    indent = "  " * level
    info = skills_info.get(skill_name, {})
    click.echo(f"{indent}└─ {skill_name} v{info.get('version', '?')}")

    deps = info.get("dependencies", [])
    for dep in deps:
        _print_dependency_tree(dep, skills_info, level + 1)


@skills.command("test")
@click.argument("skill_name")
@click.option("--project-path", default=".", help="Project directory")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--coverage", is_flag=True, help="Run with coverage report")
def test_skill(skill_name: str, project_path: str, verbose: bool, coverage: bool) -> None:
    """Run tests for a skill."""
    import subprocess
    import sys

    project_path = Path(project_path)

    # Find skill tests
    test_patterns = [
        f"tests/skills/builtins/{skill_name}_test.py",
        f"tests/skills/builtins/{skill_name}/test_*.py",
        f"tests/**/test_{skill_name}.py",
    ]

    test_args = [
        sys.executable,
        "-m",
        "pytest",
        "-v" if verbose else "-q",
    ]

    if coverage:
        test_args.extend(["--cov", f"skills/{skill_name}", "--cov-report=term-missing"])

    # Find test files
    test_found = False
    for pattern in test_patterns:
        from glob import glob
        matches = glob(str(project_path / pattern))
        if matches:
            test_args.extend(matches)
            test_found = True
            break

    if not test_found:
        # Try to find by skill name pattern
        from pathlib import Path
        tests_dir = project_path / "tests" / "skills" / "builtins"
        if tests_dir.exists():
            for test_file in tests_dir.glob(f"*{skill_name}*test*.py"):
                test_args.append(str(test_file))
                test_found = True

    if not test_found:
        click.echo(f"⚠ No test files found for skill '{skill_name}'")
        click.echo(f"  Searched patterns: {test_patterns}")
        return

    # Run tests
    click.echo(f"Running tests for skill '{skill_name}'...")
    click.echo(f"Command: {' '.join(test_args)}\n")

    try:
        result = subprocess.run(test_args, cwd=project_path)
        sys.exit(result.returncode)
    except Exception as e:
        click.echo(f"✗ Failed to run tests: {e}", err=True)
        sys.exit(1)


def register_skills_commands(cli_group: click.Group) -> None:
    """Register skills commands with CLI group."""
    cli_group.add_command(skills)
    cli_group.add_command(list_skills_command, name="list-skills")
    cli_group.add_command(enable_skill_command, name="enable-skill")
    cli_group.add_command(disable_skill_command, name="disable-skill")
