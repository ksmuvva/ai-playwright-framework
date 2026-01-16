"""E2E test for context tracking through full pipeline."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_context_tracking_e2e(initialized_project, sample_recording, runner):
    """Test that context is tracked through the entire pipeline."""
    workflow_id = "context_tracking_e2e"

    # Step 1: Ingest with context
    result = runner.run(cli, [
        "ingest",
        str(sample_recording),
        "--workflow-id", workflow_id,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Step 2: Verify context was saved
    result = runner.run(cli, [
        "context",
        "get",
        "--workflow-id", workflow_id,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
    assert "actions" in result.output

    # Step 3: Execute skill with same context
    result = runner.run(cli, [
        "skills",
        "execute",
        "e3_1_ingestion_agent",
        "parse",
        "--workflow-id", workflow_id,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Step 4: Get context history
    result = runner.run(cli, [
        "context",
        "history",
        "--workflow-id", workflow_id,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Verify multiple operations in history
    assert "ingest" in result.output.lower() or "parse" in result.output.lower()


@pytest.mark.e2e
def test_context_isolation_between_workflows(initialized_project, runner):
    """Test that context is isolated between different workflow executions."""
    # Create two workflows
    workflow_a = "workflow_isolation_a"
    workflow_b = "workflow_isolation_b"

    # Execute workflow A
    result = runner.run(cli, [
        "skills",
        "execute",
        "e1_2_state_management",
        "save",
        "--workflow-id", workflow_a,
        "--context", '{"data": "value_a"}',
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Execute workflow B
    result = runner.run(cli, [
        "skills",
        "execute",
        "e1_2_state_management",
        "save",
        "--workflow-id", workflow_b,
        "--context", '{"data": "value_b"}',
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Verify contexts are isolated
    result_a = runner.run(cli, [
        "state",
        "get",
        "--state-id", workflow_a,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    result_b = runner.run(cli, [
        "state",
        "get",
        "--state-id", workflow_b,
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Each workflow should have its own data
    assert "value_a" in result_a.output
    assert "value_b" in result_b.output
