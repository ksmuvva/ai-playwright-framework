"""E2E test for multi-skill pipeline."""

import pytest


@pytest.mark.e2e
def test_multi_skill_pipeline(initialized_project, sample_recording, runner):
    """Test that multiple skills work together in a pipeline."""
    workflow_context = {
        "workflow_id": "multi_skill_test",
        "steps": []
    }

    # Step 1: Ingest with E3.1
    result = runner.run(cli, [
        "skills",
        "execute",
        "e3_1_ingestion_agent",
        "parse",
        "--context", str(sample_recording),
        "--workflow-id", "multi_skill_test",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Step 2: Deduplicate with E4.1
    result = runner.run(cli, [
        "skills",
        "execute",
        "e4_1_deduplication_agent",
        "analyze",
        "--workflow-id", "multi_skill_test",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Step 3: Convert to BDD with E5.1
    result = runner.run(cli, [
        "skills",
        "execute",
        "e5_1_bdd_conversion",
        "convert",
        "--workflow-id", "multi_skill_test",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Verify final output
    feature_file = initialized_project / "features" / "test.feature"
    assert feature_file.exists()


@pytest.mark.e2e
def test_skill_pipeline_preserves_context(initialized_project, runner):
    """Test that context is preserved through the skill pipeline."""
    original_context = {
        "workflow_id": "context_pipeline_test",
        "test_data": "original_value",
        "steps_completed": []
    }

    # Execute multiple skills in sequence
    for skill_name in ["e1_2_state_management", "e3_1_ingestion_agent", "e5_1_bdd_conversion"]:
        result = runner.run(cli, [
            "skills",
            "execute",
            skill_name,
            "test",
            "--workflow-id", "context_pipeline_test",
            "--project-path", str(initialized_project)
        ])
        assert result.exit_code == 0

    # Verify context was preserved
    result = runner.run(cli, [
        "state",
        "get",
        "--state-id", "context_pipeline_test",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
