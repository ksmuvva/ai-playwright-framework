"""Integration tests for comprehensive skill workflows."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import yaml

from claude_playwright_agent.skills import SkillLoader
from claude_playwright_agent.skills.dependencies import DependencyGraph


@pytest.mark.integration
def test_all_45_skills_discoverable(project_path):
    """Test that all 45 skills are discoverable."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)
    discovered = loader.discover_skills()

    # Should have at least 45 skills
    assert len(discovered) >= 45, f"Expected at least 45 skills, found {len(discovered)}"

    # Group by epic
    epic_counts = {}
    for manifest in discovered:
        # Extract epic from path (e.g., e1, e2, etc.)
        path_str = str(manifest).lower()
        for epic_num in range(1, 10):
            epic = f"e{epic_num}"
            if epic in path_str:
                epic_counts[epic] = epic_counts.get(epic, 0) + 1
                break

    # Should have skills from all epics E1-E9
    for epic_num in range(1, 10):
        epic = f"e{epic_num}"
        assert epic in epic_counts, f"No skills found for {epic.upper()}"
        assert epic_counts[epic] >= 5, f"Expected at least 5 skills for {epic.upper()}, got {epic_counts[epic]}"


@pytest.mark.integration
def test_all_45_skills_loadable(project_path):
    """Test that all 45 skills can be loaded successfully."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    loaded_skills = []
    failed_skills = []

    for manifest in loader.discover_skills():
        try:
            skill = loader.load_skill(manifest)
            loaded_skills.append(skill)
        except Exception as e:
            failed_skills.append((str(manifest), str(e)))

    # All skills should load
    assert len(loaded_skills) >= 45, f"Only {len(loaded_skills)}/45 skills loaded. Failed: {failed_skills}"
    assert len(failed_skills) == 0, f"Failed to load {len(failed_skills)} skills: {failed_skills}"


@pytest.mark.integration
def test_all_skills_have_required_interfaces(project_path):
    """Test that all skills implement required interfaces."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Required attributes
        assert hasattr(skill, "name"), f"Skill missing 'name' attribute"
        assert hasattr(skill, "version"), f"Skill missing 'version' attribute"
        assert hasattr(skill, "description"), f"Skill missing 'description' attribute"

        # If agent_class is available, check the agent's interface
        if skill.agent_class:
            agent = skill.agent_class()
            # Required methods
            assert hasattr(agent, "run"), f"Skill missing 'run' method"
            assert callable(agent.run), f"Skill 'run' must be callable"
            # Context tracking
            assert hasattr(agent, "_context_history"), f"Skill missing '_context_history'"
            assert hasattr(agent, "get_context_history"), f"Skill missing 'get_context_history' method"


@pytest.mark.integration
def test_skill_versions_follow_semver(project_path):
    """Test that all skills follow semantic versioning."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Version should follow semver pattern (major.minor.patch)
        version_parts = skill.version.split(".")
        assert len(version_parts) == 3, f"Skill {skill.name} version {skill.version} doesn't follow semver"

        # All parts should be numeric
        for part in version_parts:
            assert part.isdigit(), f"Skill {skill.name} has non-numeric version part: {part}"


@pytest.mark.integration
def test_skill_manifests_are_valid(project_path):
    """Test that all skill manifests (skill.yaml) are valid."""
    import yaml

    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest_path in loader.discover_skills():
        # Read and parse manifest
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Required fields
        assert "name" in manifest, f"Manifest {manifest_path} missing 'name'"
        assert "version" in manifest, f"Manifest {manifest_path} missing 'version'"
        assert "description" in manifest, f"Manifest {manifest_path} missing 'description'"

        # Name should match directory name
        manifest_dir = manifest_path.parent.name
        assert manifest["name"] == manifest_dir, f"Skill name {manifest['name']} doesn't match directory {manifest_dir}"


@pytest.mark.integration
def test_dependency_graph_is_valid(project_path):
    """Test that the complete skill dependency graph is valid."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Build complete dependency graph from manifests
    graph = DependencyGraph()
    skills_data = {}

    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        name = manifest_data.get("name", "")
        version = manifest_data.get("version", "1.0.0")
        deps = manifest_data.get("dependencies", [])

        graph.add_skill(name, version, deps)
        skills_data[name] = {"version": version, "deps": deps}

    # No circular dependencies
    assert not graph.has_circular_dependency(), "Circular dependencies detected in skill graph"

    # Load order should be computable
    load_order = graph.get_load_order()
    assert len(load_order) > 0, "Could not compute load order"

    # All skills should be in load order
    all_skills = set(skills_data.keys())
    loaded_skills = set(load_order)
    missing = all_skills - loaded_skills
    assert len(missing) == 0, f"Skills not in load order: {missing}"

    # Dependencies should come before dependents
    positions = {skill: i for i, skill in enumerate(load_order)}
    for skill, data in skills_data.items():
        for dep in data["deps"]:
            if dep in positions:
                assert positions[dep] < positions[skill], \
                    f"Dependency {dep} should come before {skill}"


@pytest.mark.integration
def test_all_dependencies_are_valid(project_path):
    """Test that all skill dependencies reference valid skills."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Collect all skill names
    all_skill_names = set()
    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)
        all_skill_names.add(manifest_data.get("name", ""))

    # Check that all dependencies reference valid skills
    invalid_deps = []
    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        name = manifest_data.get("name", "")
        deps = manifest_data.get("dependencies", [])

        for dep in deps:
            if dep not in all_skill_names:
                invalid_deps.append((name, dep))

    assert len(invalid_deps) == 0, f"Invalid dependencies found: {invalid_deps}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_skills_handle_empty_context(project_path):
    """Test that all skills can handle empty context."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    failed = []

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()

        try:
            result = await agent.run("test", {})
            # Should return something
            assert result is not None, f"Skill {skill.name} returned None for empty context"
        except Exception as e:
            failed.append((skill.name, str(e)))

    # Most skills should handle empty context
    # Allow some failures for skills that require specific context
    assert len(failed) <= len(list(loader.discover_skills())) * 0.1, \
        f"Too many skills ({len(failed)}) failed with empty context: {failed}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_skills_track_context_history(project_path):
    """Test that all skills properly track context history."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()

        # Should have context history tracking
        assert hasattr(agent, "_context_history"), f"Skill {skill.name} missing _context_history"
        assert hasattr(agent, "get_context_history"), f"Skill {skill.name} missing get_context_history"

        # Execute skill
        context = {"workflow_id": "test_workflow"}
        await agent.run("test", context)

        # History should be accessible
        history = agent.get_context_history()
        assert isinstance(history, list), f"Skill {skill.name} history is not a list"


@pytest.mark.integration
def test_skill_names_are_unique(project_path):
    """Test that all skill names are unique."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    skill_names = []
    duplicates = []

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.name in skill_names:
            duplicates.append(skill.name)
        skill_names.append(skill.name)

    assert len(duplicates) == 0, f"Duplicate skill names found: {set(duplicates)}"


@pytest.mark.integration
def test_skill_directories_match_names(project_path):
    """Test that skill directory names match skill names."""
    import yaml

    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Directory name should match skill name
        expected_dir = manifest["name"]
        actual_dir = manifest_path.parent.name

        assert expected_dir == actual_dir, \
            f"Skill name '{expected_dir}' doesn't match directory '{actual_dir}'"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingestion_to_bdd_workflow(project_path):
    """Test complete workflow from ingestion to BDD conversion."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Find skills for the workflow by checking actual skill names
    all_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            all_skills.append(skill)

    # Try to find relevant skills
    ingestion_agent = None
    dedup_agent = None
    bdd_agent = None

    for skill in all_skills:
        skill_name_lower = skill.name.lower()
        if not ingestion_agent and ("ingestion" in skill_name_lower or "parsing" in skill_name_lower or "e3_1" in skill_name_lower):
            ingestion_agent = skill.agent_class()
        elif not dedup_agent and ("dedup" in skill_name_lower or "e4_1" in skill_name_lower):
            dedup_agent = skill.agent_class()
        elif not bdd_agent and ("bdd" in skill_name_lower or "conversion" in skill_name_lower or "e5_1" in skill_name_lower):
            bdd_agent = skill.agent_class()

    # Execute workflow if we found any skills
    workflow_context = {
        "workflow_id": "ingestion_bdd_workflow",
        "recording": {
            "actions": [
                {"action": "click", "selector": "#btn"},
                {"action": "fill", "selector": "#input", "value": "test"},
            ],
        },
        "steps": [],
    }

    # Step 1: Ingest
    if ingestion_agent:
        result = await ingestion_agent.run("parse", workflow_context)
        assert result is not None
        workflow_context["steps"].append("ingestion")

    # Step 2: Dedup (if available)
    if dedup_agent:
        result = await dedup_agent.run("analyze", workflow_context)
        assert result is not None
        workflow_context["steps"].append("deduplication")

    # Step 3: BDD conversion (if available)
    if bdd_agent:
        result = await bdd_agent.run("convert", workflow_context)
        assert result is not None
        workflow_context["steps"].append("bdd_conversion")

    # Workflow should complete if we found at least one skill
    if ingestion_agent or dedup_agent or bdd_agent:
        assert len(workflow_context["steps"]) >= 1
        assert workflow_context["workflow_id"] == "ingestion_bdd_workflow"


@pytest.mark.integration
def test_framework_foundation_skills_work(project_path):
    """Test that E1 framework foundation skills work together."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    e1_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.name.startswith("e1_"):
            e1_skills.append(skill)

    # Should have 5 E1 skills
    assert len(e1_skills) >= 5, f"Expected at least 5 E1 skills, found {len(e1_skills)}"

    # All E1 skills should load
    for skill in e1_skills:
        assert skill.name.startswith("e1_")
        assert skill.version
        assert skill.description


@pytest.mark.integration
def test_advanced_features_skills_work(project_path):
    """Test that E9 advanced features skills work together."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    e9_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.name.startswith("e9_"):
            e9_skills.append(skill)

    # Should have 5 E9 skills
    assert len(e9_skills) >= 5, f"Expected at least 5 E9 skills, found {len(e9_skills)}"

    # All E9 skills should load
    for skill in e9_skills:
        assert skill.name.startswith("e9_")
        assert skill.version
        assert skill.description
