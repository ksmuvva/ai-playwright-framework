"""Unit tests for E4.4 - Page Object Generation skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e4_4_page_object_generation import (
    PageObject,
    PageObjectGenerationAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestPageObject:
    """Test suite for PageObject dataclass."""

    @pytest.mark.unit
    def test_page_object_creation(self):
        """Test creating a page object."""
        page_obj = PageObject(
            object_id="page_001",
            class_name="LoginPage",
            selectors={"username": "#username", "password": "#password"},
            methods=["login", "logout"],
        )

        assert page_obj.object_id == "page_001"
        assert page_obj.class_name == "LoginPage"
        assert page_obj.selectors["username"] == "#username"
        assert "login" in page_obj.methods


class TestPageObjectGenerationAgent:
    """Test suite for PageObjectGenerationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return PageObjectGenerationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e4_4_page_object_generation"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_page_object(self, agent):
        """Test generating a page object."""
        context = {
            "task_type": "generate_page_object",
            "component": {
                "component_name": "LoginForm",
                "selectors": ["#username", "#password"],
            },
            "language": "python",
        }

        result = await agent.run("generate_page_object", context)

        assert "generated" in result.lower() or "page object" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_methods(self, agent):
        """Test generating methods for page object."""
        context = {
            "task_type": "generate_methods",
            "selectors": ["#login-btn"],
            "actions": ["click"],
        }

        result = await agent.run("generate_methods", context)

        assert "method" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_selector(self, agent):
        """Test adding a selector to page object."""
        context = {
            "task_type": "add_selector",
            "page_object_id": "page_001",
            "selector_name": "username",
            "selector_value": "#username",
        }

        result = await agent.run("add_selector", context)

        assert "added" in result.lower() or "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
