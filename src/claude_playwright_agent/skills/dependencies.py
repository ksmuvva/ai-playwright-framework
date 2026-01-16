"""
Advanced Skill Dependencies for Claude Playwright Agent.

This module implements:
- Version-constrained dependency resolution
- Optional dependencies
- Dependency health checking
- Conflict detection and resolution
- Dependency graph visualization
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .versioning import (
    Version,
    VersionConstraint,
    parse_version,
    parse_constraint,
    VersionResolver,
    VersionConflict,
)


# =============================================================================
# Dependency Models
# =============================================================================


class DependencyType(str, Enum):
    """Types of dependencies."""

    REQUIRED = "required"       # Must be present
    OPTIONAL = "optional"       # Nice to have, not required
    DEVELOPMENT = "development" # Only for development
    SUGGESTED = "suggested"     # Suggested but not enforced


@dataclass
class SkillDependency:
    """
    A dependency on another skill with version constraints.

    Attributes:
        name: Name of the dependency skill
        constraint: Version constraint (e.g., "^1.2.3")
        type: Dependency type (required, optional, etc.)
        reason: Human-readable reason for this dependency
        python_packages: Additional Python packages required
    """

    name: str
    constraint: str
    type: DependencyType = DependencyType.REQUIRED
    reason: str = ""
    python_packages: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""
        if self.type == DependencyType.REQUIRED:
            return f"{self.name}{self.constraint}"
        else:
            return f"{self.name}{self.constraint} ({self.type.value})"

    def is_required(self) -> bool:
        """Check if this is a required dependency."""
        return self.type == DependencyType.REQUIRED

    def is_optional(self) -> bool:
        """Check if this is an optional dependency."""
        return self.type == DependencyType.OPTIONAL

    def satisfies(self, version: str) -> bool:
        """
        Check if a version satisfies this dependency's constraint.

        Args:
            version: Version string to check

        Returns:
            True if version satisfies the constraint
        """
        try:
            dep_version = parse_version(version)
            constraint_obj = parse_constraint(self.constraint)
            return constraint_obj.satisfies(dep_version)
        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "constraint": self.constraint,
            "type": self.type.value,
            "reason": self.reason,
            "python_packages": self.python_packages,
        }


@dataclass
class DependencyResolution:
    """
    Result of dependency resolution.

    Attributes:
        skill_name: Name of the skill whose dependencies were resolved
        dependencies: List of resolved dependencies
        missing: List of missing required dependencies
        conflicts: List of version conflicts
        optional_available: List of optional dependencies that are available
        load_order: Suggested load order
    """

    skill_name: str
    dependencies: dict[str, str]  # name -> version
    missing: list[SkillDependency] = field(default_factory=list)
    conflicts: list[VersionConflict] = field(default_factory=list)
    optional_available: list[SkillDependency] = field(default_factory=list)
    load_order: list[str] = field(default_factory=list)

    def is_satisfied(self) -> bool:
        """Check if all required dependencies are satisfied."""
        return not self.missing and not self.conflicts

    def get_missing_required(self) -> list[SkillDependency]:
        """Get missing required dependencies."""
        return [d for d in self.missing if d.is_required()]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "dependencies": self.dependencies,
            "missing": [d.to_dict() for d in self.missing],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "optional_available": [d.to_dict() for d in self.optional_available],
            "load_order": self.load_order,
            "satisfied": self.is_satisfied(),
        }


@dataclass
class DependencyHealth:
    """
    Health status of skill dependencies.

    Attributes:
        skill_name: Name of the skill
        healthy: Whether dependencies are healthy
        total_dependencies: Total number of dependencies
        satisfied: Number of satisfied dependencies
        missing: Number of missing dependencies
        outdated: List of outdated dependencies
        warnings: List of warnings
    """

    skill_name: str
    healthy: bool = True
    total_dependencies: int = 0
    satisfied: int = 0
    missing: int = 0
    outdated: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def satisfaction_rate(self) -> float:
        """Get satisfaction rate as percentage."""
        if self.total_dependencies == 0:
            return 100.0
        return (self.satisfied / self.total_dependencies) * 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "healthy": self.healthy,
            "total_dependencies": self.total_dependencies,
            "satisfied": self.satisfied,
            "missing": self.missing,
            "satisfaction_rate": self.satisfaction_rate(),
            "outdated": self.outdated,
            "warnings": self.warnings,
        }


# =============================================================================
# Dependency Resolver
# =============================================================================


class DependencyResolver:
    """
    Resolve skill dependencies with version constraints.

    Features:
    - Version constraint satisfaction
    - Conflict detection and resolution
    - Optional dependency handling
    - Load order computation
    """

    def __init__(self) -> None:
        """Initialize the dependency resolver."""
        self._resolver = VersionResolver()
        self._available_versions: dict[str, list[Version]] = {}

    def set_available_versions(self, skill_name: str, versions: list[str]) -> None:
        """
        Set available versions for a skill.

        Args:
            skill_name: Name of the skill
            versions: List of available version strings
        """
        self._available_versions[skill_name] = [
            parse_version(v) for v in versions
        ]

    def resolve(
        self,
        skill_name: str,
        dependencies: list[SkillDependency],
        available_skills: dict[str, str],  # name -> version
    ) -> DependencyResolution:
        """
        Resolve dependencies for a skill.

        Args:
            skill_name: Name of the skill
            dependencies: List of dependencies
            available_skills: Map of available skill names to versions

        Returns:
            Dependency resolution result
        """
        resolution = DependencyResolution(
            skill_name=skill_name,
            dependencies={},
        )

        required: list[SkillDependency] = []
        optional: list[SkillDependency] = []

        # Separate required and optional
        for dep in dependencies:
            if dep.is_required():
                required.append(dep)
            else:
                optional.append(dep)

        # Resolve required dependencies
        for dep in required:
            dep_version = available_skills.get(dep.name)

            if dep_version is None:
                resolution.missing.append(dep)
                continue

            # Check if version satisfies constraint
            if dep.satisfies(dep_version):
                resolution.dependencies[dep.name] = dep_version
                resolution.satisfied += 1
            else:
                # Version conflict
                conflict = VersionConflict(
                    skill_name=dep.name,
                    requested_version=dep_version,
                    required_by=skill_name,
                    constraint=dep.constraint,
                    available_versions=self._available_versions.get(dep.name, []),
                )
                resolution.conflicts.append(conflict)

        # Check optional dependencies
        for dep in optional:
            dep_version = available_skills.get(dep.name)

            if dep_version and dep.satisfies(dep_version):
                resolution.optional_available.append(dep)

        # Compute load order
        resolution.load_order = self._compute_load_order(
            skill_name, dependencies
        )

        resolution.total_dependencies = len(dependencies)

        return resolution

    def resolve_all(
        self,
        skills: dict[str, list[SkillDependency]],  # name -> dependencies
        available_skills: dict[str, str],
    ) -> dict[str, DependencyResolution]:
        """
        Resolve dependencies for multiple skills.

        Args:
            skills: Map of skill names to their dependencies
            available_skills: Map of available skill names to versions

        Returns:
            Map of skill names to resolution results
        """
        resolutions: dict[str, DependencyResolution] = {}

        for skill_name, dependencies in skills.items():
            resolutions[skill_name] = self.resolve(
                skill_name, dependencies, available_skills
            )

        return resolutions

    def _compute_load_order(
        self,
        skill_name: str,
        dependencies: list[SkillDependency],
    ) -> list[str]:
        """
        Compute load order for a skill and its dependencies.

        Args:
            skill_name: Name of the skill
            dependencies: List of dependencies

        Returns:
            List of skill names in load order
        """
        order: list[str] = []
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            # Dependencies first, then the skill itself
            for dep in dependencies:
                if dep.name == name:
                    # Recursively visit dependency
                    visit(dep.name)
            if name not in order:
                order.append(name)

        # Visit all dependencies first
        for dep in dependencies:
            visit(dep.name)

        # Then the skill itself
        if skill_name not in order:
            order.append(skill_name)

        return order

    def detect_conflicts(
        self,
        skills: dict[str, list[SkillDependency]],
        available_versions: dict[str, str],
    ) -> list[VersionConflict]:
        """
        Detect version conflicts across skills.

        Args:
            skills: Map of skill names to their dependencies
            available_versions: Map of available skill names to versions

        Returns:
            List of version conflicts
        """
        constraints: dict[str, list[VersionConstraint]] = {}

        # Collect all constraints
        for skill_name, dependencies in skills.items():
            for dep in dependencies:
                if dep.name not in constraints:
                    constraints[dep.name] = []

                try:
                    constraint = parse_constraint(dep.constraint)
                    constraints[dep.name].append(constraint)
                except Exception:
                    pass

        # Check if available versions satisfy constraints
        conflicts: list[VersionConflict] = []

        for dep_name, constraint_list in constraints.items():
            dep_version_str = available_versions.get(dep_name)

            if dep_version_str:
                dep_version = parse_version(dep_version_str)

                for constraint in constraint_list:
                    if not constraint.satisfies(dep_version):
                        # Find which skill requires this
                        for skill_name, dependencies in skills.items():
                            for dep in dependencies:
                                if dep.name == dep_name:
                                    if str(constraint) == dep.constraint:
                                        conflicts.append(VersionConflict(
                                            skill_name=dep_name,
                                            requested_version=dep_version_str,
                                            required_by=skill_name,
                                            constraint=dep.constraint,
                                        ))

        return conflicts


# =============================================================================
# Dependency Health Checker
# =============================================================================


class DependencyHealthChecker:
    """
    Check health of skill dependencies.

    Features:
    - Check if dependencies are satisfied
    - Detect outdated dependencies
    - Generate warnings
    """

    def __init__(self) -> None:
        """Initialize the health checker."""
        pass

    def check_health(
        self,
        skill_name: str,
        dependencies: list[SkillDependency],
        available_skills: dict[str, str],
        latest_versions: dict[str, str] | None = None,
    ) -> DependencyHealth:
        """
        Check health of a skill's dependencies.

        Args:
            skill_name: Name of the skill
            dependencies: List of dependencies
            available_skills: Map of available skill names to versions
            latest_versions: Map of skill names to latest versions

        Returns:
            Dependency health status
        """
        health = DependencyHealth(
            skill_name=skill_name,
            total_dependencies=len(dependencies),
        )

        satisfied = 0
        missing = 0

        for dep in dependencies:
            dep_version = available_skills.get(dep.name)

            if dep_version is None:
                if dep.is_required():
                    missing += 1
                    health.warnings.append(
                        f"Missing required dependency: {dep.name}"
                    )
                continue

            # Check if version satisfies constraint
            if dep.satisfies(dep_version):
                satisfied += 1

                # Check for outdated version
                if latest_versions:
                    latest = latest_versions.get(dep.name)
                    if latest and latest != dep_version:
                        try:
                            if parse_version(latest) > parse_version(dep_version):
                                health.outdated.append({
                                    "name": dep.name,
                                    "current": dep_version,
                                    "latest": latest,
                                })
                        except Exception:
                            pass
            else:
                missing += 1
                health.warnings.append(
                    f"Version conflict for {dep.name}: "
                    f"required {dep.constraint}, have {dep_version}"
                )

        health.satisfied = satisfied
        health.missing = missing
        health.healthy = (missing == 0)

        return health

    def check_all(
        self,
        skills: dict[str, list[SkillDependency]],
        available_skills: dict[str, str],
        latest_versions: dict[str, str] | None = None,
    ) -> dict[str, DependencyHealth]:
        """
        Check health for multiple skills.

        Args:
            skills: Map of skill names to their dependencies
            available_skills: Map of available skill names to versions
            latest_versions: Map of skill names to latest versions

        Returns:
            Map of skill names to health status
        """
        health_map: dict[str, DependencyHealth] = {}

        for skill_name, dependencies in skills.items():
            health_map[skill_name] = self.check_health(
                skill_name, dependencies, available_skills, latest_versions
            )

        return health_map


# =============================================================================
# Dependency Graph
# =============================================================================


@dataclass
class GraphNode:
    """A node in the dependency graph."""

    name: str
    version: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)  # Skills that depend on this


class DependencyGraph:
    """
    Represent and visualize skill dependencies as a graph.

    Features:
    - Build dependency graph
    - Detect circular dependencies
    - Export to various formats (DOT, JSON, etc.)
    """

    def __init__(self) -> None:
        """Initialize the dependency graph."""
        self._nodes: dict[str, GraphNode] = {}

    def add_skill(
        self,
        name: str,
        version: str,
        dependencies: list[str],
    ) -> None:
        """
        Add a skill to the graph.

        Args:
            name: Name of the skill
            version: Version of the skill
            dependencies: List of dependency names
        """
        node = GraphNode(
            name=name,
            version=version,
            dependencies=dependencies.copy(),
        )
        self._nodes[name] = node

        # Update dependents for dependencies
        for dep in dependencies:
            if dep in self._nodes:
                if name not in self._nodes[dep].dependents:
                    self._nodes[dep].dependents.append(name)

    def has_circular_dependency(self) -> bool:
        """Check if the graph has circular dependencies."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in self._nodes.get(node, GraphNode("", "")).dependencies:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node_name in self._nodes:
            if node_name not in visited:
                if dfs(node_name):
                    return True

        return False

    def get_load_order(self) -> list[str]:
        """
        Get topological sort order for loading skills.

        Returns:
            List of skill names in load order
        """
        in_degree: dict[str, int] = {
            name: len(node.dependencies)
            for name, node in self._nodes.items()
        }

        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for dependent in self._nodes.get(node, GraphNode("", "")).dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def to_dot(self) -> str:
        """
        Export graph to DOT format (Graphviz).

        Returns:
            DOT format string
        """
        lines = ["digraph dependencies {"]
        lines.append("  rankdir=LR;")
        lines.append("  node[shape=box];")

        for name, node in self._nodes.items():
            label = f"{name}\\n{node.version}"
            lines.append(f'  "{name}" [label="{label}"];')

            for dep in node.dependencies:
                lines.append(f'  "{name}" -> "{dep}";')

        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": [
                {
                    "name": name,
                    "version": node.version,
                    "dependencies": node.dependencies,
                    "dependents": node.dependents,
                }
                for name, node in self._nodes.items()
            ],
            "load_order": self.get_load_order(),
            "has_circular_dependency": self.has_circular_dependency(),
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def parse_dependency(dep_string: str) -> SkillDependency:
    """
    Parse a dependency string into a SkillDependency object.

    Supports formats:
    - "skill-name" (any version)
    - "skill-name>=1.2.3" (version constraint)
    - "skill-name>=1.2.3;optional" (with type)

    Args:
        dep_string: Dependency string to parse

    Returns:
        Parsed SkillDependency object
    """
    import re

    # Parse: nameconstraint[;type]
    pattern = r"^([^><=~!]+)([^;]+)(?:;(.+))?$"
    match = re.match(pattern, dep_string.strip())

    if not match:
        raise ValueError(f"Invalid dependency string: {dep_string}")

    name = match.group(1).strip()
    constraint = match.group(2).strip() or "*"
    type_str = match.group(3)

    dep_type = DependencyType.REQUIRED
    if type_str:
        try:
            dep_type = DependencyType(type_str.strip().lower())
        except ValueError:
            pass

    return SkillDependency(
        name=name,
        constraint=constraint,
        type=dep_type,
    )


def check_dependency_compatibility(
    required: str,
    available: str,
) -> bool:
    """
    Check if an available version is compatible with a required version.

    Args:
        required: Required version string
        available: Available version string

    Returns:
        True if compatible
    """
    try:
        req_version = parse_version(required)
        avail_version = parse_version(available)
        return avail_version.is_compatible_with(req_version)
    except Exception:
        return False
