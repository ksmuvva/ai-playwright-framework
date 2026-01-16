"""Unit tests for E9.1 - Parallel Execution skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e9_1_parallel_execution import (
    ParallelExecutionAgent,
    ParallelTask,
    WorkerInfo,
    WorkerStatus,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestWorkerStatus:
    @pytest.mark.unit
    def test_worker_status_values(self):
        assert WorkerStatus.IDLE.value == "idle"
        assert WorkerStatus.BUSY.value == "busy"


class TestWorkerInfo:
    @pytest.mark.unit
    def test_worker_info_creation(self):
        info = WorkerInfo(
            worker_id="worker_001",
            status=WorkerStatus.IDLE,
        )
        assert info.worker_id == "worker_001"


class TestParallelTask:
    @pytest.mark.unit
    def test_parallel_task_creation(self):
        task = ParallelTask(
            task_id="task_001",
            task_data={"test": "data"},
        )
        assert task.task_id == "task_001"


class TestParallelExecutionAgent:
    @pytest.fixture
    def agent(self):
        return ParallelExecutionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e9_1_parallel_execution"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_execute_parallel(self, agent):
        context = {"tasks": [{"id": "t1"}, {"id": "t2"}]}
        result = await agent.run("execute", context)
        assert "parallel" in result.lower() or "executed" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_spawn_workers(self, agent):
        context = {"worker_count": 3}
        result = await agent.run("spawn", context)
        assert "worker" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_distribute_tasks(self, agent):
        context = {"tasks": [{"id": "t1"}]}
        result = await agent.run("distribute", context)
        assert "distributed" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
