"""
E1.2 - State Management System Skill.

This skill provides comprehensive state management:
- Atomic state updates with file locking
- Automatic state backups
- State recovery and rollback
- Recording tracking and metadata
- Scenario and test run management
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class StateManagementAgent(BaseAgent):
    """
    Agent for managing framework state.

    This agent provides:
    1. Atomic state updates with file locking
    2. Automatic state backups
    3. State recovery and rollback
    4. Recording tracking and metadata
    5. Scenario and test run management
    """

    name = "e1_2_state_management"
    version = "1.0.0"
    description = "E1.2 - State Management System"

    def __init__(self, **kwargs) -> None:
        """Initialize the state management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a E1.2 - State Management System agent for the Playwright test automation framework. You help users with e1.2 - state management system tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._state_manager = None

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
        Execute state management task.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Result of the state operation
        """
        from claude_playwright_agent.state import StateManager

        project_path = Path(context.get("project_path", "."))

        if self._state_manager is None:
            self._state_manager = StateManager(project_path)

        task_type = context.get("task_type", task)

        if task_type == "add_recording":
            return await self._add_recording(context)
        elif task_type == "add_scenario":
            return await self._add_scenario(context)
        elif task_type == "add_test_run":
            return await self._add_test_run(context)
        elif task_type == "get_recordings":
            return await self._get_recordings(context)
        elif task_type == "get_scenarios":
            return await self._get_scenarios(context)
        elif task_type == "get_test_runs":
            return await self._get_test_runs(context)
        elif task_type == "create_backup":
            return await self._create_backup(context)
        elif task_type == "restore_backup":
            return await self._restore_backup(context)
        elif task_type == "get_project_metadata":
            return await self._get_project_metadata(context)
        elif task_type == "update_project_metadata":
            return await self._update_project_metadata(context)
        else:
            return f"Unknown task type: {task_type}"

    async def _add_recording(self, context: dict[str, Any]) -> str:
        """Add a recording to state."""
        recording_path = context.get("recording_path")
        recording_data = context.get("recording_data", {})

        if not recording_path:
            return "Error: recording_path is required"

        recording_id = self._state_manager.add_recording(
            Path(recording_path),
            recording_data.get("name", Path(recording_path).stem),
            recording_data.get("actions", []),
        )

        return f"Recording '{recording_id}' added to state"

    async def _add_scenario(self, context: dict[str, Any]) -> str:
        """Add a scenario to state."""
        scenario_data = context.get("scenario_data", {})

        if not scenario_data:
            return "Error: scenario_data is required"

        scenario_id = self._state_manager.add_scenario(
            scenario_data.get("feature"),
            scenario_data.get("scenario_name"),
            scenario_data.get("steps", []),
            scenario_data.get("recording_id"),
            scenario_data.get("tags", []),
        )

        return f"Scenario '{scenario_id}' added to state"

    async def _add_test_run(self, context: dict[str, Any]) -> str:
        """Add a test run to state."""
        run_data = context.get("run_data", {})

        test_run_id = self._state_manager.add_test_run(
            run_data.get("total", 0),
            run_data.get("passed", 0),
            run_data.get("failed", 0),
            run_data.get("skipped", 0),
            run_data.get("duration", 0),
        )

        return f"Test run '{test_run_id}' added to state"

    async def _get_recordings(self, context: dict[str, Any]) -> str:
        """Get all recordings from state."""
        recordings = self._state_manager.get_recordings()
        return f"Found {len(recordings)} recording(s)"

    async def _get_scenarios(self, context: dict[str, Any]) -> str:
        """Get scenarios from state."""
        scenario_id = context.get("scenario_id")

        if scenario_id:
            scenario = self._state_manager.get_scenario(scenario_id)
            return f"Scenario: {scenario.scenario_name if scenario else 'Not found'}"
        else:
            scenarios = self._state_manager.get_all_scenarios()
            return f"Found {len(scenarios)} scenario(s)"

    async def _get_test_runs(self, context: dict[str, Any]) -> str:
        """Get test runs from state."""
        limit = context.get("limit", 100)
        runs = self._state_manager.get_test_runs(limit=limit)
        return f"Found {len(runs)} test run(s)"

    async def _create_backup(self, context: dict[str, Any]) -> str:
        """Create a state backup."""
        backup_path = self._state_manager.create_backup()
        return f"Backup created at: {backup_path}"

    async def _restore_backup(self, context: dict[str, Any]) -> str:
        """Restore a state backup."""
        backup_path = context.get("backup_path")

        if not backup_path:
            return "Error: backup_path is required"

        self._state_manager.restore_backup(Path(backup_path))
        return f"State restored from: {backup_path}"

    async def _get_project_metadata(self, context: dict[str, Any]) -> str:
        """Get project metadata."""
        metadata = self._state_manager.get_project_metadata()
        return f"Project: {metadata.name} (v{metadata.version})"

    async def _update_project_metadata(self, context: dict[str, Any]) -> str:
        """Update project metadata."""
        self._state_manager.update_project_metadata(
            name=context.get("name"),
            framework_type=context.get("framework_type"),
        )
        return "Project metadata updated"

    def get_state_manager(self):
        """Get the underlying StateManager instance."""
        return self._state_manager

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

