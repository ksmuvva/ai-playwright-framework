"""
Skill Manifest Parser for Claude Playwright Agent.

This module handles:
- Parsing YAML skill manifest files
- Validating manifest structure
- Extracting skill metadata
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# =============================================================================
# Manifest Models
# =============================================================================


@dataclass
class SkillManifest:
    """
    Parsed skill manifest from YAML.

    A manifest describes a skill's metadata, dependencies,
    and configuration.
    """

    # Required fields
    name: str
    version: str
    description: str

    # Optional metadata
    author: str = ""
    license: str = ""
    homepage: str = ""
    repository: str = ""

    # Skill configuration
    agent_class: str = ""  # Python class path for the agent
    entry_point: str = ""  # Entry point file
    enabled: bool = True

    # Dependencies
    dependencies: list[str] = field(default_factory=list)
    python_dependencies: list[str] = field(default_factory=list)

    # Additional metadata
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    category: str = ""

    # File path
    path: Path = field(default_factory=lambda: Path.cwd())

    # Computed checksum
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "agent_class": self.agent_class,
            "entry_point": self.entry_point,
            "enabled": self.enabled,
            "dependencies": self.dependencies,
            "python_dependencies": self.python_dependencies,
            "tags": self.tags,
            "keywords": self.keywords,
            "category": self.category,
            "path": str(self.path),
            "checksum": self.checksum,
        }


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        """
        Initialize the validation error.

        Args:
            message: Error message
            errors: Optional list of specific validation errors
        """
        super().__init__(message)
        self.errors = errors or []


# =============================================================================
# Manifest Parser
# =============================================================================


class ManifestParser:
    """
    Parse and validate skill manifest files.

    Features:
    - Parse YAML manifest files
    - Validate required fields
    - Compute manifest checksums
    - Extract skill metadata
    """

    # Required fields in manifest
    REQUIRED_FIELDS = ["name", "version", "description"]

    # Optional fields with defaults
    OPTIONAL_FIELDS = {
        "author": "",
        "license": "",
        "homepage": "",
        "repository": "",
        "agent_class": "",
        "entry_point": "",
        "enabled": True,
        "dependencies": [],
        "python_dependencies": [],
        "tags": [],
        "keywords": [],
        "category": "",
    }

    def __init__(self) -> None:
        """Initialize the manifest parser."""
        pass

    def parse(
        self,
        path: Path | str,
    ) -> SkillManifest:
        """
        Parse a skill manifest file.

        Args:
            path: Path to the manifest file

        Returns:
            Parsed SkillManifest

        Raises:
            ManifestValidationError: If validation fails
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        # Read file content
        content = path.read_text(encoding="utf-8")

        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML: {e}") from e

        # Validate
        errors = self._validate(data)

        if errors:
            raise ManifestValidationError(
                f"Manifest validation failed for {path}",
                errors,
            )

        # Compute checksum
        checksum = self._compute_checksum(content)

        # Extract fields
        manifest = SkillManifest(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data.get("author", ""),
            license=data.get("license", ""),
            homepage=data.get("homepage", ""),
            repository=data.get("repository", ""),
            agent_class=data.get("agent_class", ""),
            entry_point=data.get("entry_point", ""),
            enabled=data.get("enabled", True),
            dependencies=data.get("dependencies", []),
            python_dependencies=data.get("python_dependencies", []),
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            category=data.get("category", ""),
            path=path.parent,
            checksum=checksum,
        )

        return manifest

    def parse_string(
        self,
        content: str,
    ) -> SkillManifest:
        """
        Parse a skill manifest from string.

        Args:
            content: YAML content as string

        Returns:
            Parsed SkillManifest

        Raises:
            ManifestValidationError: If validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML: {e}") from e

        # Validate
        errors = self._validate(data)

        if errors:
            raise ManifestValidationError(
                "Manifest validation failed",
                errors,
            )

        # Compute checksum
        checksum = self._compute_checksum(content)

        # Extract fields
        manifest = SkillManifest(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data.get("author", ""),
            license=data.get("license", ""),
            homepage=data.get("homepage", ""),
            repository=data.get("repository", ""),
            agent_class=data.get("agent_class", ""),
            entry_point=data.get("entry_point", ""),
            enabled=data.get("enabled", True),
            dependencies=data.get("dependencies", []),
            python_dependencies=data.get("python_dependencies", []),
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            category=data.get("category", ""),
            checksum=checksum,
        )

        return manifest

    def _validate(
        self,
        data: dict[str, Any],
    ) -> list[str]:
        """
        Validate manifest data.

        Args:
            data: Parsed YAML data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        if "name" in data:
            if not isinstance(data["name"], str):
                errors.append("Field 'name' must be a string")
            elif not data["name"] or not data["name"][0].isalpha():
                errors.append("Field 'name' must start with a letter")
            elif not all(c.isalnum() or c in "-_" for c in data["name"]):
                errors.append("Field 'name' can only contain letters, numbers, hyphens, and underscores")

        if "version" in data:
            if not isinstance(data["version"], str):
                errors.append("Field 'version' must be a string")

        if "description" in data:
            if not isinstance(data["description"], str):
                errors.append("Field 'description' must be a string")

        if "enabled" in data and not isinstance(data["enabled"], bool):
            errors.append("Field 'enabled' must be a boolean")

        if "dependencies" in data:
            if not isinstance(data["dependencies"], list):
                errors.append("Field 'dependencies' must be a list")
            elif not all(isinstance(d, str) for d in data["dependencies"]):
                errors.append("All items in 'dependencies' must be strings")

        if "python_dependencies" in data:
            if not isinstance(data["python_dependencies"], list):
                errors.append("Field 'python_dependencies' must be a list")
            elif not all(isinstance(d, str) for d in data["python_dependencies"]):
                errors.append("All items in 'python_dependencies' must be strings")

        if "tags" in data:
            if not isinstance(data["tags"], list):
                errors.append("Field 'tags' must be a list")
            elif not all(isinstance(t, str) for t in data["tags"]):
                errors.append("All items in 'tags' must be strings")

        return errors

    def _compute_checksum(
        self,
        content: str,
    ) -> str:
        """
        Compute checksum of manifest content.

        Args:
            content: Manifest file content

        Returns:
            Hexadecimal checksum string
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def validate(
        self,
        path: Path | str,
    ) -> list[str]:
        """
        Validate a manifest file without parsing.

        Args:
            path: Path to the manifest file

        Returns:
            List of validation error messages (empty if valid)
        """
        path = Path(path)

        if not path.exists():
            return [f"Manifest file not found: {path}"]

        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return [f"YAML parsing error: {e}"]
        except Exception as e:
            return [f"File reading error: {e}"]

        return self._validate(data)


# =============================================================================
# Convenience Functions
# =============================================================================


def parse_manifest(
    path: Path | str,
) -> SkillManifest:
    """
    Parse a skill manifest file.

    Args:
        path: Path to the manifest file

    Returns:
        Parsed SkillManifest

    Raises:
        ManifestValidationError: If validation fails
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    parser = ManifestParser()
    return parser.parse(path)


def parse_manifest_string(
    content: str,
) -> SkillManifest:
    """
    Parse a skill manifest from string.

    Args:
        content: YAML content as string

    Returns:
        Parsed SkillManifest

    Raises:
        ManifestValidationError: If validation fails
        yaml.YAMLError: If YAML parsing fails
    """
    parser = ManifestParser()
    return parser.parse_string(content)


def validate_manifest(
    path: Path | str,
) -> list[str]:
    """
    Validate a manifest file without parsing.

    Args:
        path: Path to the manifest file

    Returns:
        List of validation error messages (empty if valid)
    """
    parser = ManifestParser()
    return parser.validate(path)
