"""
E3.5 - Ingestion Logging & Tracking Skill.

This skill provides ingestion logging and tracking:
- Pipeline stage logging with context
- Progress tracking through ingestion
- Error logging with context preservation
- Metrics collection and reporting
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PipelineStage(str, Enum):
    """Pipeline stages."""

    INITIALIZED = "initialized"
    VALIDATED = "validated"
    PARSED = "parsed"
    EXTRACTED = "extracted"
    ANALYZED = "analyzed"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineLogEntry:
    """
    A log entry for pipeline activity.

    Attributes:
        log_id: Unique log identifier
        recording_id: Associated recording ID
        ingestion_id: Associated ingestion ID
        workflow_id: Associated workflow ID
        stage: Pipeline stage
        level: Log level
        message: Log message
        context: Full context at time of log
        timestamp: When log was created
        metadata: Additional log metadata
    """

    log_id: str = field(default_factory=lambda: f"log_{uuid.uuid4().hex[:8]}")
    recording_id: str = ""
    ingestion_id: str = ""
    workflow_id: str = ""
    stage: PipelineStage = PipelineStage.INITIALIZED
    level: LogLevel = LogLevel.INFO
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_id": self.log_id,
            "recording_id": self.recording_id,
            "ingestion_id": self.ingestion_id,
            "workflow_id": self.workflow_id,
            "stage": self.stage.value,
            "level": self.level.value,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ProgressTracker:
    """
    Tracks progress through ingestion pipeline.

    Attributes:
        tracker_id: Unique tracker identifier
        recording_id: Associated recording ID
        ingestion_id: Associated ingestion ID
        current_stage: Current pipeline stage
        stages_completed: List of completed stages
        stages_remaining: List of remaining stages
        progress_percent: Progress percentage (0-100)
        started_at: When tracking started
        estimated_completion: Estimated completion time
        context: Tracking context
    """

    tracker_id: str = field(default_factory=lambda: f"track_{uuid.uuid4().hex[:8]}")
    recording_id: str = ""
    ingestion_id: str = ""
    current_stage: PipelineStage = PipelineStage.INITIALIZED
    stages_completed: list[PipelineStage] = field(default_factory=list)
    stages_remaining: list[PipelineStage] = field(default_factory=list)
    progress_percent: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    estimated_completion: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def advance_stage(self, new_stage: PipelineStage) -> None:
        """Advance to the next stage."""
        if self.current_stage not in self.stages_completed:
            self.stages_completed.append(self.current_stage)

        self.current_stage = new_stage

        if new_stage in self.stages_remaining:
            self.stages_remaining.remove(new_stage)

        # Update progress
        total_stages = len(self.stages_completed) + len(self.stages_remaining) + 1
        self.progress_percent = (len(self.stages_completed) / total_stages) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tracker_id": self.tracker_id,
            "recording_id": self.recording_id,
            "ingestion_id": self.ingestion_id,
            "current_stage": self.current_stage.value,
            "stages_completed": [s.value for s in self.stages_completed],
            "stages_remaining": [s.value for s in self.stages_remaining],
            "progress_percent": self.progress_percent,
            "started_at": self.started_at,
            "estimated_completion": self.estimated_completion,
            "context": self.context,
        }


@dataclass
class IngestionMetrics:
    """
    Metrics collected during ingestion.

    Attributes:
        metrics_id: Unique metrics identifier
        recording_id: Associated recording ID
        ingestion_id: Associated ingestion ID
        duration_seconds: Time taken for ingestion
        total_actions: Number of actions extracted
        total_selectors: Number of selectors extracted
        total_issues: Number of issues found
        stage_metrics: Metrics per stage
        context: Metrics context
    """

    metrics_id: str = field(default_factory=lambda: f"metrics_{uuid.uuid4().hex[:8]}")
    recording_id: str = ""
    ingestion_id: str = ""
    duration_seconds: float = 0.0
    total_actions: int = 0
    total_selectors: int = 0
    total_issues: int = 0
    stage_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics_id": self.metrics_id,
            "recording_id": self.recording_id,
            "ingestion_id": self.ingestion_id,
            "duration_seconds": self.duration_seconds,
            "total_actions": self.total_actions,
            "total_selectors": self.total_selectors,
            "total_issues": self.total_issues,
            "stage_metrics": self.stage_metrics,
            "context": self.context,
        }


@dataclass
class LoggingContext:
    """
    Context for logging operations.

    Attributes:
        logging_id: Unique logging identifier
        workflow_id: Associated workflow ID
        recording_id: Associated recording ID
        session_id: Session identifier
        log_entries: List of log entries
        progress_tracker: Progress tracker
        metrics: Ingestion metrics
        started_at: When logging started
        completed_at: When logging completed
    """

    logging_id: str = field(default_factory=lambda: f"logging_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_id: str = ""
    session_id: str = ""
    log_entries: list[PipelineLogEntry] = field(default_factory=list)
    progress_tracker: ProgressTracker | None = None
    metrics: IngestionMetrics | None = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "logging_id": self.logging_id,
            "workflow_id": self.workflow_id,
            "recording_id": self.recording_id,
            "session_id": self.session_id,
            "log_entries": [e.to_dict() for e in self.log_entries],
            "progress_tracker": self.progress_tracker.to_dict() if self.progress_tracker else None,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class IngestionLoggingAgent(BaseAgent):
    """
    Ingestion Logging and Tracking Agent.

    This agent provides:
    1. Pipeline stage logging with context
    2. Progress tracking through ingestion
    3. Error logging with context preservation
    4. Metrics collection and reporting
    """

    name = "e3_5_ingestion_logging"
    version = "1.0.0"
    description = "E3.5 - Ingestion Logging & Tracking"

    def __init__(self, **kwargs) -> None:
        """Initialize the logging agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E3.5 - Ingestion Logging & Tracking agent for the Playwright test automation framework. You help users with e3.5 - ingestion logging & tracking tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._active_logging: dict[str, LoggingContext] = {}
        self._logging_history: list[LoggingContext] = []
        self._global_log: list[PipelineLogEntry] = []

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
        Execute logging task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the logging operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "start_logging":
            return await self._start_logging(context, execution_context)
        elif task_type == "log_event":
            return await self._log_event(context, execution_context)
        elif task_type == "track_progress":
            return await self._track_progress(context, execution_context)
        elif task_type == "log_error":
            return await self._log_error(context, execution_context)
        elif task_type == "collect_metrics":
            return await self._collect_metrics(context, execution_context)
        elif task_type == "advance_stage":
            return await self._advance_stage(context, execution_context)
        elif task_type == "stop_logging":
            return await self._stop_logging(context, execution_context)
        elif task_type == "get_logs":
            return await self._get_logs(context, execution_context)
        elif task_type == "get_progress":
            return await self._get_progress(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _start_logging(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start logging for an ingestion."""
        recording_id = context.get("recording_id")
        ingestion_id = context.get("ingestion_id", getattr(execution_context, "ingestion_id", execution_context.get("ingestion_id", "")))
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        session_id = context.get("session_id", f"session_{uuid.uuid4().hex[:8]}")

        if not recording_id:
            return "Error: recording_id is required"

        # Create logging context
        logging_context = LoggingContext(
            recording_id=recording_id,
            ingestion_id=ingestion_id,
            workflow_id=workflow_id,
            session_id=session_id,
        )

        # Create progress tracker
        logging_context.progress_tracker = ProgressTracker(
            recording_id=recording_id,
            ingestion_id=ingestion_id,
        )

        # Create metrics
        logging_context.metrics = IngestionMetrics(
            recording_id=recording_id,
            ingestion_id=ingestion_id,
        )

        # Store active logging
        self._active_logging[logging_context.logging_id] = logging_context

        # Log start event
        await self._log_event_internal(
            logging_context=logging_context,
            stage=PipelineStage.INITIALIZED,
            level=LogLevel.INFO,
            message=f"Started logging for recording '{recording_id}'",
            context=execution_context,
        )

        return f"Logging started: {logging_context.logging_id}"

    async def _log_event(self, context: dict[str, Any], execution_context: Any) -> str:
        """Log a pipeline event."""
        logging_id = context.get("logging_id")
        stage = context.get("stage", PipelineStage.INITIALIZED)
        level = context.get("level", LogLevel.INFO)
        message = context.get("message", "")
        event_context = context.get("event_context", {})

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]

        await self._log_event_internal(
            logging_context=logging_context,
            stage=stage,
            level=level,
            message=message,
            context={**execution_context, **event_context},
        )

        return f"Event logged: {message[:50]}"

    async def _log_event_internal(
        self,
        logging_context: LoggingContext,
        stage: PipelineStage,
        level: LogLevel,
        message: str,
        context: dict[str, Any],
    ) -> None:
        """Internal log event method."""
        log_entry = PipelineLogEntry(
            recording_id=logging_context.recording_id,
            ingestion_id=logging_context.ingestion_id,
            workflow_id=logging_context.workflow_id,
            stage=stage,
            level=level,
            message=message,
            context=context,
        )

        logging_context.log_entries.append(log_entry)
        self._global_log.append(log_entry)

    async def _track_progress(self, context: dict[str, Any], execution_context: Any) -> str:
        """Track progress through pipeline."""
        logging_id = context.get("logging_id")
        stage = context.get("stage")

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]
        tracker = logging_context.progress_tracker

        if tracker and stage:
            tracker.advance_stage(PipelineStage(stage))

        return f"Progress tracked: {tracker.current_stage.value if tracker else 'no tracker'} ({tracker.progress_percent:.1f}%)" if tracker else "No tracker"

    async def _log_error(self, context: dict[str, Any], execution_context: Any) -> str:
        """Log an error with full context preservation."""
        logging_id = context.get("logging_id")
        stage = context.get("stage", PipelineStage.FAILED)
        error_message = context.get("error_message", "Unknown error")
        error_context = context.get("error_context", {})

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]

        # Log error with full context
        await self._log_event_internal(
            logging_context=logging_context,
            stage=stage,
            level=LogLevel.ERROR,
            message=f"Error: {error_message}",
            context={
                **execution_context,
                **error_context,
                "error_type": context.get("error_type", "unknown"),
                "stack_trace": context.get("stack_trace", ""),
            },
        )

        # Update metrics
        if logging_context.metrics:
            logging_context.metrics.total_issues += 1

        return f"Error logged: {error_message[:50]}"

    async def _collect_metrics(self, context: dict[str, Any], execution_context: Any) -> str:
        """Collect ingestion metrics."""
        logging_id = context.get("logging_id")

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]
        metrics = logging_context.metrics

        if metrics:
            return (
                f"Metrics: actions={metrics.total_actions}, "
                f"selectors={metrics.total_selectors}, "
                f"issues={metrics.total_issues}"
            )

        return "No metrics available"

    async def _advance_stage(self, context: dict[str, Any], execution_context: Any) -> str:
        """Advance to the next pipeline stage."""
        logging_id = context.get("logging_id")
        new_stage = context.get("new_stage")

        if not logging_id or not new_stage:
            return "Error: logging_id and new_stage are required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]

        # Advance progress tracker
        if logging_context.progress_tracker:
            logging_context.progress_tracker.advance_stage(PipelineStage(new_stage))

        # Log stage transition
        await self._log_event_internal(
            logging_context=logging_context,
            stage=PipelineStage(new_stage),
            level=LogLevel.INFO,
            message=f"Advanced to stage: {new_stage}",
            context=execution_context,
        )

        return f"Advanced to stage: {new_stage}"

    async def _stop_logging(self, context: dict[str, Any], execution_context: Any) -> str:
        """Stop logging and finalize."""
        logging_id = context.get("logging_id")

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id not in self._active_logging:
            return f"Error: Logging session '{logging_id}' not found"

        logging_context = self._active_logging[logging_id]
        logging_context.completed_at = datetime.now().isoformat()

        # Calculate duration
        if logging_context.metrics:
            started = datetime.fromisoformat(logging_context.started_at)
            completed = datetime.fromisoformat(logging_context.completed_at)
            logging_context.metrics.duration_seconds = (completed - started).total_seconds()

        # Log completion
        await self._log_event_internal(
            logging_context=logging_context,
            stage=PipelineStage.COMPLETED,
            level=LogLevel.INFO,
            message=f"Logging completed: {len(logging_context.log_entries)} log entries",
            context=execution_context,
        )

        # Move to history
        self._logging_history.append(logging_context)
        del self._active_logging[logging_id]

        return f"Logging stopped: {logging_id}"

    async def _get_logs(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get logs for an ingestion."""
        logging_id = context.get("logging_id")
        level = context.get("level")
        limit = context.get("limit", 100)

        if logging_id:
            if logging_id in self._active_logging:
                logs = self._active_logging[logging_id].log_entries
            else:
                # Search history
                for logging_context in self._logging_history:
                    if logging_context.logging_id == logging_id:
                        logs = logging_context.log_entries
                        break
                else:
                    return f"Error: Logging session '{logging_id}' not found"
        else:
            logs = self._global_log[-limit:]

        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.level == LogLevel(level)]

        return f"Retrieved {len(logs)} log entry(s)"

    async def _get_progress(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get progress tracking info."""
        logging_id = context.get("logging_id")

        if not logging_id:
            return "Error: logging_id is required"

        if logging_id in self._active_logging:
            tracker = self._active_logging[logging_id].progress_tracker
        else:
            for logging_context in self._logging_history:
                if logging_context.logging_id == logging_id:
                    tracker = logging_context.progress_tracker
                    break
            else:
                return f"Error: Logging session '{logging_id}' not found"

        if tracker:
            return (
                f"Progress: {tracker.current_stage.value}, "
                f"{tracker.progress_percent:.1f}% complete, "
                f"{len(tracker.stages_completed)} stages done"
            )

        return "No progress tracker found"

    def get_active_logging(self) -> dict[str, LoggingContext]:
        """Get all active logging sessions."""
        return self._active_logging.copy()

    def get_logging_history(self) -> list[LoggingContext]:
        """Get logging history."""
        return self._logging_history.copy()

    def get_global_log(self, limit: int = 1000) -> list[PipelineLogEntry]:
        """Get global log entries."""
        return self._global_log[-limit:]

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

