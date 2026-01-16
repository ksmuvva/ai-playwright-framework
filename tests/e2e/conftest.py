"""End-to-end tests conftixture."""

import pytest
from pathlib import Path
from click.testing import CliRunner
from claude_playwright_agent.cli import cli


@pytest.fixture
def runner():
    """Provide CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Provide temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def initialized_project(temp_project):
    """Provide an initialized project directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=str(temp_project)):
        result = runner.run(cli, ["init", "test_project"])
        assert result.exit_code == 0
        yield temp_project / "test_project"


@pytest.fixture
def sample_recording(temp_project):
    """Create a sample recording file."""
    recording_file = temp_project / "recording.json"
    recording_file.write_text("""{
  "actions": [
    {"action": "goto", "url": "https://example.com"},
    {"action": "click", "selector": "#login-button"},
    {"action": "fill", "selector": "#username", "value": "testuser"}
  ]
}""")
    return recording_file
