"""
Template commands - Manage project templates.

This module provides commands to:
- List available templates (built-in and custom)
- Validate custom templates
- Create new custom templates
- Export templates for sharing
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from claude_playwright_agent.scaffold import TemplateManager, TemplateMetadata, ScaffoldOptions, ProjectTemplate, FrameworkType

console = Console()


@click.group()
def template() -> None:
    """Project template management commands."""
    pass


@template.command(name="list")
@click.option(
    "--custom-dir", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom templates directory",
)
def template_list(custom_dir: Path | None) -> None:
    """
    List available project templates.

    Shows both built-in templates and any custom templates found
    in the specified directory.

    Examples:
        cpa template list                          # List built-in templates
        cpa template list --custom-dir ./templates  # Include custom templates
    """
    manager = TemplateManager()

    # Built-in templates
    console.print("\n[bold cyan]Built-in Templates:[/bold cyan]")
    builtin_table = Table(show_header=True)
    builtin_table.add_column("Template", style="cyan")
    builtin_table.add_column("Description", style="dim")

    builtin_templates = {
        "basic": "Simple project structure with minimal setup",
        "advanced": "Full-featured project with parallel execution and reporting",
        "ecommerce": "Pre-configured for e-commerce testing scenarios",
    }

    for template_name, description in builtin_templates.items():
        builtin_table.add_row(template_name, description)

    console.print(builtin_table)

    # Custom templates
    if custom_dir and custom_dir.exists():
        custom_templates = manager.list_custom_templates(custom_dir)

        if custom_templates:
            console.print("\n[bold cyan]Custom Templates:[/bold cyan]")
            custom_table = Table(show_header=True)
            custom_table.add_column("Template", style="green")
            custom_table.add_column("Version", style="dim")
            custom_table.add_column("Author", style="dim")
            custom_table.add_column("Description", style="dim")
            custom_table.add_column("Extends", style="yellow")

            for tmpl in custom_templates:
                custom_table.add_row(
                    tmpl["name"],
                    tmpl["version"],
                    tmpl["author"] or "-",
                    tmpl["description"],
                    tmpl["extends"] or "-",
                )

            console.print(custom_table)
        else:
            console.print("\n[yellow]No custom templates found in the specified directory.[/yellow]")
    elif custom_dir:
        console.print(f"\n[yellow]Custom directory not found: {custom_dir}[/yellow]")


@template.command(name="validate")
@click.argument(
    "template_path",
    type=click.Path(exists=True, path_type=Path),
)
def template_validate(template_path: Path) -> None:
    """
    Validate a custom template directory.

    Checks that the template directory has all required files
    and valid configuration.

    Examples:
        cpa template validate ./my-template
        cpa template validate ~/templates/custom
    """
    manager = TemplateManager()
    result = manager.validate_template(template_path)

    console.print("")

    if result["valid"]:
        console.print(f"[OK] Template is valid: {template_path.name}", style="bold green")

        if result["metadata"]:
            console.print("\n[bold]Template Metadata:[/bold]")
            for key, value in result["metadata"].items():
                if key != "custom_dir":
                    console.print(f"  {key}: {value}")
    else:
        console.print(f"[ERROR] Template validation failed: {template_path.name}", style="bold red")
        console.print("\n[bold]Errors:[/bold]")
        for error in result["errors"]:
            console.print(f"  [red]✗[/red] {error}")

    if result["warnings"]:
        console.print("\n[bold]Warnings:[/bold]")
        for warning in result["warnings"]:
            console.print(f"  [yellow]⚠[/yellow] {warning}")


@template.command(name="create")
@click.argument("name")
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=Path.cwd() / "templates",
    help="Directory where template will be created",
)
@click.option(
    "--extends", "-e",
    type=click.Choice(["basic", "advanced", "ecommerce"]),
    help="Base template to extend",
)
@click.option(
    "--description", "-d",
    default="",
    help="Template description",
)
@click.option(
    "--author", "-a",
    default="",
    help="Template author",
)
def template_create(
    name: str,
    output_dir: Path,
    extends: str | None,
    description: str,
    author: str,
) -> None:
    """
    Create a new custom project template.

    Creates a template directory with the necessary structure
    and a template.yaml metadata file.

    Examples:
        cpa template create my-custom-template
        cpa template create my-template --extends advanced --description "My custom template"
        cpa template create company-template -o ~/templates -a "John Doe"
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    template_path = output_dir / name

    if template_path.exists():
        console.print(f"[ERROR] Template directory already exists: {template_path}", style="bold red")
        sys.exit(1)

    # Create template structure
    template_path.mkdir()
    (template_path / "common").mkdir()
    (template_path / "behave").mkdir()
    (template_path / "pytest_bdd").mkdir()

    # Create template metadata
    metadata = TemplateMetadata(
        name=name,
        description=description or f"Custom template: {name}",
        extends=extends,
        version="1.0.0",
        author=author,
        custom_dir=template_path,
    )

    metadata_file = template_path / "template.yaml"
    metadata.to_file(metadata_file)

    # Create placeholder README
    readme_content = f"""# {name}

Custom template for Claude Playwright Agent.

## Description
{description or "No description provided."}

## Author
{author or "Unknown"}

## Version
1.0.0

## Extends
{extends or "None (base template)"}

## Files
- `common/` - Common template files for all frameworks
- `behave/` - Behave-specific template files
- `pytest_bdd/` - pytest-bdd-specific template files
- `template.yaml` - Template metadata

## Usage
```bash
cpa init --template custom --custom-template-path {template_path}
```
"""
    (template_path / "README.md").write_text(readme_content)

    # Create .gitkeep files
    (template_path / "common" / ".gitkeep").write_text("")
    (template_path / "behave" / ".gitkeep").write_text("")
    (template_path / "pytest_bdd" / ".gitkeep").write_text("")

    console.print(f"[OK] Created custom template: {name}", style="bold green")
    console.print(f"\nLocation: {template_path}")
    console.print("\nNext steps:")
    console.print("  1. Add template files to the framework directories")
    console.print("  2. Validate with: cpa template validate " + str(template_path))
    console.print(f"  3. Use with: cpa init --template custom --custom-template-path {template_path}")


@template.command(name="export")
@click.argument("template_name")
@click.argument("output_file")
@click.option(
    "--custom-dir", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom templates directory",
)
def template_export(template_name: str, output_file: str, custom_dir: Path | None) -> None:
    """
    Export a built-in template for customization.

    Copies a built-in template to a new directory that you can
    modify and use as a custom template.

    Examples:
        cpa template export advanced my-advanced-template
        cpa template export basic ./templates/my-basic
    """
    import shutil

    manager = TemplateManager()
    builtin_dir = manager.get_builtin_template_dir()

    # Find the template directory
    template_source = None
    if template_name in ["basic", "advanced", "ecommerce"]:
        # Built-in templates are in the templates directory
        template_source = builtin_dir
    else:
        console.print(f"[ERROR] Unknown template: {template_name}", style="bold red")
        console.print("Available templates: basic, advanced, ecommerce")
        sys.exit(1)

    output_path = Path(output_file)

    if output_path.exists():
        console.print(f"[ERROR] Output path already exists: {output_path}", style="bold red")
        sys.exit(1)

    # Copy the template
    shutil.copytree(template_source, output_path)

    # Create/update template metadata
    metadata_file = output_path / "template.yaml"
    metadata = TemplateMetadata(
        name=output_path.name,
        description=f"Customized template based on {template_name}",
        extends=template_name,
        version="1.0.0",
        author="",
        custom_dir=output_path,
    )
    metadata.to_file(metadata_file)

    console.print(f"[OK] Exported template to: {output_path}", style="bold green")
    console.print("\nNext steps:")
    console.print("  1. Modify the template files as needed")
    console.print("  2. Validate with: cpa template validate " + str(output_path))
    console.print(f"  3. Use with: cpa init --template custom --custom-template-path {output_path}")


@template.command(name="info")
@click.argument("template_name")
@click.option(
    "--custom-dir", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom templates directory",
)
def template_info(template_name: str, custom_dir: Path | None) -> None:
    """
    Show detailed information about a template.

    Displays metadata, file structure, and other details
    about the specified template.

    Examples:
        cpa template info advanced
        cpa template info my-custom --custom-dir ./templates
    """
    manager = TemplateManager()

    # Built-in templates
    builtin_info = {
        "basic": {
            "description": "Simple project structure with minimal setup",
            "features": ["Basic directory structure", "Behave or pytest-bdd support", "Simple configuration"],
            "suitable_for": ["Small projects", "Learning the framework", "Quick prototypes"],
        },
        "advanced": {
            "description": "Full-featured project with parallel execution and reporting",
            "features": ["Parallel test execution", "HTML reports", "Screenshot capture", "Self-healing selectors", "CI/CD integration"],
            "suitable_for": ["Production projects", "Large test suites", "Teams requiring detailed reporting"],
        },
        "ecommerce": {
            "description": "Pre-configured for e-commerce testing scenarios",
            "features": ["E-commerce page objects", "Checkout flow templates", "Payment testing support", "Inventory management tests"],
            "suitable_for": ["E-commerce websites", "Online stores", "Marketplace applications"],
        },
    }

    if template_name in builtin_info:
        info = builtin_info[template_name]

        console.print(Panel(
            f"[bold cyan]Template: {template_name}[/bold cyan]\n\n"
            f"[bold]Description:[/bold] {info['description']}\n\n"
            f"[bold]Features:[/bold]\n" +
            "\n".join(f"  • {f}" for f in info['features']) +
            "\n\n[bold]Suitable For:[/bold]\n" +
            "\n".join(f"  • {s}" for s in info['suitable_for']),
            title="Built-in Template Info",
            border_style="cyan",
        ))

        # Show template files
        builtin_dir = manager.get_builtin_template_dir()
        console.print("\n[bold]Template Files:[/bold]")
        for item in sorted(builtin_dir.rglob("*")):
            if item.is_file() and not item.name.startswith("."):
                rel_path = item.relative_to(builtin_dir)
                console.print(f"  {rel_path}")

    elif custom_dir:
        # Check for custom template
        template_path = None
        for item in custom_dir.iterdir():
            if item.is_dir() and item.name == template_name:
                template_path = item
                break

        if template_path:
            validation = manager.validate_template(template_path)
            metadata = validation.get("metadata")

            if metadata:
                console.print(Panel(
                    f"[bold cyan]Template: {metadata['name']}[/bold cyan]\n\n"
                    f"[bold]Description:[/bold] {metadata['description']}\n\n"
                    f"[bold]Version:[/bold] {metadata['version']}\n"
                    f"[bold]Author:[/bold] {metadata['author']}\n"
                    f"[bold]Extends:[/bold] {metadata['extends'] or 'None'}\n\n"
                    f"[bold]Location:[/bold] {template_path}",
                    title="Custom Template Info",
                    border_style="green",
                ))

                # Show template files
                console.print("\n[bold]Template Files:[/bold]")
                for item in sorted(template_path.rglob("*")):
                    if item.is_file() and not item.name.startswith("."):
                        rel_path = item.relative_to(template_path)
                        console.print(f"  {rel_path}")
            else:
                console.print(f"[INFO] Template '{template_name}' found but has no metadata file", style="yellow")
        else:
            console.print(f"[ERROR] Template not found: {template_name}", style="bold red")
            console.print("Use 'cpa template list' to see available templates")
    else:
        console.print(f"[ERROR] Template not found: {template_name}", style="bold red")
        console.print("Use 'cpa template list' to see available templates")
