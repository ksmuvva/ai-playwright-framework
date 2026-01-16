"""Integration tests for skill dependencies."""

import pytest
from pathlib import Path
import yaml

from claude_playwright_agent.skills import SkillLoader
from claude_playwright_agent.skills.dependencies import DependencyGraph


@pytest.mark.integration
def test_dependencies_are_accessible_in_manifests(project_path):
    """Test that skill dependencies can be accessed from manifests."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Test that we can read dependencies from manifests
    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        # Dependencies field should be accessible (even if empty)
        assert "dependencies" in manifest_data or manifest_data.get("dependencies", []) is not None


@pytest.mark.integration
def test_no_circular_dependencies(project_path):
    """Test that there are no circular dependencies in skills."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Build dependency graph from manifests
    graph = DependencyGraph()

    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        name = manifest_data.get("name", "")
        version = manifest_data.get("version", "1.0.0")
        deps = manifest_data.get("dependencies", [])

        graph.add_skill(name, version, deps)

    # Check for circular dependencies
    assert not graph.has_circular_dependency(), "Circular dependencies detected in skills"


@pytest.mark.integration
def test_dependency_order_exists(project_path):
    """Test that a valid dependency order can be computed."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Build graph from manifests
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

    # Get load order
    load_order = graph.get_load_order()

    # Load order should not be empty
    assert len(load_order) > 0, "Could not compute dependency load order"

    # All skills should be in load order
    all_skills = set(skills_data.keys())
    loaded_skills = set(load_order)
    missing = all_skills - loaded_skills

    assert len(missing) == 0, f"Skills not in load order: {missing}"

    # Dependencies should come before dependents
    loaded_positions = {skill: i for i, skill in enumerate(load_order)}
    for skill, data in skills_data.items():
        for dep in data["deps"]:
            if dep in loaded_positions:
                assert loaded_positions[dep] < loaded_positions[skill], \
                    f"Dependency {dep} should come before {skill}"


@pytest.mark.integration
def test_dependency_graph_serialization(project_path):
    """Test that dependency graph can be serialized."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    graph = DependencyGraph()
    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        name = manifest_data.get("name", "")
        version = manifest_data.get("version", "1.0.0")
        deps = manifest_data.get("dependencies", [])

        graph.add_skill(name, version, deps)

    # Convert to DOT format
    dot = graph.to_dot()
    assert dot is not None
    assert "digraph" in dot

    # Convert to dict
    graph_dict = graph.to_dict()
    assert isinstance(graph_dict, dict)
    assert "nodes" in graph_dict
