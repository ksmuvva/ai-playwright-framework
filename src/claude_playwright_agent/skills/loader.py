"""
Skill Loader - Discover and load skills from various locations.

This module provides:
- Skill discovery from built-in and custom locations
- Dynamic agent class loading
- Dependency resolution
- Skill registration
"""

import importlib.util
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from .manifest import SkillManifest, parse_manifest
from .models import Skill, SkillRegistry, get_registry


# =============================================================================
# Constants
# =============================================================================

# Built-in skills directory (relative to package root)
BUILTIN_SKILLS_DIR = Path(__file__).parent / "builtins"

# Custom skills directories (relative to project root)
CUSTOM_SKILLS_DIRS = [".cpa/skills", "skills"]

# Skill manifest filenames
MANIFEST_NAMES = ["skill.yaml", "skill.yml"]


# =============================================================================
# Exceptions
# =============================================================================


class SkillLoadError(Exception):
    """Base exception for skill loading errors."""

    pass


class SkillNotFoundError(SkillLoadError):
    """Exception raised when a skill is not found."""

    pass


class DependencyError(SkillLoadError):
    """Exception raised when skill dependencies cannot be resolved."""

    pass


class CircularDependencyError(SkillLoadError):
    """Exception raised when circular dependencies are detected."""

    pass


# =============================================================================
# Skill Loader
# =============================================================================


class SkillLoader:
    """
    Discover and load skills from various locations.

    Features:
    - Scan directories for skill manifests
    - Parse skill manifests
    - Dynamically load agent classes
    - Resolve dependencies
    - Register skills in global registry
    """

    def __init__(
        self,
        project_path: Path | None = None,
        include_builtins: bool = True,
    ) -> None:
        """
        Initialize the skill loader.

        Args:
            project_path: Path to project root for custom skills
            include_builtins: Whether to include built-in skills
        """
        self._project_path = project_path or Path.cwd()
        self._include_builtins = include_builtins
        self._registry = get_registry()

        # Track loaded skills to prevent duplicates
        self._loaded_skills: dict[str, Skill] = {}

        # Track manifests for dependency checking
        self._loaded_manifests: dict[str, SkillManifest] = {}

        # Track dependencies for resolution
        self._dependency_graph: dict[str, list[str]] = defaultdict(list)

    def discover_skills(self) -> list[Path]:
        """
        Discover all skill manifests in configured locations.

        Returns:
            List of paths to skill manifest files
        """
        manifests = []

        # Scan built-in skills directory
        if self._include_builtins and BUILTIN_SKILLS_DIR.exists():
            manifests.extend(self._scan_directory(BUILTIN_SKILLS_DIR))

        # Scan custom skills directories
        for skills_dir in CUSTOM_SKILLS_DIRS:
            custom_path = self._project_path / skills_dir
            if custom_path.exists():
                manifests.extend(self._scan_directory(custom_path))

        return manifests

    def _scan_directory(self, directory: Path) -> list[Path]:
        """
        Scan a directory for skill manifests.

        Args:
            directory: Directory to scan

        Returns:
            List of manifest file paths
        """
        manifests = []

        for manifest_name in MANIFEST_NAMES:
            # Check for manifest in directory root
            manifest_path = directory / manifest_name
            if manifest_path.is_file():
                manifests.append(manifest_path)
                continue

            # Scan subdirectories
            for item in directory.iterdir():
                if item.is_dir():
                    skill_manifest = item / manifest_name
                    if skill_manifest.is_file():
                        manifests.append(skill_manifest)

        return manifests

    def load_skill(self, manifest_path: Path) -> Skill:
        """
        Load a skill from a manifest file.

        Args:
            manifest_path: Path to skill manifest file

        Returns:
            Loaded Skill instance

        Raises:
            SkillLoadError: If skill cannot be loaded
        """
        # Parse manifest
        try:
            manifest = parse_manifest(manifest_path)
        except Exception as e:
            raise SkillLoadError(f"Failed to parse manifest: {e}") from e

        # Check if already loaded
        if manifest.name in self._loaded_skills:
            return self._loaded_skills[manifest.name]

        # Load agent class if specified
        agent_class = None
        if manifest.agent_class:
            agent_class = self._load_agent_class(manifest)

        # Create skill
        skill = Skill(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            agent_class=agent_class,
            enabled=manifest.enabled,
            path=str(manifest_path.parent),
        )

        # Track loaded skill and manifest
        self._loaded_skills[manifest.name] = skill
        self._loaded_manifests[manifest.name] = manifest

        # Track dependencies
        if manifest.dependencies:
            self._dependency_graph[manifest.name] = manifest.dependencies

        return skill

    def _load_agent_class(self, manifest: SkillManifest) -> type[Any] | None:
        """
        Dynamically load an agent class from a skill.

        Args:
            manifest: Skill manifest

        Returns:
            Loaded agent class, or None if not found

        Raises:
            SkillLoadError: If agent class cannot be loaded
        """
        if not manifest.agent_class:
            return None

        # Parse module path: "my_module.MyAgent"
        if "." not in manifest.agent_class:
            raise SkillLoadError(
                f"Invalid agent_class format: {manifest.agent_class}. "
                "Expected 'module.ClassName'"
            )

        module_path, class_name = manifest.agent_class.rsplit(".", 1)

        # Determine entry point
        if manifest.entry_point:
            entry_point = manifest.path / manifest.entry_point
        else:
            # Default to main.py or __init__.py
            entry_point = manifest.path / "main.py"
            if not entry_point.exists():
                entry_point = manifest.path / "__init__.py"

        if not entry_point.exists():
            raise SkillLoadError(
                f"Entry point not found for skill '{manifest.name}': {entry_point}"
            )

        # Load module dynamically
        try:
            spec = importlib.util.spec_from_file_location(module_path, entry_point)
            if spec is None or spec.loader is None:
                raise SkillLoadError(f"Cannot load module from {entry_point}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)

            # Get agent class
            agent_class = getattr(module, class_name, None)
            if agent_class is None:
                raise SkillLoadError(
                    f"Agent class '{class_name}' not found in {entry_point}"
                )

            return agent_class

        except Exception as e:
            raise SkillLoadError(
                f"Failed to load agent class for skill '{manifest.name}': {e}"
            ) from e

    def load_all(self) -> list[Skill]:
        """
        Load all discovered skills.

        Returns:
            List of loaded skills

        Raises:
            CircularDependencyError: If circular dependencies are detected
            DependencyError: If dependencies cannot be resolved
        """
        # Discover all skills
        manifest_paths = self.discover_skills()

        # Load all skills (without resolving dependencies yet)
        skills = []
        for manifest_path in manifest_paths:
            try:
                skill = self.load_skill(manifest_path)
                skills.append(skill)
            except SkillLoadError as e:
                # Log but continue loading other skills
                print(f"Warning: Failed to load skill from {manifest_path}: {e}")

        # Resolve load order based on dependencies
        load_order = self._resolve_dependencies()

        # Register skills in dependency order
        registered = []
        for skill_name in load_order:
            if skill_name in self._loaded_skills:
                skill = self._loaded_skills[skill_name]
                if not self._registry.get(skill.name):
                    self._registry.register(skill)
                    registered.append(skill)

        return registered

    def _resolve_dependencies(self) -> list[str]:
        """
        Resolve dependency order using topological sort.

        Returns:
            List of skill names in dependency order

        Raises:
            CircularDependencyError: If circular dependencies are detected
        """
        # Build full dependency graph
        graph = self._dependency_graph.copy()

        # Add all loaded skills (even those without dependencies)
        for skill_name in self._loaded_manifests:
            if skill_name not in graph:
                graph[skill_name] = []

        # Topological sort using Kahn's algorithm
        in_degree: dict[str, int] = {skill: 0 for skill in graph}

        for skill in graph:
            for dep in graph[skill]:
                if dep in in_degree:
                    in_degree[skill] += 1

        # Start with skills that have no dependencies
        queue = [skill for skill, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            skill = queue.pop(0)
            result.append(skill)

            # Reduce in-degree for dependent skills
            for dependent, deps in graph.items():
                if skill in deps:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check for circular dependencies
        if len(result) != len(graph):
            cycle = self._find_cycle(graph)
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        return result

    def _find_cycle(self, graph: dict[str, list[str]]) -> list[str]:
        """
        Find a cycle in the dependency graph.

        Args:
            graph: Dependency graph

        Returns:
            List of skill names forming a cycle
        """
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(skill: str) -> list[str] | None:
            visited.add(skill)
            rec_stack.add(skill)
            path.append(skill)

            for dep in graph.get(skill, []):
                if dep not in visited:
                    result = dfs(dep)
                    if result:
                        return result
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep)
                    return path[cycle_start:] + [dep]

            path.pop()
            rec_stack.remove(skill)
            return None

        for skill in graph:
            if skill not in visited:
                cycle = dfs(skill)
                if cycle:
                    return cycle

        return []

    def check_dependencies(self, skill_name: str) -> bool:
        """
        Check if all dependencies for a skill are available.

        Args:
            skill_name: Name of the skill to check

        Returns:
            True if all dependencies are available
        """
        if skill_name not in self._loaded_manifests:
            return False

        dependencies = self._loaded_manifests[skill_name].dependencies

        for dep in dependencies:
            if dep not in self._loaded_manifests:
                return False

        return True

    def get_missing_dependencies(self, skill_name: str) -> list[str]:
        """
        Get missing dependencies for a skill.

        Args:
            skill_name: Name of the skill to check

        Returns:
            List of missing dependency names
        """
        if skill_name not in self._loaded_manifests:
            return []

        dependencies = self._loaded_manifests[skill_name].dependencies
        return [dep for dep in dependencies if dep not in self._loaded_manifests]


# =============================================================================
# Convenience Functions
# =============================================================================


def load_skills(
    project_path: Path | None = None,
    include_builtins: bool = True,
) -> list[Skill]:
    """
    Load all skills from configured locations.

    Args:
        project_path: Path to project root for custom skills
        include_builtins: Whether to include built-in skills

    Returns:
        List of loaded skills
    """
    loader = SkillLoader(project_path=project_path, include_builtins=include_builtins)
    return loader.load_all()


def discover_skills(
    project_path: Path | None = None,
    include_builtins: bool = True,
) -> list[Path]:
    """
    Discover all skill manifests in configured locations.

    Args:
        project_path: Path to project root for custom skills
        include_builtins: Whether to include built-in skills

    Returns:
        List of paths to skill manifest files
    """
    loader = SkillLoader(project_path=project_path, include_builtins=include_builtins)
    return loader.discover_skills()
