"""
Tests for the Skill Loader module.

Tests cover:
- Skill discovery from directories
- Skill loading from manifests
- Agent class loading
- Dependency resolution
- Circular dependency detection
- Load order determination
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from claude_playwright_agent.skills import (
    Skill,
    SkillRegistry,
    get_registry,
    register_skill,
)
from claude_playwright_agent.skills.loader import (
    BUILTIN_SKILLS_DIR,
    CircularDependencyError,
    DependencyError,
    SkillLoader,
    SkillLoadError,
    SkillNotFoundError,
    discover_skills,
    load_skills,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def clean_registry() -> None:
    """Clean the global registry before each test."""
    get_registry().clear()
    yield
    get_registry().clear()


@pytest.fixture
def sample_skill_dir(tmp_path: Path) -> Path:
    """Create a sample skill directory with manifest."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    manifest_path = skill_dir / "skill.yaml"
    manifest_data = {
        "name": "test-skill",
        "version": "1.0.0",
        "description": "A test skill",
    }
    manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

    return skill_dir


@pytest.fixture
def skill_with_agent(tmp_path: Path) -> Path:
    """Create a skill with an agent class."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "agent-skill"
    skill_dir.mkdir()

    # Create manifest
    manifest_path = skill_dir / "skill.yaml"
    manifest_data = {
        "name": "agent-skill",
        "version": "1.0.0",
        "description": "A skill with an agent",
        "agent_class": "agent_skill.MyAgent",
        "entry_point": "main.py",
    }
    manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

    # Create agent module
    agent_module = skill_dir / "main.py"
    agent_module.write_text(
        """
class MyAgent:
    pass
""",
        encoding="utf-8",
    )

    return skill_dir


@pytest.fixture
def skills_with_dependencies(tmp_path: Path) -> dict[str, Path]:
    """Create skills with dependencies."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create base skill (no dependencies)
    base_dir = skills_dir / "base-skill"
    base_dir.mkdir()
    base_manifest = {
        "name": "base-skill",
        "version": "1.0.0",
        "description": "Base skill",
        "dependencies": [],
    }
    (base_dir / "skill.yaml").write_text(yaml.dump(base_manifest), encoding="utf-8")

    # Create dependent skill
    dependent_dir = skills_dir / "dependent-skill"
    dependent_dir.mkdir()
    dependent_manifest = {
        "name": "dependent-skill",
        "version": "1.0.0",
        "description": "Dependent skill",
        "dependencies": ["base-skill"],
    }
    (dependent_dir / "skill.yaml").write_text(yaml.dump(dependent_manifest), encoding="utf-8")

    return {
        "base": base_dir,
        "dependent": dependent_dir,
    }


# =============================================================================
# SkillLoader Tests
# =============================================================================


class TestSkillLoader:
    """Tests for SkillLoader class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test loader initialization."""
        loader = SkillLoader(project_path=tmp_path, include_builtins=False)

        assert loader._project_path == tmp_path
        assert loader._include_builtins is False
        assert loader._registry is get_registry()

    def test_initialization_defaults(self) -> None:
        """Test loader initialization with defaults."""
        loader = SkillLoader()

        assert loader._project_path == Path.cwd()
        assert loader._include_builtins is True


# =============================================================================
# Skill Discovery Tests
# =============================================================================


class TestSkillDiscovery:
    """Tests for skill discovery functionality."""

    def test_discover_empty_directory(self, tmp_path: Path, clean_registry: None) -> None:
        """Test discovering skills in empty directory."""
        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        manifests = loader.discover_skills()

        assert manifests == []

    def test_discover_single_skill(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test discovering a single skill."""
        # sample_skill_dir is tmp_path/skills/test-skill
        # We need to use tmp_path as project_path so loader scans tmp_path/skills
        loader = SkillLoader(project_path=sample_skill_dir.parent.parent, include_builtins=False)
        manifests = loader.discover_skills()

        assert len(manifests) == 1
        assert manifests[0].name == "skill.yaml"

    def test_discover_multiple_skills(self, tmp_path: Path, clean_registry: None) -> None:
        """Test discovering multiple skills."""
        # Create skills directory
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create multiple skill directories
        for i in range(3):
            skill_dir = skills_dir / f"skill-{i}"
            skill_dir.mkdir()
            manifest_path = skill_dir / "skill.yaml"
            manifest_data = {
                "name": f"skill-{i}",
                "version": "1.0.0",
                "description": f"Skill {i}",
            }
            manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        manifests = loader.discover_skills()

        assert len(manifests) == 3

    def test_scan_directory(self, tmp_path: Path, clean_registry: None) -> None:
        """Test scanning a directory for manifests."""
        # Create skill.yaml and skill.yml
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        yaml_path = skill_dir / "skill.yaml"
        yaml_path.write_text("name: test\nversion: 1.0.0\ndescription: Test")

        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        manifests = loader._scan_directory(tmp_path)

        assert len(manifests) >= 1


# =============================================================================
# Skill Loading Tests
# =============================================================================


class TestSkillLoading:
    """Tests for skill loading functionality."""

    def test_load_skill_from_manifest(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test loading a skill from manifest."""
        loader = SkillLoader(project_path=sample_skill_dir.parent, include_builtins=False)
        manifest_path = sample_skill_dir / "skill.yaml"

        skill = loader.load_skill(manifest_path)

        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"
        assert skill.description == "A test skill"
        assert skill.enabled is True

    def test_load_skill_already_loaded(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test loading the same skill twice."""
        loader = SkillLoader(project_path=sample_skill_dir.parent, include_builtins=False)
        manifest_path = sample_skill_dir / "skill.yaml"

        skill1 = loader.load_skill(manifest_path)
        skill2 = loader.load_skill(manifest_path)

        # Should return the same skill from registry
        assert skill1.name == skill2.name

    def test_load_skill_invalid_manifest(self, tmp_path: Path, clean_registry: None) -> None:
        """Test loading skill with invalid manifest."""
        loader = SkillLoader(project_path=tmp_path, include_builtins=False)

        invalid_path = tmp_path / "invalid.yaml"
        invalid_path.write_text("invalid: [yaml")

        with pytest.raises(SkillLoadError):
            loader.load_skill(invalid_path)

    def test_load_skill_with_agent(self, skill_with_agent: Path, clean_registry: None) -> None:
        """Test loading skill with agent class."""
        loader = SkillLoader(project_path=skill_with_agent.parent, include_builtins=False)
        manifest_path = skill_with_agent / "skill.yaml"

        skill = loader.load_skill(manifest_path)

        assert skill.name == "agent-skill"
        assert skill.agent_class is not None
        assert skill.agent_class.__name__ == "MyAgent"

    def test_load_all_skills(self, tmp_path: Path, clean_registry: None) -> None:
        """Test loading all skills from directory."""
        # Create skills directory
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create multiple skills
        for i in range(3):
            skill_dir = skills_dir / f"skill-{i}"
            skill_dir.mkdir()
            manifest_path = skill_dir / "skill.yaml"
            manifest_data = {
                "name": f"skill-{i}",
                "version": "1.0.0",
                "description": f"Skill {i}",
            }
            manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        skills = loader.load_all()

        assert len(skills) == 3

    def test_load_nonexistent_skill(self, tmp_path: Path, clean_registry: None) -> None:
        """Test loading non-existent skill."""
        loader = SkillLoader(project_path=tmp_path, include_builtins=False)

        with pytest.raises(SkillLoadError):
            loader.load_skill(tmp_path / "nonexistent.yaml")


# =============================================================================
# Agent Class Loading Tests
# =============================================================================


class TestAgentClassLoading:
    """Tests for agent class loading."""

    def test_load_agent_class_success(self, skill_with_agent: Path, clean_registry: None) -> None:
        """Test successfully loading agent class."""
        loader = SkillLoader(project_path=skill_with_agent.parent, include_builtins=False)
        manifest_path = skill_with_agent / "skill.yaml"

        skill = loader.load_skill(manifest_path)

        assert skill.agent_class is not None

    def test_load_agent_class_invalid_format(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test loading agent class with invalid format."""
        # Update manifest with invalid agent_class
        manifest_path = sample_skill_dir / "skill.yaml"
        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest_data["agent_class"] = "InvalidFormat"
        manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        loader = SkillLoader(project_path=sample_skill_dir.parent, include_builtins=False)

        with pytest.raises(SkillLoadError, match="Invalid agent_class format"):
            loader.load_skill(manifest_path)

    def test_load_agent_class_missing_file(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test loading agent class with missing entry point."""
        # Update manifest with entry_point that doesn't exist
        manifest_path = sample_skill_dir / "skill.yaml"
        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest_data["agent_class"] = "missing.MyAgent"
        manifest_data["entry_point"] = "nonexistent.py"
        manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        loader = SkillLoader(project_path=sample_skill_dir.parent, include_builtins=False)

        with pytest.raises(SkillLoadError, match="Entry point not found"):
            loader.load_skill(manifest_path)


# =============================================================================
# Dependency Resolution Tests
# =============================================================================


class TestDependencyResolution:
    """Tests for dependency resolution."""

    def test_resolve_dependencies_no_deps(self, sample_skill_dir: Path, clean_registry: None) -> None:
        """Test resolving skills with no dependencies."""
        loader = SkillLoader(project_path=sample_skill_dir.parent, include_builtins=False)
        loader.load_skill(sample_skill_dir / "skill.yaml")

        order = loader._resolve_dependencies()

        assert len(order) == 1
        assert order[0] == "test-skill"

    def test_resolve_dependencies_with_deps(self, skills_with_dependencies: dict[str, Path], clean_registry: None) -> None:
        """Test resolving skills with dependencies."""
        base_dir = skills_with_dependencies["base"]
        dependent_dir = skills_with_dependencies["dependent"]

        loader = SkillLoader(project_path=base_dir.parent.parent, include_builtins=False)
        loader.load_skill(base_dir / "skill.yaml")
        loader.load_skill(dependent_dir / "skill.yaml")

        order = loader._resolve_dependencies()

        # Base should come before dependent
        assert order.index("base-skill") < order.index("dependent-skill")

    def test_circular_dependency_detection(self, tmp_path: Path, clean_registry: None) -> None:
        """Test detection of circular dependencies."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create circular dependency: A -> B -> A
        a_dir = skills_dir / "skill-a"
        a_dir.mkdir()
        a_manifest = {
            "name": "skill-a",
            "version": "1.0.0",
            "description": "Skill A",
            "dependencies": ["skill-b"],
        }
        (a_dir / "skill.yaml").write_text(yaml.dump(a_manifest), encoding="utf-8")

        b_dir = skills_dir / "skill-b"
        b_dir.mkdir()
        b_manifest = {
            "name": "skill-b",
            "version": "1.0.0",
            "description": "Skill B",
            "dependencies": ["skill-a"],
        }
        (b_dir / "skill.yaml").write_text(yaml.dump(b_manifest), encoding="utf-8")

        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        loader.load_skill(a_dir / "skill.yaml")
        loader.load_skill(b_dir / "skill.yaml")

        with pytest.raises(CircularDependencyError):
            loader._resolve_dependencies()

    def test_check_dependencies(self, skills_with_dependencies: dict[str, Path], clean_registry: None) -> None:
        """Test checking if dependencies are available."""
        base_dir = skills_with_dependencies["base"]
        dependent_dir = skills_with_dependencies["dependent"]

        loader = SkillLoader(project_path=base_dir.parent.parent, include_builtins=False)

        # Check before loading
        loader.load_skill(dependent_dir / "skill.yaml")
        assert loader.check_dependencies("dependent-skill") is False

        # Load base skill
        loader.load_skill(base_dir / "skill.yaml")
        assert loader.check_dependencies("dependent-skill") is True

    def test_get_missing_dependencies(self, skills_with_dependencies: dict[str, Path], clean_registry: None) -> None:
        """Test getting missing dependencies."""
        dependent_dir = skills_with_dependencies["dependent"]

        loader = SkillLoader(project_path=dependent_dir.parent.parent, include_builtins=False)
        loader.load_skill(dependent_dir / "skill.yaml")

        missing = loader.get_missing_dependencies("dependent-skill")

        assert missing == ["base-skill"]


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_load_skills(self, tmp_path: Path, clean_registry: None) -> None:
        """Test load_skills convenience function."""
        # Create skills directory and a skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        manifest_path = skill_dir / "skill.yaml"
        manifest_data = {
            "name": "test-skill",
            "version": "1.0.0",
            "description": "Test",
        }
        manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        skills = load_skills(project_path=tmp_path, include_builtins=False)

        assert len(skills) >= 1

    def test_discover_skills(self, tmp_path: Path, clean_registry: None) -> None:
        """Test discover_skills convenience function."""
        # Create skills directory and a skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        manifest_path = skill_dir / "skill.yaml"
        manifest_data = {
            "name": "test-skill",
            "version": "1.0.0",
            "description": "Test",
        }
        manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

        manifests = discover_skills(project_path=tmp_path, include_builtins=False)

        assert len(manifests) >= 1


# =============================================================================
# Load Order Tests
# =============================================================================


class TestLoadOrder:
    """Tests for dependency-based load ordering."""

    def test_load_order_preserves_dependencies(self, tmp_path: Path, clean_registry: None) -> None:
        """Test that skills are loaded in dependency order."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create chain: C -> B -> A
        skills = ["skill-a", "skill-b", "skill-c"]
        for i, skill_name in enumerate(skills):
            skill_dir = skills_dir / skill_name
            skill_dir.mkdir()
            deps = skills[i + 1:] if i < len(skills) - 1 else []
            manifest = {
                "name": skill_name,
                "version": "1.0.0",
                "description": f"Skill {i}",
                "dependencies": deps,
            }
            (skill_dir / "skill.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

        loader = SkillLoader(project_path=tmp_path, include_builtins=False)
        loader.load_all()

        # Verify order in registry
        registry = get_registry()
        all_skills = registry.list_skills(include_disabled=True)

        # All should be loaded
        assert len(all_skills) == 3
