"""
Tests for the Errors module.

Tests cover:
- Custom exception classes
- Error formatting and display
- Error context handling
- Error suggestion display
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from claude_playwright_agent.errors import (
    AgentError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    StateError,
    StateLockError,
    StateValidationError,
    NotInitializedError,
    SkillError,
    SkillLoadError,
    SkillNotFoundError,
    DependencyError,
    CircularDependencyError,
    ManifestValidationError,
    RecordingError,
    RecordingNotFoundError,
    RecordingParseError,
    ExecutionError,
    TestExecutionError,
    FrameworkNotFoundError,
    BrowserError,
    BrowserNotFoundError,
    BrowserLaunchError,
    format_error,
    print_error,
    handle_error,
    create_error_context,
)


# =============================================================================
# AgentError Tests
# =============================================================================


class TestAgentError:
    """Tests for AgentError base class."""

    def test_basic_error_message(self) -> None:
        """Test basic error message."""
        error = AgentError("Test error")
        assert str(error) == "Test error"

    def test_error_with_suggestion(self) -> None:
        """Test error with suggestion."""
        error = AgentError("Test error", suggestion="Try this instead")
        output = str(error)
        assert "Test error" in output
        assert "Suggestion:" in output
        assert "Try this instead" in output

    def test_error_with_context(self) -> None:
        """Test error with context."""
        error = AgentError("Test error", context={"key": "value", "count": 5})
        output = str(error)
        assert "Test error" in output
        assert "Context:" in output
        assert "key: value" in output
        assert "count: 5" in output

    def test_error_with_suggestion_and_context(self) -> None:
        """Test error with both suggestion and context."""
        error = AgentError(
            "Test error",
            suggestion="Fix it",
            context={"file": "test.py"},
        )
        output = str(error)
        assert "Test error" in output
        assert "Suggestion:" in output
        assert "Fix it" in output
        assert "Context:" in output
        assert "file: test.py" in output

    def test_empty_context(self) -> None:
        """Test error with empty context."""
        error = AgentError("Test error", context={})
        output = str(error)
        assert "Test error" in output
        assert "Context:" not in output


# =============================================================================
# Configuration Error Tests
# =============================================================================


class TestConfigErrors:
    """Tests for configuration error classes."""

    def test_config_not_found_error(self) -> None:
        """Test ConfigNotFoundError."""
        config_path = Path("/test/config.yaml")
        error = ConfigNotFoundError(config_path)

        assert "Configuration file not found" in str(error)
        assert str(config_path) in str(error)
        assert "Suggestion:" in str(error)
        assert "cpa init" in str(error)
        assert error.context["config_path"] == str(config_path)

    def test_config_validation_error_basic(self) -> None:
        """Test ConfigValidationError without errors list."""
        error = ConfigValidationError("Invalid value")

        assert "Configuration validation failed" in str(error)
        assert "Invalid value" in str(error)
        assert "Suggestion:" in str(error)

    def test_config_validation_error_with_errors(self) -> None:
        """Test ConfigValidationError with errors list."""
        errors = ["Missing field: name", "Invalid type for version"]
        error = ConfigValidationError("Validation failed", errors=errors)

        assert "Configuration validation failed" in str(error)
        assert "Validation failed" in str(error)
        assert error.context["validation_errors"] == errors
        assert "Missing field: name" in str(error.context["validation_errors"])


# =============================================================================
# State Error Tests
# =============================================================================


class TestStateErrors:
    """Tests for state error classes."""

    def test_state_lock_error(self) -> None:
        """Test StateLockError."""
        lock_file = Path("/test/lock")
        error = StateLockError(lock_file)

        assert "State is locked" in str(error)
        assert str(lock_file) in str(error)
        assert "Suggestion:" in str(error)
        assert error.context["lock_file"] == str(lock_file)

    def test_state_validation_error(self) -> None:
        """Test StateValidationError."""
        error = StateValidationError("Invalid state data")

        assert "State validation failed" in str(error)
        assert "Invalid state data" in str(error)
        assert "Suggestion:" in str(error)
        assert ".cpa/state/" in str(error)

    def test_not_initialized_error(self) -> None:
        """Test NotInitializedError."""
        project_path = Path("/test/project")
        error = NotInitializedError(project_path)

        assert "Project not initialized" in str(error)
        assert str(project_path) in str(error)
        assert "Suggestion:" in str(error)
        assert "cpa init" in str(error)
        assert error.context["project_path"] == str(project_path)


# =============================================================================
# Skill Error Tests
# =============================================================================


class TestSkillErrors:
    """Tests for skill error classes."""

    def test_skill_load_error(self) -> None:
        """Test SkillLoadError."""
        error = SkillLoadError("test-skill", "Module not found")

        assert "Failed to load skill" in str(error)
        assert "test-skill" in str(error)
        assert "Module not found" in str(error)
        assert "Suggestion:" in str(error)
        assert error.context["skill_name"] == "test-skill"

    def test_skill_not_found_error(self) -> None:
        """Test SkillNotFoundError."""
        error = SkillNotFoundError("missing-skill")

        assert "Skill not found" in str(error)
        assert "missing-skill" in str(error)
        assert "Suggestion:" in str(error)
        assert "cpa skills list" in str(error)

    def test_dependency_error(self) -> None:
        """Test DependencyError."""
        error = DependencyError("my-skill", "dependency-skill")

        assert "Dependency" in str(error)
        assert "not found" in str(error)
        assert "my-skill" in str(error)
        assert "dependency-skill" in str(error)
        assert error.context["skill_name"] == "my-skill"
        assert error.context["dependency"] == "dependency-skill"

    def test_circular_dependency_error(self) -> None:
        """Test CircularDependencyError."""
        cycle = ["skill-a", "skill-b", "skill-c"]
        error = CircularDependencyError(cycle)

        output = str(error)
        assert "Circular dependency detected" in output
        assert "skill-a" in output
        assert "skill-b" in output
        assert "skill-c" in output
        assert "Suggestion:" in output
        assert error.context["cycle"] == "skill-a -> skill-b -> skill-c -> skill-a"

    def test_manifest_validation_error(self) -> None:
        """Test ManifestValidationError."""
        manifest_path = Path("/skills/test/skill.yaml")
        errors = ["Missing name field", "Invalid version format"]
        error = ManifestValidationError(manifest_path, errors)

        assert "Manifest validation failed" in str(error)
        assert str(manifest_path) in str(error)
        assert error.context["manifest_path"] == str(manifest_path)
        assert error.context["errors"] == errors


# =============================================================================
# Recording Error Tests
# =============================================================================


class TestRecordingErrors:
    """Tests for recording error classes."""

    def test_recording_not_found_error(self) -> None:
        """Test RecordingNotFoundError."""
        recording_path = Path("/recordings/test.js")
        error = RecordingNotFoundError(recording_path)

        assert "Recording not found" in str(error)
        assert str(recording_path) in str(error)
        assert "Suggestion:" in str(error)
        assert "recordings/" in str(error)

    def test_recording_parse_error(self) -> None:
        """Test RecordingParseError."""
        recording_path = Path("/recordings/bad.js")
        error = RecordingParseError(recording_path, "Invalid JSON")

        assert "Failed to parse recording" in str(error)
        assert str(recording_path) in str(error)
        assert "Invalid JSON" in str(error)
        assert "Suggestion:" in str(error)


# =============================================================================
# Execution Error Tests
# =============================================================================


class TestExecutionErrors:
    """Tests for execution error classes."""

    def test_test_execution_error(self) -> None:
        """Test TestExecutionError without exit code."""
        from claude_playwright_agent.errors import TestExecutionError
        error = TestExecutionError("Tests failed")

        assert "Test execution failed" in str(error)
        assert "Tests failed" in str(error)
        assert "Suggestion:" in str(error)

    def test_test_execution_error_with_exit_code(self) -> None:
        """Test TestExecutionError with exit code."""
        from claude_playwright_agent.errors import TestExecutionError
        error = TestExecutionError("Tests failed", exit_code=2)

        assert "Test execution failed" in str(error)
        assert error.context["exit_code"] == 2

    def test_framework_not_found_error(self) -> None:
        """Test FrameworkNotFoundError."""
        error = FrameworkNotFoundError("pytest-bdd")

        assert "Test framework not found" in str(error)
        assert "pytest-bdd" in str(error)
        assert "Suggestion:" in str(error)
        assert "pip install" in str(error)


# =============================================================================
# Browser Error Tests
# =============================================================================


class TestBrowserErrors:
    """Tests for browser error classes."""

    def test_browser_not_found_error(self) -> None:
        """Test BrowserNotFoundError."""
        error = BrowserNotFoundError("chromium")

        assert "Browser not installed" in str(error)
        assert "chromium" in str(error)
        assert "Suggestion:" in str(error)
        assert "playwright install" in str(error)

    def test_browser_launch_error(self) -> None:
        """Test BrowserLaunchError."""
        error = BrowserLaunchError("firefox", "Display not set")

        assert "Failed to launch browser" in str(error)
        assert "firefox" in str(error)
        assert "Display not set" in str(error)
        assert "Suggestion:" in str(error)


# =============================================================================
# Error Formatting Tests
# =============================================================================


class TestErrorFormatting:
    """Tests for error formatting utilities."""

    def test_format_agent_error(self) -> None:
        """Test formatting AgentError."""
        error = AgentError("Test error", suggestion="Fix it")
        formatted = format_error(error)

        assert "Test error" in formatted
        assert "Fix it" in formatted

    def test_format_standard_exception(self) -> None:
        """Test formatting standard exception."""
        error = ValueError("Invalid value")
        formatted = format_error(error)

        assert "ValueError" in formatted
        assert "Invalid value" in formatted

    def test_format_file_not_found_error(self) -> None:
        """Test formatting FileNotFoundError."""
        error = FileNotFoundError("/test/file.txt")
        formatted = format_error(error)

        assert "FileNotFoundError" in formatted
        assert "Suggestion:" in formatted
        assert "file exists" in formatted.lower()

    def test_format_permission_error(self) -> None:
        """Test formatting PermissionError."""
        error = PermissionError("Permission denied")
        formatted = format_error(error)

        assert "PermissionError" in formatted
        assert "Suggestion:" in formatted
        assert "permissions" in formatted.lower()

    def test_format_value_error(self) -> None:
        """Test formatting ValueError."""
        error = ValueError("Invalid input")
        formatted = format_error(error)

        assert "ValueError" in formatted
        assert "Suggestion:" in formatted
        assert "valid" in formatted.lower()

    def test_format_import_error(self) -> None:
        """Test formatting ImportError."""
        error = ImportError("No module named 'test'")
        formatted = format_error(error)

        assert "ImportError" in formatted
        assert "Suggestion:" in formatted
        assert "pip" in formatted.lower()

    def test_format_keyboard_interrupt(self) -> None:
        """Test formatting KeyboardInterrupt."""
        error = KeyboardInterrupt()
        formatted = format_error(error)

        assert "cancelled" in formatted.lower()
        assert "Suggestion:" not in formatted


# =============================================================================
# Print Error Tests
# =============================================================================


class TestPrintError:
    """Tests for print_error utility."""

    @patch("rich.console.Console")
    def test_print_error_basic(self, mock_console: Mock) -> None:
        """Test basic error printing."""
        error = AgentError("Test error")
        print_error(error)

        mock_console.return_value.print.assert_called_once()

    @patch("rich.console.Console")
    @patch("traceback.format_exc")
    def test_print_error_verbose(self, mock_tb: Mock, mock_console: Mock) -> None:
        """Test verbose error printing with traceback."""
        error = AgentError("Test error")

        # Give the error a traceback
        try:
            raise error
        except AgentError:
            print_error(error, verbose=True)

        # Should print error and traceback
        assert mock_console.return_value.print.call_count >= 1


# =============================================================================
# Handle Error Tests
# =============================================================================


class TestHandleError:
    """Tests for handle_error utility."""

    def test_handle_error_exits(self) -> None:
        """Test that handle_error calls sys.exit."""
        error = AgentError("Test error")

        with pytest.raises(SystemExit) as exc_info:
            handle_error(error)

        assert exc_info.value.code == 1

    def test_handle_error_custom_exit_code(self) -> None:
        """Test handle_error with custom exit code."""
        error = AgentError("Test error")

        with pytest.raises(SystemExit) as exc_info:
            handle_error(error, exit_code=42)

        assert exc_info.value.code == 42


# =============================================================================
# Create Error Context Tests
# =============================================================================


class TestCreateErrorContext:
    """Tests for create_error_context utility."""

    def test_create_simple_context(self) -> None:
        """Test creating simple context."""
        context = create_error_context(name="test", count=5)

        assert context == {"name": "test", "count": 5}

    def test_create_context_with_path(self) -> None:
        """Test creating context with Path object."""
        path = Path("/test/file.txt")
        context = create_error_context(file=path)

        assert context["file"] == str(path)

    def test_create_context_with_complex_object(self) -> None:
        """Test creating context with non-primitive object."""
        obj = object()
        context = create_error_context(item=obj)

        assert isinstance(context["item"], str)

    def test_create_context_with_primitives(self) -> None:
        """Test creating context with primitive types."""
        context = create_error_context(
            string="text",
            integer=42,
            float=3.14,
            boolean=True,
            none=None,
        )

        assert context["string"] == "text"
        assert context["integer"] == 42
        assert context["float"] == 3.14
        assert context["boolean"] is True
        assert context["none"] is None


# =============================================================================
# Exception Hierarchy Tests
# =============================================================================


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_agent_error_is_exception(self) -> None:
        """Test that AgentError inherits from Exception."""
        assert issubclass(AgentError, Exception)

    def test_config_error_is_agent_error(self) -> None:
        """Test that ConfigError inherits from AgentError."""
        assert issubclass(ConfigError, AgentError)

    def test_config_not_found_is_config_error(self) -> None:
        """Test that ConfigNotFoundError inherits from ConfigError."""
        assert issubclass(ConfigNotFoundError, ConfigError)

    def test_state_error_is_agent_error(self) -> None:
        """Test that StateError inherits from AgentError."""
        assert issubclass(StateError, AgentError)

    def test_skill_error_is_agent_error(self) -> None:
        """Test that SkillError inherits from AgentError."""
        assert issubclass(SkillError, AgentError)

    def test_recording_error_is_agent_error(self) -> None:
        """Test that RecordingError inherits from AgentError."""
        assert issubclass(RecordingError, AgentError)

    def test_execution_error_is_agent_error(self) -> None:
        """Test that ExecutionError inherits from AgentError."""
        assert issubclass(ExecutionError, AgentError)

    def test_browser_error_is_agent_error(self) -> None:
        """Test that BrowserError inherits from AgentError."""
        assert issubclass(BrowserError, AgentError)

    def test_catch_base_exception(self) -> None:
        """Test that specific errors can be caught by base exceptions."""
        errors = [
            ConfigNotFoundError(Path("/test")),
            NotInitializedError(Path("/test")),
            SkillLoadError("test", "reason"),
            RecordingNotFoundError(Path("/test")),
            TestExecutionError("failed"),
            BrowserNotFoundError("chromium"),
        ]

        for error in errors:
            # All should be catchable as AgentError
            assert isinstance(error, AgentError)
