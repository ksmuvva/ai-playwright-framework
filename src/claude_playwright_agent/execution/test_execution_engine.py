"""
Test Execution Engine for AI Playwright Framework

Executes tests with support for:
- Parallel execution
- Retry logic with exponential backoff
- Real-time progress tracking
- Memory integration for learning
- Comprehensive reporting
"""

import asyncio
import subprocess
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
import json

from .test_discovery import DiscoveredTest, TestType, TestFramework


class ExecutionStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    RETRYING = "retrying"


@dataclass
class TestExecutionResult:
    """Result of a test execution."""
    test_id: str
    test_name: str
    status: ExecutionStatus
    duration: float = 0.0
    start_time: str = ""
    end_time: str = ""
    error_message: str = ""
    stack_trace: str = ""
    retry_count: int = 0
    output: str = ""
    screenshots: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "output": self.output,
            "screenshots": self.screenshots,
            "artifacts": self.artifacts,
        }


@dataclass
class ExecutionConfig:
    """Configuration for test execution."""
    max_parallel: int = 3
    max_retries: int = 2
    retry_backoff_base: float = 1.0
    retry_backoff_multiplier: float = 2.0
    max_retry_delay: float = 30.0
    timeout: int = 300  # 5 minutes per test
    enable_video: bool = True
    enable_screenshots: bool = True
    enable_tracing: bool = False
    memory_enabled: bool = True
    headless: bool = True


class TestExecutionEngine:
    """
    Execute tests with parallel execution and retry logic.

    Features:
    - Parallel test execution
    - Automatic retry on failure
    - Real-time progress tracking
    - Memory integration
    - Comprehensive reporting
    """

    def __init__(
        self,
        project_path: str = ".",
        config: ExecutionConfig = None,
        memory_manager=None,
    ):
        """
        Initialize the execution engine.

        Args:
            project_path: Root project directory
            config: Execution configuration
            memory_manager: Optional memory manager for learning
        """
        self.project_path = Path(project_path)
        self.config = config or ExecutionConfig()
        self.memory = memory_manager

        self.results: dict[str, TestExecutionResult] = {}
        self.execution_queue: asyncio.Queue = None
        self.workers: list[asyncio.Task] = []

    async def run_tests(
        self,
        tests: list[DiscoveredTest],
        tags: Optional[list[str]] = None,
    ) -> list[TestExecutionResult]:
        """
        Run tests with parallel execution.

        Args:
            tests: List of tests to run
            tags: Optional tags to filter by

        Returns:
            List of execution results
        """
        # Filter tests by tags if specified
        if tags:
            tests = [t for t in tests if any(tag in t.tags for tag in tags)]

        # Initialize queue
        self.execution_queue = asyncio.Queue()
        for test in tests:
            await self.execution_queue.put(test)

        # Create worker tasks
        self.workers = [
            asyncio.create_task(self._worker(worker_id))
            for worker_id in range(self.config.max_parallel)
        ]

        # Wait for all tests to complete
        await self.execution_queue.join()

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish cancellation
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Store results in memory
        if self.memory:
            await self._store_results_in_memory()

        return list(self.results.values())

    async def _worker(self, worker_id: int) -> None:
        """
        Worker process for executing tests.

        Args:
            worker_id: Worker identifier
        """
        while True:
            try:
                # Get test from queue
                test: DiscoveredTest = await self.execution_queue.get()

                # Execute test
                result = await self._execute_test(test)
                self.results[test.test_id] = result

                # Mark task as done
                self.execution_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

    async def _execute_test(
        self,
        test: DiscoveredTest,
    ) -> TestExecutionResult:
        """
        Execute a single test with retry logic.

        Args:
            test: Test to execute

        Returns:
            Execution result
        """
        result = TestExecutionResult(
            test_id=test.test_id,
            test_name=test.name,
            status=ExecutionStatus.PENDING,
        )

        retry_count = 0
        max_retries = self.config.max_retries

        while retry_count <= max_retries:
            if retry_count > 0:
                result.status = ExecutionStatus.RETRYING
                await self._log_retry(test, retry_count)

                # Calculate backoff delay
                delay = min(
                    self.config.retry_backoff_base *
                    (self.config.retry_backoff_multiplier ** (retry_count - 1)),
                    self.config.max_retry_delay,
                )
                await asyncio.sleep(delay)

            # Execute test
            result = await self._run_single_test(test)
            result.retry_count = retry_count

            # Check if we should retry
            if result.status in [ExecutionStatus.PASSED, ExecutionStatus.SKIPPED]:
                break

            if retry_count < max_retries:
                retry_count += 1
            else:
                break

        return result

    async def _run_single_test(
        self,
        test: DiscoveredTest,
    ) -> TestExecutionResult:
        """
        Run a single test.

        Args:
            test: Test to run

        Returns:
            Execution result
        """
        result = TestExecutionResult(
            test_id=test.test_id,
            test_name=test.name,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now().isoformat(),
        )

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute based on test type
            if test.test_type == TestType.BDD_FEATURE:
                await self._run_bdd_test(test, result)
            elif test.test_type == TestType.PLAYWRIGHT_RECORDING:
                await self._run_playwright_test(test, result)
            elif test.test_type == TestType.PYTHON_TEST:
                await self._run_python_test(test, result)
            else:
                result.status = ExecutionStatus.ERROR
                result.error_message = f"Unknown test type: {test.test_type}"

        except Exception as e:
            result.status = ExecutionStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = __import__('traceback').format_exc()

        end_time = asyncio.get_event_loop().time()
        result.duration = end_time - start_time
        result.end_time = datetime.now().isoformat()

        return result

    async def _run_bdd_test(self, test: DiscoveredTest, result: TestExecutionResult) -> None:
        """
        Run a BDD test using behave.

        Args:
            test: Test to run
            result: Result object to update
        """
        # Determine command based on framework
        if test.framework == TestFramework.BEHAVE:
            cmd = [
                "behave",
                test.file_path,
                "-f", "json",
                "--outfile", "-",
            ]

            # Add scenario filter if test is a scenario
            if ":" in test.name:
                cmd.extend(["--name", test.name])

        elif test.framework == TestFramework.PYTEST_BDD:
            cmd = [
                "pytest",
                test.file_path,
                "-v",
                "--tb=short",
            ]
        else:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Unknown BDD framework: {test.framework}"
            return

        # Run command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_path,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout,
            )

            result.output = stdout.decode('utf-8', errors='ignore')

            if process.returncode == 0:
                result.status = ExecutionStatus.PASSED
            else:
                result.status = ExecutionStatus.FAILED
                result.error_message = stderr.decode('utf-8', errors='ignore')

        except asyncio.TimeoutError:
            process.kill()
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Test timed out after {self.config.timeout} seconds"

    async def _run_playwright_test(self, test: DiscoveredTest, result: TestExecutionResult) -> None:
        """
        Run a Playwright test.

        Args:
            test: Test to run
            result: Result object to update
        """
        cmd = [
            "npx",
            "playwright",
            "test",
            test.file_path,
            "--reporter=json",
        ]

        if self.config.headless:
            cmd.append("--headed=false")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_path,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout,
            )

            result.output = stdout.decode('utf-8', errors='ignore')

            if process.returncode == 0:
                result.status = ExecutionStatus.PASSED
            else:
                result.status = ExecutionStatus.FAILED
                result.error_message = stderr.decode('utf-8', errors='ignore')

        except asyncio.TimeoutError:
            process.kill()
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Test timed out after {self.config.timeout} seconds"

    async def _run_python_test(self, test: DiscoveredTest, result: TestExecutionResult) -> None:
        """
        Run a Python test using pytest.

        Args:
            test: Test to run
            result: Result object to update
        """
        cmd = [
            "pytest",
            test.file_path,
            "-k", test.name,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file", "-",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_path,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout,
            )

            result.output = stdout.decode('utf-8', errors='ignore')

            if process.returncode == 0:
                result.status = ExecutionStatus.PASSED
            else:
                result.status = ExecutionStatus.FAILED
                result.error_message = stderr.decode('utf-8', errors='ignore')

        except asyncio.TimeoutError:
            process.kill()
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Test timed out after {self.config.timeout} seconds"

    async def _log_retry(self, test: DiscoveredTest, retry_count: int) -> None:
        """
        Log a retry attempt.

        Args:
            test: Test being retried
            retry_count: Retry attempt number
        """
        print(f"Retrying {test.name} (attempt {retry_count})")

    async def _store_results_in_memory(self) -> None:
        """Store test results in memory for learning."""
        if not self.memory:
            return

        for result in self.results.values():
            await self.memory.store(
                key=f"test_result:{result.test_id}",
                value=result.to_dict(),
                type=self.memory.MemoryType.EPISODIC,
                priority=self.memory.MemoryPriority.MEDIUM,
                tags=["test_execution", result.status.value],
            )

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Get summary of test execution.

        Returns:
            Dictionary with execution summary
        """
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.status == ExecutionStatus.PASSED)
        failed = sum(1 for r in self.results.values() if r.status == ExecutionStatus.FAILED)
        errors = sum(1 for r in self.results.values() if r.status == ExecutionStatus.ERROR)
        skipped = sum(1 for r in self.results.values() if r.status == ExecutionStatus.SKIPPED)

        total_duration = sum(r.duration for r in self.results.values())

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "total_duration": total_duration,
            "average_duration": total_duration / total if total > 0 else 0,
            "retried_tests": sum(1 for r in self.results.values() if r.retry_count > 0),
        }
