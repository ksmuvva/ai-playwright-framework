"""
E7.4 - Skill Lifecycle Management Skill.

This skill provides skill lifecycle management:
- Skill lifecycle state tracking
- Load/unload operations
- Dependency resolution
- Lifecycle event tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills import get_registry


class LifecycleState(str, Enum):
    """Skill lifecycle states."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"
    DEPRECATED = "deprecated"


class LifecycleEvent(str, Enum):
    """Lifecycle events."""

    REGISTER = "register"
    LOAD = "load"
    UNLOAD = "unload"
    ENABLE = "enable"
    DISABLE = "disable"
    UPDATE = "update"
    DEPRECATE = "deprecate"
    ERROR = "error"


@dataclass
class LifecycleEventRecord:
    """
    A record of a lifecycle event.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of event
        skill_name: Affected skill name
        previous_state: State before event
        next_state: State after event
        event_context: Context at event time
        timestamp: When event occurred
        result: Event result
        error: Error message if failed
    """

    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    event_type: LifecycleEvent = LifecycleEvent.REGISTER
    skill_name: str = ""
    previous_state: LifecycleState = LifecycleState.UNLOADED
    next_state: LifecycleState = LifecycleState.UNLOADED
    event_context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    result: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "skill_name": self.skill_name,
            "previous_state": self.previous_state.value,
            "next_state": self.next_state.value,
            "event_context": self.event_context,
            "timestamp": self.timestamp,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class SkillLifecycle:
    """
    Lifecycle state for a skill.

    Attributes:
        lifecycle_id: Unique lifecycle identifier
        skill_name: Name of the skill
        current_state: Current lifecycle state
        load_order: Load order number
        dependencies: List of dependencies
        dependents: List of dependent skills
        event_history: List of lifecycle events
        metadata: Additional metadata
        created_at: When lifecycle was created
        updated_at: When lifecycle was last updated
    """

    lifecycle_id: str = field(default_factory=lambda: f"lc_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    current_state: LifecycleState = LifecycleState.UNLOADED
    load_order: int = 0
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    event_history: list[LifecycleEventRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lifecycle_id": self.lifecycle_id,
            "skill_name": self.skill_name,
            "current_state": self.current_state.value,
            "load_order": self.load_order,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "event_history": [e.to_dict() for e in self.event_history],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class LifecycleContext:
    """
    Context for lifecycle operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        events_processed: Number of events processed
        skills_managed: Number of skills managed
        state_transitions: Number of state transitions
        event_history: List of events
        started_at: When context was created
        completed_at: When context was completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    events_processed: int = 0
    skills_managed: int = 0
    state_transitions: int = 0
    event_history: list[LifecycleEventRecord] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "events_processed": self.events_processed,
            "skills_managed": self.skills_managed,
            "state_transitions": self.state_transitions,
            "event_history": [e.to_dict() for e in self.event_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class SkillLifecycleManagementAgent(BaseAgent):
    """
    Skill Lifecycle Management Agent.

    This agent provides:
    1. Skill lifecycle state tracking
    2. Load/unload operations
    3. Dependency resolution
    4. Lifecycle event tracking
    """

    name = "e7_4_lifecycle_management"
    version = "1.0.0"
    description = "E7.4 - Skill Lifecycle Management"

    def __init__(self, **kwargs) -> None:
        """Initialize the lifecycle management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E7.4 - Skill Lifecycle Management agent for the Playwright test automation framework. You help users with e7.4 - skill lifecycle management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[LifecycleContext] = []
        self._lifecycle_registry: dict[str, SkillLifecycle] = {}
        self._event_history: list[LifecycleEventRecord] = []
        self._registry = get_registry()

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
        Execute lifecycle management task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the lifecycle operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "load_skill":
            return await self._load_skill(context, execution_context)
        elif task_type == "unload_skill":
            return await self._unload_skill(context, execution_context)
        elif task_type == "get_lifecycle":
            return await self._get_lifecycle(context, execution_context)
        elif task_type == "get_state":
            return await self._get_state(context, execution_context)
        elif task_type == "resolve_dependencies":
            return await self._resolve_dependencies(context, execution_context)
        elif task_type == "transition_state":
            return await self._transition_state(context, execution_context)
        elif task_type == "get_lifecycle_context":
            return await self._get_lifecycle_context(context, execution_context)
        elif task_type == "get_events":
            return await self._get_events(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _load_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Load a skill with context tracking."""
        skill_name = context.get("skill_name")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        # Get or create lifecycle
        lifecycle = self._lifecycle_registry.get(skill_name)
        if not lifecycle:
            lifecycle = SkillLifecycle(
                skill_name=skill_name,
                current_state=LifecycleState.UNLOADED,
            )
            self._lifecycle_registry[skill_name] = lifecycle

        previous_state = lifecycle.current_state

        # Create event record
        event = LifecycleEventRecord(
            event_type=LifecycleEvent.LOAD,
            skill_name=skill_name,
            previous_state=previous_state,
            event_context={
                "workflow_id": workflow_id,
            },
        )

        try:
            # Check if skill exists in registry
            skill = self._registry.get(skill_name)
            if not skill:
                lifecycle.current_state = LifecycleState.ERROR
                event.next_state = LifecycleState.ERROR
                event.error = f"Skill '{skill_name}' not found in registry"
                return f"Error: Skill '{skill_name}' not found"

            # Load skill
            lifecycle.current_state = LifecycleState.LOADED
            event.next_state = LifecycleState.LOADED
            event.result = "loaded"

            lifecycle.updated_at = datetime.now().isoformat()

            return f"Loaded skill: {skill_name}"

        finally:
            event.timestamp = datetime.now().isoformat()
            lifecycle.event_history.append(event)
            self._event_history.append(event)

    async def _unload_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Unload a skill."""
        skill_name = context.get("skill_name")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        lifecycle = self._lifecycle_registry.get(skill_name)
        if not lifecycle:
            return f"Error: Lifecycle for '{skill_name}' not found"

        previous_state = lifecycle.current_state

        event = LifecycleEventRecord(
            event_type=LifecycleEvent.UNLOAD,
            skill_name=skill_name,
            previous_state=previous_state,
            event_context={"workflow_id": workflow_id},
        )

        try:
            # Check for dependents
            if lifecycle.dependents:
                dependent_names = ", ".join(lifecycle.dependents)
                event.error = f"Cannot unload: has dependents ({dependent_names})"
                return f"Cannot unload: has dependents ({dependent_names})"

            lifecycle.current_state = LifecycleState.UNLOADED
            event.next_state = LifecycleState.UNLOADED
            event.result = "unloaded"

            lifecycle.updated_at = datetime.now().isoformat()

            return f"Unloaded skill: {skill_name}"

        finally:
            lifecycle.event_history.append(event)
            self._event_history.append(event)

    async def _get_lifecycle(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get lifecycle for a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        lifecycle = self._lifecycle_registry.get(skill_name)
        if lifecycle:
            return (
                f"Lifecycle for '{skill_name}': "
                f"state={lifecycle.current_state.value}, "
                f"{len(lifecycle.event_history)} event(s)"
            )

        return f"Error: Lifecycle for '{skill_name}' not found"

    async def _get_state(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get current state of a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        lifecycle = self._lifecycle_registry.get(skill_name)
        if lifecycle:
            return f"State: {lifecycle.current_state.value}"

        return f"State: {LifecycleState.UNLOADED.value} (no lifecycle)"

    async def _resolve_dependencies(self, context: dict[str, Any], execution_context: Any) -> str:
        """Resolve skill dependencies."""
        skill_name = context.get("skill_name")
        dependencies = context.get("dependencies", [])

        if not skill_name:
            return "Error: skill_name is required"

        lifecycle = self._lifecycle_registry.get(skill_name)
        if not lifecycle:
            lifecycle = SkillLifecycle(skill_name=skill_name)
            self._lifecycle_registry[skill_name] = lifecycle

        lifecycle.dependencies = dependencies

        return f"Dependencies for '{skill_name}': {dependencies}"

    async def _transition_state(self, context: dict[str, Any], execution_context: Any) -> str:
        """Transition skill to new state."""
        skill_name = context.get("skill_name")
        new_state = context.get("new_state")

        if not skill_name or not new_state:
            return "Error: skill_name and new_state are required"

        lifecycle = self._lifecycle_registry.get(skill_name)
        if not lifecycle:
            return f"Error: Lifecycle for '{skill_name}' not found"

        if isinstance(new_state, str):
            new_state = LifecycleState(new_state)

        previous_state = lifecycle.current_state
        lifecycle.current_state = new_state
        lifecycle.updated_at = datetime.now().isoformat()

        # Record event
        event = LifecycleEventRecord(
            event_type=LifecycleEvent.UPDATE,
            skill_name=skill_name,
            previous_state=previous_state,
            next_state=new_state,
            event_context={"transition": f"{previous_state.value} -> {new_state.value}"},
            result="transitioned",
        )

        lifecycle.event_history.append(event)
        self._event_history.append(event)

        return f"Transitioned '{skill_name}': {previous_state.value} -> {new_state.value}"

    async def _get_lifecycle_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get lifecycle context."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for lifecycle_context in self._context_history:
            if lifecycle_context.context_id == context_id:
                return (
                    f"Lifecycle context '{context_id}': "
                    f"{lifecycle_context.skills_managed} skill(s), "
                    f"{lifecycle_context.events_processed} event(s)"
                )

        return f"Error: Lifecycle context '{context_id}' not found"

    async def _get_events(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get event history."""
        skill_name = context.get("skill_name")
        limit = context.get("limit", 100)

        events = [e for e in self._event_history if not skill_name or e.skill_name == skill_name]

        return f"Events: {len(events[:limit])} found"

    def get_lifecycle_registry(self) -> dict[str, SkillLifecycle]:
        """Get lifecycle registry."""
        return self._lifecycle_registry.copy()

    def get_event_history(self) -> list[LifecycleEventRecord]:
        """Get event history."""
        return self._event_history.copy()

    def get_context_history(self) -> list[LifecycleContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

