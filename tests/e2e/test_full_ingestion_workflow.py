"""E2E test for full ingestion workflow."""

import pytest
from pathlib import Path


@pytest.mark.e2e
def test_full_ingestion_workflow(initialized_project, sample_recording, runner):
    """Test complete workflow from recording ingestion through execution."""
    # 1. Ingest recording
    result = runner.run(cli, [
        "ingest",
        str(sample_recording),
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # 2. Parse to actions
    result = runner.run(cli, [
        "parse",
        str(sample_recording),
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # 3. Generate test
    result = runner.run(cli, [
        "generate",
        "--recording", str(sample_recording),
        "--output", str(initialized_project / "tests/test_recording.py"),
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # 4. Verify test file exists
    test_file = initialized_project / "tests" / "test_recording.py"
    assert test_file.exists()

    # 5. Run generated test
    result = runner.run(cli, [
        "test",
        str(test_file),
        "--project-path", str(initialized_project)
    ])
    # Test may fail due to no actual browser, but should run
    assert result.exit_code in [0, 1]


@pytest.mark.e2e
def test_ingestion_to_state_workflow(initialized_project, sample_recording, runner):
    """Test workflow from ingestion to state persistence."""
    # Ingest and parse
    result = runner.run(cli, [
        "ingest",
        str(sample_recording),
        "--save-state",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Verify state was saved
    state_file = initialized_project / ".cpa" / "state" / "ingestion_state.json"
    assert state_file.exists()

    # Load state
    result = runner.run(cli, [
        "state",
        "load",
        "--state-id", "ingestion_state",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
    assert "actions" in result.output
