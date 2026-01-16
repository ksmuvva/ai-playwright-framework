"""Integration tests for skill execution."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills import SkillLoader


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_all_skills_basic_task(project_path):
    """Test that all skills can execute a basic task."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    failed = []

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        try:
            # Instantiate agent if agent_class is available
            if skill.agent_class:
                agent = skill.agent_class()
                # Execute a simple task
                result = await agent.run("test_task", {})
                assert result is not None
            else:
                # Skill without agent_class - skip execution test
                pass
        except Exception as e:
            failed.append((skill.name, str(e)))

    # Most skills should handle unknown task types gracefully
    # Only truly broken skills would fail completely
    assert len(failed) == 0, f"Failed to execute {len(failed)} skills: {failed}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_preserves_context(project_path):
    """Test that skills preserve execution context."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Test with a few representative skills
    test_skills = [
        "e1_2_state_management",
        "e3_1_ingestion_agent",
        "e5_1_bdd_conversion",
    ]

    for skill_name in test_skills:
        # Find and load the skill
        for manifest in loader.discover_skills():
            skill = loader.load_skill(manifest)
            if skill.name == skill_name:
                if skill.agent_class:
                    agent = skill.agent_class()
                    # Test context preservation
                    context = {
                        "workflow_id": "test_workflow",
                        "project_path": str(project_path),
                    }

                    original_workflow_id = context["workflow_id"]
                    await agent.run("test", context)

                    # Context should be preserved
                    assert context.get("workflow_id") == original_workflow_id, \
                        f"Skill {skill_name} did not preserve context"
                break


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_error_handling(project_path):
    """Test that skills handle errors gracefully."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()

        # Test with invalid context
        try:
            result = await agent.run("invalid_task_that_should_not_exist", {})
            # Should return error message, not raise exception
            assert result is not None
            assert isinstance(result, str)
        except Exception as e:
            # Skill should not raise exception for unknown task
            raise AssertionError(f"Skill {skill.name} raised exception: {e}")


@pytest.mark.integration
def test_skill_context_history_tracking(project_path):
    """Test that skills track context history."""
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

        # Context history should be accessible
        history = agent.get_context_history()
        assert isinstance(history, list)
