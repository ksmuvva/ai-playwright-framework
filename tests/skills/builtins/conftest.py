"""Shared fixtures for skill unit tests."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import Any

from claude_playwright_agent.skills import SkillLoader
from claude_playwright_agent.state import StateManager


@pytest.fixture
def project_path():
    """Provide test project path."""
    return Path.cwd()


@pytest.fixture
def temp_project_path(tmp_path):
    """Provide temporary project path."""
    return tmp_path


@pytest.fixture
def skill_loader(project_path):
    """Provide skill loader instance."""
    return SkillLoader(project_path=project_path, include_builtins=True)


@pytest.fixture
def mock_execution_context():
    """Provide mock execution context."""
    return {
        "task_id": "test_task_001",
        "workflow_id": "test_workflow_001",
        "project_path": str(Path.cwd()),
        "recording_id": "test_recording_001",
    }


@pytest.fixture
def mock_task_context(mock_execution_context):
    """Provide mock task context."""
    return {
        **mock_execution_context,
        "created_at": "2024-01-01T00:00:00Z",
        "metadata": {
            "test_name": "unit_test",
            "test_type": "skill_test",
        },
    }


@pytest.fixture
def state_manager(temp_project_path):
    """Provide StateManager instance with temporary path."""
    return StateManager(temp_project_path)


@pytest.fixture
def mock_async_result():
    """Provide mock async result."""
    result = MagicMock()
    result.status = "completed"
    result.data = {"test": "data"}
    result.context = {"workflow_id": "test_workflow_001"}
    return result


@pytest.fixture
async def mock_agent_response():
    """Provide mock agent response."""
    return "Test operation completed successfully"


@pytest.fixture
def sample_recording_data():
    """Provide sample recording data."""
    return {
        "recording_id": "test_recording_001",
        "title": "Test Login Flow",
        "file_path": "/tmp/test_recording.js",
        "actions": [
            {
                "action_id": "act_001",
                "action_type": "navigate",
                "url": "https://example.com/login",
                "line_number": 1,
            },
            {
                "action_id": "act_002",
                "action_type": "fill",
                "selector": "#username",
                "value": "testuser",
                "line_number": 2,
            },
        ],
    }


@pytest.fixture
def sample_scenario_data():
    """Provide sample BDD scenario data."""
    return {
        "scenario_id": "scenario_001",
        "name": "User Login",
        "feature": "Authentication",
        "steps": [
            {
                "step_id": "step_001",
                "keyword": "Given",
                "text": "the user is on the login page",
            },
            {
                "step_id": "step_002",
                "keyword": "When",
                "text": "the user enters valid credentials",
            },
            {
                "step_id": "step_003",
                "keyword": "Then",
                "text": "the user should be logged in",
            },
        ],
    }


@pytest.fixture
def sample_element_context():
    """Provide sample element context."""
    return {
        "recording_id": "test_recording_001",
        "page_url": "https://example.com/login",
        "action_type": "fill",
        "line_number": 2,
        "element_index": 0,
        "value": "testuser",
    }


@pytest.fixture
def skill_manifest_path(temp_project_path):
    """Provide a skill manifest path in temp directory."""
    skill_dir = temp_project_path / "skills" / "test_skill"
    skill_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = skill_dir / "skill.yaml"
    return manifest_path


@pytest.fixture
def sample_skill_manifest():
    """Provide sample skill manifest content."""
    return """
name: test_skill
version: 1.0.0
description: A test skill for unit testing

author: Test Author
license: MIT

python_dependencies: []
dependencies: []

tags:
  - test
  - example

capabilities:
  - test_capability

settings:
  enabled: true
"""


@pytest.fixture
def mock_base_agent():
    """Provide mock BaseAgent with common attributes."""
    agent = MagicMock()
    agent.name = "test_skill"
    agent.version = "1.0.0"
    agent.description = "Test skill for unit testing"
    agent._context_history = []
    agent.run = AsyncMock(return_value="Test completed")
    return agent


@pytest.fixture
def sample_workflow_context():
    """Provide sample workflow context for multi-skill tests."""
    return {
        "workflow_id": "workflow_test_001",
        "project_path": str(Path.cwd()),
        "started_at": "2024-01-01T00:00:00Z",
        "skills_executed": [],
        "context_chain": [],
        "metadata": {
            "workflow_type": "test_workflow",
            "test_mode": True,
        },
    }


@pytest.fixture
def mock_skill_registry():
    """Provide mock skill registry."""
    return {}


@pytest.fixture
def mock_context_history():
    """Provide mock context history list."""
    return []


# Pytest markers configuration


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit test")
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "e2e: End-to-end test")
    config.addinivalue_line("markers", "slow: Slow running test")
    config.addinivalue_line("markers", "requires_network: Test requires network access")


# Helper functions for tests


def create_mock_agent(
    name: str = "test_agent",
    version: str = "1.0.0",
    description: str = "Test agent",
) -> MagicMock:
    """Create a mock agent with specified attributes."""
    agent = MagicMock()
    agent.name = name
    agent.version = version
    agent.description = description
    agent._context_history = []
    agent.run = AsyncMock(return_value="Operation completed")
    return agent


def assert_base_agent_attributes(agent, expected_name, expected_version):
    """Assert that agent has required BaseAgent attributes."""
    assert hasattr(agent, "name")
    assert hasattr(agent, "version")
    assert hasattr(agent, "description")
    assert agent.name == expected_name
    assert agent.version == expected_version


def assert_context_preserved(context, required_keys):
    """Assert that required context keys are preserved."""
    for key in required_keys:
        assert key in context, f"Context key '{key}' was lost"
