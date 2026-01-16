"""
Skills system for Claude Playwright Agent.

This module provides:
- Skill registry for managing available skills
- Core skill loading from built-in locations
- Custom skill loading from project directories
- Skill lifecycle management (enable/disable)
- Skill manifest parsing from YAML
"""

from typing import Any

from claude_playwright_agent.agents.base import BaseAgent

# Import models to avoid circular imports
from .models import (
    Skill,
    SkillRegistry,
    disable_skill,
    enable_skill,
    get_registry,
    get_skill,
    list_skills,
    register_skill,
)

# Import loader functionality
from .loader import (
    CircularDependencyError,
    DependencyError,
    SkillLoader,
    SkillLoadError,
    SkillNotFoundError,
    discover_skills,
    load_skills,
)

# Import manifest functionality
from .manifest import (
    ManifestParser,
    ManifestValidationError,
    SkillManifest,
    parse_manifest,
    parse_manifest_string,
    validate_manifest,
)

# Import versioning functionality (E7.1)
from .versioning import (
    PreReleaseType,
    Version,
    VersionParseError,
    ConstraintOperator,
    VersionConstraint,
    VersionRange,
    VersionConflict,
    VersionResolver,
    MigrationStep,
    MigrationPath,
    MigrationPlanner,
    parse_version,
    parse_constraint,
    compare_versions,
    get_compatible_versions,
)

# Import dependencies functionality (E7.2)
from .dependencies import (
    DependencyType,
    SkillDependency,
    DependencyResolution,
    DependencyHealth,
    DependencyResolver,
    DependencyHealthChecker,
    DependencyGraph,
    GraphNode,
    parse_dependency,
    check_dependency_compatibility,
)

__all__ = [
    # Models
    "Skill",
    "SkillRegistry",
    "get_registry",
    "register_skill",
    "list_skills",
    "get_skill",
    "enable_skill",
    "disable_skill",
    # Manifest
    "SkillManifest",
    "ManifestParser",
    "ManifestValidationError",
    "parse_manifest",
    "parse_manifest_string",
    "validate_manifest",
    # Loader
    "SkillLoader",
    "SkillLoadError",
    "SkillNotFoundError",
    "DependencyError",
    "CircularDependencyError",
    "discover_skills",
    "load_skills",
    # Versioning (E7.1)
    "PreReleaseType",
    "Version",
    "VersionParseError",
    "ConstraintOperator",
    "VersionConstraint",
    "VersionRange",
    "VersionConflict",
    "VersionResolver",
    "MigrationStep",
    "MigrationPath",
    "MigrationPlanner",
    "parse_version",
    "parse_constraint",
    "compare_versions",
    "get_compatible_versions",
    # Dependencies (E7.2)
    "DependencyType",
    "SkillDependency",
    "DependencyResolution",
    "DependencyHealth",
    "DependencyResolver",
    "DependencyHealthChecker",
    "DependencyGraph",
    "GraphNode",
    "parse_dependency",
    "check_dependency_compatibility",
]
