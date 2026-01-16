"""Unit tests for E4.5 - Selector Catalog skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e4_5_selector_catalog import (
    SelectorCatalogAgent,
    SelectorEntry,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestSelectorEntry:
    """Test suite for SelectorEntry dataclass."""

    @pytest.mark.unit
    def test_selector_entry_creation(self):
        """Test creating a selector entry."""
        entry = SelectorEntry(
            entry_id="entry_001",
            selector="#submit-btn",
            component="LoginForm",
            page_url="https://example.com/login",
            stable=True,
        )

        assert entry.entry_id == "entry_001"
        assert entry.selector == "#submit-btn"
        assert entry.component == "LoginForm"
        assert entry.stable is True


class TestSelectorCatalogAgent:
    """Test suite for SelectorCatalogAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return SelectorCatalogAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e4_5_selector_catalog"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with catalog."""
        assert hasattr(agent, "_catalog")
        assert isinstance(agent._catalog, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_add_selector(self, agent):
        """Test adding a selector to catalog."""
        context = {
            "task_type": "add_selector",
            "selector": "#submit-btn",
            "component": "LoginForm",
        }

        result = await agent.run("add_selector", context)

        assert "added" in result.lower() or "selector" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_lookup_selector(self, agent):
        """Test looking up a selector in catalog."""
        agent._catalog["#submit-btn"] = SelectorEntry(
            entry_id="entry_001",
            selector="#submit-btn",
            component="LoginForm",
        )

        context = {
            "task_type": "lookup_selector",
            "selector": "#submit-btn",
        }

        result = await agent.run("lookup_selector", context)

        assert "LoginForm" in result or "found" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_find_similar(self, agent):
        """Test finding similar selectors."""
        context = {
            "task_type": "find_similar",
            "selector": "#submit-btn",
        }

        result = await agent.run("find_similar", context)

        assert "similar" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_export_catalog(self, agent):
        """Test exporting catalog."""
        context = {
            "task_type": "export_catalog",
            "format": "json",
        }

        result = await agent.run("export_catalog", context)

        assert "exported" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_catalog(self, agent):
        """Test getting catalog."""
        agent._catalog["#btn"] = SelectorEntry(
            entry_id="entry_001",
            selector="#btn",
            component="Test",
        )

        result = agent.get_catalog()

        assert isinstance(result, dict)
        assert "#btn" in result
