"""
Error handling utilities for Claude Playwright Agent.

This module provides:
- Custom exception classes for specific error scenarios
- User-friendly error formatting with helpful context
- Error recovery suggestions
- Error reporting utilities
"""

import sys
from pathlib import Path
from typing import Any


# =============================================================================
# Base Exception Classes
# =============================================================================


class AgentError(Exception):
    """
    Base exception for all agent-related errors.

    All custom exceptions should inherit from this class
    for consistent error handling.
    """

    def __init__(
        self,
        message: str,
        suggestion: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the agent error.

        Args:
            message: Error message
            suggestion: Optional suggestion for fixing the error
            context: Optional context information
        """
        super().__init__(message)
        self.suggestion = suggestion
        self.context = context or {}

    def __str__(self) -> str:
        """Return formatted error message."""
        msg = str(super().__str__())

        if self.suggestion:
            msg += f"\n\n💡 Suggestion: {self.suggestion}"

        if self.context:
            ctx_str = "\n".join(f"  {k}: {v}" for k, v in self.context.items())
            msg += f"\n\n📋 Context:\n{ctx_str}"

        return msg


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigError(AgentError):
    """Base exception for configuration errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""

    def __init__(self, config_path: Path) -> None:
        super().__init__(
            f"Configuration file not found: {config_path}",
            suggestion="Run 'cpa init' to initialize the project",
            context={"config_path": str(config_path)},
        )


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        errors: list[str] | None = None,
    ) -> None:
        context = {"validation_errors": errors} if errors else None
        super().__init__(
            f"Configuration validation failed: {message}",
            suggestion="Check your configuration file with 'cpa config validate'",
            context=context,
        )


# =============================================================================
# State Errors
# =============================================================================


class StateError(AgentError):
    """Base exception for state management errors."""

    pass


class StateLockError(StateError):
    """Raised when state is locked by another process."""

    def __init__(self, lock_file: Path) -> None:
        super().__init__(
            f"State is locked: {lock_file}",
            suggestion="Wait for the other process to finish or remove the lock file manually",
            context={"lock_file": str(lock_file)},
        )


class StateValidationError(StateError):
    """Raised when state validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(
            f"State validation failed: {message}",
            suggestion="Check your state files in .cpa/state/",
        )


class NotInitializedError(StateError):
    """Raised when project is not initialized."""

    def __init__(self, project_path: Path) -> None:
        super().__init__(
            f"Project not initialized: {project_path}",
            suggestion="Run 'cpa init' to initialize the project",
            context={"project_path": str(project_path)},
        )


# =============================================================================
# Skill Errors
# =============================================================================


class SkillError(AgentError):
    """Base exception for skill-related errors."""

    pass


class SkillLoadError(SkillError):
    """Raised when skill fails to load."""

    def __init__(self, skill_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to load skill '{skill_name}': {reason}",
            suggestion="Check the skill manifest file and dependencies",
            context={"skill_name": skill_name},
        )


class SkillNotFoundError(SkillError):
    """Raised when skill is not found."""

    def __init__(self, skill_name: str) -> None:
        super().__init__(
            f"Skill not found: {skill_name}",
            suggestion="Use 'cpa skills list' to see available skills",
            context={"skill_name": skill_name},
        )


class DependencyError(SkillError):
    """Raised when skill dependency is not satisfied."""

    def __init__(self, skill_name: str, dependency: str) -> None:
        super().__init__(
            f"Dependency '{dependency}' not found for skill '{skill_name}'",
            suggestion=f"Install the '{dependency}' skill first",
            context={"skill_name": skill_name, "dependency": dependency},
        )


class CircularDependencyError(SkillError):
    """Raised when circular dependencies are detected."""

    def __init__(self, cycle: list[str]) -> None:
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(
            f"Circular dependency detected: {cycle_str}",
            suggestion="Review skill dependencies and break the cycle",
            context={"cycle": cycle_str},
        )


class ManifestValidationError(SkillError):
    """Raised when skill manifest validation fails."""

    def __init__(self, manifest_path: Path, errors: list[str]) -> None:
        super().__init__(
            f"Manifest validation failed for {manifest_path}",
            suggestion="Fix the errors in the manifest file",
            context={"manifest_path": str(manifest_path), "errors": errors},
        )


# =============================================================================
# Recording Errors
# =============================================================================


class RecordingError(AgentError):
    """Base exception for recording-related errors."""

    pass


class RecordingNotFoundError(RecordingError):
    """Raised when recording file is not found."""

    def __init__(self, recording_path: Path) -> None:
        super().__init__(
            f"Recording not found: {recording_path}",
            suggestion="Check that the recording file exists in the recordings/ directory",
            context={"recording_path": str(recording_path)},
        )


class RecordingParseError(RecordingError):
    """Raised when recording parsing fails."""

    def __init__(self, recording_path: Path, reason: str) -> None:
        super().__init__(
            f"Failed to parse recording: {recording_path}",
            suggestion=f"Ensure the recording is a valid Playwright recording: {reason}",
            context={"recording_path": str(recording_path)},
        )


# =============================================================================
# Execution Errors
# =============================================================================


class ExecutionError(AgentError):
    """Base exception for execution-related errors."""

    pass


class TestExecutionError(ExecutionError):
    """Raised when test execution fails."""

    def __init__(self, message: str, exit_code: int | None = None) -> None:
        context = {"exit_code": exit_code} if exit_code else None
        super().__init__(
            f"Test execution failed: {message}",
            suggestion="Check test logs for detailed error information",
            context=context,
        )


class FrameworkNotFoundError(ExecutionError):
    """Raised when test framework is not found."""

    def __init__(self, framework: str) -> None:
        super().__init__(
            f"Test framework not found: {framework}",
            suggestion=f"Install {framework} using: pip install {framework}",
            context={"framework": framework},
        )


# =============================================================================
# Browser Errors
# =============================================================================


class BrowserError(AgentError):
    """Base exception for browser-related errors."""

    pass


class BrowserNotFoundError(BrowserError):
    """Raised when browser is not installed."""

    def __init__(self, browser: str) -> None:
        super().__init__(
            f"Browser not installed: {browser}",
            suggestion=f"Install the browser: playwright install {browser}",
            context={"browser": browser},
        )


class BrowserLaunchError(BrowserError):
    """Raised when browser fails to launch."""

    def __init__(self, browser: str, reason: str) -> None:
        super().__init__(
            f"Failed to launch browser {browser}: {reason}",
            suggestion="Check browser installation and display settings",
            context={"browser": browser},
        )


# =============================================================================
# Error Formatting Utilities
# =============================================================================


def format_error(error: Exception) -> str:
    """
    Format an exception for user-friendly display.

    Args:
        error: Exception to format

    Returns:
        Formatted error message
    """
    if isinstance(error, AgentError):
        return str(error)

    # Standard exception formatting
    error_type = type(error).__name__
    error_msg = str(error)

    # Add context for common exceptions
    suggestion = None
    if isinstance(error, FileNotFoundError):
        suggestion = "Check that the file exists and the path is correct"
    elif isinstance(error, PermissionError):
        suggestion = "Check file/directory permissions"
    elif isinstance(error, ValueError):
        suggestion = "Check that the input values are valid"
    elif isinstance(error, ImportError):
        suggestion = "Install the missing module using pip"
    elif isinstance(error, KeyboardInterrupt):
        return "Operation cancelled by user"

    output = f"[{error_type}] {error_msg}"
    if suggestion:
        output += f"\n\n💡 Suggestion: {suggestion}"

    return output


def print_error(error: Exception, verbose: bool = False) -> None:
    """
    Print an error to stderr with optional traceback.

    Args:
        error: Exception to print
        verbose: Whether to print full traceback
    """
    from rich.console import Console

    console = Console(stderr=True)

    # Print formatted error
    console.print(format_error(error), style="bold red")

    # Print traceback if verbose
    if verbose and hasattr(error, "__traceback__") and error.__traceback__:
        import traceback

        console.print("\n[bold]Traceback:[/bold]")
        console.print(traceback.format_exc(), style="dim")


def handle_error(error: Exception, exit_code: int = 1) -> None:
    """
    Handle an error by printing and exiting.

    Args:
        error: Exception to handle
        exit_code: Exit code (default: 1)
    """
    print_error(error)
    sys.exit(exit_code)


def create_error_context(
    **context: Any,
) -> dict[str, Any]:
    """
    Create error context dictionary.

    Args:
        **context: Key-value pairs for context

    Returns:
        Context dictionary
    """
    def convert_value(v: Any) -> Any:
        """Convert value to string if needed."""
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    return {k: convert_value(v) for k, v in context.items()}


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Base exceptions
    "AgentError",
    # Configuration errors
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # State errors
    "StateError",
    "StateLockError",
    "StateValidationError",
    "NotInitializedError",
    # Skill errors
    "SkillError",
    "SkillLoadError",
    "SkillNotFoundError",
    "DependencyError",
    "CircularDependencyError",
    "ManifestValidationError",
    # Recording errors
    "RecordingError",
    "RecordingNotFoundError",
    "RecordingParseError",
    # Execution errors
    "ExecutionError",
    "TestExecutionError",
    "FrameworkNotFoundError",
    # Browser errors
    "BrowserError",
    "BrowserNotFoundError",
    "BrowserLaunchError",
    # Utilities
    "format_error",
    "print_error",
    "handle_error",
    "create_error_context",
]
