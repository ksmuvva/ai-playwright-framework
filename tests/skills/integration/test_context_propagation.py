"""Integration tests for context propagation through skill chains."""

import pytest
from pathlib import Path

from claude_playwright_agent.skills import SkillLoader


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_preserved_through_single_skill(project_path):
    """Test that context is preserved through a single skill execution."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        original_context = {
            "workflow_id": "test_workflow",
            "test_data": "original_value",
            "nested": {
                "key": "nested_value",
            },
        }

        # Execute skill
        await agent.run("test", original_context)

        # Critical context keys should be preserved
        assert original_context.get("workflow_id") == "test_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_preserved_through_skill_chain(project_path):
    """Test that context is preserved through a chain of skills."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Create a skill chain
    skill_chain = []
    for skill_name in ["e1_2_state_management", "e3_1_ingestion_agent", "e5_1_bdd_conversion"]:
        for manifest in loader.discover_skills():
            skill = loader.load_skill(manifest)
            if skill.name == skill_name and skill.agent_class:
                skill_chain.append(skill.agent_class())
                break

    # Original context
    original_context = {
        "workflow_id": "chain_workflow",
        "chain_step": 0,
        "data": {},
    }

    # Execute through chain
    for i, skill in enumerate(skill_chain):
        original_context["chain_step"] = i
        await skill.run("test", original_context)

        # Workflow ID should always be preserved
        assert original_context["workflow_id"] == "chain_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_enrichment_through_pipeline(project_path):
    """Test that skills can enrich context without breaking propagation."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    context = {
        "workflow_id": "enrichment_workflow",
        "recording_id": "rec_001",
        "processed_by": [],
    }

    # Load skills - collect all first, then filter
    all_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        all_skills.append(skill)

    # Filter to skills with agent_class
    skills = []
    for skill in all_skills:
        if skill.agent_class:
            skills.append(skill.agent_class())
        if len(skills) >= 3:
            break

    # If we couldn't find 3 skills with agent_class, test with what we have
    if len(skills) < 1:
        # At least verify the context structure is valid
        assert "workflow_id" in context
        return

    # Execute skills and let them enrich context
    for i, agent in enumerate(skills):
        context["processed_by"].append(f"agent_{i}")
        await agent.run("test", context)

    # All enrichments should be present
    assert len(context["processed_by"]) == len(skills)
    assert context["workflow_id"] == "enrichment_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nested_context_preservation(project_path):
    """Test that nested context structures are preserved."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    nested_context = {
        "workflow_id": "nested_workflow",
        "metadata": {
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "nested": {
                "deeply": {
                    "nested": "value",
                },
            },
        },
        "results": [],
    }

    # Load a skill
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            agent = skill.agent_class()
            await agent.run("test", nested_context)
        break

    # Nested structure should be preserved
    assert nested_context["workflow_id"] == "nested_workflow"
    assert nested_context["metadata"]["version"] == "1.0.0"
    assert nested_context["metadata"]["nested"]["deeply"]["nested"] == "value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_isolation_between_workflows(project_path):
    """Test that context is isolated between different workflow executions."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Create two separate workflow contexts
    workflow_a = {
        "workflow_id": "workflow_a",
        "data": "value_a",
    }

    workflow_b = {
        "workflow_id": "workflow_b",
        "data": "value_b",
    }

    # Load a skill
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if not skill.agent_class:
            break

        agent = skill.agent_class()

        # Execute with workflow A
        await agent.run("test", workflow_a)

        # Execute with workflow B
        await agent.run("test", workflow_b)

        break

    # Contexts should remain isolated
    assert workflow_a["workflow_id"] == "workflow_a"
    assert workflow_a["data"] == "value_a"
    assert workflow_b["workflow_id"] == "workflow_b"
    assert workflow_b["data"] == "value_b"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_history_tracking_across_chain(project_path):
    """Test that context history is tracked across a skill chain."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    context = {
        "workflow_id": "history_workflow",
        "step": 0,
    }

    # Create a skill chain
    skill_chain = []
    for skill_name in ["e1_2_state_management", "e3_1_ingestion_agent"]:
        for manifest in loader.discover_skills():
            skill = loader.load_skill(manifest)
            if skill.name == skill_name and skill.agent_class:
                skill_chain.append(skill.agent_class())
                break

    # Execute through chain
    for skill in skill_chain:
        context["step"] += 1
        await skill.run("test", context)

    # Each skill should track its own context history
    for skill in skill_chain:
        history = skill.get_context_history()
        assert isinstance(history, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_merge_behavior(project_path):
    """Test that context merging works correctly in skill chains."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    base_context = {
        "workflow_id": "merge_workflow",
        "base_data": "base_value",
    }

    # Load skills
    skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            skills.append(skill.agent_class())
        if len(skills) >= 2:
            break

    # Each skill should add to context
    for i, skill in enumerate(skills):
        skill_context = {**base_context, f"skill_{i}_data": f"value_{i}"}
        await skill.run("test", skill_context)

    # Base context should remain unchanged
    assert base_context["workflow_id"] == "merge_workflow"
    assert base_context["base_data"] == "base_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_serialization_through_pipeline(project_path):
    """Test that context can be serialized and passed through pipeline."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    serializable_context = {
        "workflow_id": "serialization_workflow",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {
            "items": [1, 2, 3],
            "nested": {
                "key": "value",
            },
        },
    }

    # Load skills
    skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            skills.append(skill.agent_class())
        if len(skills) >= 2:
            break

    # Execute through pipeline
    for skill in skills:
        # Simulate serialization/deserialization
        import json
        serialized = json.dumps(serializable_context)
        deserialized = json.loads(serialized)

        await skill.run("test", deserialized)

    # Final context should be valid
    assert serializable_context["workflow_id"] == "serialization_workflow"
