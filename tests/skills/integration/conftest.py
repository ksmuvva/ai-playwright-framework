"""Integration tests conftest."""

import pytest
from pathlib import Path


@pytest.fixture
def project_path():
    """Provide project path for integration tests."""
    return Path.cwd()


@pytest.fixture
def temp_project_path(tmp_path):
    """Provide temporary project path."""
    return tmp_path


@pytest.fixture
def sample_recording(temp_project_path):
    """Create a sample recording file."""
    recording_file = temp_project_path / "test_recording.js"
    recording_file.write_text("""
module.exports = {
    actions: [
        {
            action: "click",
            selector: "#login-btn",
        },
        {
            action: "fill",
            selector: "#username",
            value: "testuser",
        },
    ],
};
""")
    return recording_file
