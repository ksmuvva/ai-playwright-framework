"""
E1.4 - Configuration Management Skill.

This skill provides configuration management:
- Profile-based configuration
- Configuration validation
- Dynamic configuration updates
- Configuration import/export
- Environment variable overrides
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ConfigurationManagementAgent(BaseAgent):
    """
    Agent for configuration management.

    This agent provides:
    1. Profile-based configuration
    2. Configuration validation
    3. Dynamic configuration updates
    4. Configuration import/export
    5. Environment variable overrides
    """

    name = "e1_4_configuration_management"
    version = "1.0.0"
    description = "E1.4 - Configuration Management"

    def __init__(self, **kwargs) -> None:
        """Initialize the configuration management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E1.4 - Configuration Management agent for the Playwright test automation framework. You help users with e1.4 - configuration management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._config_manager = None

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
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute configuration management task.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Result of the configuration operation
        """
        from claude_playwright_agent.config import ConfigManager

        project_path = Path(context.get("project_path", "."))
        profile = context.get("profile", "default")

        if self._config_manager is None:
            self._config_manager = ConfigManager(project_path, profile=profile)

        task_type = context.get("task_type", task)

        if task_type == "get_config":
            return await self._get_config(context)
        elif task_type == "set_config":
            return await self._set_config(context)
        elif task_type == "update_config":
            return await self._update_config(context)
        elif task_type == "validate_config":
            return await self._validate_config(context)
        elif task_type == "switch_profile":
            return await self._switch_profile(context)
        elif task_type == "export_config":
            return await self._export_config(context)
        elif task_type == "import_config":
            return await self._import_config(context)
        elif task_type == "get_all_profiles":
            return await self._get_all_profiles(context)
        else:
            return f"Unknown task type: {task_type}"

    async def _get_config(self, context: dict[str, Any]) -> str:
        """Get a configuration value."""
        key = context.get("key")

        if not key:
            return "Error: key is required"

        # Navigate config hierarchy
        parts = key.split(".")
        value = self._config_manager

        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return f"Error: Configuration key '{key}' not found"

        return f"Configuration value for '{key}': {value}"

    async def _set_config(self, context: dict[str, Any]) -> str:
        """Set a configuration value."""
        key = context.get("key")
        value = context.get("value")

        if not key or value is None:
            return "Error: key and value are required"

        # Convert key dot notation to underscore notation
        key_underscore = key.replace(".", "_")
        updates = {key_underscore: value}

        self._config_manager.update(**updates)
        self._config_manager.save()

        return f"Configuration '{key}' set to '{value}'"

    async def _update_config(self, context: dict[str, Any]) -> str:
        """Update multiple configuration values."""
        updates = context.get("updates", {})

        if not updates:
            return "Error: updates dictionary is required"

        self._config_manager.update(**updates)
        self._config_manager.save()

        return f"Configuration updated with {len(updates)} change(s)"

    async def _validate_config(self, context: dict[str, Any]) -> str:
        """Validate configuration."""
        try:
            # Validate by accessing config sections
            _ = self._config_manager.framework
            _ = self._config_manager.browser
            _ = self._config_manager.execution
            _ = self._config_manager.logging
            return "Configuration is valid"
        except Exception as e:
            return f"Configuration validation failed: {e}"

    async def _switch_profile(self, context: dict[str, Any]) -> str:
        """Switch configuration profile."""
        profile = context.get("profile")

        if not profile:
            return "Error: profile is required"

        self._config_manager.set_profile(profile)
        return f"Switched to profile: {profile}"

    async def _export_config(self, context: dict[str, Any]) -> str:
        """Export configuration to file."""
        import json

        output_path = context.get("output_path", "config_export.json")

        config_data = {
            "framework": {
                "bdd_framework": self._config_manager.framework.bdd_framework.value,
                "template": self._config_manager.framework.template,
                "base_url": self._config_manager.framework.base_url,
            },
            "browser": {
                "browser": self._config_manager.browser.browser.value,
                "headless": self._config_manager.browser.headless,
            },
            "execution": {
                "parallel_workers": self._config_manager.execution.parallel_workers,
                "retry_failed": self._config_manager.execution.retry_failed,
            },
        }

        output_file = Path(output_path)
        output_file.write_text(json.dumps(config_data, indent=2))

        return f"Configuration exported to: {output_path}"

    async def _import_config(self, context: dict[str, Any]) -> str:
        """Import configuration from file."""
        import json

        input_path = context.get("input_path")

        if not input_path:
            return "Error: input_path is required"

        input_file = Path(input_path)
        if not input_file.exists():
            return f"Error: File not found: {input_path}"

        config_data = json.loads(input_file.read_text())

        # Import configuration
        for section, values in config_data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    self._config_manager.update(**{f"{section}_{key}": value})

        self._config_manager.save()

        return f"Configuration imported from: {input_path}"

    async def _get_all_profiles(self, context: dict[str, Any]) -> str:
        """Get all available profiles."""
        from claude_playwright_agent.config import PROFILES

        return f"Available profiles: {', '.join(PROFILES)}"

    def get_config_manager(self):
        """Get the underlying ConfigManager instance."""
        return self._config_manager

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

