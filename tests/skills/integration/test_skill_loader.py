"""Integration tests for skill loading."""

import pytest
from pathlib import Path

from claude_playwright_agent.skills import SkillLoader


@pytest.mark.integration
def test_load_all_45_skills(project_path):
    """Test that all 45 skills can be loaded."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Should have at least 45 skill manifests
    assert len(discovered) >= 45

    # Try to load each skill
    loaded = []
    failed = []

    for manifest in discovered:
        try:
            skill = loader.load_skill(manifest)
            loaded.append(skill.name)
        except Exception as e:
            failed.append((manifest, str(e)))

    # All skills should load successfully
    assert len(loaded) >= 45, f"Only {len(loaded)}/45 skills loaded. Failed: {failed}"

    # Verify skill names
    epics = {}
    for skill_name in loaded:
        epic = skill_name.split("_")[0]
        epics[epic] = epics.get(epic, 0) + 1

    # Should have skills from E1-E9
    for epic_num in range(1, 10):
        epic = f"e{epic_num}"
        assert epic in epics, f"No skills found for {epic.upper()}"
        assert epics[epic] >= 5, f"Expected at least 5 skills for {epic.upper()}, got {epics[epic]}"


@pytest.mark.integration
def test_all_skills_have_required_metadata(project_path):
    """Test that all skills have required metadata."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Required attributes
        assert skill.name, f"Skill from {manifest} missing name"
        assert skill.version, f"Skill {skill.name} missing version"
        assert skill.description, f"Skill {skill.name} missing description"

        # Should have path
        assert skill.path is not None, f"Skill {skill.name} missing path"


@pytest.mark.integration
def test_skill_discovery_consistency(project_path):
    """Test that skill discovery is consistent."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Discover multiple times
    discovered_1 = loader.discover_skills()
    discovered_2 = loader.discover_skills()

    # Should return same results
    assert len(discovered_1) == len(discovered_2)

    # Convert to sets for comparison
    paths_1 = set(str(p) for p in discovered_1)
    paths_2 = set(str(p) for p in discovered_2)

    assert paths_1 == paths_2
