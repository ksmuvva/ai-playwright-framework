"""
Template Manager for project scaffolding.

This module implements the TemplateManager class which handles:
- Template discovery and loading
- Project structure creation
- Template file rendering
- Configuration file generation
- Custom template support
- Template validation
"""

import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from claude_playwright_agent.scaffold.models import (
    BrowserType,
    FrameworkType,
    ProjectTemplate,
    ScaffoldContext,
    ScaffoldOptions,
    TemplateMetadata,
)

# =============================================================================
# Constants
# =============================================================================

TEMPLATE_DIR = Path(__file__).parent / "templates"
FRAMEWORK_TEMPLATES = {
    FrameworkType.BEHAVE: "behave",
    FrameworkType.PYTEST_BDD: "pytest_bdd",
}
PROJECT_TEMPLATES = {
    ProjectTemplate.BASIC: "basic",
    ProjectTemplate.ADVANCED: "advanced",
    ProjectTemplate.ECOMMERCE: "ecommerce",
}


# =============================================================================
# Template Manager
# =============================================================================


class TemplateManager:
    """
    Manages project scaffolding templates.

    Features:
    - Template discovery and loading
    - Project structure creation
    - Jinja2-based template rendering
    - Framework-specific file generation
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        Initialize the TemplateManager.

        Args:
            template_dir: Custom template directory. Defaults to builtin templates.
        """
        self._template_dir = Path(template_dir) if template_dir else TEMPLATE_DIR
        self._env = Environment(
            loader=FileSystemLoader(self._template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def scaffold_project(
        self,
        project_path: Path,
        options: ScaffoldOptions,
    ) -> list[Path]:
        """
        Scaffold a complete project.

        Args:
            project_path: Path where project will be created
            options: Scaffolding options

        Returns:
            List of created file paths
        """
        context = ScaffoldContext.from_options(options)
        created_files: list[Path] = []

        # Create project structure
        project_path.mkdir(parents=True, exist_ok=True)

        # Create base directories
        directories = self._get_directories(options.framework)
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            created_files.append(dir_path)

        # Create framework-specific files
        framework_files = self._get_framework_files(options.framework, options.template)
        for file_info in framework_files:
            file_path = project_path / file_info["path"]
            content = self._render_template(
                file_info["template"],
                context,
                options.framework,
            )
            file_path.write_text(content, encoding="utf-8")
            created_files.append(file_path)

        # Create README
        readme_content = self._render_template("README.md.j2", context, options.framework)
        (project_path / "README.md").write_text(readme_content, encoding="utf-8")
        created_files.append(project_path / "README.md")

        # Create .gitignore
        gitignore_content = self._render_template(".gitignore.j2", context, options.framework)
        (project_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")
        created_files.append(project_path / ".gitignore")

        # Create requirements.txt
        requirements_content = self._render_template(
            "requirements.txt.j2",
            context,
            options.framework,
        )
        (project_path / "requirements.txt").write_text(requirements_content, encoding="utf-8")
        created_files.append(project_path / "requirements.txt")

        return created_files

    def _get_directories(self, framework: FrameworkType) -> list[str]:
        """Get list of directories to create for a framework."""
        directories = [
            ".cpa",
            ".cpa/logs",
            ".cpa/backups",
            ".cpa/profiles",
            "features",
            "pages",
            "steps",
            "recordings",
            "reports",
        ]

        if framework == FrameworkType.PYTEST_BDD:
            # pytest-bdd uses tests/ directory
            directories = [
                ".cpa",
                ".cpa/logs",
                ".cpa/backups",
                ".cpa/profiles",
                "tests",
                "tests/features",
                "pages",
                "recordings",
                "reports",
            ]

        return directories

    def _get_framework_files(
        self,
        framework: FrameworkType,
        template: ProjectTemplate,
    ) -> list[dict[str, str]]:
        """
        Get framework-specific files to create.

        Returns:
            List of dicts with 'path' and 'template' keys
        """
        files: list[dict[str, str]] = []

        if framework == FrameworkType.BEHAVE:
            files.extend([
                {"path": "features/.gitkeep", "template": "features/gitkeep.j2"},
                {"path": "steps/.gitkeep", "template": "steps/gitkeep.j2"},
                {"path": "pages/.gitkeep", "template": "pages/gitkeep.j2"},
                {"path": ".behaverc", "template": "behave/behave_rc.j2"},
                {"path": "features/environment.py", "template": "behave/environment.j2"},
            ])
        elif framework == FrameworkType.PYTEST_BDD:
            files.extend([
                {"path": "tests/features/.gitkeep", "template": "features/gitkeep.j2"},
                {"path": "tests/conftest.py", "template": "pytest_bdd/conftest.j2"},
                {"path": "pages/.gitkeep", "template": "pages/gitkeep.j2"},
            ])

        # Template-specific files
        if template == ProjectTemplate.ADVANCED or template == ProjectTemplate.ECOMMERCE:
            if framework == FrameworkType.BEHAVE:
                files.append({
                    "path": "steps/common.py",
                    "template": "behave/steps_common.j2",
                })
                files.append({
                    "path": "pages/base.py",
                    "template": "pages/base_page.j2",
                })

        return files

    def _render_template(
        self,
        template_name: str,
        context: ScaffoldContext,
        framework: FrameworkType,
    ) -> str:
        """
        Render a template with context.

        Args:
            template_name: Name of the template file (may include subdirectory)
            context: Rendering context
            framework: Framework type

        Returns:
            Rendered template content
        """
        # For .gitkeep files, return empty content
        if "gitkeep" in template_name:
            return ""

        # The template_name may already include a subdirectory (like "behave/behave_rc.j2")
        # or it might be a simple filename (like "README.md.j2")

        # Try the exact template path first
        try:
            template = self._env.get_template(template_name)
            return template.render(**context.to_dict())
        except Exception:
            pass

        # Try framework-specific directory
        framework_dir = FRAMEWORK_TEMPLATES[framework]
        framework_template = f"{framework_dir}/{template_name}"

        try:
            template = self._env.get_template(framework_template)
            return template.render(**context.to_dict())
        except Exception:
            pass

        # Fall back to common template
        try:
            template = self._env.get_template(f"common/{template_name}")
            return template.render(**context.to_dict())
        except Exception:
            # Last resort - try as-is in common
            try:
                template = self._env.get_template(f"common/{Path(template_name).name}")
                return template.render(**context.to_dict())
            except Exception as e:
                raise FileNotFoundError(
                    f"Template not found: {template_name} (tried: {template_name}, {framework_template}, common/{template_name})"
                ) from e

    def validate_template(self, template_path: Path) -> dict[str, Any]:
        """
        Validate a custom template directory.

        Args:
            template_path: Path to the custom template directory

        Returns:
            Validation result with 'valid', 'errors', and 'warnings' keys
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": None,
        }

        # Check if directory exists
        if not template_path.exists():
            result["valid"] = False
            result["errors"].append(f"Template directory not found: {template_path}")
            return result

        # Check for template.yaml metadata
        metadata_file = template_path / "template.yaml"
        if metadata_file.exists():
            try:
                metadata = TemplateMetadata.from_file(metadata_file)
                result["metadata"] = metadata.model_dump()

                # Validate that extended template exists
                if metadata.extends and metadata.extends not in PROJECT_TEMPLATES:
                    result["warnings"].append(
                        f"Template extends '{metadata.extends}' which is not a built-in template"
                    )
            except Exception as e:
                result["valid"] = False
                result["errors"].append(f"Invalid template.yaml: {e}")
        else:
            result["warnings"].append("No template.yaml found - template will use basic defaults")

        # Check for required files
        required_files = ["README.md.j2", ".gitignore.j2"]
        for required_file in required_files:
            file_path = template_path / required_file
            if not file_path.exists():
                result["warnings"].append(f"Missing recommended file: {required_file}")

        # Check for framework-specific files
        for framework_name in FRAMEWORK_TEMPLATES.values():
            framework_dir = template_path / framework_name
            if framework_dir.exists():
                framework_files = list(framework_dir.glob("*.j2"))
                if not framework_files:
                    result["warnings"].append(f"Framework directory {framework_name} exists but contains no .j2 files")

        # Check for common directory
        common_dir = template_path / "common"
        if common_dir.exists():
            common_files = list(common_dir.glob("*.j2"))
            if not common_files:
                result["warnings"].append("Common directory exists but contains no .j2 files")

        return result

    def list_custom_templates(self, custom_dir: Path) -> list[dict[str, Any]]:
        """
        List all custom templates in a directory.

        Args:
            custom_dir: Directory to search for custom templates

        Returns:
            List of template information dictionaries
        """
        templates = []

        if not custom_dir.exists():
            return templates

        for item in custom_dir.iterdir():
            if item.is_dir():
                # Skip if it's a framework directory (part of builtin structure)
                if item.name in FRAMEWORK_TEMPLATES.values() or item.name == "common":
                    continue

                metadata_file = item / "template.yaml"
                metadata = None

                if metadata_file.exists():
                    try:
                        metadata = TemplateMetadata.from_file(metadata_file)
                        templates.append({
                            "name": metadata.name,
                            "path": str(item),
                            "description": metadata.description,
                            "version": metadata.version,
                            "author": metadata.author,
                            "extends": metadata.extends,
                        })
                    except Exception:
                        # Invalid metadata, skip
                        pass
                else:
                    # No metadata, add as basic template
                    templates.append({
                        "name": item.name,
                        "path": str(item),
                        "description": "No description available",
                        "version": "unknown",
                        "author": "",
                        "extends": None,
                    })

        return templates

    def scaffold_with_custom_template(
        self,
        project_path: Path,
        options: ScaffoldOptions,
        custom_template_path: Path,
    ) -> list[Path]:
        """
        Scaffold a project using a custom template.

        Args:
            project_path: Path where project will be created
            options: Scaffolding options
            custom_template_path: Path to custom template directory

        Returns:
            List of created file paths
        """
        # Validate custom template
        validation = self.validate_template(custom_template_path)
        if not validation["valid"]:
            raise ValueError(f"Invalid custom template: {', '.join(validation['errors'])}")

        # Create a template manager with the custom template directory
        custom_env = Environment(
            loader=FileSystemLoader([custom_template_path, self._template_dir]),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Save original env and use custom env
        original_env = self._env
        self._env = custom_env

        try:
            # Scaffold the project
            return self.scaffold_project(project_path, options)
        finally:
            # Restore original env
            self._env = original_env

    @classmethod
    def get_builtin_template_dir(cls) -> Path:
        """Get the builtin template directory."""
        return TEMPLATE_DIR

    @classmethod
    def list_templates(cls) -> list[str]:
        """List available project templates."""
        return [t.value for t in ProjectTemplate]

    @classmethod
    def list_frameworks(cls) -> list[str]:
        """List available frameworks."""
        return [f.value for f in FrameworkType]


# =============================================================================
# Template Manager Singleton
# =============================================================================

_default_manager: TemplateManager | None = None


def get_template_manager() -> TemplateManager:
    """Get the default template manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = TemplateManager()
    return _default_manager
