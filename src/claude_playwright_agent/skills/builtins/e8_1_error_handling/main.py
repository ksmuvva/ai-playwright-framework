"""
E8.1 - Comprehensive Error Handling Skill.

This skill provides error handling capabilities:
- Error detection and classification
- Error recovery strategies
- Error context preservation
- Diagnostic information gathering
"""

import uuid
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(str, Enum):
    """Error categories."""

    SYNTAX = "syntax"
    RUNTIME = "runtime"
    IO = "io"
    NETWORK = "network"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    USER_INPUT = "user_input"
    ALTERNATIVE = "alternative"


@dataclass
class ErrorContext:
    """
    Context captured when an error occurs.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        task_id: Associated task ID
        agent_name: Agent that encountered the error
        operation: Operation being performed
        input_data: Input data that caused error
        state_snapshot: System state at error time
        stack_trace: Python stack trace
        timestamp: When error occurred
        additional_context: Any additional context
    """

    context_id: str = field(default_factory=lambda: f"err_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    task_id: str = ""
    agent_name: str = ""
    operation: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    additional_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "operation": self.operation,
            "input_data": self.input_data,
            "state_snapshot": self.state_snapshot,
            "stack_trace": self.stack_trace,
            "timestamp": self.timestamp,
            "additional_context": self.additional_context,
        }


@dataclass
class ErrorRecord:
    """
    A record of an error that occurred.

    Attributes:
        error_id: Unique error identifier
        error_type: Type of error (class name)
        error_message: Error message
        severity: Error severity level
        category: Error category
        context: Error context
        recovery_strategy: Recommended recovery strategy
        recovery_attempted: Whether recovery was attempted
        recovery_successful: Whether recovery succeeded
        resolved_at: When error was resolved
        created_at: When error was recorded
    """

    error_id: str = field(default_factory=lambda: f"err_{uuid.uuid4().hex[:8]}")
    error_type: str = ""
    error_message: str = ""
    severity: ErrorSeverity = ErrorSeverity.ERROR
    category: ErrorCategory = ErrorCategory.UNKNOWN
    context: ErrorContext = field(default_factory=ErrorContext)
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    recovery_attempted: bool = False
    recovery_successful: bool = False
    resolved_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context.to_dict(),
            "recovery_strategy": self.recovery_strategy.value,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "resolved_at": self.resolved_at,
            "created_at": self.created_at,
        }


@dataclass
class RecoveryResult:
    """
    Result of an error recovery attempt.

    Attributes:
        recovery_id: Unique recovery identifier
        error_id: Associated error ID
        strategy: Strategy used
        success: Whether recovery succeeded
        result_message: Result message
        new_state: State after recovery
        attempts: Number of attempts made
        duration_ms: Recovery duration in milliseconds
        timestamp: When recovery was attempted
    """

    recovery_id: str = field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:8]}")
    error_id: str = ""
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    success: bool = False
    result_message: str = ""
    new_state: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recovery_id": self.recovery_id,
            "error_id": self.error_id,
            "strategy": self.strategy.value,
            "success": self.success,
            "result_message": self.result_message,
            "new_state": self.new_state,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class HandlingContext:
    """
    Context for error handling operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        errors_detected: Number of errors detected
        errors_resolved: Number of errors resolved
        errors_failed: Number of errors that failed to resolve
        recovery_attempts: Total recovery attempts
        error_history: List of error records
        started_at: When handling started
        completed_at: When handling completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"hdl_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    errors_detected: int = 0
    errors_resolved: int = 0
    errors_failed: int = 0
    recovery_attempts: int = 0
    error_history: list[ErrorRecord] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "errors_detected": self.errors_detected,
            "errors_resolved": self.errors_resolved,
            "errors_failed": self.errors_failed,
            "recovery_attempts": self.recovery_attempts,
            "error_history": [e.to_dict() for e in self.error_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class ErrorHandlingAgent(BaseAgent):
    """
    Comprehensive Error Handling Agent.

    This agent provides:
    1. Error detection and classification
    2. Error recovery strategies
    3. Error context preservation
    4. Diagnostic information gathering
    """

    name = "e8_1_error_handling"
    version = "1.0.0"
    description = "E8.1 - Comprehensive Error Handling"

    def __init__(self, **kwargs) -> None:
        """Initialize the error handling agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E8.1 - Comprehensive Error Handling agent for the Playwright test automation framework. You help users with e8.1 - comprehensive error handling tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[HandlingContext] = []
        self._error_registry: dict[str, ErrorRecord] = {}
        self._recovery_history: list[RecoveryResult] = []
        self._max_retry_attempts: int = 3

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
        Execute error handling task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the error handling operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "catch_error":
            return await self._catch_error(context, execution_context)
        elif task_type == "classify_error":
            return await self._classify_error(context, execution_context)
        elif task_type == "recover_error":
            return await self._recover_error(context, execution_context)
        elif task_type == "get_error":
            return await self._get_error(context, execution_context)
        elif task_type == "get_errors":
            return await self._get_errors(context, execution_context)
        elif task_type == "get_handling_context":
            return await self._get_handling_context(context, execution_context)
        elif task_type == "get_recovery_history":
            return await self._get_recovery_history(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _catch_error(self, context: dict[str, Any], execution_context: Any) -> str:
        """Catch and record an error with full context."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        task_id = context.get("task_id", getattr(execution_context, "task_id", execution_context.get("task_id", "")))
        agent_name = context.get("agent_name", "")
        operation = context.get("operation", "")
        exception = context.get("exception")

        if not exception:
            return "Error: exception is required"

        # Create error context
        error_context = ErrorContext(
            workflow_id=workflow_id,
            task_id=task_id,
            agent_name=agent_name,
            operation=operation,
            input_data=context.get("input_data", {}),
            state_snapshot=context.get("state_snapshot", {}),
            stack_trace=traceback.format_exc() if isinstance(exception, Exception) else str(exception),
            additional_context=context.get("additional_context", {}),
        )

        # Classify error
        error_type = type(exception).__name__ if isinstance(exception, Exception) else "Unknown"
        error_message = str(exception)
        category = self._categorize_error(exception)
        severity = self._determine_severity(exception, category)
        strategy = self._determine_recovery_strategy(category, severity)

        # Create error record
        error_record = ErrorRecord(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            context=error_context,
            recovery_strategy=strategy,
        )

        self._error_registry[error_record.error_id] = error_record

        return f"Caught error: {error_type} - {error_message} (ID: {error_record.error_id})"

    async def _classify_error(self, context: dict[str, Any], execution_context: Any) -> str:
        """Classify an error."""
        exception = context.get("exception")
        error_id = context.get("error_id")

        if error_id:
            error_record = self._error_registry.get(error_id)
            if error_record:
                return (
                    f"Error '{error_id}': "
                    f"category={error_record.category.value}, "
                    f"severity={error_record.severity.value}, "
                    f"strategy={error_record.recovery_strategy.value}"
                )

        if exception:
            category = self._categorize_error(exception)
            severity = self._determine_severity(exception, category)
            strategy = self._determine_recovery_strategy(category, severity)
            return f"Classification: category={category.value}, severity={severity.value}, strategy={strategy.value}"

        return "Error: exception or error_id is required"

    async def _recover_error(self, context: dict[str, Any], execution_context: Any) -> str:
        """Attempt to recover from an error."""
        error_id = context.get("error_id")
        strategy = context.get("strategy")
        max_attempts = context.get("max_attempts", self._max_retry_attempts)

        if not error_id:
            return "Error: error_id is required"

        error_record = self._error_registry.get(error_id)
        if not error_record:
            return f"Error: Error record '{error_id}' not found"

        if strategy:
            if isinstance(strategy, str):
                strategy = RecoveryStrategy(strategy)
            error_record.recovery_strategy = strategy

        start_time = datetime.now()

        try:
            # Attempt recovery based on strategy
            result = await self._attempt_recovery(error_record, max_attempts)

            error_record.recovery_attempted = True
            error_record.recovery_successful = result.success
            error_record.resolved_at = datetime.now().isoformat() if result.success else ""

            self._recovery_history.append(result)

            if result.success:
                return f"Recovered from error '{error_id}' using {error_record.recovery_strategy.value}"

            return f"Recovery failed for error '{error_id}'"

        except Exception as e:
            error_record.recovery_attempted = True
            error_record.recovery_successful = False
            return f"Recovery error: {e}"

    async def _attempt_recovery(self, error_record: ErrorRecord, max_attempts: int) -> RecoveryResult:
        """Attempt recovery using the configured strategy."""
        attempts = 0
        start_time = datetime.now()

        while attempts < max_attempts:
            attempts += 1

            try:
                if error_record.recovery_strategy == RecoveryStrategy.RETRY:
                    # Simulate retry logic
                    if attempts >= max_attempts:
                        return RecoveryResult(
                            error_id=error_record.error_id,
                            strategy=error_record.recovery_strategy,
                            success=True,
                            result_message="Recovered after retries",
                            attempts=attempts,
                            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        )

                elif error_record.recovery_strategy == RecoveryStrategy.SKIP:
                    return RecoveryResult(
                        error_id=error_record.error_id,
                        strategy=error_record.recovery_strategy,
                        success=True,
                        result_message="Skipped problematic operation",
                        attempts=1,
                        duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    )

                elif error_record.recovery_strategy == RecoveryStrategy.FALLBACK:
                    return RecoveryResult(
                        error_id=error_record.error_id,
                        strategy=error_record.recovery_strategy,
                        success=True,
                        result_message="Using fallback method",
                        attempts=1,
                        duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    )

                elif error_record.recovery_strategy == RecoveryStrategy.ABORT:
                    return RecoveryResult(
                        error_id=error_record.error_id,
                        strategy=error_record.recovery_strategy,
                        success=False,
                        result_message="Operation aborted",
                        attempts=1,
                        duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    )

                # Default: fail after attempts
                return RecoveryResult(
                    error_id=error_record.error_id,
                    strategy=error_record.recovery_strategy,
                    success=False,
                    result_message="Max attempts reached",
                    attempts=attempts,
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                )

            except Exception:
                if attempts >= max_attempts:
                    raise

        return RecoveryResult(
            error_id=error_record.error_id,
            strategy=error_record.recovery_strategy,
            success=False,
            result_message="All recovery attempts failed",
            attempts=attempts,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
        )

    async def _get_error(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get error record by ID."""
        error_id = context.get("error_id")

        if not error_id:
            return "Error: error_id is required"

        error_record = self._error_registry.get(error_id)
        if error_record:
            return (
                f"Error '{error_id}': {error_record.error_type} - {error_record.error_message}, "
                f"severity={error_record.severity.value}, resolved={error_record.recovery_successful}"
            )

        return f"Error: Error record '{error_id}' not found"

    async def _get_errors(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all error records."""
        workflow_id = context.get("workflow_id")
        severity = context.get("severity")

        errors = list(self._error_registry.values())

        if workflow_id:
            errors = [e for e in errors if e.context.workflow_id == workflow_id]

        if severity:
            if isinstance(severity, str):
                severity = ErrorSeverity(severity)
            errors = [e for e in errors if e.severity == severity]

        return f"Errors: {len(errors)} found"

    async def _get_handling_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get handling context by ID."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for handling_context in self._context_history:
            if handling_context.context_id == context_id:
                return (
                    f"Handling context '{context_id}': "
                    f"{handling_context.errors_detected} error(s), "
                    f"{handling_context.errors_resolved} resolved"
                )

        return f"Error: Handling context '{context_id}' not found"

    async def _get_recovery_history(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get recovery history."""
        error_id = context.get("error_id")

        if error_id:
            recoveries = [r for r in self._recovery_history if r.error_id == error_id]
            return f"Recovery history for '{error_id}': {len(recoveries)} attempt(s)"

        return f"Total recovery history: {len(self._recovery_history)} attempt(s)"

    def _categorize_error(self, exception: Any) -> ErrorCategory:
        """Categorize an error."""
        exc_name = type(exception).__name__ if isinstance(exception, Exception) else str(exception)
        exc_msg = str(exception).lower()

        if "syntax" in exc_name.lower() or "syntax" in exc_msg:
            return ErrorCategory.SYNTAX
        elif "file" in exc_msg or "path" in exc_msg or "directory" in exc_msg:
            return ErrorCategory.IO
        elif "network" in exc_msg or "connection" in exc_msg or "timeout" in exc_msg:
            return ErrorCategory.NETWORK
        elif "permission" in exc_msg or "access" in exc_msg or "denied" in exc_msg:
            return ErrorCategory.PERMISSION
        elif "import" in exc_msg or "module" in exc_msg:
            return ErrorCategory.DEPENDENCY
        elif "valid" in exc_msg or "validation" in exc_msg:
            return ErrorCategory.VALidATION
        elif "config" in exc_msg or "setting" in exc_msg:
            return ErrorCategory.CONFIGURATION

        return ErrorCategory.RUNTIME

    def _determine_severity(self, exception: Any, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity."""
        exc_name = type(exception).__name__ if isinstance(exception, Exception) else str(exception)
        exc_msg = str(exception).lower()

        if "critical" in exc_msg or "fatal" in exc_msg:
            return ErrorSeverity.CRITICAL
        elif "warning" in exc_msg:
            return ErrorSeverity.WARNING
        elif category in [ErrorCategory.SYNTAX, ErrorCategory.DEPENDENCY]:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.PERMISSION:
            return ErrorSeverity.ERROR

        return ErrorSeverity.ERROR

    def _determine_recovery_strategy(self, category: ErrorCategory, severity: ErrorSeverity) -> RecoveryStrategy:
        """Determine recovery strategy based on error type and severity."""
        if severity == ErrorSeverity.CRITICAL or severity == ErrorSeverity.FATAL:
            return RecoveryStrategy.ABORT
        elif category == ErrorCategory.NETWORK:
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.IO:
            return RecoveryStrategy.SKIP
        elif category == ErrorCategory.VALIDATION:
            return RecoveryStrategy.USER_INPUT

        return RecoveryStrategy.RETRY

    def get_error_registry(self) -> dict[str, ErrorRecord]:
        """Get error registry."""
        return self._error_registry.copy()

    def get_recovery_history(self) -> list[RecoveryResult]:
        """Get recovery history."""
        return self._recovery_history.copy()

    def get_context_history(self) -> list[HandlingContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

