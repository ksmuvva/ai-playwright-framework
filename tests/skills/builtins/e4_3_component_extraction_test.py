"""Unit tests for E4.3 - Component Extraction skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e4_3_component_extraction import (
    Component,
    ComponentExtractionAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestComponent:
    """Test suite for Component dataclass."""

    @pytest.mark.unit
    def test_component_creation(self):
        """Test creating a component."""
        component = Component(
            component_id="comp_001",
            component_name="LoginForm",
            selectors=["#username", "#password", "#login-btn"],
            page_url="https://example.com/login",
        )

        assert component.component_id == "comp_001"
        assert component.component_name == "LoginForm"
        assert len(component.selectors) == 3


class TestComponentExtractionAgent:
    """Test suite for ComponentExtractionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ComponentExtractionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e4_3_component_extraction"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_extract_components(self, agent):
        """Test extracting components from selectors."""
        context = {
            "task_type": "extract_components",
            "selectors": [
                "#username",
                "#password",
                "#login-btn",
            ],
            "page_url": "https://example.com/login",
        }

        result = await agent.run("extract_components", context)

        assert "component" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_identify_component_boundaries(self, agent):
        """Test identifying component boundaries."""
        context = {
            "task_type": "identify_boundaries",
            "selectors": ["#header-logo", "#nav-menu", "#content"],
        }

        result = await agent.run("identify_boundaries", context)

        assert "boundary" in result.lower() or "component" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_naming_component(self, agent):
        """Test naming a component."""
        context = {
            "task_type": "name_component",
            "selectors": ["#username", "#password", "#login-btn"],
        }

        result = await agent.run("name_component", context)

        assert "name" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
