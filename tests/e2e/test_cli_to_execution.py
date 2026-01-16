"""E2E test for CLI to execution workflow."""

import pytest


@pytest.mark.e2e
def test_cli_init_to_test_workflow(temp_project, runner):
    """Test complete workflow from CLI init to test execution."""
    # 1. Initialize project
    result = runner.run(cli, [
        "init",
        "my_test_project",
        "--project-path", str(temp_project)
    ])
    assert result.exit_code == 0

    project_path = temp_project / "my_test_project"
    assert project_path.exists()

    # 2. Create a simple test
    test_content = '''
def test_example():
    assert True
'''
    test_file = project_path / "tests" / "test_example.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_content)

    # 3. Run test via CLI
    result = runner.run(cli, [
        "test",
        str(test_file),
        "--project-path", str(project_path)
    ])
    assert result.exit_code == 0

    # 4. Check status
    result = runner.run(cli, [
        "status",
        "--project-path", str(project_path)
    ])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_cli_skill_commands_workflow(initialized_project, runner):
    """Test CLI skill commands work end-to-end."""
    # List skills
    result = runner.run(cli, [
        "skills",
        "list",
        "--format", "compact",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
    assert "e1_1" in result.output

    # Describe a skill
    result = runner.run(cli, [
        "skills",
        "describe",
        "e1_2_state_management",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
    assert "State Management" in result.output

    # Show dependency tree
    result = runner.run(cli, [
        "skills",
        "tree",
        "--format", "text",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # Execute a skill
    result = runner.run(cli, [
        "skills",
        "execute",
        "e1_2_state_management",
        "test",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
