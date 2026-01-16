"""
Skill Versioning for Claude Playwright Agent.

This module implements:
- Semantic Versioning (semver) support
- Version comparison and compatibility
- Version constraint resolution
- Version conflict detection
- Migration path support
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import re


# =============================================================================
# Version Models
# =============================================================================


class PreReleaseType(str, Enum):
    """Pre-release types."""
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    NONE = ""


@dataclass
class Version:
    """
    Semantic version following semver.org specification.

    Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

    Attributes:
        major: Major version (incompatible API changes)
        minor: Minor version (backward-compatible functionality)
        patch: Patch version (backward-compatible bug fixes)
        prerelease: Pre-release identifier (alpha, beta, rc)
        prerelease_number: Pre-release version number
        build_metadata: Build metadata
    """

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: PreReleaseType = PreReleaseType.NONE
    prerelease_number: int = 0
    build_metadata: str = ""

    def __str__(self) -> str:
        """String representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"

        if self.prerelease != PreReleaseType.NONE:
            version += f"-{self.prerelease.value}.{self.prerelease_number}"

        if self.build_metadata:
            version += f"+{self.build_metadata}"

        return version

    def __repr__(self) -> str:
        """Representation."""
        return f"Version('{self}')"

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease and
            self.prerelease_number == other.prerelease_number
        )

    def __lt__(self, other: object) -> bool:
        """Check less than."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major, minor, patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Compare prerelease
        # Pre-release versions have lower precedence than normal versions
        if self.prerelease == PreReleaseType.NONE and other.prerelease != PreReleaseType.NONE:
            return False
        if self.prerelease != PreReleaseType.NONE and other.prerelease == PreReleaseType.NONE:
            return True

        if self.prerelease != other.prerelease:
            # alpha < beta < rc
            order = [PreReleaseType.ALPHA, PreReleaseType.BETA, PreReleaseType.RC]
            return order.index(self.prerelease) < order.index(other.prerelease)

        # Compare prerelease number
        return self.prerelease_number < other.prerelease_number

    def __le__(self, other: object) -> bool:
        """Check less than or equal."""
        if not isinstance(other, Version):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        """Check greater than."""
        if not isinstance(other, Version):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        """Check greater than or equal."""
        if not isinstance(other, Version):
            return NotImplemented
        return not self < other

    def __hash__(self) -> int:
        """Hash for dict/set usage."""
        return hash((self.major, self.minor, self.patch, self.prerelease, self.prerelease_number))

    def is_stable(self) -> bool:
        """Check if version is stable (no prerelease)."""
        return self.prerelease == PreReleaseType.NONE

    def is_compatible_with(self, other: "Version") -> bool:
        """
        Check if this version is compatible with another.

        Uses semantic versioning compatibility rules:
        - MAJOR version must match exactly
        - MINOR and PATCH can be greater or equal

        Args:
            other: Version to check compatibility with

        Returns:
            True if versions are compatible
        """
        return self.major == other.major and (
            self.minor > other.minor or
            (self.minor == other.minor and self.patch >= other.patch)
        )

    def bump_major(self) -> "Version":
        """Return a new version with bumped major."""
        return Version(
            major=self.major + 1,
            minor=0,
            patch=0,
        )

    def bump_minor(self) -> "Version":
        """Return a new version with bumped minor."""
        return Version(
            major=self.major,
            minor=self.minor + 1,
            patch=0,
        )

    def bump_patch(self) -> "Version":
        """Return a new version with bumped patch."""
        return Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease.value,
            "prerelease_number": self.prerelease_number,
            "build_metadata": self.build_metadata,
        }


# =============================================================================
# Version Constraints
# =============================================================================


class ConstraintOperator(str, Enum):
    """Version constraint operators."""

    EQ = "=="      # Exactly equal
    NE = "!="      # Not equal
    GT = ">"       # Greater than
    GE = ">="      # Greater than or equal
    LT = "<"       # Less than
    LE = "<="      # Less than or equal
    CARET = "^"    # Caret constraint (compatible)
    TILDE = "~"    # Tilde constraint (patch-level)
    WILDCARD = "*" # Wildcard (any)


@dataclass
class VersionConstraint:
    """
    Version constraint for skill dependencies.

    Supports semantic versioning constraints like:
    - "^1.2.3" - Compatible with 1.2.3 <= version < 2.0.0
    - "~1.2.3" - Compatible with 1.2.3 <= version < 1.3.0
    - ">=1.2.3" - Greater than or equal to 1.2.3
    - "1.2.*" - Any patch version for 1.2

    Attributes:
        operator: Constraint operator
        version: Version to compare against
    """

    operator: ConstraintOperator
    version: Version

    def __str__(self) -> str:
        """String representation."""
        if self.operator in (ConstraintOperator.CARET, ConstraintOperator.TILDE):
            return f"{self.operator.value}{self.version}"
        elif self.operator == ConstraintOperator.WILDCARD:
            return f"{self.version.major}.{self.version.minor}.*"
        else:
            return f"{self.operator.value}{self.version}"

    def satisfies(self, version: Version) -> bool:
        """
        Check if a version satisfies this constraint.

        Args:
            version: Version to check

        Returns:
            True if version satisfies the constraint
        """
        match self.operator:
            case ConstraintOperator.EQ:
                return version == self.version
            case ConstraintOperator.NE:
                return version != self.version
            case ConstraintOperator.GT:
                return version > self.version
            case ConstraintOperator.GE:
                return version >= self.version
            case ConstraintOperator.LT:
                return version < self.version
            case ConstraintOperator.LE:
                return version <= self.version
            case ConstraintOperator.CARET:
                # ^1.2.3 means >=1.2.3 and <2.0.0
                return (
                    version >= self.version and
                    version.major == self.version.major
                )
            case ConstraintOperator.TILDE:
                # ~1.2.3 means >=1.2.3 and <1.3.0
                return (
                    version >= self.version and
                    version.major == self.version.major and
                    version.minor == self.version.minor
                )
            case ConstraintOperator.WILDCARD:
                # 1.2.* means any version with major=1, minor=2
                return (
                    version.major == self.version.major and
                    version.minor == self.version.minor
                )

    def get_min_version(self) -> Version:
        """Get the minimum version that satisfies this constraint."""
        match self.operator:
            case ConstraintOperator.GT:
                return self.version.bump_patch()
            case ConstraintOperator.GE | ConstraintOperator.EQ | ConstraintOperator.CARET | ConstraintOperator.TILDE:
                return self.version
            case ConstraintOperator.LT | ConstraintOperator.LE:
                # No minimum (or 0.0.0)
                return Version()
            case ConstraintOperator.NE | ConstraintOperator.WILDCARD:
                return Version()
            case _:
                return Version()

    def get_max_version(self) -> Version | None:
        """Get the maximum version that satisfies this constraint."""
        match self.operator:
            case ConstraintOperator.LT:
                return self.version
            case ConstraintOperator.LE:
                return self.version
            case ConstraintOperator.EQ:
                return self.version
            case ConstraintOperator.CARET:
                # ^1.2.3 means <2.0.0
                return Version(major=self.version.major + 1)
            case ConstraintOperator.TILDE:
                # ~1.2.3 means <1.3.0
                return Version(major=self.version.major, minor=self.version.minor + 1)
            case _:
                return None


@dataclass
class VersionRange:
    """
    A range of versions defined by min and max constraints.

    Attributes:
        min_version: Minimum version (inclusive)
        max_version: Maximum version (exclusive, None for no limit)
        include_min: Whether min_version is inclusive
        include_max: Whether max_version is inclusive
    """

    min_version: Version | None = None
    max_version: Version | None = None
    include_min: bool = True
    include_max: bool = False

    def satisfies(self, version: Version) -> bool:
        """Check if a version is within this range."""
        if self.min_version:
            if self.include_min:
                if version < self.min_version:
                    return False
            else:
                if version <= self.min_version:
                    return False

        if self.max_version:
            if self.include_max:
                if version > self.max_version:
                    return False
            else:
                if version >= self.max_version:
                    return False

        return True


# =============================================================================
# Version Parsing
# =============================================================================


class VersionParseError(Exception):
    """Raised when version string cannot be parsed."""
    pass


def parse_version(version_string: str) -> Version:
    """
    Parse a version string into a Version object.

    Supports:
    - "1.2.3"
    - "1.2.3-alpha.1"
    - "1.2.3-beta.2"
    - "1.2.3-rc.3"
    - "1.2.3+build.1"

    Args:
        version_string: Version string to parse

    Returns:
        Parsed Version object

    Raises:
        VersionParseError: If version string is invalid
    """
    version_string = version_string.strip()

    # Pattern for semantic versioning
    # 1.2.3[-prerelease.number][+build.metadata]
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.(\d+))?(?:\+(.+))?$"
    match = re.match(pattern, version_string)

    if not match:
        raise VersionParseError(f"Invalid version string: {version_string}")

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    prerelease_str = match.group(4)
    prerelease_number = int(match.group(5)) if match.group(5) else 0
    build_metadata = match.group(6) or ""

    # Parse prerelease type
    prerelease = PreReleaseType.NONE
    if prerelease_str:
        try:
            prerelease = PreReleaseType(prerelease_str)
        except ValueError:
            raise VersionParseError(f"Invalid prerelease type: {prerelease_str}")

    return Version(
        major=major,
        minor=minor,
        patch=patch,
        prerelease=prerelease,
        prerelease_number=prerelease_number,
        build_metadata=build_metadata,
    )


def parse_constraint(constraint_string: str) -> VersionConstraint:
    """
    Parse a constraint string into a VersionConstraint object.

    Supports:
    - "==1.2.3"
    - "!=1.2.3"
    - ">1.2.3"
    - ">=1.2.3"
    - "<1.2.3"
    - "<=1.2.3"
    - "^1.2.3"
    - "~1.2.3"
    - "1.2.*"

    Args:
        constraint_string: Constraint string to parse

    Returns:
        Parsed VersionConstraint object

    Raises:
        VersionParseError: If constraint string is invalid
    """
    constraint_string = constraint_string.strip()

    # Try each operator pattern
    patterns = [
        (r"^>=(.+)", ConstraintOperator.GE),
        (r"^<=(.+)", ConstraintOperator.LE),
        (r"^!=(.+)", ConstraintOperator.NE),
        (r"^==(.+)", ConstraintOperator.EQ),
        (r"^>(.+)", ConstraintOperator.GT),
        (r"^<(.+)", ConstraintOperator.LT),
        (r"^\^(.+)", ConstraintOperator.CARET),
        (r"^~(.+)", ConstraintOperator.TILDE),
        (r"^(\d+)\.(\d+)\.\*", ConstraintOperator.WILDCARD),
    ]

    for pattern, operator in patterns:
        match = re.match(pattern, constraint_string)
        if match:
            if operator == ConstraintOperator.WILDCARD:
                # Parse wildcard constraint
                major = int(match.group(1))
                minor = int(match.group(2))
                version = Version(major=major, minor=minor, patch=0)
            else:
                version = parse_version(match.group(1))

            return VersionConstraint(operator=operator, version=version)

    # Try plain version (defaults to ==)
    try:
        version = parse_version(constraint_string)
        return VersionConstraint(operator=ConstraintOperator.EQ, version=version)
    except VersionParseError:
        raise VersionParseError(f"Invalid constraint string: {constraint_string}")


# =============================================================================
# Version Resolution
# =============================================================================


@dataclass
class VersionConflict:
    """
    Represents a version conflict between skills.

    Attributes:
        skill_name: Name of the skill with conflict
        requested_version: Requested version
        required_by: Skill that requires this version
        constraint: Version constraint that caused the conflict
        available_versions: List of available versions
    """

    skill_name: str
    requested_version: str
    required_by: str
    constraint: str
    available_versions: list[Version] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "requested_version": self.requested_version,
            "required_by": self.required_by,
            "constraint": self.constraint,
            "available_versions": [str(v) for v in self.available_versions],
        }


class VersionResolver:
    """
    Resolve version constraints for skill dependencies.

    Features:
    - Find compatible versions
    - Detect conflicts
    - Suggest resolution
    """

    def __init__(self) -> None:
        """Initialize the version resolver."""
        pass

    def find_compatible_version(
        self,
        constraint: VersionConstraint,
        available_versions: list[Version],
    ) -> Version | None:
        """
        Find a compatible version from available versions.

        Args:
            constraint: Version constraint to satisfy
            available_versions: List of available versions

        Returns:
            Compatible version or None if not found
        """
        # Sort versions (newest first)
        sorted_versions = sorted(available_versions, reverse=True)

        for version in sorted_versions:
            if constraint.satisfies(version):
                return version

        return None

    def resolve_constraints(
        self,
        constraints: dict[str, list[VersionConstraint]],
    ) -> dict[str, Version] | list[VersionConflict]:
        """
        Resolve multiple version constraints.

        Args:
            constraints: Map of skill name to list of constraints

        Returns:
            Dictionary of resolved versions, or list of conflicts
        """
        # For each skill, find a version that satisfies all constraints
        resolved: dict[str, Version] = {}
        conflicts: list[VersionConflict] = []

        for skill_name, constraint_list in constraints.items():
            if not constraint_list:
                continue

            # Find intersection of all constraint ranges
            compatible_versions: set[Version] = set()

            for i, constraint in enumerate(constraint_list):
                # Get versions that satisfy this constraint
                satisfied = set()
                for v in self._get_all_versions_for_skill(skill_name):
                    if constraint.satisfies(v):
                        satisfied.add(v)

                if i == 0:
                    compatible_versions = satisfied
                else:
                    compatible_versions &= satisfied

                if not compatible_versions:
                    conflicts.append(VersionConflict(
                        skill_name=skill_name,
                        requested_version=str(constraint.version),
                        required_by=f"constraint_{i}",
                        constraint=str(constraint),
                        available_versions=[],
                    ))
                    break

            if compatible_versions:
                # Pick the latest compatible version
                resolved[skill_name] = max(compatible_versions)

        if conflicts:
            return conflicts

        return resolved

    def detect_conflicts(
        self,
        skill_versions: dict[str, Version],
        dependencies: dict[str, dict[str, str]],
    ) -> list[VersionConflict]:
        """
        Detect version conflicts in skill dependencies.

        Args:
            skill_versions: Map of skill name to version
            dependencies: Map of skill to its dependencies (name -> constraint)

        Returns:
            List of version conflicts
        """
        conflicts: list[VersionConflict] = []

        for skill_name, skill_deps in dependencies.items():
            for dep_name, constraint_str in skill_deps.items():
                constraint = parse_constraint(constraint_str)
                dep_version = skill_versions.get(dep_name)

                if dep_version and not constraint.satisfies(dep_version):
                    conflicts.append(VersionConflict(
                        skill_name=dep_name,
                        requested_version=str(dep_version),
                        required_by=skill_name,
                        constraint=constraint_str,
                    ))

        return conflicts

    def _get_all_versions_for_skill(self, skill_name: str) -> list[Version]:
        """
        Get all available versions for a skill.

        In a real implementation, this would query a registry.
        For now, return common versions.
        """
        return [
            Version(1, 0, 0),
            Version(1, 1, 0),
            Version(1, 2, 0),
            Version(2, 0, 0),
        ]


# =============================================================================
# Migration Support
# =============================================================================


@dataclass
class MigrationStep:
    """
    A single migration step.

    Attributes:
        from_version: Version this migration applies from
        to_version: Version this migration applies to
        description: Description of the migration
        script: Path to migration script
        auto_apply: Whether to apply automatically
    """

    from_version: Version
    to_version: Version
    description: str
    script: Path | None = None
    auto_apply: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": str(self.from_version),
            "to_version": str(self.to_version),
            "description": self.description,
            "script": str(self.script) if self.script else None,
            "auto_apply": self.auto_apply,
        }


@dataclass
class MigrationPath:
    """
    A migration path between versions.

    Attributes:
        skill_name: Name of the skill
        current_version: Current version
        target_version: Target version
        steps: Migration steps to apply
    """

    skill_name: str
    current_version: Version
    target_version: Version
    steps: list[MigrationStep] = field(default_factory=list)

    def is_upgrade(self) -> bool:
        """Check if this is an upgrade."""
        return self.target_version > self.current_version

    def is_downgrade(self) -> bool:
        """Check if this is a downgrade."""
        return self.target_version < self.current_version

    def requires_manual_steps(self) -> bool:
        """Check if any steps require manual intervention."""
        return any(not s.auto_apply for s in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "current_version": str(self.current_version),
            "target_version": str(self.target_version),
            "steps": [s.to_dict() for s in self.steps],
            "is_upgrade": self.is_upgrade(),
            "is_downgrade": self.is_downgrade(),
            "requires_manual_steps": self.requires_manual_steps(),
        }


class MigrationPlanner:
    """
    Plan migration paths for skill version changes.

    Features:
    - Find shortest migration path
    - Detect breaking changes
    - Validate migration steps
    """

    def __init__(self) -> None:
        """Initialize the migration planner."""
        self._migrations: dict[str, list[MigrationStep]] = {}

    def register_migration(self, skill_name: str, step: MigrationStep) -> None:
        """
        Register a migration step for a skill.

        Args:
            skill_name: Name of the skill
            step: Migration step to register
        """
        if skill_name not in self._migrations:
            self._migrations[skill_name] = []
        self._migrations[skill_name].append(step)

    def plan_migration(
        self,
        skill_name: str,
        current_version: Version,
        target_version: Version,
    ) -> MigrationPath | None:
        """
        Plan a migration path between versions.

        Args:
            skill_name: Name of the skill
            current_version: Current version
            target_version: Target version

        Returns:
            Migration path or None if no path exists
        """
        if current_version == target_version:
            return MigrationPath(
                skill_name=skill_name,
                current_version=current_version,
                target_version=target_version,
            )

        skill_migrations = self._migrations.get(skill_name, [])

        # Find applicable migrations
        steps: list[MigrationStep] = []

        if target_version > current_version:
            # Upgrade - find forward path
            version = current_version
            while version < target_version:
                found = False
                for step in skill_migrations:
                    if step.from_version == version:
                        steps.append(step)
                        version = step.to_version
                        found = True
                        break

                if not found:
                    # No direct migration, try to skip
                    # For now, return None (no path found)
                    return None
        else:
            # Downgrade - find reverse path
            version = current_version
            while version > target_version:
                found = False
                for step in skill_migrations:
                    if step.to_version == version:
                        steps.append(step)
                        version = step.from_version
                        found = True
                        break

                if not found:
                    return None

        return MigrationPath(
            skill_name=skill_name,
            current_version=current_version,
            target_version=target_version,
            steps=steps,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """
    version1 = parse_version(v1)
    version2 = parse_version(v2)

    if version1 < version2:
        return -1
    elif version1 > version2:
        return 1
    else:
        return 0


def get_compatible_versions(
    version: str,
    available_versions: list[str],
) -> list[str]:
    """
    Get compatible versions for a given version.

    Args:
        version: Version string to check compatibility against
        available_versions: List of available version strings

    Returns:
        List of compatible version strings
    """
    base_version = parse_version(version)
    compatible: list[str] = []

    for v_str in available_versions:
        v = parse_version(v_str)
        if v.is_compatible_with(base_version):
            compatible.append(v_str)

    return compatible
