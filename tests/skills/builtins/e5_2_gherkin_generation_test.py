"""Unit tests for E5.2 - Gherkin Generation skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e5_2_gherkin_generation import (
    GherkinDocument,
    GherkinGenerationAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestGherkinDocument:
    """Test suite for GherkinDocument dataclass."""

    @pytest.mark.unit
    def test_gherkin_document_creation(self):
        """Test creating a Gherkin document."""
        doc = GherkinDocument(
            document_id="doc_001",
            feature="Authentication",
            scenarios=["User Login", "User Logout"],
        )

        assert doc.document_id == "doc_001"
        assert doc.feature == "Authentication"
        assert len(doc.scenarios) == 2


class TestGherkinGenerationAgent:
    """Test suite for GherkinGenerationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return GherkinGenerationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e5_2_gherkin_generation"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_feature(self, agent):
        """Test generating a Gherkin feature."""
        context = {
            "task_type": "generate_feature",
            "feature_name": "Login",
            "description": "User login functionality",
        }

        result = await agent.run("generate_feature", context)

        assert "feature" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_scenario_steps(self, agent):
        """Test generating scenario steps."""
        context = {
            "task_type": "generate_steps",
            "actions": [
                {"action": "navigate", "url": "/login"},
                {"action": "fill", "selector": "#username"},
            ],
        }

        result = await agent.run("generate_steps", context)

        assert "step" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_format_gherkin(self, agent):
        """Test formatting as Gherkin."""
        context = {
            "task_type": "format_gherkin",
            "feature": "Login",
            "scenarios": ["User logs in"],
        }

        result = await agent.run("format_gherkin", context)

        assert "gherkin" in result.lower() or "feature" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
