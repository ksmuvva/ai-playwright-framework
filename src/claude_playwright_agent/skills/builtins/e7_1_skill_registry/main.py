"""
E7.1 - Skill Registry System Skill.

This skill provides skill registry functionality:
- Skill registration with context
- Skill lookup and retrieval
- Enable/disable operations
- Registry state tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills import Skill, get_registry


class SkillStatus(str, Enum):
    """Skill lifecycle status."""

    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNREGISTERED = "unregistered"
    ERROR = "error"


@dataclass
class RegistryEntry:
    """
    An entry in the skill registry.

    Attributes:
        entry_id: Unique entry identifier
        skill_name: Name of the skill
        skill_version: Version of the skill
        skill_path: Path to skill directory
        status: Current status
        registration_context: Context at registration time
        enabled: Whether skill is enabled
        registered_at: When skill was registered
        last_modified: When entry was last modified
        metadata: Additional metadata
    """

    entry_id: str = field(default_factory=lambda: f"entry_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    skill_version: str = ""
    skill_path: str = ""
    status: SkillStatus = SkillStatus.REGISTERED
    registration_context: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "skill_path": self.skill_path,
            "status": self.status.value,
            "registration_context": self.registration_context,
            "enabled": self.enabled,
            "registered_at": self.registered_at,
            "last_modified": self.last_modified,
            "metadata": self.metadata,
        }


@dataclass
class RegistryOperation:
    """
    A registry operation with context.

    Attributes:
        operation_id: Unique operation identifier
        operation_type: Type of operation
        skill_name: Affected skill name
        operation_context: Context at operation time
        result: Operation result
        timestamp: When operation occurred
        error: Error message if failed
    """

    operation_id: str = field(default_factory=lambda: f"op_{uuid.uuid4().hex[:8]}")
    operation_type: str = ""
    skill_name: str = ""
    operation_context: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "skill_name": self.skill_name,
            "operation_context": self.operation_context,
            "result": self.result,
            "timestamp": self.timestamp,
            "error": self.error,
        }


@dataclass
class RegistryContext:
    """
    Context for registry operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        operations_performed: Number of operations performed
        skills_registered: Number of skills registered
        skills_enabled: Number of skills enabled
        skills_disabled: Number of skills disabled
        operation_history: List of operations
        started_at: When context was created
        completed_at: When context was completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    operations_performed: int = 0
    skills_registered: int = 0
    skills_enabled: int = 0
    skills_disabled: int = 0
    operation_history: list[RegistryOperation] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "operations_performed": self.operations_performed,
            "skills_registered": self.skills_registered,
            "skills_enabled": self.skills_enabled,
            "skills_disabled": self.skills_disabled,
            "operation_history": [op.to_dict() for op in self.operation_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class SkillRegistryAgent(BaseAgent):
    """
    Skill Registry System Agent.

    This agent provides:
    1. Skill registration with context
    2. Skill lookup and retrieval
    3. Enable/disable operations
    4. Registry state tracking
    """

    name = "e7_1_skill_registry"
    version = "1.0.0"
    description = "E7.1 - Skill Registry System"

    def __init__(self, **kwargs) -> None:
        """Initialize the skill registry agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E7.1 - Skill Registry System agent for the Playwright test automation framework. You help users with e7.1 - skill registry system tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._registry = get_registry()
        self._context_history: list[RegistryContext] = []
        self._entry_cache: dict[str, RegistryEntry] = {}
        self._operation_history: list[RegistryOperation] = []

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
        Execute skill registry task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the registry operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "register_skill":
            return await self._register_skill(context, execution_context)
        elif task_type == "unregister_skill":
            return await self._unregister_skill(context, execution_context)
        elif task_type == "get_skill":
            return await self._get_skill(context, execution_context)
        elif task_type == "list_skills":
            return await self._list_skills(context, execution_context)
        elif task_type == "enable_skill":
            return await self._enable_skill(context, execution_context)
        elif task_type == "disable_skill":
            return await self._disable_skill(context, execution_context)
        elif task_type == "get_registry_context":
            return await self._get_registry_context(context, execution_context)
        elif task_type == "check_dependencies":
            return await self._check_dependencies(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _register_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Register a skill with full context."""
        skill_name = context.get("skill_name")
        skill_version = context.get("skill_version", "1.0.0")
        skill_path = context.get("skill_path", "")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        # Create registry entry
        entry = RegistryEntry(
            skill_name=skill_name,
            skill_version=skill_version,
            skill_path=skill_path,
            registration_context={
                "workflow_id": workflow_id,
                "auto_registered": context.get("auto_registered", False),
            },
        )

        # Create operation
        operation = RegistryOperation(
            operation_type="register",
            skill_name=skill_name,
            operation_context={
                "workflow_id": workflow_id,
            },
        )

        try:
            # Check if already registered
            existing = self._registry.get(skill_name)
            if existing:
                operation.result = "already_registered"
                operation.error = f"Skill '{skill_name}' already registered"
                return f"Skill '{skill_name}' already registered"

            # Create skill object
            skill = Skill(
                name=skill_name,
                version=skill_version,
                description=context.get("description", ""),
                enabled=context.get("enabled", True),
                path=Path(skill_path) if skill_path else None,
            )

            # Register in global registry
            self._registry.register(skill)

            entry.status = SkillStatus.REGISTERED
            entry.enabled = skill.enabled
            operation.result = "registered"

            # Track entry
            self._entry_cache[entry.entry_id] = entry

            return f"Registered skill: {skill_name}@{skill_version}"

        except Exception as e:
            entry.status = SkillStatus.ERROR
            operation.error = str(e)
            return f"Error registering skill: {e}"

        finally:
            operation.timestamp = datetime.now().isoformat()
            self._operation_history.append(operation)

    async def _unregister_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Unregister a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        # Create operation
        operation = RegistryOperation(
            operation_type="unregister",
            skill_name=skill_name,
        )

        try:
            result = self._registry.unregister(skill_name)
            if result:
                operation.result = "unregistered"
                return f"Unregistered skill: {skill_name}"
            else:
                operation.result = "not_found"
                return f"Skill '{skill_name}' not found"

        finally:
            self._operation_history.append(operation)

    async def _get_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get a skill by name."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        skill = self._registry.get(skill_name)
        if skill:
            return f"Skill: {skill.name}@{skill.version} (enabled={skill.enabled})"

        return f"Skill '{skill_name}' not found"

    async def _list_skills(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all skills."""
        include_disabled = context.get("include_disabled", False)

        skills = self._registry.list_skills(include_disabled=include_disabled)

        return f"Skills: {len(skills)} total"

    async def _enable_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Enable a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        result = self._registry.enable(skill_name)

        if result:
            # Update entry
            for entry in self._entry_cache.values():
                if entry.skill_name == skill_name:
                    entry.status = SkillStatus.ENABLED
                    entry.enabled = True
                    entry.last_modified = datetime.now().isoformat()
                    break

            return f"Enabled skill: {skill_name}"

        return f"Skill '{skill_name}' not found"

    async def _disable_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Disable a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        result = self._registry.disable(skill_name)

        if result:
            # Update entry
            for entry in self._entry_cache.values():
                if entry.skill_name == skill_name:
                    entry.status = SkillStatus.DISABLED
                    entry.enabled = False
                    entry.last_modified = datetime.now().isoformat()
                    break

            return f"Disabled skill: {skill_name}"

        return f"Skill '{skill_name}' not found"

    async def _get_registry_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get registry context."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for registry_context in self._context_history:
            if registry_context.context_id == context_id:
                return (
                    f"Registry context '{context_id}': "
                    f"{registry_context.skills_registered} registered, "
                    f"{registry_context.operations_performed} operations"
                )

        return f"Error: Registry context '{context_id}' not found"

    async def _check_dependencies(self, context: dict[str, Any], execution_context: Any) -> str:
        """Check skill dependencies."""
        skill_name = context.get("skill_name")
        dependencies = context.get("dependencies", [])

        if not skill_name:
            return "Error: skill_name is required"

        missing = []
        for dep in dependencies:
            if not self._registry.get(dep):
                missing.append(dep)

        if missing:
            return f"Missing dependencies: {missing}"

        return f"All dependencies available for '{skill_name}'"

    def get_context_history(self) -> list[RegistryContext]:
        """Get context history."""
        return self._context_history.copy()

    def get_entry_cache(self) -> dict[str, RegistryEntry]:
        """Get entry cache."""
        return self._entry_cache.copy()

    def get_operation_history(self) -> list[RegistryOperation]:
        """Get operation history."""
        return self._operation_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

