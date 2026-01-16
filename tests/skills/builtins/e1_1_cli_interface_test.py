"""Unit tests for E1.1 - CLI Interface skill."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e1_1_cli_interface import (
    CLIInterfaceAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestCLIInterfaceAgent:
    """Test suite for CLIInterfaceAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return CLIInterfaceAgent()

    @pytest.fixture
    def mock_command_handler(self):
        """Create mock command handler."""
        return MagicMock(return_value="Handler executed")

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert hasattr(agent, "description")
        assert agent.name == "e1_1_cli_interface"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        """Verify agent initializes with empty command registry."""
        assert hasattr(agent, "_commands")
        assert hasattr(agent, "_command_groups")
        assert agent._commands == {}
        assert agent._command_groups == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_command(self, agent, mock_command_handler):
        """Test registering a command."""
        context = {
            "command_name": "test_command",
            "command_handler": mock_command_handler,
            "command_group": "test_group",
            "description": "Test command description",
        }

        result = await agent.run("register_command", context)

        assert "registered successfully" in result.lower()
        assert "test_command" in agent._commands
        assert "test_group" in agent._command_groups

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_command_missing_params(self, agent):
        """Test registering a command with missing parameters."""
        context = {
            "command_name": "test_command",
            # Missing command_handler
        }

        result = await agent.run("register_command", context)

        assert "error" in result.lower()
        assert "test_command" not in agent._commands

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_execute_command(self, agent, mock_command_handler):
        """Test executing a registered command."""
        # First register the command
        agent._commands["test_cmd"] = {
            "handler": mock_command_handler,
            "group": "test",
            "description": "Test",
        }

        context = {
            "command_name": "test_cmd",
            "args": {"arg1": "value1"},
        }

        result = await agent.run("execute_command", context)

        assert "executed" in result.lower()
        mock_command_handler.assert_called_once_with(arg1="value1")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_execute_command_not_found(self, agent):
        """Test executing a non-existent command."""
        context = {
            "command_name": "nonexistent_cmd",
        }

        result = await agent.run("execute_command", context)

        assert "not found" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_list_commands_empty(self, agent):
        """Test listing commands when none registered."""
        context = {}

        result = await agent.run("list_commands", context)

        assert "available commands" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_list_commands_with_commands(self, agent):
        """Test listing commands with registered commands."""
        agent._commands = {
            "cmd1": {"handler": lambda: None, "group": "group1", "description": "Command 1"},
            "cmd2": {"handler": lambda: None, "group": "group1", "description": "Command 2"},
        }
        agent._command_groups = {
            "group1": ["cmd1", "cmd2"],
        }

        context = {}
        result = await agent.run("list_commands", context)

        assert "cmd1" in result
        assert "cmd2" in result
        assert "group1" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_list_commands_by_group(self, agent):
        """Test listing commands filtered by group."""
        agent._commands = {
            "cmd1": {"handler": lambda: None, "group": "group1", "description": "Command 1"},
            "cmd2": {"handler": lambda: None, "group": "group2", "description": "Command 2"},
        }
        agent._command_groups = {
            "group1": ["cmd1"],
            "group2": ["cmd2"],
        }

        context = {"group": "group1"}
        result = await agent.run("list_commands", context)

        assert "cmd1" in result
        assert "cmd2" not in result
        assert "group1" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_help(self, agent):
        """Test getting help for a command."""
        agent._commands["test_cmd"] = {
            "handler": lambda: None,
            "group": "test_group",
            "description": "Test command description",
        }

        context = {"command_name": "test_cmd"}
        result = await agent.run("get_help", context)

        assert "test_cmd" in result
        assert "test command description" in result.lower()
        assert "test_group" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_help_missing_name(self, agent):
        """Test getting help without command name."""
        context = {}
        result = await agent.run("get_help", context)

        assert "usage" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_get_help_command_not_found(self, agent):
        """Test getting help for non-existent command."""
        context = {"command_name": "nonexistent"}
        result = await agent.run("get_help", context)

        assert "not found" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_format_output_info(self, agent):
        """Test formatting info output."""
        context = {
            "message": "Test message",
            "output_type": "info",
        }

        result = await agent.run("format_output", context)

        assert "Test message" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_format_output_success(self, agent):
        """Test formatting success output."""
        context = {
            "message": "Success message",
            "output_type": "success",
        }

        result = await agent.run("format_output", context)

        assert "Success message" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_format_output_error(self, agent):
        """Test formatting error output."""
        context = {
            "message": "Error message",
            "output_type": "error",
        }

        result = await agent.run("format_output", context)

        assert "Error message" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_registered_commands(self, agent):
        """Test getting registered commands."""
        agent._commands = {"cmd1": {"handler": lambda: None}}

        commands = agent.get_registered_commands()

        assert commands == agent._commands
        assert commands is not agent._commands  # Should be a copy

    @pytest.mark.unit
    def test_get_command_groups(self, agent):
        """Test getting command groups."""
        agent._command_groups = {"group1": ["cmd1"]}

        groups = agent.get_command_groups()

        assert groups == agent._command_groups
        assert groups is not agent._command_groups  # Should be a copy
