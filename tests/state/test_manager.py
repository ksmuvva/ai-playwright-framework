"""
Comprehensive tests for StateManager.

Tests cover:
- State initialization
- Recording management
- Scenario management
- Test run management
- Agent task management
- Component and page object management
- Query interface
- Event logging
- Backup and recovery
- Thread safety
"""

import json
from pathlib import Path
from threading import Thread
from time import sleep
from unittest.mock import MagicMock, patch

import pytest

from claude_playwright_agent.state import (
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
    StateError,
    StateManager,
    StateValidationError,
    ExecutionRun,
    UIComponent,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def state_manager(temp_project_dir: Path) -> StateManager:
    """Create a StateManager instance for testing."""
    return StateManager(temp_project_dir)


@pytest.fixture
def populated_state_manager(state_manager: StateManager) -> StateManager:
    """Create a StateManager with populated test data."""
    # Add recordings
    state_manager.add_recording("rec_001", "/path/to/recording1.js")
    state_manager.add_recording("rec_002", "/path/to/recording2.js", RecordingStatus.COMPLETED)

    # Add scenarios
    state_manager.add_scenario(
        "scen_001",
        "/features/login.feature",
        "Successful login",
        "rec_001",
        ["@smoke", "@auth"],
    )
    state_manager.add_scenario(
        "scen_002",
        "/features/login.feature",
        "Failed login",
        "rec_001",
        ["@negative"],
    )

    # Add test run
    state_manager.add_test_run(
        total=10, passed=8, failed=2, skipped=0, duration=45.5, browser="chromium"
    )

    return state_manager


# =============================================================================
# State Initialization Tests
# =============================================================================


class TestStateInitialization:
    """Tests for state initialization."""

    def test_initialize_new_state(self, temp_project_dir: Path) -> None:
        """Test that new state is initialized correctly."""
        manager = StateManager(temp_project_dir)

        metadata = manager.get_project_metadata()

        assert metadata.name == temp_project_dir.name
        assert metadata.framework_type == FrameworkType.BEHAVE
        assert metadata.version == "1.0.0"
        assert isinstance(metadata.created_at, str)

    def test_state_file_created(self, state_manager: StateManager) -> None:
        """Test that state.json file is created."""
        state_file = state_manager._state_file

        assert state_file.exists()

        with open(state_file, "r") as f:
            data = json.load(f)

        assert "project_metadata" in data
        assert "recordings" in data
        assert "scenarios" in data
        assert "test_runs" in data

    def test_load_existing_state(self, temp_project_dir: Path) -> None:
        """Test loading existing state from file."""
        # Create initial state
        manager1 = StateManager(temp_project_dir)
        manager1.add_recording("rec_001", "/path/test.js")

        # Create new manager that should load existing state
        manager2 = StateManager(temp_project_dir)

        recordings = manager2.get_recordings()
        assert len(recordings) == 1
        assert recordings[0].recording_id == "rec_001"

    def test_invalid_state_creates_new(self, temp_project_dir: Path) -> None:
        """Test that invalid state file creates new state."""
        # Create invalid state file
        state_dir = temp_project_dir / ".cpa"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"

        with open(state_file, "w") as f:
            f.write("invalid json {{{")

        # Should create new state
        manager = StateManager(temp_project_dir)

        metadata = manager.get_project_metadata()
        assert metadata.name == temp_project_dir.name


# =============================================================================
# Recording Management Tests
# =============================================================================


class TestRecordingManagement:
    """Tests for recording management."""

    def test_add_recording(self, state_manager: StateManager) -> None:
        """Test adding a new recording."""
        recording = state_manager.add_recording(
            "rec_001", "/path/to/recording.js", RecordingStatus.PENDING
        )

        assert recording.recording_id == "rec_001"
        assert recording.file_path == "/path/to/recording.js"
        assert recording.status == RecordingStatus.PENDING

        # Verify it's in state
        retrieved = state_manager.get_recording("rec_001")
        assert retrieved is not None
        assert retrieved.recording_id == "rec_001"

    def test_update_recording_status(self, state_manager: StateManager) -> None:
        """Test updating recording status."""
        state_manager.add_recording("rec_001", "/path/test.js")

        state_manager.update_recording_status(
            "rec_001",
            RecordingStatus.COMPLETED,
            feature_file="/features/test.feature",
            actions_count=15,
            scenarios_count=3,
        )

        recording = state_manager.get_recording("rec_001")
        assert recording.status == RecordingStatus.COMPLETED
        assert recording.feature_file == "/features/test.feature"
        assert recording.actions_count == 15
        assert recording.scenarios_count == 3

    def test_get_recordings_filtered(self, populated_state_manager: StateManager) -> None:
        """Test getting recordings filtered by status."""
        completed = populated_state_manager.get_recordings(RecordingStatus.COMPLETED)
        pending = populated_state_manager.get_recordings(RecordingStatus.PENDING)

        assert len(completed) == 1
        assert completed[0].recording_id == "rec_002"

        assert len(pending) == 1
        assert pending[0].recording_id == "rec_001"

    def test_get_recordings_with_limit(self, populated_state_manager: StateManager) -> None:
        """Test getting recordings with limit."""
        recordings = populated_state_manager.get_recordings(limit=1)

        assert len(recordings) == 1

    def test_delete_recording(self, state_manager: StateManager) -> None:
        """Test deleting a recording."""
        state_manager.add_recording("rec_001", "/path/test.js")

        assert state_manager.get_recording("rec_001") is not None

        state_manager.delete_recording("rec_001")

        assert state_manager.get_recording("rec_001") is None

    def test_update_nonexistent_recording_raises_error(self, state_manager: StateManager) -> None:
        """Test that updating nonexistent recording raises error."""
        with pytest.raises(StateError, match="Recording not found"):
            state_manager.update_recording_status("nonexistent", RecordingStatus.COMPLETED)


# =============================================================================
# Scenario Management Tests
# =============================================================================


class TestScenarioManagement:
    """Tests for scenario management."""

    def test_add_scenario(self, state_manager: StateManager) -> None:
        """Test adding a new scenario."""
        scenario = state_manager.add_scenario(
            scenario_id="scen_001",
            feature_file="/features/login.feature",
            scenario_name="Successful login",
            recording_source="rec_001",
            tags=["@smoke", "@auth"],
        )

        assert scenario.scenario_id == "scen_001"
        assert scenario.scenario_name == "Successful login"
        assert scenario.tags == ["@smoke", "@auth"]

    def test_get_scenario_by_id(self, state_manager: StateManager) -> None:
        """Test getting scenario by ID."""
        state_manager.add_scenario(
            "scen_001", "/features/test.feature", "Test scenario", "rec_001"
        )

        scenario = state_manager.get_scenario("scen_001")

        assert scenario is not None
        assert scenario.scenario_id == "scen_001"

    def test_get_scenarios_by_feature(self, populated_state_manager: StateManager) -> None:
        """Test getting scenarios by feature file."""
        scenarios = populated_state_manager.get_scenarios_by_feature("/features/login.feature")

        assert len(scenarios) == 2
        assert all(s.feature_file == "/features/login.feature" for s in scenarios)

    def test_get_scenarios_by_recording(self, populated_state_manager: StateManager) -> None:
        """Test getting scenarios by recording source."""
        scenarios = populated_state_manager.get_scenarios_by_recording("rec_001")

        assert len(scenarios) == 2
        assert all(s.recording_source == "rec_001" for s in scenarios)

    def test_get_all_scenarios_filtered_by_tag(self, populated_state_manager: StateManager) -> None:
        """Test getting scenarios filtered by tag."""
        smoke_scenarios = populated_state_manager.get_all_scenarios(tag="@smoke")
        negative_scenarios = populated_state_manager.get_all_scenarios(tag="@negative")

        assert len(smoke_scenarios) == 1
        assert smoke_scenarios[0].scenario_id == "scen_001"

        assert len(negative_scenarios) == 1
        assert negative_scenarios[0].scenario_id == "scen_002"


# =============================================================================
# Test Run Management Tests
# =============================================================================


class TestTestRunManagement:
    """Tests for test run management."""

    def test_add_test_run(self, state_manager: StateManager) -> None:
        """Test adding a test run."""
        test_run = state_manager.add_test_run(
            total=20, passed=15, failed=3, skipped=2, duration=120.5
        )

        assert test_run.total == 20
        assert test_run.passed == 15
        assert test_run.failed == 3
        assert test_run.skipped == 2
        assert test_run.duration == 120.5
        assert test_run.run_id.startswith("run_")

    def test_get_test_run(self, state_manager: StateManager) -> None:
        """Test getting a specific test run."""
        test_run = state_manager.add_test_run(
            total=10, passed=10, failed=0, skipped=0, duration=30.0
        )

        retrieved = state_manager.get_test_run(test_run.run_id)

        assert retrieved is not None
        assert retrieved.run_id == test_run.run_id

    def test_get_test_runs_with_limit(self, state_manager: StateManager) -> None:
        """Test getting test runs with limit."""
        for i in range(15):
            state_manager.add_test_run(
                total=10, passed=10, failed=0, skipped=0, duration=30.0
            )

        runs = state_manager.get_test_runs(limit=5)

        assert len(runs) == 5

    def test_get_latest_test_run(self, state_manager: StateManager) -> None:
        """Test getting the latest test run."""
        state_manager.add_test_run(total=5, passed=5, failed=0, skipped=0, duration=10.0)
        state_manager.add_test_run(total=10, passed=8, failed=2, skipped=0, duration=20.0)

        latest = state_manager.get_latest_test_run()

        assert latest is not None
        assert latest.total == 10

    def test_get_latest_test_run_when_empty(self, state_manager: StateManager) -> None:
        """Test getting latest test run when no runs exist."""
        assert state_manager.get_latest_test_run() is None


# =============================================================================
# Agent Task Management Tests
# =============================================================================


class TestAgentTaskManagement:
    """Tests for agent task management."""

    def test_add_agent_task(self, state_manager: StateManager) -> None:
        """Test adding an agent task."""
        task = state_manager.add_agent_task("agent_001", "ingestion")

        assert task.agent_id == "agent_001"
        assert task.agent_type == "ingestion"
        assert task.status == AgentStatus.SPAWNING

    def test_update_agent_task_to_completed(self, state_manager: StateManager) -> None:
        """Test updating agent task to completed."""
        state_manager.add_agent_task("agent_001", "ingestion")

        state_manager.update_agent_task(
            "agent_001",
            AgentStatus.COMPLETED,
            result={"scenarios_created": 5},
        )

        task = state_manager.get_agent_task("agent_001")

        assert task.status == AgentStatus.COMPLETED
        assert task.end_time != ""
        assert task.result == {"scenarios_created": 5}

    def test_update_agent_task_to_failed(self, state_manager: StateManager) -> None:
        """Test updating agent task to failed."""
        state_manager.add_agent_task("agent_001", "ingestion")

        state_manager.update_agent_task(
            "agent_001",
            AgentStatus.FAILED,
            error_message="Parse error: invalid JavaScript",
        )

        task = state_manager.get_agent_task("agent_001")

        assert task.status == AgentStatus.FAILED
        assert task.end_time != ""
        assert task.error_message == "Parse error: invalid JavaScript"

    def test_get_active_agents(self, state_manager: StateManager) -> None:
        """Test getting active agents."""
        state_manager.add_agent_task("agent_001", "ingestion")
        state_manager.add_agent_task("agent_002", "deduplication")

        state_manager.update_agent_task("agent_001", AgentStatus.RUNNING)
        state_manager.update_agent_task("agent_002", AgentStatus.COMPLETED)

        active = state_manager.get_active_agents()

        assert len(active) == 1
        assert active[0].agent_id == "agent_001"

    def test_get_failed_agents(self, state_manager: StateManager) -> None:
        """Test getting failed agents."""
        state_manager.add_agent_task("agent_001", "ingestion")
        state_manager.add_agent_task("agent_002", "deduplication")

        state_manager.update_agent_task("agent_001", AgentStatus.FAILED, error_message="Error 1")
        state_manager.update_agent_task("agent_002", AgentStatus.COMPLETED)

        failed = state_manager.get_failed_agents()

        assert len(failed) == 1
        assert failed[0].agent_id == "agent_001"


# =============================================================================
# Component and Page Object Tests
# =============================================================================


class TestComponentAndPageObjectManagement:
    """Tests for component and page object management."""

    def test_store_and_get_components(self, state_manager: StateManager) -> None:
        """Test storing and retrieving components."""
        component = UIComponent(
            component_id="comp_001",
            name="LoginForm",
            component_type="form",
            elements={
                "username": ComponentElement(
                    selector="#username",
                    selector_type="css",
                    fragility_score=0.2,
                    usage_count=5,
                )
            },
        )

        state_manager.store_components({"comp_001": component})

        retrieved = state_manager.get_components()

        assert "comp_001" in retrieved
        assert retrieved["comp_001"].name == "LoginForm"

    def test_store_and_get_page_objects(self, state_manager: StateManager) -> None:
        """Test storing and retrieving page objects."""
        page_object = PageObject(
            page_object_id="po_001",
            class_name="LoginPage",
            file_path="/pages/login.py",
            url_pattern="/login",
        )

        state_manager.store_page_objects({"po_001": page_object})

        retrieved = state_manager.get_page_objects()

        assert "po_001" in retrieved
        assert retrieved["po_001"].class_name == "LoginPage"

    def test_add_to_selector_catalog(self, state_manager: StateManager) -> None:
        """Test adding to selector catalog."""
        element = ComponentElement(
            selector="#email",
            selector_type="css",
            fragility_score=0.1,
            usage_count=3,
        )

        state_manager.add_to_selector_catalog("#email", element)

        catalog = state_manager.get_selector_catalog()

        assert "#email" in catalog
        assert catalog["#email"].fragility_score == 0.1


# =============================================================================
# Query Interface Tests
# =============================================================================


class TestQueryInterface:
    """Tests for query interface."""

    def test_query_all_recordings(self, populated_state_manager: StateManager) -> None:
        """Test querying all recordings."""
        results = populated_state_manager.query("recordings")

        assert len(results) == 2

    def test_query_recordings_by_status(self, populated_state_manager: StateManager) -> None:
        """Test querying recordings by status."""
        results = populated_state_manager.query("recordings.status=completed")

        assert len(results) == 1
        assert results[0].recording_id == "rec_002"

    def test_query_all_scenarios(self, populated_state_manager: StateManager) -> None:
        """Test querying all scenarios."""
        results = populated_state_manager.query("scenarios")

        assert len(results) == 2

    def test_query_test_runs_with_failed(self, populated_state_manager: StateManager) -> None:
        """Test querying test runs with failures."""
        results = populated_state_manager.query("test_runs.failed>0")

        assert len(results) == 1
        assert results[0].failed == 2

    def test_query_invalid_entity_type_raises_error(self, state_manager: StateManager) -> None:
        """Test that invalid entity type raises error."""
        with pytest.raises(StateError, match="Unknown entity type"):
            state_manager.query("invalid_entity")

    def test_query_invalid_format_raises_error(self, state_manager: StateManager) -> None:
        """Test that invalid entity type raises error."""
        with pytest.raises(StateError, match="Unknown entity type"):
            state_manager.query("invalid")


# =============================================================================
# Event Logging Tests
# =============================================================================


class TestEventLogging:
    """Tests for event logging."""

    def test_events_are_logged(self, state_manager: StateManager) -> None:
        """Test that operations are logged as events."""
        state_manager.add_recording("rec_001", "/path/test.js")

        events = state_manager.get_events(entity_type="recording", limit=10)

        assert len(events) > 0
        assert events[0]["event_type"] == "create"
        assert events[0]["entity_type"] == "recording"
        assert events[0]["entity_id"] == "rec_001"

    def test_get_events_filtered_by_type(self, populated_state_manager: StateManager) -> None:
        """Test getting events filtered by entity type."""
        recording_events = populated_state_manager.get_events(entity_type="recording")

        assert len(recording_events) > 0
        assert all(e["entity_type"] == "recording" for e in recording_events)

    def test_get_events_filtered_by_id(self, state_manager: StateManager) -> None:
        """Test getting events filtered by entity ID."""
        state_manager.add_recording("rec_001", "/path/test.js")

        events = state_manager.get_events(entity_id="rec_001")

        assert len(events) > 0
        assert all(e["entity_id"] == "rec_001" for e in events)

    def test_get_events_with_limit(self, populated_state_manager: StateManager) -> None:
        """Test getting events with limit."""
        events = populated_state_manager.get_events(limit=2)

        assert len(events) <= 2


# =============================================================================
# Backup and Recovery Tests
# =============================================================================


class TestBackupAndRecovery:
    """Tests for backup and recovery."""

    def test_backup_is_created_on_save(self, state_manager: StateManager) -> None:
        """Test that backup is created on save."""
        # Initial save creates backup on second save
        state_manager.save(create_backup=False)
        state_manager.add_recording("rec_001", "/path/test.js")

        backups = list(state_manager._backup_dir.glob("state_*.json"))

        assert len(backups) > 0

    def test_old_backups_are_cleaned(self, state_manager: StateManager) -> None:
        """Test that old backups are cleaned up."""
        # Create multiple backups
        for _ in range(10):
            state_manager.add_recording(f"rec_{_}", "/path/test.js")

        backups = list(state_manager._backup_dir.glob("state_*.json"))

        assert len(backups) <= 5  # MAX_BACKUPS


# =============================================================================
# Export/Import Tests
# =============================================================================


class TestExportImport:
    """Tests for export and import."""

    def test_export_state(self, state_manager: StateManager, tmp_path: Path) -> None:
        """Test exporting state to file."""
        state_manager.add_recording("rec_001", "/path/test.js")

        export_file = tmp_path / "exported_state.json"
        state_manager.export_state(export_file)

        assert export_file.exists()

        with open(export_file, "r") as f:
            data = json.load(f)

        # New export format wraps state in "state" key
        assert "state" in data
        # add_recording adds to "recordings" list, not "recordings_data" dict
        assert "recordings" in data["state"]
        assert len(data["state"]["recordings"]) == 1
        # Check metadata
        assert "exported_at" in data

    def test_import_state_replaces(self, temp_project_dir: Path, tmp_path: Path) -> None:
        """Test importing state replaces existing."""
        # Create export file
        manager1 = StateManager(temp_project_dir)
        manager1.add_recording("rec_001", "/path/test.js")

        export_file = tmp_path / "export.json"
        manager1.export_state(export_file)

        # Create new manager and import
        manager2 = StateManager(temp_project_dir / "project2")
        manager2.import_state(export_file, merge=False)

        recordings = manager2.get_recordings()
        assert len(recordings) == 1
        assert recordings[0].recording_id == "rec_001"


# =============================================================================
# Thread Safety Tests
# =============================================================================


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_recording_adds(self, state_manager: StateManager) -> None:
        """Test concurrent recording additions are thread-safe."""

        def add_recording(i: int) -> None:
            state_manager.add_recording(f"rec_{i:03d}", f"/path/recording_{i}.js")

        threads = [Thread(target=add_recording, args=(i,)) for i in range(50)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        recordings = state_manager.get_recordings()

        assert len(recordings) == 50

    def test_concurrent_state_updates(self, state_manager: StateManager) -> None:
        """Test concurrent state updates are thread-safe."""
        state_manager.add_recording("rec_001", "/path/test.js")

        def update_status(i: int) -> None:
            status = RecordingStatus.COMPLETED if i % 2 == 0 else RecordingStatus.PENDING
            try:
                state_manager.update_recording_status("rec_001", status)
            except StateError:
                pass  # May occur during concurrent updates

        threads = [Thread(target=update_status, args=(i,)) for i in range(20)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # State should be consistent
        recording = state_manager.get_recording("rec_001")
        assert recording is not None


# =============================================================================
# Project Metadata Tests
# =============================================================================


class TestProjectMetadata:
    """Tests for project metadata."""

    def test_get_project_metadata(self, temp_project_dir: Path) -> None:
        """Test getting project metadata."""
        manager = StateManager(temp_project_dir)

        metadata = manager.get_project_metadata()

        assert metadata.name == temp_project_dir.name
        assert metadata.framework_type == FrameworkType.BEHAVE

    def test_update_project_metadata(self, state_manager: StateManager) -> None:
        """Test updating project metadata."""
        state_manager.update_project_metadata(
            description="Test project", framework_type=FrameworkType.PYTEST_BDD
        )

        metadata = state_manager.get_project_metadata()

        assert metadata.description == "Test project"
        assert metadata.framework_type == FrameworkType.PYTEST_BDD
