"""E2E test for error recovery workflow."""

import pytest


@pytest.mark.e2e
def test_error_recovery_in_workflow(initialized_project, runner):
    """Test that errors are recovered from gracefully in workflows."""
    # Create a test that will fail
    test_content = '''
def test_will_fail():
    assert False, "Intentional failure for testing"
'''
    test_file = initialized_project / "tests" / "test_fail.py"
    test_file.write_text(test_content)

    # Run with error handling enabled
    result = runner.run(cli, [
        "test",
        str(test_file),
        "--continue-on-error",
        "--project-path", str(initialized_project)
    ])
    # Should not crash even with test failure
    assert result.exit_code in [0, 1]

    # Check that error was logged
    result = runner.run(cli, [
        "errors",
        "list",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_skill_error_recovery(initialized_project, runner):
    """Test that skills handle errors gracefully."""
    # Execute skill with invalid task
    result = runner.run(cli, [
        "skills",
        "execute",
        "e1_2_state_management",
        "invalid_task",
        "--project-path", str(initialized_project)
    ])
    # Should not crash
    assert result.exit_code == 0
    assert "unknown" in result.output.lower() or "error" in result.output.lower()

    # Execute skill with invalid context
    result = runner.run(cli, [
        "skills",
        "execute",
        "e1_2_state_management",
        "save",
        "--context", "{invalid json",
        "--project-path", str(initialized_project)
    ])
    # Should handle gracefully
    assert result.exit_code == 0
    assert "error" in result.output.lower() or "invalid" in result.output.lower()
