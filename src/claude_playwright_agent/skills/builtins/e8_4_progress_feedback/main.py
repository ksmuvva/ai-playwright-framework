"""
E8.4 - Progress Indicators & Feedback Skill.

This skill provides progress tracking capabilities:
- Progress bar rendering
- Status updates
- Milestone tracking
- Feedback generation
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ProgressStatus(str, Enum):
    """Progress status types."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class FeedbackType(str, Enum):
    """Feedback types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class IndicatorStyle(str, Enum):
    """Progress indicator styles."""

    BAR = "bar"
    SPINNER = "spinner"
    PERCENTAGE = "percentage"
    STEPS = "steps"
    DOTS = "dots"


@dataclass
class ProgressMilestone:
    """
    A milestone within a progress operation.

    Attributes:
        milestone_id: Unique milestone identifier
        name: Milestone name
        description: Milestone description
        target_value: Target value for completion
        current_value: Current progress value
        status: Current status
        reached_at: When milestone was reached
        metadata: Additional metadata
    """

    milestone_id: str = field(default_factory=lambda: f"milestone_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    target_value: int = 0
    current_value: int = 0
    status: ProgressStatus = ProgressStatus.PENDING
    reached_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "milestone_id": self.milestone_id,
            "name": self.name,
            "description": self.description,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "status": self.status.value,
            "reached_at": self.reached_at,
            "metadata": self.metadata,
        }

    @property
    def percent_complete(self) -> float:
        """Calculate percentage complete."""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)


@dataclass
class ProgressIndicator:
    """
    A progress indicator for tracking operation progress.

    Attributes:
        indicator_id: Unique indicator identifier
        workflow_id: Associated workflow ID
        operation_name: Name of the operation
        total_steps: Total number of steps
        completed_steps: Number of completed steps
        status: Current status
        style: Display style
        started_at: When operation started
        estimated_completion: Estimated completion time
        milestones: List of milestones
        metadata: Additional metadata
    """

    indicator_id: str = field(default_factory=lambda: f"prog_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    operation_name: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    status: ProgressStatus = ProgressStatus.PENDING
    style: IndicatorStyle = IndicatorStyle.BAR
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    estimated_completion: str = ""
    milestones: list[ProgressMilestone] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "indicator_id": self.indicator_id,
            "workflow_id": self.workflow_id,
            "operation_name": self.operation_name,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "status": self.status.value,
            "style": self.style.value,
            "started_at": self.started_at,
            "estimated_completion": self.estimated_completion,
            "milestones": [m.to_dict() for m in self.milestones],
            "metadata": self.metadata,
        }

    @property
    def percent_complete(self) -> float:
        """Calculate percentage complete."""
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.completed_steps / self.total_steps) * 100)

    @property
    def remaining_steps(self) -> int:
        """Calculate remaining steps."""
        return max(0, self.total_steps - self.completed_steps)


@dataclass
class FeedbackMessage:
    """
    A feedback message for the user.

    Attributes:
        message_id: Unique message identifier
        feedback_type: Type of feedback
        title: Message title
        content: Message content
        details: Additional details
        timestamp: When message was created
        workflow_id: Associated workflow ID
        context_id: Associated context ID
        metadata: Additional metadata
    """

    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    feedback_type: FeedbackType = FeedbackType.INFO
    title: str = ""
    content: str = ""
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    workflow_id: str = ""
    context_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "feedback_type": self.feedback_type.value,
            "title": self.title,
            "content": self.content,
            "details": self.details,
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "context_id": self.context_id,
            "metadata": self.metadata,
        }

    def render(self) -> str:
        """Render the feedback message."""
        icons = {
            FeedbackType.INFO: "ℹ️",
            FeedbackType.SUCCESS: "✅",
            FeedbackType.WARNING: "⚠️",
            FeedbackType.ERROR: "❌",
            FeedbackType.DEBUG: "🔍",
        }

        icon = icons.get(self.feedback_type, "")
        output = f"{icon} {self.title}" if icon else self.title

        if self.content:
            output += f"\n{self.content}"

        if self.details:
            output += f"\n\nDetails: {self.details}"

        return output


@dataclass
class FeedbackContext:
    """
    Context for feedback operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        indicators_created: Number of indicators created
        messages_sent: Number of messages sent
        milestones_reached: Number of milestones reached
        feedback_history: List of feedback messages
        started_at: When feedback started
        completed_at: When feedback completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"fdbk_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    indicators_created: int = 0
    messages_sent: int = 0
    milestones_reached: int = 0
    feedback_history: list[FeedbackMessage] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "indicators_created": self.indicators_created,
            "messages_sent": self.messages_sent,
            "milestones_reached": self.milestones_reached,
            "feedback_history": [m.to_dict() for m in self.feedback_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class ProgressFeedbackAgent(BaseAgent):
    """
    Progress Indicators and Feedback Agent.

    This agent provides:
    1. Progress tracking and rendering
    2. Status updates
    3. Milestone tracking
    4. Feedback generation
    """

    name = "e8_4_progress_feedback"
    version = "1.0.0"
    description = "E8.4 - Progress Indicators & Feedback"

    def __init__(self, **kwargs) -> None:
        """Initialize the progress feedback agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E8.4 - Progress Indicators & Feedback agent for the Playwright test automation framework. You help users with e8.4 - progress indicators & feedback tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[FeedbackContext] = []
        self._indicator_registry: dict[str, ProgressIndicator] = {}
        self._message_history: list[FeedbackMessage] = []
        self._milestone_registry: dict[str, ProgressMilestone] = {}

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
        Execute progress feedback task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the progress operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "create_indicator":
            return await self._create_indicator(context, execution_context)
        elif task_type == "update_progress":
            return await self._update_progress(context, execution_context)
        elif task_type == "complete_indicator":
            return await self._complete_indicator(context, execution_context)
        elif task_type == "send_feedback":
            return await self._send_feedback(context, execution_context)
        elif task_type == "add_milestone":
            return await self._add_milestone(context, execution_context)
        elif task_type == "get_indicator":
            return await self._get_indicator(context, execution_context)
        elif task_type == "get_status":
            return await self._get_status(context, execution_context)
        elif task_type == "render_progress":
            return await self._render_progress(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _create_indicator(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a new progress indicator."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        operation_name = context.get("operation_name", "Operation")
        total_steps = context.get("total_steps", 0)
        style = context.get("style", IndicatorStyle.BAR)

        if isinstance(style, str):
            style = IndicatorStyle(style)

        indicator = ProgressIndicator(
            workflow_id=workflow_id,
            operation_name=operation_name,
            total_steps=total_steps,
            style=style,
        )

        self._indicator_registry[indicator.indicator_id] = indicator

        return f"Created indicator '{indicator.indicator_id}' for '{operation_name}' ({total_steps} steps)"

    async def _update_progress(self, context: dict[str, Any], execution_context: Any) -> str:
        """Update progress for an indicator."""
        indicator_id = context.get("indicator_id")
        steps_completed = context.get("steps_completed", 1)

        if not indicator_id:
            return "Error: indicator_id is required"

        indicator = self._indicator_registry.get(indicator_id)
        if not indicator:
            return f"Error: Indicator '{indicator_id}' not found"

        indicator.completed_steps += steps_completed
        indicator.status = ProgressStatus.IN_PROGRESS

        # Check for milestone completion
        for milestone in indicator.milestones:
            if milestone.status == ProgressStatus.PENDING:
                milestone.current_value = indicator.completed_steps
                if milestone.current_value >= milestone.target_value:
                    milestone.status = ProgressStatus.COMPLETED
                    milestone.reached_at = datetime.now().isoformat()

        # Check for completion
        if indicator.completed_steps >= indicator.total_steps:
            indicator.status = ProgressStatus.COMPLETED

        return f"Progress: {indicator.percent_complete:.1f}% ({indicator.completed_steps}/{indicator.total_steps} steps)"

    async def _complete_indicator(self, context: dict[str, Any], execution_context: Any) -> str:
        """Mark an indicator as complete."""
        indicator_id = context.get("indicator_id")

        if not indicator_id:
            return "Error: indicator_id is required"

        indicator = self._indicator_registry.get(indicator_id)
        if not indicator:
            return f"Error: Indicator '{indicator_id}' not found"

        indicator.completed_steps = indicator.total_steps
        indicator.status = ProgressStatus.COMPLETED

        # Mark all pending milestones as complete
        for milestone in indicator.milestones:
            if milestone.status == ProgressStatus.PENDING:
                milestone.status = ProgressStatus.COMPLETED
                milestone.reached_at = datetime.now().isoformat()

        return f"Completed indicator '{indicator_id}'"

    async def _send_feedback(self, context: dict[str, Any], execution_context: Any) -> str:
        """Send a feedback message."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        feedback_type = context.get("feedback_type", FeedbackType.INFO)
        title = context.get("title", "")
        content = context.get("content", "")
        details = context.get("details", "")

        if isinstance(feedback_type, str):
            feedback_type = FeedbackType(feedback_type)

        message = FeedbackMessage(
            feedback_type=feedback_type,
            title=title,
            content=content,
            details=details,
            workflow_id=workflow_id,
        )

        self._message_history.append(message)

        # Send to current feedback context
        if self._context_history:
            self._context_history[-1].feedback_history.append(message)

        return f"Sent feedback: {message.message_id}"

    async def _add_milestone(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add a milestone to an indicator."""
        indicator_id = context.get("indicator_id")
        name = context.get("name", "Milestone")
        target_value = context.get("target_value", 0)

        if not indicator_id:
            return "Error: indicator_id is required"

        indicator = self._indicator_registry.get(indicator_id)
        if not indicator:
            return f"Error: Indicator '{indicator_id}' not found"

        milestone = ProgressMilestone(
            name=name,
            target_value=target_value,
        )

        indicator.milestones.append(milestone)
        self._milestone_registry[milestone.milestone_id] = milestone

        return f"Added milestone '{name}' at step {target_value}"

    async def _get_indicator(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get indicator by ID."""
        indicator_id = context.get("indicator_id")

        if not indicator_id:
            return "Error: indicator_id is required"

        indicator = self._indicator_registry.get(indicator_id)
        if indicator:
            return (
                f"Indicator '{indicator_id}': "
                f"{indicator.operation_name}, "
                f"{indicator.percent_complete:.1f}% complete, "
                f"status={indicator.status.value}"
            )

        return f"Error: Indicator '{indicator_id}' not found"

    async def _get_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get overall status."""
        workflow_id = context.get("workflow_id")

        indicators = list(self._indicator_registry.values())

        if workflow_id:
            indicators = [i for i in indicators if i.workflow_id == workflow_id]

        if not indicators:
            return "No indicators found"

        total_steps = sum(i.total_steps for i in indicators)
        completed_steps = sum(i.completed_steps for i in indicators)
        percent = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return f"Status: {percent:.1f}% complete ({completed_steps}/{total_steps} steps)"

    async def _render_progress(self, context: dict[str, Any], execution_context: Any) -> str:
        """Render progress display."""
        indicator_id = context.get("indicator_id")

        if indicator_id:
            indicator = self._indicator_registry.get(indicator_id)
            if indicator:
                return self._render_indicator(indicator)

        # Render all indicators
        outputs = []
        for indicator in self._indicator_registry.values():
            outputs.append(self._render_indicator(indicator))

        return "\n\n".join(outputs) if outputs else "No progress to display"

    def _render_indicator(self, indicator: ProgressIndicator) -> str:
        """Render a single indicator."""
        percent = indicator.percent_complete

        if indicator.style == IndicatorStyle.BAR:
            bar_width = 40
            filled = int(bar_width * percent / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            return f"{indicator.operation_name}: [{bar}] {percent:.1f}%"

        elif indicator.style == IndicatorStyle.PERCENTAGE:
            return f"{indicator.operation_name}: {percent:.1f}%"

        elif indicator.style == IndicatorStyle.STEPS:
            return f"{indicator.operation_name}: {indicator.completed_steps}/{indicator.total_steps} steps"

        elif indicator.style == IndicatorStyle.DOTS:
            dots = "." * int(percent / 10)
            return f"{indicator.operation_name}: {dots}"

        elif indicator.style == IndicatorStyle.SPINNER:
            spinners = ["|", "/", "-", "\\"]
            idx = int(percent / 25) % 4
            return f"{indicator.operation_name}: {spinners[idx]} {percent:.1f}%"

        return f"{indicator.operation_name}: {percent:.1f}%"

    def get_indicator_registry(self) -> dict[str, ProgressIndicator]:
        """Get indicator registry."""
        return self._indicator_registry.copy()

    def get_message_history(self) -> list[FeedbackMessage]:
        """Get message history."""
        return self._message_history.copy()

    def get_context_history(self) -> list[FeedbackContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

