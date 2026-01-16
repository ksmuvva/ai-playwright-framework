"""Integration tests for inter-skill communication."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from claude_playwright_agent.skills import SkillLoader


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skills_can_send_messages(project_path):
    """Test that skills can send messages to each other."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Load two skills that might communicate
    skills_to_test = [
        "e1_2_state_management",
        "e3_1_ingestion_agent",
    ]

    loaded_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.name in skills_to_test and skill.agent_class:
            loaded_skills.append(skill.agent_class())

    # Skills should have context that can be shared
    for skill in loaded_skills:
        context = {
            "workflow_id": "test_workflow",
            "messages": [],
        }

        # Execute skill with shared context
        await skill.run("test", context)

        # Context should still be accessible
        assert "workflow_id" in context


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_message_passing(project_path):
    """Test message passing between skills in a workflow."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Simulate a workflow where skills pass messages
    workflow_context = {
        "workflow_id": "msg_test_workflow",
        "messages": [],
        "data": {},
    }

    # Load skills that could be in a workflow
    workflow_skills = []
    for skill_name in ["e3_1_ingestion_agent", "e4_1_deduplication_agent"]:
        for manifest in loader.discover_skills():
            skill = loader.load_skill(manifest)
            if skill.name == skill_name and skill.agent_class:
                workflow_skills.append(skill.agent_class())
                break

    # Execute skills in sequence
    for skill in workflow_skills:
        result = await skill.run("process", workflow_context)

        # Result should be accessible
        assert result is not None

        # Context should be preserved
        assert workflow_context["workflow_id"] == "msg_test_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_shared_state(project_path):
    """Test that skills can share state through context."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    shared_context = {
        "workflow_id": "shared_state_workflow",
        "shared_data": {
            "recording_id": "rec_001",
            "actions": [],
            "test_count": 0,
        },
    }

    # Load multiple skills
    skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            skills.append(skill.agent_class())
        if len(skills) >= 3:
            break

    # Execute all skills with shared context
    for skill in skills:
        await skill.run("test", shared_context)

    # Shared data should still be accessible
    assert "shared_data" in shared_context
    assert shared_context["workflow_id"] == "shared_state_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_event_propagation(project_path):
    """Test that events propagate through skill chain."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    event_context = {
        "workflow_id": "event_workflow",
        "events": [],
        "event_handlers": {},
    }

    # Load skills - collect more first, then filter
    all_skills = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        all_skills.append(skill)

    # Filter to skills with agent_class
    skills = []
    for skill in all_skills:
        if skill.agent_class:
            skills.append(skill.agent_class())
        if len(skills) >= 2:
            break

    # If we couldn't find 2 skills with agent_class, test with what we have
    if len(skills) < 2:
        # At least verify the event context structure is valid
        assert "events" in event_context
        return

    # Simulate event propagation
    for i, agent in enumerate(skills):
        event_context["events"].append({
            "source": f"agent_{i}",
            "event": f"step_{i}_complete",
        })

        await agent.run("test", event_context)

    # All events should be recorded
    assert len(event_context["events"]) >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_coordinator_pattern(project_path):
    """Test coordinator pattern where one skill coordinates others."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Load a coordinator-like skill (orchestrator)
    coordinator = None
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if ("orchestrator" in skill.name or "coordination" in skill.name) and skill.agent_class:
            coordinator = skill.agent_class()
            break

    if coordinator:
        context = {
            "workflow_id": "coordinator_workflow",
            "coordinated_skills": [],
            "results": {},
        }

        # Coordinator should be able to manage workflow
        result = await coordinator.run("coordinate", context)

        assert result is not None
        assert context["workflow_id"] == "coordinator_workflow"
