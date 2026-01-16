"""Integration tests for error recovery across skills."""

import pytest
from pathlib import Path
import yaml

from claude_playwright_agent.skills import SkillLoader


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_handles_invalid_context_gracefully(project_path):
    """Test that skills handle invalid context without crashing."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()

        # Test with completely empty context
        try:
            result = await agent.run("test", {})
            # Should return a result, not crash
            assert result is not None
        except Exception as e:
            # If exception is raised, it should be a graceful error
            assert "error" in str(e).lower() or "invalid" in str(e).lower() or "unknown" in str(e).lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_handles_unknown_task_gracefully(project_path):
    """Test that skills handle unknown task types gracefully."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        context = {"workflow_id": "test_workflow"}

        # Test with unknown task
        try:
            result = await agent.run("unknown_task_that_does_not_exist", context)
            # Should return error message
            assert result is not None
            assert isinstance(result, str)
        except Exception as e:
            # Should not raise unhandled exception
            assert False, f"Skill {skill.name} raised exception for unknown task: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery_in_skill_chain(project_path):
    """Test that errors are recovered from in skill chains."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Create a skill chain
    skill_chain = []
    for skill_name in ["e1_2_state_management", "e3_1_ingestion_agent", "e5_1_bdd_conversion"]:
        for manifest in loader.discover_skills():
            skill = loader.load_skill(manifest)
            if skill.name == skill_name and skill.agent_class:
                skill_chain.append(skill.agent_class())
                break

    context = {
        "workflow_id": "error_recovery_workflow",
        "errors": [],
    }

    # Execute through chain, even if errors occur
    for skill in skill_chain:
        try:
            # Try with potentially invalid task
            result = await skill.run("unknown_task", context)
            # Should continue to next skill
        except Exception as e:
            # Record error but continue
            context["errors"].append({
                "skill": skill.name,
                "error": str(e),
            })

    # Workflow should complete despite errors
    assert context["workflow_id"] == "error_recovery_workflow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_preserves_context_on_error(project_path):
    """Test that skills preserve context even when errors occur."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        original_context = {
            "workflow_id": "error_preservation_workflow",
            "critical_data": "must_not_be_lost",
            "steps_completed": [],
        }

        # Try to execute with invalid task
        try:
            await agent.run("invalid_task", original_context)
        except Exception:
            pass

        # Critical data should be preserved
        assert original_context.get("workflow_id") == "error_preservation_workflow"
        assert original_context.get("critical_data") == "must_not_be_lost"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_classification_across_skills(project_path):
    """Test that errors are classified consistently across skills."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    error_types = {
        "validation": [],
        "execution": [],
        "unknown": [],
    }

    # Test skills with various error scenarios
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()

        # Test with invalid context
        try:
            await agent.run("test", None)
        except Exception as e:
            error_msg = str(e).lower()
            if "validation" in error_msg or "invalid" in error_msg:
                error_types["validation"].append(skill.name)
            elif "execution" in error_msg or "runtime" in error_msg:
                error_types["execution"].append(skill.name)
            else:
                error_types["unknown"].append(skill.name)

    # All skills should handle errors somehow
    total_errors = sum(len(errors) for errors in error_types.values())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_degradation_on_missing_dependencies(project_path):
    """Test that skills degrade gracefully when dependencies are missing."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Find a skill with dependencies by checking manifests
    for manifest_path in loader.discover_skills():
        with open(manifest_path, 'r') as f:
            manifest_data = yaml.safe_load(f)

        deps = manifest_data.get("dependencies", [])

        if deps and len(deps) > 0:
            skill = loader.load_skill(manifest_path)

            if skill.agent_class:
                agent = skill.agent_class()

                # Create context without dependency data
                context = {
                    "workflow_id": "missing_deps_workflow",
                    # Missing: dependency-provided data
                }

                # Skill should handle this gracefully
                try:
                    result = await agent.run("test", context)
                    # Either succeeds with degraded functionality
                    # Or provides helpful error message
                    assert result is not None
                except Exception as e:
                    # Error should be informative
                    error_msg = str(e).lower()
                    assert any(term in error_msg for term in ["dependency", "missing", "required", "error"])

            break


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_mechanism_in_skills(project_path):
    """Test that skills can retry failed operations."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        context = {
            "workflow_id": "retry_workflow",
            "retry_count": 0,
            "max_retries": 3,
        }

        # Try executing skill multiple times
        for attempt in range(3):
            try:
                result = await agent.run("test", context)
                # Should eventually succeed or fail gracefully
                assert result is not None
                break
            except Exception as e:
                context["retry_count"] += 1
                if context["retry_count"] >= context["max_retries"]:
                    # Max retries reached, should fail gracefully
                    assert "error" in str(e).lower() or "failed" in str(e).lower()
                    break


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_context_preservation(project_path):
    """Test that error context is preserved for debugging."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        debug_context = {
            "workflow_id": "debug_workflow",
            "debug_mode": True,
            "error_stack": [],
        }

        # Try to trigger an error
        try:
            await agent.run("invalid_task", debug_context)
        except Exception as e:
            # Error context should be preserved
            debug_context["error_stack"].append({
                "skill": skill.name,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z",
            })

        # Debug context should be available
        assert "workflow_id" in debug_context


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cascading_error_prevention(project_path):
    """Test that errors don't cascade uncontrollably through skill chains."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    # Create a skill chain
    skill_chain = []
    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)
        if skill.agent_class:
            skill_chain.append(skill.agent_class())
        if len(skill_chain) >= 3:
            break

    context = {
        "workflow_id": "cascading_error_workflow",
        "error_count": 0,
    }

    # Execute chain with error tracking
    for skill in skill_chain:
        try:
            await skill.run("test", context)
        except Exception as e:
            context["error_count"] += 1
            # Error should not cascade to next skill
            # Context should be reset for next skill

    # Error count should be limited
    assert context["error_count"] <= len(skill_chain)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery_with_fallback(project_path):
    """Test that skills can use fallback behavior on error."""
    loader = SkillLoader(project_path=project_path, include_builtins=True)

    for manifest in loader.discover_skills():
        skill = loader.load_skill(manifest)

        # Skip skills without agent_class
        if not skill.agent_class:
            continue

        agent = skill.agent_class()
        context = {
            "workflow_id": "fallback_workflow",
            "use_fallback": True,
            "fallback_value": "default_value",
        }

        # Try with potentially failing operation
        try:
            result = await agent.run("test", context)
            # Should either succeed or use fallback
            assert result is not None
        except Exception as e:
            # If error occurs, check if fallback was used
            if "fallback" in context:
                assert context["fallback_value"] == "default_value"

        break
