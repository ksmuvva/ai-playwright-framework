"""Unit tests for E8.3 - CLI Help skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e8_3_cli_help import CLIHelpAgent
from claude_playwright_agent.agents.base import BaseAgent


class TestCLIHelpAgent:
    @pytest.fixture
    def agent(self):
        return CLIHelpAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e8_3_cli_help"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_help(self, agent):
        context = {"topic": "init"}
        result = await agent.run("help", context)
        assert "help" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_list_commands(self, agent):
        result = await agent.run("list_commands", {})
        assert "command" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_show_example(self, agent):
        context = {"command": "init"}
        result = await agent.run("example", context)
        assert "example" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
