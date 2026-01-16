"""
State data models for Claude Playwright Agent.

This module defines all the data models used in state management
following the state.json schema defined in STATE_SCHEMA.md.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent execution status."""
    SPAWNING = "spawning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RecordingStatus(str, Enum):
    """Recording ingestion status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FrameworkType(str, Enum):
    """Supported BDD frameworks."""
    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"


class BrowserType(str, Enum):
    """Supported browsers."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


# =============================================================================
# Project Metadata Models
# =============================================================================


class ProjectMetadata(BaseModel):
    """Project metadata stored in state."""

    name: str = Field(..., description="Project name")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format creation timestamp"
    )
    framework_type: FrameworkType = Field(
        default=FrameworkType.BEHAVE,
        description="BDD framework type"
    )
    version: str = Field(default="1.0.0", description="Framework version")
    description: str = Field(default="", description="Project description")


# =============================================================================
# Recording Models
# =============================================================================


class Recording(BaseModel):
    """Represents an ingested Playwright recording."""

    recording_id: str = Field(..., description="Unique recording ID")
    file_path: str = Field(..., description="Path to source recording file")
    ingested_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format ingestion timestamp"
    )
    status: RecordingStatus = Field(
        default=RecordingStatus.PENDING,
        description="Ingestion status"
    )
    feature_file: str = Field(default="", description="Generated feature file path")
    actions_count: int = Field(default=0, description="Number of actions extracted")
    scenarios_count: int = Field(default=0, description="Number of scenarios generated")
    error_message: str = Field(default="", description="Error message if failed")


# =============================================================================
# Scenario Models
# =============================================================================


class Scenario(BaseModel):
    """Represents a BDD scenario."""

    scenario_id: str = Field(..., description="Unique scenario ID")
    feature_file: str = Field(..., description="Feature file path")
    scenario_name: str = Field(..., description="Scenario name")
    recording_source: str = Field(..., description="Source recording ID")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format creation timestamp"
    )
    tags: list[str] = Field(default_factory=list, description="Scenario tags")
    line_number: int = Field(default=0, description="Line number in feature file")
    steps_count: int = Field(default=0, description="Number of steps")


# =============================================================================
# Test Run Models
# =============================================================================


class ExecutionRun(BaseModel):
    """Represents a test execution run."""

    run_id: str = Field(..., description="Unique test run ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format execution timestamp"
    )
    total: int = Field(default=0, description="Total tests run")
    passed: int = Field(default=0, description="Tests passed")
    failed: int = Field(default=0, description="Tests failed")
    skipped: int = Field(default=0, description="Tests skipped")
    duration: float = Field(default=0.0, description="Duration in seconds")
    browser: BrowserType = Field(default=BrowserType.CHROMIUM, description="Browser used")
    parallel_workers: int = Field(default=1, description="Number of parallel workers")
    report_path: str = Field(default="", description="Path to generated report")


# =============================================================================
# Agent Status Models
# =============================================================================


class AgentTask(BaseModel):
    """Represents an agent task status."""

    agent_id: str = Field(..., description="Unique agent ID")
    agent_type: str = Field(..., description="Agent type (e.g., 'ingestion', 'deduplication')")
    status: AgentStatus = Field(default=AgentStatus.SPAWNING, description="Agent status")
    start_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format start time"
    )
    end_time: str = Field(default="", description="ISO format end time")
    parent_task_id: str = Field(default="", description="Parent task ID for workflows")
    result: dict[str, Any] = Field(default_factory=dict, description="Task result data")
    error_message: str = Field(default="", description="Error message if failed")


# =============================================================================
# Component Models (Deduplication)
# =============================================================================


class ComponentElement(BaseModel):
    """A reusable UI component element."""

    selector: str = Field(..., description="Primary selector")
    selector_type: str = Field(..., description="Selector type (css, xpath, text, etc.)")
    fragility_score: float = Field(..., description="Fragility score (0-1, higher is more fragile)")
    usage_count: int = Field(default=1, description="Number of times used")
    recordings: list[str] = Field(default_factory=list, description="Recording IDs using this")
    alternatives: list[str] = Field(default_factory=list, description="Alternative selectors")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UIComponent(BaseModel):
    """A reusable UI component."""

    component_id: str = Field(..., description="Unique component ID")
    name: str = Field(..., description="Component name")
    component_type: str = Field(..., description="Component type (form, button_group, etc.)")
    elements: dict[str, ComponentElement] = Field(
        default_factory=dict,
        description="Component elements by name"
    )
    pages: list[str] = Field(default_factory=list, description="Pages where this appears")


# =============================================================================
# Page Object Models
# =============================================================================


class PageObject(BaseModel):
    """Generated page object class."""

    page_object_id: str = Field(..., description="Unique page object ID")
    class_name: str = Field(..., description="Generated class name")
    file_path: str = Field(..., description="Generated file path")
    url_pattern: str = Field(default="", description="URL pattern for this page")
    elements: dict[str, ComponentElement] = Field(
        default_factory=dict,
        description="Page elements by name"
    )
    methods: list[str] = Field(default_factory=list, description="Generated method names")


# =============================================================================
# Main State Model
# =============================================================================


class FrameworkState(BaseModel):
    """
    Complete framework state.

    This is the main state model that gets serialized to state.json.
    """

    project_metadata: ProjectMetadata = Field(
        default_factory=ProjectMetadata,
        description="Project metadata"
    )
    recordings: list[Recording] = Field(
        default_factory=list,
        description="Ingested recordings"
    )
    recordings_data: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Parsed recording data including actions and URLs"
    )
    scenarios: list[Scenario] = Field(
        default_factory=list,
        description="Generated scenarios"
    )
    test_runs: list["ExecutionRun"] = Field(
        default_factory=list,
        description="Test execution runs"
    )
    agent_status: list[AgentTask] = Field(
        default_factory=list,
        description="Agent task statuses"
    )
    components: dict[str, UIComponent] = Field(
        default_factory=dict,
        description="Deduplicated UI components"
    )
    page_objects: dict[str, PageObject] = Field(
        default_factory=dict,
        description="Generated page objects"
    )
    selector_catalog: dict[str, ComponentElement] = Field(
        default_factory=dict,
        description="Global selector catalog"
    )
    # Context tracking fields
    workflow_contexts: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Workflow execution contexts (task_id -> context dict)"
    )
    agent_chains: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent execution chains (task_id -> chain dict)"
    )

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "project_metadata": {
                    "name": "my-test-project",
                    "created_at": "2025-01-11T10:00:00",
                    "framework_type": "behave",
                    "version": "1.0.0"
                },
                "recordings": [],
                "scenarios": [],
                "test_runs": [],
                "agent_status": []
            }
        }

    def model_dump_json(self, **kwargs: Any) -> str:
        """Export to JSON with custom formatting."""
        kwargs.setdefault("indent", 2)
        return super().model_dump_json(**kwargs)
