"""
State Manager - Core state management for Claude Playwright Agent.

This module implements the StateManager class which handles:
- Loading and saving state.json
- Thread-safe state operations
- Query interface for state data
- Event logging for state changes
- Atomic writes for data consistency
"""

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Final

# Cross-platform file locking
if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

from pydantic import ValidationError

from claude_playwright_agent.state.models import (
    AgentStatus,
    AgentTask,
    ComponentElement,
    FrameworkState,
    FrameworkType,
    PageObject,
    ProjectMetadata,
    Recording,
    RecordingStatus,
    Scenario,
    ExecutionRun,
    UIComponent,
)

# =============================================================================
# Constants
# =============================================================================

STATE_DIR_NAME: Final = ".cpa"
STATE_FILE_NAME: Final = "state.json"
STATE_LOCK_FILE: Final = "state.lock"
STATE_BACKUP_DIR: Final = "backups"
MAX_BACKUPS: Final = 5
MAX_EVENT_LOG_SIZE: Final = 1000


# =============================================================================
# Exceptions
# =============================================================================


class StateError(Exception):
    """Base exception for state errors."""

    pass


class StateLockError(StateError):
    """Exception raised when state lock cannot be acquired."""

    pass


class StateValidationError(StateError):
    """Exception raised when state validation fails."""

    pass


class NotInitializedError(StateError):
    """Exception raised when project is not initialized."""

    pass


# =============================================================================
# Event Logger
# =============================================================================


class StateEvent:
    """Represents a state change event."""

    def __init__(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a state event."""
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.data = data or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
        }


# =============================================================================
# State Manager
# =============================================================================


class StateManager:
    """
    Manages framework state with thread-safe operations.

    Features:
    - Atomic writes using file locking
    - Automatic backups
    - Event logging
    - Query interface
    - Thread-safe operations
    """

    def __init__(self, project_path: str | Path | None = None) -> None:
        """
        Initialize the StateManager.

        Args:
            project_path: Path to project root. Defaults to current directory.
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._state_dir = self._project_path / STATE_DIR_NAME
        self._state_file = self._state_dir / STATE_FILE_NAME
        self._lock_file = self._state_dir / STATE_LOCK_FILE
        self._backup_dir = self._state_dir / STATE_BACKUP_DIR
        self._event_log: list[StateEvent] = []
        self._event_log_lock = threading.Lock()

        # Thread lock for state operations
        self._lock = threading.Lock()

        # Ensure directories exist BEFORE loading/saving state
        self._ensure_directories()

        # Load or initialize state
        self._state: FrameworkState = self._load_or_initialize_state()

    @classmethod
    def is_initialized(cls, project_path: str | Path | None = None) -> bool:
        """
        Check if a project has been properly initialized.

        A project is considered initialized if:
        1. The .cpa directory exists
        2. The state.json file exists with valid state

        Args:
            project_path: Path to project root. Defaults to current directory.

        Returns:
            True if project is initialized, False otherwise
        """
        path = Path(project_path) if project_path else Path.cwd()
        state_dir = path / STATE_DIR_NAME
        state_file = state_dir / STATE_FILE_NAME

        # Check if state file exists
        if not state_file.exists():
            return False

        # Try to load and validate the state
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            FrameworkState(**data)
            return True
        except (json.JSONDecodeError, ValidationError, Exception):
            return False

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def _load_or_initialize_state(self) -> FrameworkState:
        """
        Load existing state or initialize new state.

        Returns:
            FrameworkState instance
        """
        if self._state_file.exists():
            try:
                return self._load_state()
            except (ValidationError, json.JSONDecodeError, StateValidationError) as e:
                # Try to load from backup
                backup = self._find_latest_backup()
                if backup:
                    try:
                        state = self._load_state_from_file(backup)
                        self._log_event(
                            "recovery",
                            "state",
                            "main",
                            {"recovered_from": str(backup)},
                        )
                        # Save recovered state
                        self._state = state
                        self.save(create_backup=False)
                        return state
                    except Exception:
                        pass

                # Initialize new state if all else fails
                state = self._initialize_state()
                self._state = state
                self.save(create_backup=False)
                return state

        # Initialize new state
        state = self._initialize_state()
        self._state = state
        self.save(create_backup=False)
        return state

    def _load_state(self) -> FrameworkState:
        """
        Load state from state file.

        Returns:
            FrameworkState instance

        Raises:
            StateValidationError: If state file is invalid
        """
        return self._load_state_from_file(self._state_file)

    def _load_state_from_file(self, file_path: Path) -> FrameworkState:
        """
        Load state from a specific file.

        Args:
            file_path: Path to state file

        Returns:
            FrameworkState instance

        Raises:
            StateValidationError: If state file is invalid
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return FrameworkState(**data)
        except (ValidationError, json.JSONDecodeError) as e:
            raise StateValidationError(f"Invalid state file {file_path}: {e}") from e
        except Exception as e:
            raise StateError(f"Failed to load state from {file_path}: {e}") from e

    def _initialize_state(self) -> FrameworkState:
        """
        Initialize new state.

        Returns:
            New FrameworkState instance
        """
        metadata = ProjectMetadata(
            name=self._project_path.name,
            created_at=datetime.now().isoformat(),
            framework_type=FrameworkType.BEHAVE,
        )

        self._log_event("initialize", "state", "main", {"project_name": metadata.name})

        return FrameworkState(project_metadata=metadata)

    # =========================================================================
    # State Persistence
    # =========================================================================

    def save(self, create_backup: bool = True) -> None:
        """
        Save state to file with atomic write.

        Args:
            create_backup: Whether to create a backup before saving

        Raises:
            StateLockError: If lock cannot be acquired
            StateError: If save fails
        """
        with self._lock:
            try:
                # Create backup if requested
                if create_backup and self._state_file.exists():
                    self._create_backup()

                # Write to temporary file first
                temp_file = self._state_file.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(self._state.model_dump_json(indent=2))

                # Atomic rename
                temp_file.replace(self._state_file)

                self._log_event("save", "state", "main")

            except OSError as e:
                raise StateError(f"Failed to save state: {e}") from e

    def _create_backup(self) -> Path:
        """
        Create a backup of the current state.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self._backup_dir / f"state_{timestamp}.json"

        # Copy current state to backup
        import shutil

        shutil.copy2(self._state_file, backup_file)

        # Clean up old backups
        self._cleanup_old_backups()

        self._log_event("backup", "state", "main", {"backup_file": str(backup_file)})

        return backup_file

    def _cleanup_old_backups(self) -> None:
        """Remove old backups keeping only MAX_BACKUPS."""
        backups = sorted(self._backup_dir.glob("state_*.json"), reverse=True)

        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()

    def _find_latest_backup(self) -> Path | None:
        """
        Find the most recent backup file.

        Returns:
            Path to latest backup or None if no backups exist
        """
        backups = list(self._backup_dir.glob("state_*.json"))
        if not backups:
            return None
        return max(backups, key=lambda p: p.stat().st_mtime)

    # =========================================================================
    # Event Logging
    # =========================================================================

    def _log_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a state change event.

        Args:
            event_type: Type of event (create, update, delete, etc.)
            entity_type: Type of entity (recording, scenario, etc.)
            entity_id: ID of the entity
            data: Additional event data
        """
        with self._event_log_lock:
            event = StateEvent(event_type, entity_type, entity_id, data)
            self._event_log.append(event)

            # Trim log if too large
            if len(self._event_log) > MAX_EVENT_LOG_SIZE:
                self._event_log = self._event_log[-MAX_EVENT_LOG_SIZE:]

    def get_events(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get events from the log.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        with self._event_log_lock:
            events = self._event_log

            if entity_type:
                events = [e for e in events if e.entity_type == entity_type]
            if entity_id:
                events = [e for e in events if e.entity_id == entity_id]

            return [e.to_dict() for e in events[-limit:]]

    # =========================================================================
    # Project Metadata
    # =========================================================================

    def get_project_metadata(self) -> ProjectMetadata:
        """Get project metadata."""
        return self._state.project_metadata

    def update_project_metadata(self, **kwargs: Any) -> None:
        """
        Update project metadata fields.

        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self._state.project_metadata, key):
                setattr(self._state.project_metadata, key, value)

        self._log_event("update", "project", "main", kwargs)
        self.save()

    # =========================================================================
    # Recordings
    # =========================================================================

    def add_recording(
        self,
        recording_id: str,
        file_path: str,
        status: RecordingStatus = RecordingStatus.PENDING,
    ) -> Recording:
        """
        Add a recording to state.

        Args:
            recording_id: Unique recording ID
            file_path: Path to recording file
            status: Initial status

        Returns:
            Created Recording instance
        """
        recording = Recording(
            recording_id=recording_id,
            file_path=file_path,
            status=status,
        )

        self._state.recordings.append(recording)
        self._log_event("create", "recording", recording_id, {"file_path": file_path})
        self.save()

        return recording

    def update_recording_status(
        self,
        recording_id: str,
        status: RecordingStatus,
        **kwargs: Any,
    ) -> None:
        """
        Update recording status and metadata.

        Args:
            recording_id: Recording ID to update
            status: New status
            **kwargs: Additional fields to update
        """
        for recording in self._state.recordings:
            if recording.recording_id == recording_id:
                recording.status = status
                for key, value in kwargs.items():
                    if hasattr(recording, key):
                        setattr(recording, key, value)

                self._log_event(
                    "update",
                    "recording",
                    recording_id,
                    {"status": status.value, **kwargs},
                )
                self.save()
                return

        raise StateError(f"Recording not found: {recording_id}")

    def get_recording(self, recording_id: str) -> Recording | None:
        """
        Get a recording by ID.

        Args:
            recording_id: Recording ID

        Returns:
            Recording instance or None
        """
        for recording in self._state.recordings:
            if recording.recording_id == recording_id:
                return recording
        return None

    def get_recordings(
        self, status: RecordingStatus | None = None, limit: int | None = None
    ) -> list[Recording]:
        """
        Get recordings, optionally filtered.

        Args:
            status: Filter by status
            limit: Maximum number to return

        Returns:
            List of Recording instances
        """
        recordings = self._state.recordings

        if status:
            recordings = [r for r in recordings if r.status == status]

        if limit:
            recordings = recordings[-limit:]

        return recordings

    def delete_recording(self, recording_id: str) -> None:
        """
        Delete a recording from state.

        Args:
            recording_id: Recording ID to delete
        """
        self._state.recordings = [
            r for r in self._state.recordings if r.recording_id != recording_id
        ]
        self._log_event("delete", "recording", recording_id)
        self.save()

    # =========================================================================
    # Scenarios
    # =========================================================================

    def add_scenario(
        self,
        scenario_id: str,
        feature_file: str,
        scenario_name: str,
        recording_source: str,
        tags: list[str] | None = None,
    ) -> Scenario:
        """
        Add a scenario to state.

        Args:
            scenario_id: Unique scenario ID
            feature_file: Feature file path
            scenario_name: Scenario name
            recording_source: Source recording ID
            tags: Scenario tags

        Returns:
            Created Scenario instance
        """
        scenario = Scenario(
            scenario_id=scenario_id,
            feature_file=feature_file,
            scenario_name=scenario_name,
            recording_source=recording_source,
            tags=tags or [],
        )

        self._state.scenarios.append(scenario)
        self._log_event(
            "create",
            "scenario",
            scenario_id,
            {"feature_file": feature_file, "recording_source": recording_source},
        )
        self.save()

        return scenario

    def get_scenario(self, scenario_id: str) -> Scenario | None:
        """
        Get a scenario by ID.

        Args:
            scenario_id: Scenario ID

        Returns:
            Scenario instance or None
        """
        for scenario in self._state.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_feature(self, feature_file: str) -> list[Scenario]:
        """
        Get all scenarios for a feature file.

        Args:
            feature_file: Feature file path

        Returns:
            List of Scenario instances
        """
        return [s for s in self._state.scenarios if s.feature_file == feature_file]

    def get_scenarios_by_recording(self, recording_id: str) -> list[Scenario]:
        """
        Get all scenarios from a recording.

        Args:
            recording_id: Source recording ID

        Returns:
            List of Scenario instances
        """
        return [s for s in self._state.scenarios if s.recording_source == recording_id]

    def get_all_scenarios(self, tag: str | None = None) -> list[Scenario]:
        """
        Get all scenarios, optionally filtered by tag.

        Args:
            tag: Filter by tag

        Returns:
            List of Scenario instances
        """
        scenarios = self._state.scenarios

        if tag:
            scenarios = [s for s in scenarios if tag in s.tags]

        return scenarios

    # =========================================================================
    # Test Runs
    # =========================================================================

    def add_test_run(
        self,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        browser: str = "chromium",
        parallel_workers: int = 1,
        report_path: str = "",
    ) -> ExecutionRun:
        """
        Add a test run to state.

        Args:
            total: Total tests run
            passed: Tests passed
            failed: Tests failed
            skipped: Tests skipped
            duration: Duration in seconds
            browser: Browser used
            parallel_workers: Number of parallel workers
            report_path: Path to generated report

        Returns:
            Created ExecutionRun instance with run_id
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        test_run = ExecutionRun(
            run_id=run_id,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            browser=browser,
            parallel_workers=parallel_workers,
            report_path=report_path,
        )

        self._state.test_runs.append(test_run)
        self._log_event(
            "create",
            "test_run",
            run_id,
            {
                "total": total,
                "passed": passed,
                "failed": failed,
                "duration": duration,
            },
        )
        self.save()

        return test_run

    def get_test_run(self, run_id: str) -> ExecutionRun | None:
        """
        Get a test run by ID.

        Args:
            run_id: Test run ID

        Returns:
            ExecutionRun instance or None
        """
        for run in self._state.test_runs:
            if run.run_id == run_id:
                return run
        return None

    def get_test_runs(self, limit: int = 10) -> list[ExecutionRun]:
        """
        Get recent test runs.

        Args:
            limit: Maximum number to return

        Returns:
            List of ExecutionRun instances
        """
        return self._state.test_runs[-limit:]

    def get_latest_test_run(self) -> ExecutionRun | None:
        """
        Get the most recent test run.

        Returns:
            ExecutionRun instance or None
        """
        if not self._state.test_runs:
            return None
        return self._state.test_runs[-1]

    # =========================================================================
    # Agent Status
    # =========================================================================

    def add_agent_task(
        self,
        agent_id: str,
        agent_type: str,
        parent_task_id: str = "",
    ) -> AgentTask:
        """
        Add an agent task to state.

        Args:
            agent_id: Unique agent ID
            agent_type: Type of agent
            parent_task_id: Parent task ID for workflows

        Returns:
            Created AgentTask instance
        """
        task = AgentTask(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.SPAWNING,
            parent_task_id=parent_task_id,
        )

        self._state.agent_status.append(task)
        self._log_event("create", "agent_task", agent_id, {"agent_type": agent_type})
        self.save()

        return task

    def update_agent_task(
        self,
        agent_id: str,
        status: AgentStatus,
        result: dict[str, Any] | None = None,
        error_message: str = "",
    ) -> None:
        """
        Update agent task status.

        Args:
            agent_id: Agent ID to update
            status: New status
            result: Task result data
            error_message: Error message if failed
        """
        for task in self._state.agent_status:
            if task.agent_id == agent_id:
                task.status = status

                if status in [AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.TIMEOUT]:
                    task.end_time = datetime.now().isoformat()

                if result is not None:
                    task.result = result

                if error_message:
                    task.error_message = error_message

                self._log_event(
                    "update",
                    "agent_task",
                    agent_id,
                    {"status": status.value, "has_error": bool(error_message)},
                )
                self.save()
                return

        raise StateError(f"Agent task not found: {agent_id}")

    def get_agent_task(self, agent_id: str) -> AgentTask | None:
        """
        Get an agent task by ID.

        Args:
            agent_id: Agent ID

        Returns:
            AgentTask instance or None
        """
        for task in self._state.agent_status:
            if task.agent_id == agent_id:
                return task
        return None

    def get_active_agents(self) -> list[AgentTask]:
        """Get all currently active agent tasks."""
        return [
            task
            for task in self._state.agent_status
            if task.status in [AgentStatus.SPAWNING, AgentStatus.RUNNING]
        ]

    def get_failed_agents(self) -> list[AgentTask]:
        """Get all failed agent tasks."""
        return [task for task in self._state.agent_status if task.status == AgentStatus.FAILED]

    # =========================================================================
    # Components and Page Objects
    # =========================================================================

    def store_components(self, components: dict[str, UIComponent]) -> None:
        """
        Store deduplicated components.

        Args:
            components: Components dictionary
        """
        self._state.components = components
        self._log_event("store", "components", "main", {"count": len(components)})
        self.save()

    def get_components(self) -> dict[str, UIComponent]:
        """Get all stored components."""
        return self._state.components

    def store_page_objects(self, page_objects: dict[str, PageObject]) -> None:
        """
        Store generated page objects.

        Args:
            page_objects: Page objects dictionary
        """
        self._state.page_objects = page_objects
        self._log_event("store", "page_objects", "main", {"count": len(page_objects)})
        self.save()

    def get_page_objects(self) -> dict[str, PageObject]:
        """Get all stored page objects."""
        return self._state.page_objects

    def add_to_selector_catalog(self, selector_id: str, element: ComponentElement) -> None:
        """
        Add an element to the selector catalog.

        Args:
            selector_id: Selector ID (typically the selector string itself)
            element: Element to add
        """
        self._state.selector_catalog[selector_id] = element
        self._log_event("add", "selector_catalog", selector_id)
        self.save()

    def get_selector_catalog(self) -> dict[str, ComponentElement]:
        """Get the entire selector catalog."""
        return self._state.selector_catalog

    # =========================================================================
    # Query Interface
    # =========================================================================

    def query(self, query: str) -> list[Any]:
        """
        Query state data using a simple query language.

        Query format: "entity_type" or "entity_type.field=value" or "entity_type.field>value"

        Examples:
            "recordings" - get all recordings
            "recordings.status=completed" - get completed recordings
            "scenarios.tags=@smoke" - get scenarios tagged with @smoke
            "test_runs.failed>0" - get failed test runs

        Args:
            query: Query string

        Returns:
            List of matching entities

        Raises:
            StateError: If query is invalid
        """
        # Check for simple entity query (no dot)
        if "." not in query:
            entity_type = query
            filter_str = ""
        else:
            parts = query.split(".", 1)
            if len(parts) != 2:
                raise StateError(f"Invalid query format: {query}")
            entity_type, filter_str = parts

        # Get entity collection
        collection_map = {
            "recordings": self._state.recordings,
            "scenarios": self._state.scenarios,
            "test_runs": self._state.test_runs,
            "agent_status": self._state.agent_status,
        }

        if entity_type not in collection_map:
            raise StateError(f"Unknown entity type: {entity_type}")

        collection = collection_map[entity_type]

        # If no filter, return all
        if not filter_str or ("=" not in filter_str and not any(
            op in filter_str for op in [">", "<", ">=", "<=", "!="]
        )):
            return collection

        # Parse filter
        field, op, value = self._parse_filter(filter_str)

        # Apply filter
        results = []
        for item in collection:
            item_value = getattr(item, field, None)
            if self._matches_filter(item_value, op, value):
                results.append(item)

        return results

    def _parse_filter(self, filter_str: str) -> tuple[str, str, Any]:
        """Parse a filter string into field, operator, and value."""
        for op in [">=", "<=", "!=", ">", "<", "="]:
            if op in filter_str:
                field, value = filter_str.split(op, 1)
                return field.strip(), op, value.strip()

        raise StateError(f"Invalid filter: {filter_str}")

    def _matches_filter(self, item_value: Any, op: str, filter_value: str) -> bool:
        """Check if an item value matches a filter."""
        # Handle enum values
        if hasattr(item_value, "value"):
            # item_value is an enum
            item_value = item_value.value

        # Type conversion
        try:
            if isinstance(item_value, int):
                filter_value = int(filter_value)
            elif isinstance(item_value, float):
                filter_value = float(filter_value)
        except (ValueError, TypeError):
            pass

        if op == "=":
            return str(item_value) == filter_value
        elif op == "!=":
            return str(item_value) != filter_value
        elif op == ">":
            return item_value is not None and item_value > filter_value
        elif op == "<":
            return item_value is not None and item_value < filter_value
        elif op == ">=":
            return item_value is not None and item_value >= filter_value
        elif op == "<=":
            return item_value is not None and item_value <= filter_value

        return False

    # =========================================================================
    # Context Tracking
    # =========================================================================

    def update_workflow_context(
        self,
        task_id: str,
        context_data: dict[str, Any],
    ) -> None:
        """
        Update workflow context in state.

        Args:
            task_id: Task identifier
            context_data: Context data dictionary
        """
        self._state.workflow_contexts[task_id] = context_data
        self._log_event("update", "workflow_context", task_id)
        self.save()

    def get_workflow_context(self, task_id: str) -> dict[str, Any] | None:
        """
        Get workflow context by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Context data dictionary or None if not found
        """
        return self._state.workflow_contexts.get(task_id)

    def update_agent_chain(
        self,
        task_id: str,
        chain_data: dict[str, Any],
    ) -> None:
        """
        Update agent execution chain in state.

        Args:
            task_id: Task identifier
            chain_data: Chain data dictionary
        """
        self._state.agent_chains[task_id] = chain_data
        self._log_event("update", "agent_chain", task_id)
        self.save()

    def get_agent_chain(self, task_id: str) -> dict[str, Any] | None:
        """
        Get agent execution chain by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Chain data dictionary or None if not found
        """
        return self._state.agent_chains.get(task_id)

    # =========================================================================
    # Export/Import
    # =========================================================================

    def export_state(
        self,
        output_path: str | Path,
        format: str = "json",
        sections: list[str] | None = None,
    ) -> None:
        """
        Export state to a file.

        Args:
            output_path: Path to export file
            format: Export format ("json" or "yaml")
            sections: Optional list of sections to export (e.g., ["recordings", "scenarios"])
                      If None, exports all sections
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get state data
        if sections:
            # Export only specified sections
            state_dict = self._state.model_dump()
            exported_data = {
                "exported_at": datetime.now().isoformat(),
                "sections": sections,
            }
            for section in sections:
                if section in state_dict:
                    exported_data[section] = state_dict[section]
        else:
            # Export full state
            exported_data = {
                "exported_at": datetime.now().isoformat(),
                "state": self._state.model_dump(),
            }

        # Write in specified format
        if format.lower() == "yaml":
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(exported_data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(exported_data, f, indent=2)

        self._log_event("export", "state", "main", {
            "output": str(output_path),
            "format": format,
            "sections": sections,
        })

    def import_state(
        self,
        input_path: str | Path,
        merge: bool = False,
        merge_strategy: str = "replace",
    ) -> None:
        """
        Import state from a file.

        Args:
            input_path: Path to import file
            merge: Whether to merge with existing state or replace
            merge_strategy: How to merge ("replace", "append", "update")
        """
        input_path = Path(input_path)

        # Detect format and load
        if input_path.suffix in (".yaml", ".yml"):
            import yaml
            with open(input_path, encoding="utf-8") as f:
                imported_data = yaml.safe_load(f)
        else:
            with open(input_path, encoding="utf-8") as f:
                imported_data = json.load(f)

        # Check if this is a partial export or full state
        if "state" in imported_data:
            # Full state export
            state_data = imported_data["state"]
        else:
            # Partial export or direct state
            state_data = imported_data

        # Load and validate state
        try:
            imported_state = FrameworkState(**state_data)
        except ValidationError as e:
            raise StateValidationError(f"Invalid state file: {e}") from e

        if merge and merge_strategy == "replace":
            # Keep existing project metadata, replace rest
            existing_metadata = self._state.project_metadata
            self._state = imported_state
            self._state.project_metadata = existing_metadata
        elif merge and merge_strategy == "append":
            # Append recordings, scenarios, test runs
            self._append_state_data(imported_state)
        elif merge and merge_strategy == "update":
            # Update existing entities by ID
            self._update_state_data(imported_state)
        else:
            # Full replace
            self._state = imported_state

        self.save()
        self._log_event("import", "state", "main", {
            "input": str(input_path),
            "merge": merge,
            "merge_strategy": merge_strategy,
        })

    def _append_state_data(self, new_state: FrameworkState) -> None:
        """
        Append new state data to existing state.

        Args:
            new_state: New state data to append
        """
        # Append recordings
        for recording in new_state.recordings_data:
            # Check if recording already exists
            existing = next(
                (r for r in self._state.recordings_data if r.recording_id == recording.recording_id),
                None,
            )
            if not existing:
                self._state.recordings_data.append(recording)

        # Append scenarios
        for scenario in new_state.scenarios:
            existing = next(
                (s for s in self._state.scenarios if s.scenario_id == scenario.scenario_id),
                None,
            )
            if not existing:
                self._state.scenarios.append(scenario)

        # Append test runs
        for run in new_state.test_runs:
            existing = next(
                (r for r in self._state.test_runs if r.run_id == run.run_id),
                None,
            )
            if not existing:
                self._state.test_runs.append(run)

    def _update_state_data(self, new_state: FrameworkState) -> None:
        """
        Update existing state data with new data by ID.

        Args:
            new_state: New state data to update with
        """
        # Update recordings
        for recording in new_state.recordings_data:
            existing = next(
                (r for r in self._state.recordings_data if r.recording_id == recording.recording_id),
                None,
            )
            if existing:
                # Update in place
                idx = self._state.recordings_data.index(existing)
                self._state.recordings_data[idx] = recording
            else:
                self._state.recordings_data.append(recording)

        # Update scenarios
        for scenario in new_state.scenarios:
            existing = next(
                (s for s in self._state.scenarios if s.scenario_id == scenario.scenario_id),
                None,
            )
            if existing:
                idx = self._state.scenarios.index(existing)
                self._state.scenarios[idx] = scenario
            else:
                self._state.scenarios.append(scenario)

        # Update test runs
        for run in new_state.test_runs:
            existing = next(
                (r for r in self._state.test_runs if r.run_id == run.run_id),
                None,
            )
            if existing:
                idx = self._state.test_runs.index(existing)
                self._state.test_runs[idx] = run
            else:
                self._state.test_runs.append(run)
