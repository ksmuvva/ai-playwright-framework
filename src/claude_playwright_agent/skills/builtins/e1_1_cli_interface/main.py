"""
E1.1 - CLI Interface & Command System Skill.

This skill provides comprehensive command-line interface functionality:
- Command registration and discovery
- Argument parsing and validation
- Help system
- Output formatting with rich console
- Command execution orchestration
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class CLIInterfaceAgent(BaseAgent):
    """
    Agent for managing the CLI interface and command system.

    This agent provides:
    1. Command registration and discovery
    2. Argument parsing and validation
    3. Interactive help system
    4. Rich console output formatting
    5. Command execution orchestration
    """

    name = "e1_1_cli_interface"
    version = "1.0.0"
    description = "E1.1 - CLI Interface & Command System"

    def __init__(self, **kwargs) -> None:
        """Initialize the CLI interface agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a agent for the Playwright test automation framework. You help users with tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._commands: dict[str, Any] = {}
        self._command_groups: dict[str, list[str]] = {}


    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": str(type(self)._get_current_timestamp())
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute the CLI interface task.

        Args:
            task: Task to perform (register_command, execute_command, list_commands, etc.)
            context: Execution context containing task parameters

        Returns:
            Result of the CLI operation
        """
        task_type = context.get("task_type", task)

        if task_type == "register_command":
            return await self._register_command(context)
        elif task_type == "execute_command":
            return await self._execute_command(context)
        elif task_type == "list_commands":
            return await self._list_commands(context)
        elif task_type == "get_help":
            return await self._get_help(context)
        elif task_type == "format_output":
            return await self._format_output(context)
        else:
            return f"Unknown task type: {task_type}"

    async def _register_command(self, context: dict[str, Any]) -> str:
        """Register a new command with the CLI."""
        command_name = context.get("command_name")
        command_handler = context.get("command_handler")
        command_group = context.get("command_group", "default")

        if not command_name or not command_handler:
            return "Error: command_name and command_handler are required"

        self._commands[command_name] = {
            "handler": command_handler,
            "group": command_group,
            "description": context.get("description", ""),
        }

        if command_group not in self._command_groups:
            self._command_groups[command_group] = []
        self._command_groups[command_group].append(command_name)

        return f"Command '{command_name}' registered successfully"

    async def _execute_command(self, context: dict[str, Any]) -> str:
        """Execute a registered command."""
        command_name = context.get("command_name")
        args = context.get("args", {})

        if command_name not in self._commands:
            return f"Error: Command '{command_name}' not found"

        command = self._commands[command_name]
        handler = command["handler"]

        # Execute the command handler
        if callable(handler):
            result = handler(**args)
            return f"Command executed: {result}"
        else:
            return f"Error: Invalid handler for command '{command_name}'"

    async def _list_commands(self, context: dict[str, Any]) -> str:
        """List all registered commands."""
        group_filter = context.get("group")

        if group_filter:
            commands = [
                name for name, cmd in self._commands.items()
                if cmd.get("group") == group_filter
            ]
            return f"Commands in group '{group_filter}': {', '.join(commands)}"
        else:
            output = ["Available Commands:"]
            for group, commands in self._command_groups.items():
                output.append(f"\n{group}:")
                for cmd_name in commands:
                    cmd = self._commands[cmd_name]
                    desc = cmd.get("description", "No description")
                    output.append(f"  - {cmd_name}: {desc}")
            return "\n".join(output)

    async def _get_help(self, context: dict[str, Any]) -> str:
        """Get help for a command."""
        command_name = context.get("command_name")

        if not command_name:
            return "Usage: get_help command_name=<name>"

        if command_name not in self._commands:
            return f"Command '{command_name}' not found"

        command = self._commands[command_name]
        output = [
            f"Command: {command_name}",
            f"Description: {command.get('description', 'No description')}",
            f"Group: {command.get('group', 'default')}",
        ]
        return "\n".join(output)

    async def _format_output(self, context: dict[str, Any]) -> str:
        """Format output for display."""
        message = context.get("message", "")
        output_type = context.get("output_type", "info")

        # Format based on output type
        prefixes = {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ",
        }

        prefix = prefixes.get(output_type, "")
        return f"{prefix} {message}" if prefix else message

    def get_registered_commands(self) -> dict[str, Any]:
        """Get all registered commands."""
        return self._commands.copy()

    def get_command_groups(self) -> dict[str, list[str]]:
        """Get all command groups."""
        return self._command_groups.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

