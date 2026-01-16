"""
Tests for the Skills module.

Tests cover:
- Skill model
- SkillRegistry class
- Global registry functions
- Skill enabling/disabling
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills import (
    Skill,
    SkillRegistry,
    disable_skill,
    enable_skill,
    get_registry,
    get_skill,
    list_skills,
    register_skill,
)


# =============================================================================
# Skill Model Tests
# =============================================================================


class TestSkill:
    """Tests for Skill model."""

    def test_create_skill(self) -> None:
        """Test creating a skill."""
        skill = Skill(
            name="test-skill",
            version="1.0.0",
            description="A test skill",
        )

        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"
        assert skill.description == "A test skill"
        assert skill.enabled is True
        assert skill.agent_class is None
        assert skill.path is None

    def test_create_skill_with_agent(self) -> None:
        """Test creating a skill with agent class."""
        class TestAgent(BaseAgent):
            pass

        skill = Skill(
            name="agent-skill",
            version="1.0.0",
            description="Skill with agent",
            agent_class=TestAgent,
        )

        assert skill.agent_class == TestAgent

    def test_create_skill_disabled(self) -> None:
        """Test creating a disabled skill."""
        skill = Skill(
            name="disabled-skill",
            version="1.0.0",
            description="A disabled skill",
            enabled=False,
        )

        assert skill.enabled is False

    def test_create_skill_with_path(self) -> None:
        """Test creating a skill with path."""
        skill = Skill(
            name="path-skill",
            version="1.0.0",
            description="Skill with path",
            path=Path("/skills/test"),
        )

        assert skill.path == Path("/skills/test")

    def test_skill_to_dict(self) -> None:
        """Test converting skill to dictionary."""
        skill = Skill(
            name="test",
            version="1.0.0",
            description="Test skill",
            path=Path("/test"),
        )

        data = skill.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test skill"
        assert data["enabled"] is True
        assert data["path"] == str(Path("/test"))

    def test_skill_repr(self) -> None:
        """Test skill string representation."""
        skill = Skill(
            name="test",
            version="1.0.0",
            description="Test",
            enabled=True,
        )

        assert "test" in repr(skill)
        assert "1.0.0" in repr(skill)
        assert "enabled" in repr(skill)


# =============================================================================
# SkillRegistry Tests
# =============================================================================


class TestSkillRegistry:
    """Tests for SkillRegistry class."""

    def test_initialization(self) -> None:
        """Test registry initialization."""
        registry = SkillRegistry()

        assert registry.count() == 0
        assert registry.list_skills() == []

    def test_register_skill(self) -> None:
        """Test registering a skill."""
        registry = SkillRegistry()
        skill = Skill(
            name="test",
            version="1.0.0",
            description="Test skill",
        )

        registry.register(skill)

        assert registry.count() == 1
        assert registry.get("test") == skill

    def test_register_duplicate_raises(self) -> None:
        """Test that registering duplicate skill raises error."""
        registry = SkillRegistry()
        skill1 = Skill(
            name="test",
            version="1.0.0",
            description="First",
        )
        skill2 = Skill(
            name="test",
            version="2.0.0",
            description="Second",
        )

        registry.register(skill1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(skill2)

    def test_unregister_skill(self) -> None:
        """Test unregistering a skill."""
        registry = SkillRegistry()
        skill = Skill(
            name="test",
            version="1.0.0",
            description="Test",
        )

        registry.register(skill)
        assert registry.count() == 1

        unregistered = registry.unregister("test")
        assert unregistered == skill
        assert registry.count() == 0

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering non-existent skill."""
        registry = SkillRegistry()

        result = registry.unregister("nonexistent")

        assert result is None

    def test_get_skill(self) -> None:
        """Test getting a skill."""
        registry = SkillRegistry()
        skill = Skill(
            name="test",
            version="1.0.0",
            description="Test",
        )

        registry.register(skill)

        assert registry.get("test") == skill
        assert registry.get("nonexistent") is None

    def test_list_skills_empty(self) -> None:
        """Test listing skills when empty."""
        registry = SkillRegistry()

        skills = registry.list_skills()

        assert skills == []

    def test_list_skills_enabled_only(self) -> None:
        """Test listing only enabled skills."""
        registry = SkillRegistry()

        registry.register(Skill("skill1", "1.0", "Test 1", enabled=True))
        registry.register(Skill("skill2", "1.0", "Test 2", enabled=False))
        registry.register(Skill("skill3", "1.0", "Test 3", enabled=True))

        skills = registry.list_skills(include_disabled=False)

        assert len(skills) == 2
        assert all(s.enabled for s in skills)
        assert {s.name for s in skills} == {"skill1", "skill3"}

    def test_list_skills_with_disabled(self) -> None:
        """Test listing all skills including disabled."""
        registry = SkillRegistry()

        registry.register(Skill("skill1", "1.0", "Test 1", enabled=True))
        registry.register(Skill("skill2", "1.0", "Test 2", enabled=False))

        skills = registry.list_skills(include_disabled=True)

        assert len(skills) == 2
        assert {s.name for s in skills} == {"skill1", "skill2"}

    def test_list_skills_sorted(self) -> None:
        """Test that skills are sorted by name."""
        registry = SkillRegistry()

        registry.register(Skill("zebra", "1.0", "Z"))
        registry.register(Skill("alpha", "1.0", "A"))
        registry.register(Skill("beta", "1.0", "B"))

        skills = registry.list_skills()

        assert [s.name for s in skills] == ["alpha", "beta", "zebra"]

    def test_enable_skill(self) -> None:
        """Test enabling a skill."""
        registry = SkillRegistry()

        skill = Skill("test", "1.0", "Test", enabled=False)
        registry.register(skill)

        assert skill.enabled is False

        result = registry.enable("test")

        assert result is True
        assert skill.enabled is True

    def test_enable_nonexistent(self) -> None:
        """Test enabling non-existent skill."""
        registry = SkillRegistry()

        result = registry.enable("nonexistent")

        assert result is False

    def test_disable_skill(self) -> None:
        """Test disabling a skill."""
        registry = SkillRegistry()

        skill = Skill("test", "1.0", "Test", enabled=True)
        registry.register(skill)

        assert skill.enabled is True

        result = registry.disable("test")

        assert result is True
        assert skill.enabled is False

    def test_disable_nonexistent(self) -> None:
        """Test disabling non-existent skill."""
        registry = SkillRegistry()

        result = registry.disable("nonexistent")

        assert result is False

    def test_count_all(self) -> None:
        """Test counting all skills."""
        registry = SkillRegistry()

        registry.register(Skill("skill1", "1.0", "Test 1"))
        registry.register(Skill("skill2", "1.0", "Test 2", enabled=False))

        assert registry.count(include_disabled=True) == 2
        assert registry.count(include_disabled=False) == 1

    def test_clear(self) -> None:
        """Test clearing all skills."""
        registry = SkillRegistry()

        registry.register(Skill("skill1", "1.0", "Test 1"))
        registry.register(Skill("skill2", "1.0", "Test 2"))

        assert registry.count() == 2

        registry.clear()

        assert registry.count() == 0

    def test_to_dict(self) -> None:
        """Test converting registry to dictionary."""
        registry = SkillRegistry()

        registry.register(Skill("skill1", "1.0", "Test 1"))
        registry.register(Skill("skill2", "1.0", "Test 2", enabled=False))

        data = registry.to_dict()

        assert data["total"] == 2
        assert data["enabled"] == 1
        assert len(data["skills"]) == 2


# =============================================================================
# Global Registry Tests
# =============================================================================


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_registry_singleton(self) -> None:
        """Test that get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_register_skill_global(self) -> None:
        """Test registering skill globally."""
        # Clear registry first
        get_registry().clear()

        skill = Skill("global", "1.0", "Global skill")
        register_skill(skill)

        assert get_skill("global") == skill

    def test_list_skills_global(self) -> None:
        """Test listing skills globally."""
        # Clear registry first
        get_registry().clear()

        register_skill(Skill("skill1", "1.0", "Test 1"))
        register_skill(Skill("skill2", "1.0", "Test 2"))

        skills = list_skills()

        assert len(skills) == 2

    def test_get_skill_global(self) -> None:
        """Test getting skill globally."""
        # Clear registry first
        get_registry().clear()

        skill = Skill("test", "1.0", "Test")
        register_skill(skill)

        assert get_skill("test") == skill
        assert get_skill("nonexistent") is None

    def test_enable_skill_global(self) -> None:
        """Test enabling skill globally."""
        # Clear registry first
        get_registry().clear()

        skill = Skill("test", "1.0", "Test", enabled=False)
        register_skill(skill)

        assert enable_skill("test") is True
        assert get_skill("test").enabled is True

    def test_disable_skill_global(self) -> None:
        """Test disabling skill globally."""
        # Clear registry first
        get_registry().clear()

        skill = Skill("test", "1.0", "Test", enabled=True)
        register_skill(skill)

        assert disable_skill("test") is True
        assert get_skill("test").enabled is False
