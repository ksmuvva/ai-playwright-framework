"""
E8.2 - Interactive Prompts & User Input Skill.

This skill provides interactive capabilities:
- Interactive prompts for user input
- Confirmation dialogs
- Multi-step wizards
- Rich input handling
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class PromptType(str, Enum):
    """Prompt types."""

    TEXT = "text"
    PASSWORD = "password"
    CONFIRMATION = "confirmation"
    SELECTION = "selection"
    MULTI_SELECT = "multi_select"
    PATH = "path"
    NUMBER = "number"


class WizardStatus(str, Enum):
    """Wizard status types."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class PromptResponse:
    """
    A response from a user prompt.

    Attributes:
        response_id: Unique response identifier
        prompt_type: Type of prompt
        value: User-provided value
        confirmed: Whether user confirmed
        skipped: Whether user skipped
        timestamp: When response was received
        context_id: Associated context ID
        metadata: Additional metadata
    """

    response_id: str = field(default_factory=lambda: f"resp_{uuid.uuid4().hex[:8]}")
    prompt_type: PromptType = PromptType.TEXT
    value: Any = None
    confirmed: bool = False
    skipped: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_id": self.response_id,
            "prompt_type": self.prompt_type.value,
            "value": self.value,
            "confirmed": self.confirmed,
            "skipped": self.skipped,
            "timestamp": self.timestamp,
            "context_id": self.context_id,
            "metadata": self.metadata,
        }


@dataclass
class PromptConfig:
    """
    Configuration for a prompt.

    Attributes:
        config_id: Unique config identifier
        prompt_type: Type of prompt
        message: Prompt message
        default_value: Default value
        required: Whether input is required
        validation_regex: Validation regex pattern
        choices: Available choices (for selection)
        show_hint: Whether to show hint
        hint_text: Hint text to display
    """

    config_id: str = field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:8]}")
    prompt_type: PromptType = PromptType.TEXT
    message: str = ""
    default_value: Any = None
    required: bool = False
    validation_regex: str = ""
    choices: list[Any] = field(default_factory=list)
    show_hint: bool = False
    hint_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "prompt_type": self.prompt_type.value,
            "message": self.message,
            "default_value": self.default_value,
            "required": self.required,
            "validation_regex": self.validation_regex,
            "choices": self.choices,
            "show_hint": self.show_hint,
            "hint_text": self.hint_text,
        }


@dataclass
class WizardStep:
    """
    A step in a multi-step wizard.

    Attributes:
        step_id: Unique step identifier
        name: Step name
        title: Step title
        description: Step description
        prompt_config: Prompt configuration for this step
        order: Step order
        dependencies: Steps this step depends on
        condition: Condition for showing this step
    """

    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    name: str = ""
    title: str = ""
    description: str = ""
    prompt_config: PromptConfig = field(default_factory=PromptConfig)
    order: int = 0
    dependencies: list[str] = field(default_factory=list)
    condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "prompt_config": self.prompt_config.to_dict(),
            "order": self.order,
            "dependencies": self.dependencies,
            "condition": self.condition,
        }


@dataclass
class WizardContext:
    """
    Context for wizard operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        prompts_shown: Number of prompts shown
        responses_collected: Number of responses collected
        wizards_completed: Number of wizards completed
        response_history: List of prompt responses
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"wiz_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    prompts_shown: int = 0
    responses_collected: int = 0
    wizards_completed: int = 0
    response_history: list[PromptResponse] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "prompts_shown": self.prompts_shown,
            "responses_collected": self.responses_collected,
            "wizards_completed": self.wizards_completed,
            "response_history": [r.to_dict() for r in self.response_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class InteractivePromptsAgent(BaseAgent):
    """
    Interactive Prompts and User Input Agent.

    This agent provides:
    1. Interactive prompts for user input
    2. Confirmation dialogs
    3. Multi-step wizards
    4. Rich input handling
    """

    name = "e8_2_interactive_prompts"
    version = "1.0.0"
    description = "E8.2 - Interactive Prompts & User Input"

    def __init__(self, **kwargs) -> None:
        """Initialize the interactive prompts agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E8.2 - Interactive Prompts & User Input agent for the Playwright test automation framework. You help users with e8.2 - interactive prompts & user input tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[WizardContext] = []
        self._response_history: list[PromptResponse] = []
        self._active_wizards: dict[str, dict[str, Any]] = {}

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
        """Execute interactive prompt task."""
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "prompt":
            return await self._prompt(context, execution_context)
        elif task_type == "confirm":
            return await self._confirm(context, execution_context)
        elif task_type == "select":
            return await self._select(context, execution_context)
        elif task_type == "start_wizard":
            return await self._start_wizard(context, execution_context)
        elif task_type == "next_step":
            return await self._next_step(context, execution_context)
        elif task_type == "complete_wizard":
            return await self._complete_wizard(context, execution_context)
        elif task_type == "get_response":
            return await self._get_response(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _prompt(self, context: dict[str, Any], execution_context: Any) -> str:
        """Show an interactive prompt."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        message = context.get("message", "")
        prompt_type = context.get("prompt_type", PromptType.TEXT)
        default_value = context.get("default_value")
        required = context.get("required", False)

        if isinstance(prompt_type, str):
            prompt_type = PromptType(prompt_type)

        # Create response (simulated)
        response = PromptResponse(
            prompt_type=prompt_type,
            value=default_value,
            context_id=workflow_id,
        )

        self._response_history.append(response)

        value_str = str(default_value) if default_value is not None else "(no default)"
        return f"Prompt: {message} [{value_str}] (ID: {response.response_id})"

    async def _confirm(self, context: dict[str, Any], execution_context: Any) -> str:
        """Show a confirmation dialog."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        message = context.get("message", "")
        default_value = context.get("default", True)

        # Create response (simulated)
        response = PromptResponse(
            prompt_type=PromptType.CONFIRMATION,
            value=default_value,
            confirmed=default_value,
            context_id=workflow_id,
        )

        self._response_history.append(response)

        result = "yes" if default_value else "no"
        return f"Confirm: {message} -> {result}"

    async def _select(self, context: dict[str, Any], execution_context: Any) -> str:
        """Show a selection prompt."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        message = context.get("message", "")
        choices = context.get("choices", [])
        default = context.get("default")

        # Create response (simulated)
        selected = default if default is not None else (choices[0] if choices else None)

        response = PromptResponse(
            prompt_type=PromptType.SELECTION,
            value=selected,
            context_id=workflow_id,
        )

        self._response_history.append(response)

        choices_str = ", ".join(str(c) for c in choices[:3])
        return f"Select: {message} [{choices_str}...] -> Selected: {selected}"

    async def _start_wizard(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start a multi-step wizard."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        wizard_name = context.get("wizard_name", "")
        steps = context.get("steps", [])

        wizard_id = f"wizard_{uuid.uuid4().hex[:8]}"

        # Create wizard state
        self._active_wizards[wizard_id] = {
            "wizard_id": wizard_id,
            "wizard_name": wizard_name,
            "workflow_id": workflow_id,
            "steps": steps,
            "current_step": 0,
            "responses": {},
            "started_at": datetime.now().isoformat(),
        }

        return f"Started wizard '{wizard_name}' with {len(steps)} step(s) (ID: {wizard_id})"

    async def _next_step(self, context: dict[str, Any], execution_context: Any) -> str:
        """Execute next wizard step."""
        wizard_id = context.get("wizard_id")

        if not wizard_id:
            return "Error: wizard_id is required"

        wizard = self._active_wizards.get(wizard_id)
        if not wizard:
            return f"Error: Wizard '{wizard_id}' not found"

        current_step = wizard["current_step"]
        steps = wizard["steps"]

        if current_step >= len(steps):
            return "Wizard complete: No more steps"

        step = steps[current_step]
        step_name = step.get("name", f"Step {current_step + 1}")

        wizard["current_step"] += 1

        return f"Wizard step: {step_name} ({current_step + 1}/{len(steps)})"

    async def _complete_wizard(self, context: dict[str, Any], execution_context: Any) -> str:
        """Complete a wizard."""
        wizard_id = context.get("wizard_id")

        if not wizard_id:
            return "Error: wizard_id is required"

        wizard = self._active_wizards.get(wizard_id)
        if not wizard:
            return f"Error: Wizard '{wizard_id}' not found"

        wizard["completed_at"] = datetime.now().isoformat()
        wizard["status"] = "completed"

        response_count = len(wizard.get("responses", {}))

        return f"Completed wizard '{wizard['wizard_name']}': {response_count} response(s)"

    async def _get_response(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get a prompt response."""
        response_id = context.get("response_id")

        if not response_id:
            return "Error: response_id is required"

        for response in self._response_history:
            if response.response_id == response_id:
                return f"Response: {response.value}"

        return f"Error: Response '{response_id}' not found"

    def get_response_history(self) -> list[PromptResponse]:
        """Get response history."""
        return self._response_history.copy()

    def get_active_wizards(self) -> dict[str, dict[str, Any]]:
        """Get active wizards."""
        return self._active_wizards.copy()

    def get_context_history(self) -> list[WizardContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

