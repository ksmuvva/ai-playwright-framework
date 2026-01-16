"""
Skill models for Claude Playwright Agent.

This module provides:
- Skill model
- SkillRegistry for managing skills
"""

from pathlib import Path
from typing import Any


# =============================================================================
# Skill Models
# =============================================================================


class Skill:
    """
    Represents a loaded skill.

    A skill is a reusable unit of functionality that can be
    dynamically loaded into the agent framework.
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        agent_class: type[Any] | None = None,
        enabled: bool = True,
        path: Path | None = None,
    ) -> None:
        """
        Initialize a skill.

        Args:
            name: Skill name
            version: Skill version
            description: Skill description
            agent_class: Optional agent class for this skill
            enabled: Whether the skill is enabled
            path: Path to skill directory
        """
        self.name = name
        self.version = version
        self.description = description
        self.agent_class = agent_class
        self.enabled = enabled
        self.path = path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "path": str(self.path) if self.path else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self.enabled else "disabled"
        return f"Skill({self.name}@{self.version}, {status})"


# =============================================================================
# Skill Registry
# =============================================================================


class SkillRegistry:
    """
    Registry for managing skills.

    Features:
    - Register and unregister skills
    - Enable/disable skills
    - List available skills
    - Get skill by name
    """

    def __init__(self) -> None:
        """Initialize the skill registry."""
        self._skills: dict[str, Skill] = {}

    def register(
        self,
        skill: Skill,
    ) -> None:
        """
        Register a skill.

        Args:
            skill: The skill to register

        Raises:
            ValueError: If a skill with the same name is already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")

        self._skills[skill.name] = skill

    def unregister(
        self,
        name: str,
    ) -> Skill | None:
        """
        Unregister a skill.

        Args:
            name: Name of the skill to unregister

        Returns:
            The unregistered skill, or None if not found
        """
        return self._skills.pop(name, None)

    def get(
        self,
        name: str,
    ) -> Skill | None:
        """
        Get a skill by name.

        Args:
            name: Name of the skill

        Returns:
            The skill, or None if not found
        """
        return self._skills.get(name)

    def list_skills(
        self,
        include_disabled: bool = False,
    ) -> list[Skill]:
        """
        List all registered skills.

        Args:
            include_disabled: Whether to include disabled skills

        Returns:
            List of skills
        """
        skills = list(self._skills.values())

        if not include_disabled:
            skills = [s for s in skills if s.enabled]

        return sorted(skills, key=lambda s: s.name)

    def enable(
        self,
        name: str,
    ) -> bool:
        """
        Enable a skill.

        Args:
            name: Name of the skill to enable

        Returns:
            True if the skill was enabled, False if not found
        """
        skill = self.get(name)
        if skill:
            skill.enabled = True
            return True
        return False

    def disable(
        self,
        name: str,
    ) -> bool:
        """
        Disable a skill.

        Args:
            name: Name of the skill to disable

        Returns:
            True if the skill was disabled, False if not found
        """
        skill = self.get(name)
        if skill:
            skill.enabled = False
            return True
        return False

    def count(
        self,
        include_disabled: bool = False,
    ) -> int:
        """
        Count registered skills.

        Args:
            include_disabled: Whether to include disabled skills

        Returns:
            Number of skills
        """
        if include_disabled:
            return len(self._skills)
        return len([s for s in self._skills.values() if s.enabled])

    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert registry to dictionary.

        Returns:
            Dictionary with skills information
        """
        return {
            "skills": [s.to_dict() for s in self.list_skills(include_disabled=True)],
            "total": self.count(include_disabled=True),
            "enabled": self.count(include_disabled=False),
        }


# =============================================================================
# Global Registry
# =============================================================================


# Global skill registry instance
_global_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """
    Get the global skill registry.

    Returns:
        The global skill registry
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = SkillRegistry()

    return _global_registry


def register_skill(skill: Skill) -> None:
    """
    Register a skill in the global registry.

    Args:
        skill: The skill to register
    """
    get_registry().register(skill)


def list_skills(include_disabled: bool = False) -> list[Skill]:
    """
    List all skills in the global registry.

    Args:
        include_disabled: Whether to include disabled skills

    Returns:
        List of skills
    """
    return get_registry().list_skills(include_disabled=include_disabled)


def get_skill(name: str) -> Skill | None:
    """
    Get a skill from the global registry.

    Args:
        name: Name of the skill

    Returns:
        The skill, or None if not found
    """
    return get_registry().get(name)


def enable_skill(name: str) -> bool:
    """
    Enable a skill in the global registry.

    Args:
        name: Name of the skill to enable

    Returns:
        True if the skill was enabled, False if not found
    """
    return get_registry().enable(name)


def disable_skill(name: str) -> bool:
    """
    Disable a skill in the global registry.

    Args:
        name: Name of the skill to disable

    Returns:
        True if the skill was disabled, False if not found
    """
    return get_registry().disable(name)
