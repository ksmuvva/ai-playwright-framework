"""
Tests for the Execution Agent.

Tests cover:
- ExecutionAgent initialization
- Processing execution requests
- Error handling for invalid frameworks
- Running tests with different parameters
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from claude_playwright_agent.agents.exec_agent import ExecutionAgent


# =============================================================================
# ExecutionAgent Tests
# =============================================================================


class TestExecutionAgent:
    """Tests for ExecutionAgent class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test agent initialization."""
        agent = ExecutionAgent(tmp_path)

        assert agent._project_path == tmp_path
        assert agent._engine is not None

    def test_initialization_without_path(self) -> None:
        """Test agent initialization without path."""
        agent = ExecutionAgent()

        assert agent._project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_process_valid_framework(self, tmp_path: Path) -> None:
        """Test processing with valid framework."""
        agent = ExecutionAgent(tmp_path)
        await agent.initialize()

        # Mock the engine to return a result
        mock_result = AsyncMock()
        mock_result.to_dict.return_value = {
            "framework": "behave",
            "total_tests": 1,
            "passed": 1,
            "failed": 0,
        }

        with patch.object(agent._engine, "execute_tests", return_value=mock_result):
            result = await agent.process({
                "framework": "behave",
            })

            assert result["success"] is True
            assert "result" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_invalid_framework(self, tmp_path: Path) -> None:
        """Test processing with invalid framework."""
        agent = ExecutionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "framework": "invalid_framework",
        })

        assert result["success"] is False
        assert "error" in result
        assert "Unknown framework" in result["error"]

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_run_tests_method(self, tmp_path: Path) -> None:
        """Test the run_tests method."""
        agent = ExecutionAgent(tmp_path)
        await agent.initialize()

        mock_result = AsyncMock()
        mock_result.to_dict.return_value = {"total_tests": 1, "passed": 1}

        with patch.object(agent._engine, "execute_tests", return_value=mock_result):
            result = await agent.run_tests(
                framework="behave",
                feature_files=["test.feature"],
            )

            assert result["success"] is True

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_run_all_tests(self, tmp_path: Path) -> None:
        """Test running all tests."""
        agent = ExecutionAgent(tmp_path)
        await agent.initialize()

        mock_result = AsyncMock()
        mock_result.to_dict.return_value = {"total_tests": 5, "passed": 3, "failed": 2}

        with patch.object(agent._engine, "execute_tests", return_value=mock_result):
            result = await agent.run_all_tests(
                framework="pytest-bdd",
                parallel=True,
                workers=2,
            )

            assert result["success"] is True

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_run_tagged_tests(self, tmp_path: Path) -> None:
        """Test running tests with tags."""
        agent = ExecutionAgent(tmp_path)
        await agent.initialize()

        mock_result = AsyncMock()
        mock_result.to_dict.return_value = {"total_tests": 2, "passed": 2}

        with patch.object(agent._engine, "execute_tests", return_value=mock_result):
            result = await agent.run_tagged_tests(
                tags=["@smoke", "@fast"],
                framework="behave",
            )

            assert result["success"] is True

        await agent.cleanup()
