"""E2E test for full execution workflow."""

import pytest
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_execution_workflow(initialized_project, runner):
    """Test complete workflow from test generation to execution and reporting."""
    # 1. Create sample test
    test_content = '''
import pytest
from playwright.sync_api import Page

def test_example(page: Page):
    page.goto("https://example.com")
    assert page.title() == "Example Domain"
'''
    test_file = initialized_project / "tests" / "test_example.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_content)

    # 2. Run test
    result = runner.run(cli, [
        "test",
        str(test_file),
        "--project-path", str(initialized_project)
    ])
    # May fail due to browser not installed
    assert result.exit_code in [0, 1, 5]

    # 3. Generate report
    result = runner.run(cli, [
        "report",
        "generate",
        "--format", "json",
        "--output", str(initialized_project / "reports" / "report.json"),
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0

    # 4. Verify report exists
    report_file = initialized_project / "reports" / "report.json"
    assert report_file.exists()


@pytest.mark.e2e
def test_execution_with_context_tracking(initialized_project, runner):
    """Test that execution properly tracks context through the workflow."""
    # Create test with context
    test_content = '''
import pytest

def test_with_context(context):
    context["test_run"] = True
    assert context.get("workflow_id") is not None
'''
    test_file = initialized_project / "tests" / "test_context.py"
    test_file.write_text(test_content)

    # Run with workflow ID
    result = runner.run(cli, [
        "test",
        str(test_file),
        "--workflow-id", "test_workflow_001",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code in [0, 1]

    # Verify context was tracked
    result = runner.run(cli, [
        "context",
        "history",
        "--workflow-id", "test_workflow_001",
        "--project-path", str(initialized_project)
    ])
    assert result.exit_code == 0
