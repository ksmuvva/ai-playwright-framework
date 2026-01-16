"""
Scaffolding data models.

This module defines Pydantic models for scaffolding configuration.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FrameworkType(str, Enum):
    """Supported BDD frameworks."""
    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"


class ProjectTemplate(str, Enum):
    """Project templates."""
    BASIC = "basic"
    ADVANCED = "advanced"
    ECOMMERCE = "ecommerce"
    CUSTOM = "custom"  # User-defined custom template


class BrowserType(str, Enum):
    """Supported browsers."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class TemplateMetadata(BaseModel):
    """Metadata for a project template."""

    name: str = Field(description="Template name")
    description: str = Field(default="", description="Template description")
    extends: str | None = Field(default=None, description="Base template to extend")
    version: str = Field(default="1.0.0", description="Template version")
    author: str = Field(default="", description="Template author")
    custom_dir: Path | None = Field(default=None, description="Custom template directory")

    @classmethod
    def from_file(cls, metadata_file: Path) -> "TemplateMetadata":
        """Load metadata from a template.yaml file."""
        import yaml

        if not metadata_file.exists():
            raise FileNotFoundError(f"Template metadata file not found: {metadata_file}")

        with open(metadata_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_file(self, metadata_file: Path) -> None:
        """Save metadata to a template.yaml file."""
        import yaml

        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


class ScaffoldOptions(BaseModel):
    """Options for project scaffolding."""

    project_name: str = Field(
        description="Project name"
    )
    framework: FrameworkType = Field(
        default=FrameworkType.BEHAVE,
        description="BDD framework to use"
    )
    template: ProjectTemplate = Field(
        default=ProjectTemplate.BASIC,
        description="Project template"
    )
    custom_template_path: str | None = Field(
        default=None,
        description="Path to custom template directory (required for CUSTOM template)"
    )
    browser: BrowserType = Field(
        default=BrowserType.CHROMIUM,
        description="Default browser"
    )
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for testing"
    )
    with_screenshots: bool = Field(
        default=True,
        description="Enable screenshots on failure"
    )
    with_videos: bool = Field(
        default=False,
        description="Enable video recording"
    )
    with_reports: bool = Field(
        default=True,
        description="Enable HTML reports"
    )
    self_healing: bool = Field(
        default=True,
        description="Enable self-healing locators"
    )
    parallel_workers: int = Field(
        default=1,
        description="Number of parallel workers for test execution",
        ge=1,
        le=10,
    )
    retry_failed: bool = Field(
        default=False,
        description="Enable retry logic for failed tests"
    )
    max_retries: int = Field(
        default=2,
        description="Maximum number of retries for failed tests",
        ge=0,
        le=5,
    )

    @field_validator("custom_template_path")
    @classmethod
    def validate_custom_template(cls, v: str | None, info) -> str | None:
        """Validate custom template path when template is CUSTOM."""
        if info.data.get("template") == ProjectTemplate.CUSTOM and not v:
            raise ValueError("custom_template_path is required when using CUSTOM template")
        return v


class ScaffoldContext(BaseModel):
    """
    Context for template rendering.

    Provides all variables available in templates.
    """

    project_name: str
    framework: FrameworkType
    template: ProjectTemplate
    browser: BrowserType
    base_url: str
    with_screenshots: bool
    with_videos: bool
    with_reports: bool
    self_healing: bool
    parallel_workers: int = 1
    retry_failed: bool = False
    max_retries: int = 2
    year: int = 2025

    @classmethod
    def from_options(cls, options: ScaffoldOptions) -> "ScaffoldContext":
        """Create context from scaffold options."""
        return cls(
            project_name=options.project_name,
            framework=options.framework,
            template=options.template,
            browser=options.browser,
            base_url=options.base_url,
            with_screenshots=options.with_screenshots,
            with_videos=options.with_videos,
            with_reports=options.with_reports,
            self_healing=options.self_healing,
            parallel_workers=options.parallel_workers,
            retry_failed=options.retry_failed,
            max_retries=options.max_retries,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "project_name": self.project_name,
            "framework": self.framework.value,
            "template": self.template.value,
            "browser": self.browser.value,
            "base_url": self.base_url,
            "with_screenshots": self.with_screenshots,
            "with_videos": self.with_videos,
            "with_reports": self.with_reports,
            "self_healing": self.self_healing,
            "parallel_workers": self.parallel_workers,
            "retry_failed": self.retry_failed,
            "max_retries": self.max_retries,
            "year": self.year,
            "framework_class": "Behave" if self.framework == FrameworkType.BEHAVE else "PytestBDD",
        }
