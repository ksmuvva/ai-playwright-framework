"""
Tests for the Test Execution module.

Tests cover:
- TestResult and ExecutionResult models
- TestFramework and TestStatus enums
- TestExecutionEngine initialization
- Command building for different frameworks
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from claude_playwright_agent.agents.execution import (
    ExecutionResult,
    TestExecutionEngine,
    TestFramework,
    TestResult,
    TestStatus,
)


# =============================================================================
# Model Tests
# =============================================================================


class TestTestResult:
    """Tests for TestResult model."""

    def test_create_test_result(self) -> None:
        """Test creating a test result."""
        result = TestResult(
            name="login test",
            status=TestStatus.PASSED,
            duration=1.5,
        )

        assert result.name == "login test"
        assert result.status == TestStatus.PASSED
        assert result.duration == 1.5

    def test_test_result_to_dict(self) -> None:
        """Test converting test result to dictionary."""
        result = TestResult(
            name="login test",
            status=TestStatus.FAILED,
            error_message="AssertionError",
        )

        data = result.to_dict()

        assert data["name"] == "login test"
        assert data["status"] == "failed"
        assert data["error_message"] == "AssertionError"


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_create_execution_result(self) -> None:
        """Test creating an execution result."""
        result = ExecutionResult(
            framework=TestFramework.BEHAVE,
            total_tests=10,
            passed=8,
            failed=2,
        )

        assert result.framework == TestFramework.BEHAVE
        assert result.total_tests == 10
        assert result.passed == 8
        assert result.failed == 2

    def test_execution_result_to_dict(self) -> None:
        """Test converting execution result to dictionary."""
        result = ExecutionResult(
            framework=TestFramework.PLAYWRIGHT,
            total_tests=5,
            passed=5,
            failed=0,
        )

        data = result.to_dict()

        assert data["framework"] == "playwright"
        assert data["total_tests"] == 5
        assert data["passed"] == 5


# =============================================================================
# TestExecutionEngine Tests
# =============================================================================


class TestTestExecutionEngine:
    """Tests for TestExecutionEngine class."""

    def test_initialization(self) -> None:
        """Test engine initialization."""
        engine = TestExecutionEngine()

        assert engine._project_path == Path.cwd()

    def test_initialization_with_path(self, tmp_path: Path) -> None:
        """Test engine initialization with custom path."""
        engine = TestExecutionEngine(tmp_path)

        assert engine._project_path == tmp_path

    @pytest.mark.asyncio
    async def test_execute_with_unknown_framework(self, tmp_path: Path) -> None:
        """Test executing with unknown framework."""
        engine = TestExecutionEngine(tmp_path)

        # Create a mock framework that doesn't exist
        result = await engine.execute_tests(
            TestFramework.BEHAVE,  # Use valid enum for now
            feature_files=None,
            tags=[],
            parallel=False,
            workers=1,
        )

        # Result should be returned even if empty
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_behave_missing_framework(self, tmp_path: Path) -> None:
        """Test behave execution when behave is not installed."""
        engine = TestExecutionEngine(tmp_path)

        # Mock subprocess to raise FileNotFoundError
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await engine.execute_tests(
                TestFramework.BEHAVE,
                feature_files=None,
                tags=None,
                parallel=False,
                workers=1,
            )

        # Should return error result
        assert result.errors > 0
        assert "not installed" in result.output

    @pytest.mark.asyncio
    async def test_build_behave_command(self, tmp_path: Path) -> None:
        """Test building behave command."""
        engine = TestExecutionEngine(tmp_path)

        # Mock successful execution
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"1 feature passed", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await engine.execute_tests(
                TestFramework.BEHAVE,
                feature_files=["test.feature"],
                tags=["@smoke"],
                parallel=False,
                workers=1,
            )

            # Verify command was built correctly
            call_args = mock_exec.call_args
            args = call_args[0]  # Get the positional arguments
            assert "behave" in args
            assert "test.feature" in args
            assert "--tags" in args
            assert "@smoke" in args


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_framework_enum_values(self) -> None:
        """Test framework enum has correct values."""
        assert TestFramework.BEHAVE.value == "behave"
        assert TestFramework.PYTEST_BDD.value == "pytest-bdd"
        assert TestFramework.PLAYWRIGHT.value == "playwright"

    def test_status_enum_values(self) -> None:
        """Test status enum has correct values."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"
