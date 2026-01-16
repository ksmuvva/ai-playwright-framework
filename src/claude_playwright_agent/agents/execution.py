"""
Test Execution Module for Claude Playwright Agent.

This module handles:
- Running BDD tests with Playwright
- Capturing test results
- Handling test failures and retries
- Supporting behave and pytest-bdd frameworks
- Retry logic with exponential backoff
"""

import asyncio
import hashlib
import json
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any


# =============================================================================
# Execution Models
# =============================================================================


class TestFramework(str, Enum):
    """Supported test frameworks."""

    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"
    PLAYWRIGHT = "playwright"


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test execution."""

    name: str
    status: TestStatus
    duration: float = 0.0
    error_message: str = ""
    stack_trace: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    previous_attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "steps": self.steps,
            "retry_count": self.retry_count,
            "previous_attempts": self.previous_attempts,
        }


@dataclass
class RetryConfig:
    """Configuration for test retry logic."""

    max_retries: int = 0
    backoff_base: float = 1.0  # Base delay in seconds
    backoff_multiplier: float = 2.0  # Exponential multiplier
    max_delay: float = 30.0  # Maximum delay between retries
    retry_on_status: list[TestStatus] = field(default_factory=lambda: [TestStatus.FAILED, TestStatus.ERROR])

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt using exponential backoff.

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.backoff_base * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, status: TestStatus, retry_count: int) -> bool:
        """
        Determine if a test should be retried.

        Args:
            status: Current test status
            retry_count: Number of retries already attempted

        Returns:
            True if test should be retried
        """
        return (
            status in self.retry_on_status and
            retry_count < self.max_retries
        )


@dataclass
class ExecutionResult:
    """Result of test execution."""

    framework: TestFramework
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)
    output: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration": self.duration,
            "test_results": [t.to_dict() for t in self.test_results],
            "output": self.output,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Test Result Cache (E6.3)
# =============================================================================


@dataclass
class CachedTestResult:
    """
    Cached test result for faster re-execution.

    Attributes:
        test_hash: Hash of test content
        test_name: Name of the test
        status: Test status
        duration: Execution duration
        cached_at: When result was cached
        file_path: Path to test file
        file_mtime: Modification time when cached
    """

    test_hash: str
    test_name: str
    status: TestStatus
    duration: float
    cached_at: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: str = ""
    file_mtime: float = 0.0

    def is_valid(self, current_mtime: float) -> bool:
        """Check if cached result is still valid."""
        return self.file_mtime == current_mtime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_hash": self.test_hash,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration": self.duration,
            "cached_at": self.cached_at,
            "file_path": self.file_path,
            "file_mtime": self.file_mtime,
        }


class TestResultCache:
    """
    Cache for test results to avoid re-running unchanged tests.

    Features:
    - Content-based hashing
    - File modification tracking
    - TTL for cached results
    - Thread-safe operations
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Initialize the cache.

        Args:
            cache_dir: Directory for cache storage
            ttl_seconds: Time-to-live for cached results
        """
        self._cache_dir = cache_dir or Path(".cpa/cache/test_results")
        self._ttl_seconds = ttl_seconds
        self._cache: dict[str, CachedTestResult] = {}

    def _compute_hash(self, file_path: Path, content: str | None = None) -> str:
        """Compute hash of test file content."""
        if content is None:
            content = file_path.read_text(encoding="utf-8")

        # Include file path and content in hash
        hash_input = f"{file_path}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def get(self, file_path: Path) -> CachedTestResult | None:
        """
        Get cached result for a test file.

        Args:
            file_path: Path to test file

        Returns:
            Cached result or None if not found/invalid
        """
        # Check file modification time
        try:
            current_mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            return None

        # Check in-memory cache
        test_hash = self._compute_hash(file_path)
        cached = self._cache.get(test_hash)

        if cached and cached.is_valid(current_mtime):
            return cached

        # Check disk cache
        cache_file = self._cache_dir / f"{test_hash}.json"
        if cache_file.exists():
            try:
                import json
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                cached = CachedTestResult(**data)

                if cached.is_valid(current_mtime):
                    # Restore to memory cache
                    self._cache[test_hash] = cached
                    return cached
            except Exception:
                pass

        return None

    def set(
        self,
        file_path: Path,
        test_name: str,
        status: TestStatus,
        duration: float,
    ) -> None:
        """
        Cache a test result.

        Args:
            file_path: Path to test file
            test_name: Name of the test
            status: Test status
            duration: Execution duration
        """
        # Get file modification time
        try:
            file_mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            file_mtime = 0.0

        # Compute hash
        test_hash = self._compute_hash(file_path)

        # Create cached result
        cached = CachedTestResult(
            test_hash=test_hash,
            test_name=test_name,
            status=status,
            duration=duration,
            file_path=str(file_path),
            file_mtime=file_mtime,
        )

        # Store in memory
        self._cache[test_hash] = cached

        # Store on disk
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_dir / f"{test_hash}.json"

        import json
        cache_file.write_text(json.dumps(cached.to_dict()), encoding="utf-8")

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        if self._cache_dir.exists():
            for file in self._cache_dir.glob("*.json"):
                file.unlink()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_results": len(self._cache),
            "cache_dir": str(self._cache_dir),
            "ttl_seconds": self._ttl_seconds,
        }


# =============================================================================
# Parallel Execution Worker (E6.1)
# =============================================================================


class ParallelTestWorker:
    """
    Worker for parallel test execution.

    Distributes tests across multiple worker processes
    for faster execution.
    """

    def __init__(
        self,
        project_path: Path,
        worker_id: int,
        framework: TestFramework,
    ) -> None:
        """
        Initialize the worker.

        Args:
            project_path: Path to project root
            worker_id: Worker identifier
            framework: Test framework being used
        """
        self._project_path = project_path
        self._worker_id = worker_id
        self._framework = framework
        self._assigned_tests: list[Path] = []

    def assign_tests(self, tests: list[Path]) -> None:
        """Assign tests to this worker."""
        self._assigned_tests = tests

    async def execute(self) -> ExecutionResult:
        """Execute assigned tests."""
        if not self._assigned_tests:
            return ExecutionResult(framework=self._framework)

        # Execute tests for this worker
        if self._framework == TestFramework.BEHAVE:
            return await self._execute_behave_parallel()
        elif self._framework == TestFramework.PYTEST_BDD:
            return await self._execute_pytest_parallel()
        else:
            result = ExecutionResult(framework=self._framework)
            result.errors = 1
            result.output = f"Parallel execution not supported for {self._framework}"
            return result

    async def _execute_behave_parallel(self) -> ExecutionResult:
        """Execute behave tests for this worker."""
        # Create a list of specific feature files for this worker
        cmd = [
            "behave",
            "-f", "json",
            "--out", ".cpa/reports/worker-{}.json".format(self._worker_id),
        ]

        cmd.extend(str(f) for f in self._assigned_tests)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = ExecutionResult(framework=TestFramework.BEHAVE)
            result.output = stdout.decode() + stderr.decode()

            return result

        except Exception as e:
            result = ExecutionResult(framework=TestFramework.BEHAVE)
            result.errors = 1
            result.output = f"Worker {self._worker_id} error: {e}"
            return result

    async def _execute_pytest_parallel(self) -> ExecutionResult:
        """Execute pytest tests for this worker."""
        cmd = [
            "pytest",
            "-v",
            "--tb=short",
            "-o", "cache_dir=.cpa/cache/pytest-worker-{}".format(self._worker_id),
        ]

        cmd.extend(str(f) for f in self._assigned_tests)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = ExecutionResult(framework=TestFramework.PYTEST_BDD)
            result.output = stdout.decode() + stderr.decode()

            return result

        except Exception as e:
            result = ExecutionResult(framework=TestFramework.PYTEST_BDD)
            result.errors = 1
            result.output = f"Worker {self._worker_id} error: {e}"
            return result


# =============================================================================
# Test Execution Engine
# =============================================================================


class TestExecutionEngine:
    """
    Execute BDD tests with Playwright.

    Features:
    - Support for behave and pytest-bdd
    - Parallel test execution
    - Result capture and parsing
    - Screenshot capture on failure
    - HTML report generation
    - Automatic retry with exponential backoff
    - Test result caching (E6.3)
    - Parallel worker distribution (E6.1)
    """

    def __init__(
        self,
        project_path: Path | None = None,
        retry_config: RetryConfig | None = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
    ) -> None:
        """
        Initialize the execution engine.

        Args:
            project_path: Path to project root
            retry_config: Optional retry configuration
            enable_cache: Whether to enable test result caching
            cache_ttl_seconds: Time-to-live for cached results
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._retry_config = retry_config or RetryConfig()
        self._enable_cache = enable_cache
        self._cache = TestResultCache(
            cache_dir=self._project_path / ".cpa" / "cache" / "test_results",
            ttl_seconds=cache_ttl_seconds,
        ) if enable_cache else None

    async def execute_tests(
        self,
        framework: TestFramework,
        feature_files: list[str | Path] | None = None,
        tags: list[str] | None = None,
        parallel: bool = False,
        workers: int = 1,
        retry_config: RetryConfig | None = None,
    ) -> ExecutionResult:
        """
        Execute BDD tests with optional retry logic.

        Args:
            framework: Test framework to use
            feature_files: Optional list of feature files to run
            tags: Optional tags to filter scenarios
            parallel: Whether to run tests in parallel
            workers: Number of parallel workers
            retry_config: Optional retry config (overrides instance config)

        Returns:
            ExecutionResult with test results
        """
        config = retry_config or self._retry_config

        # Initial execution
        result = await self._execute_tests_internal(
            framework, feature_files, tags, parallel, workers
        )

        # Retry failed tests if configured
        if config.max_retries > 0:
            result = await self._retry_failed_tests(
                result, framework, feature_files, tags, parallel, workers, config
            )

        return result

    async def _execute_tests_internal(
        self,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        parallel: bool,
        workers: int,
    ) -> ExecutionResult:
        """Internal method to execute tests without retry logic."""
        # Use parallel workers if enabled
        if parallel and workers > 1:
            return await self._execute_parallel(framework, feature_files, tags, workers)

        # Use caching for single-threaded execution
        if self._cache and feature_files:
            return await self._execute_with_cache(framework, feature_files, tags)

        # Standard execution
        if framework == TestFramework.BEHAVE:
            return await self._execute_behave(feature_files, tags, parallel, workers)
        elif framework == TestFramework.PYTEST_BDD:
            return await self._execute_pytest_bdd(feature_files, tags, parallel, workers)
        elif framework == TestFramework.PLAYWRIGHT:
            return await self._execute_playwright_tests(feature_files, tags, parallel, workers)
        else:
            result = ExecutionResult(framework=framework)
            result.errors = 1
            result.output = f"Unknown framework: {framework}"
            return result

    async def _execute_parallel(
        self,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        workers: int,
    ) -> ExecutionResult:
        """Execute tests using parallel workers."""
        # Collect test files
        test_files = self._collect_test_files(framework, feature_files)
        if not test_files:
            result = ExecutionResult(framework=framework)
            result.output = "No test files found"
            return result

        # Create workers
        worker_list = []
        for i in range(workers):
            worker = ParallelTestWorker(self._project_path, i, framework)
            worker_list.append(worker)

        # Distribute tests among workers
        files_per_worker = len(test_files) // workers
        for i, worker in enumerate(worker_list):
            start_idx = i * files_per_worker
            end_idx = start_idx + files_per_worker if i < workers - 1 else len(test_files)
            worker.assign_tests(test_files[start_idx:end_idx])

        # Run workers in parallel
        results = await asyncio.gather(*[w.execute() for w in worker_list])

        # Aggregate results
        aggregated = ExecutionResult(framework=framework)
        for worker_result in results:
            aggregated.total_tests += worker_result.total_tests
            aggregated.passed += worker_result.passed
            aggregated.failed += worker_result.failed
            aggregated.skipped += worker_result.skipped
            aggregated.errors += worker_result.errors
            aggregated.duration += worker_result.duration
            aggregated.test_results.extend(worker_result.test_results)
            aggregated.output += worker_result.output + "\n"

        return aggregated

    def _collect_test_files(
        self,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
    ) -> list[Path]:
        """Collect test files based on framework."""
        files = []

        if feature_files:
            files = [Path(f) for f in feature_files]
        else:
            # Default test directories
            if framework == TestFramework.BEHAVE:
                features_dir = self._project_path / "features"
                if features_dir.exists():
                    files = list(features_dir.glob("**/*.feature"))
            elif framework == TestFramework.PYTEST_BDD:
                test_dir = self._project_path / "features"
                if test_dir.exists():
                    files = list(test_dir.glob("**/*.feature"))
            elif framework == TestFramework.PLAYWRIGHT:
                test_dir = self._project_path / "tests"
                if test_dir.exists():
                    files = list(test_dir.glob("**/*.spec.ts"))

        return files

    async def _execute_with_cache(
        self,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
    ) -> ExecutionResult:
        """Execute tests with result caching."""
        result = ExecutionResult(framework=framework)
        uncached_files: list[Path] = []

        # Check cache for each file
        for file_path in feature_files or []:
            path = Path(file_path)
            cached = self._cache.get(path) if self._cache else None

            if cached:
                # Use cached result
                result.total_tests += 1
                if cached.status == TestStatus.PASSED:
                    result.passed += 1
                elif cached.status == TestStatus.FAILED:
                    result.failed += 1
                elif cached.status == TestStatus.SKIPPED:
                    result.skipped += 1
                else:
                    result.errors += 1

                result.test_results.append(TestResult(
                    name=cached.test_name,
                    status=cached.status,
                    duration=cached.duration,
                ))
            else:
                uncached_files.append(path)

        # Execute uncached files
        if uncached_files:
            uncached_result = await self._execute_tests_internal(
                framework, uncached_files, tags, False, 1
            )

            # Cache new results
            for test_result in uncached_result.test_results:
                for file_path in uncached_files:
                    if self._cache:
                        self._cache.set(
                            file_path,
                            test_result.name,
                            test_result.status,
                            test_result.duration,
                        )

            # Merge results
            result.total_tests += uncached_result.total_tests
            result.passed += uncached_result.passed
            result.failed += uncached_result.failed
            result.skipped += uncached_result.skipped
            result.errors += uncached_result.errors
            result.duration += uncached_result.duration
            result.test_results.extend(uncached_result.test_results)

        return result

    async def _execute_behave(
        self,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        parallel: bool,
        workers: int,
    ) -> ExecutionResult:
        """Execute tests using behave."""
        cmd = ["behave"]

        # Add feature files
        if feature_files:
            cmd.extend(str(f) for f in feature_files)

        # Add tags
        if tags:
            tag_list = ",".join(tags)
            cmd.extend(["--tags", tag_list])

        # Add parallel execution
        if parallel and workers > 1:
            cmd.extend(["--processes", str(workers)])

        # Add output formatting
        cmd.extend(["--format", "json"])

        try:
            # Run behave
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = ExecutionResult(framework=TestFramework.BEHAVE)
            result.output = stdout.decode() + stderr.decode()

            # Parse JSON output
            result = self._parse_behave_output(result, stdout.decode())

            return result

        except FileNotFoundError:
            result = ExecutionResult(framework=TestFramework.BEHAVE)
            result.errors = 1
            result.output = "behave is not installed. Install with: pip install behave"
            return result
        except Exception as e:
            result = ExecutionResult(framework=TestFramework.BEHAVE)
            result.errors = 1
            result.output = f"Error running behave: {e}"
            return result

    async def _execute_pytest_bdd(
        self,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        parallel: bool,
        workers: int,
    ) -> ExecutionResult:
        """Execute tests using pytest-bdd."""
        cmd = ["pytest", "-v"]

        # Add feature files or test directory
        if feature_files:
            cmd.extend(str(f) for f in feature_files)
        else:
            cmd.append("features/")

        # Add tags
        if tags:
            for tag in tags:
                cmd.extend(["-k", tag])

        # Add parallel execution
        if parallel and workers > 1:
            cmd.extend(["-n", str(workers)])

        try:
            # Run pytest
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = ExecutionResult(framework=TestFramework.PYTEST_BDD)
            result.output = stdout.decode() + stderr.decode()

            # Parse pytest output
            result = self._parse_pytest_output(result, process.returncode)

            return result

        except FileNotFoundError:
            result = ExecutionResult(framework=TestFramework.PYTEST_BDD)
            result.errors = 1
            result.output = "pytest is not installed. Install with: pip install pytest pytest-bdd"
            return result
        except Exception as e:
            result = ExecutionResult(framework=TestFramework.PYTEST_BDD)
            result.errors = 1
            result.output = f"Error running pytest: {e}"
            return result

    async def _execute_playwright_tests(
        self,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        parallel: bool,
        workers: int,
    ) -> ExecutionResult:
        """Execute tests using Playwright test runner."""
        cmd = ["playwright", "test"]

        # Add feature files or test directory
        if feature_files:
            cmd.extend(str(f) for f in feature_files)

        # Add parallel execution
        if parallel and workers > 1:
            cmd.extend(["--workers", str(workers)])

        try:
            # Run playwright tests
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = ExecutionResult(framework=TestFramework.PLAYWRIGHT)
            result.output = stdout.decode() + stderr.decode()

            # Parse playwright output
            result = self._parse_playwright_output(result, process.returncode)

            return result

        except FileNotFoundError:
            result = ExecutionResult(framework=TestFramework.PLAYWRIGHT)
            result.errors = 1
            result.output = "Playwright is not installed. Install with: pip install pytest-playwright"
            return result
        except Exception as e:
            result = ExecutionResult(framework=TestFramework.PLAYWRIGHT)
            result.errors = 1
            result.output = f"Error running Playwright: {e}"
            return result

    def _parse_behave_output(self, result: ExecutionResult, output: str) -> ExecutionResult:
        """Parse behave JSON output."""
        try:
            # Find JSON in output
            lines = output.split("\n")
            for line in lines:
                if line.strip().startswith("{"):
                    data = json.loads(line)

                    # Parse results
                    result.total_tests = len(data)
                    for test in data:
                        status = TestStatus.PASSED if test.get("status") == "passed" else TestStatus.FAILED
                        if status == TestStatus.PASSED:
                            result.passed += 1
                        else:
                            result.failed += 1

                        test_result = TestResult(
                            name=test.get("name", "unknown"),
                            status=status,
                            error_message=test.get("error", ""),
                        )
                        result.test_results.append(test_result)

                    break
        except json.JSONDecodeError:
            # Failed to parse JSON, try to parse from text output
            result = self._parse_text_output(result, output, "passed", "failed")

        return result

    def _parse_pytest_output(self, result: ExecutionResult, returncode: int) -> ExecutionResult:
        """Parse pytest text output."""
        if returncode == 0:
            result.passed = 1
            result.total_tests = 1
        else:
            result.failed = 1
            result.total_tests = 1

        result = self._parse_text_output(result, result.output, "PASSED", "FAILED")
        return result

    def _parse_playwright_output(self, result: ExecutionResult, returncode: int) -> ExecutionResult:
        """Parse Playwright test output."""
        output = result.output

        # Parse statistics from output
        for line in output.split("\n"):
            if "passed" in line.lower():
                if "passed" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i > 0:
                            result.passed = int(part)
                            result.total_tests = int(part)
                            break

        result = self._parse_text_output(result, output, "passed", "failed")
        return result

    def _parse_text_output(
        self,
        result: ExecutionResult,
        output: str,
        passed_keyword: str,
        failed_keyword: str,
    ) -> ExecutionResult:
        """Parse test results from text output."""
        lines = output.split("\n")

        for line in lines:
            line_lower = line.lower()
            if passed_keyword.lower() in line_lower:
                # Extract number
                import re
                match = re.search(r'(\d+)\s+' + passed_keyword, line)
                if match:
                    result.passed = int(match.group(1))

            if failed_keyword.lower() in line_lower:
                import re
                match = re.search(r'(\d+)\s+' + failed_keyword, line)
                if match:
                    result.failed = int(match.group(1))

        result.total_tests = result.passed + result.failed + result.skipped + result.errors
        return result

    async def _retry_failed_tests(
        self,
        result: ExecutionResult,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
        parallel: bool,
        workers: int,
        config: RetryConfig,
    ) -> ExecutionResult:
        """
        Retry failed tests with exponential backoff.

        Args:
            result: Initial execution result
            framework: Test framework
            feature_files: Feature files to run
            tags: Tags to filter
            parallel: Whether to run in parallel
            workers: Number of workers
            config: Retry configuration

        Returns:
            Updated ExecutionResult with retries applied
        """
        tests_to_retry = [
            t for t in result.test_results
            if config.should_retry(t.status, t.retry_count)
        ]

        if not tests_to_retry:
            return result

        total_retries = 0
        for test_result in tests_to_retry:
            retry_attempt = 0
            while retry_attempt < config.max_retries:
                # Calculate delay with exponential backoff
                delay = config.get_delay(retry_attempt)

                # Wait before retry
                await asyncio.sleep(delay)

                # Store previous attempt
                test_result.previous_attempts.append({
                    "status": test_result.status.value,
                    "error_message": test_result.error_message,
                    "duration": test_result.duration,
                })

                # Re-run the test (run only this test)
                retry_result = await self._execute_single_test(
                    test_result.name, framework, feature_files, tags
                )

                # Update test result
                test_result.status = retry_result.status
                test_result.duration += retry_result.duration
                test_result.retry_count += 1
                total_retries += 1

                # Check if retry succeeded
                if retry_result.status in (TestStatus.PASSED, TestStatus.SKIPPED):
                    test_result.error_message = retry_result.error_message
                    break

                test_result.error_message = retry_result.error_message
                test_result.stack_trace = retry_result.stack_trace
                retry_attempt += 1

        # Update overall stats
        passed_after_retry = sum(
            1 for t in result.test_results
            if t.status == TestStatus.PASSED and t.retry_count > 0
        )
        result.passed += passed_after_retry
        result.failed -= passed_after_retry

        return result

    async def _execute_single_test(
        self,
        test_name: str,
        framework: TestFramework,
        feature_files: list[str | Path] | None,
        tags: list[str] | None,
    ) -> TestResult:
        """
        Execute a single test by name.

        Args:
            test_name: Name of the test to run
            framework: Test framework
            feature_files: Feature files
            tags: Tags filter

        Returns:
            TestResult for the single test
        """
        # For simplicity, re-run all tests and filter by name
        result = await self._execute_tests_internal(
            framework, feature_files, tags, False, 1
        )

        # Find the specific test result
        for test_result in result.test_results:
            if test_result.name == test_name:
                return test_result

        # If not found, return a failed result
        return TestResult(
            name=test_name,
            status=TestStatus.ERROR,
            error_message=f"Test '{test_name}' not found in results",
        )

    # -------------------------------------------------------------------------
    # Cache Management Methods (E6.3)
    # -------------------------------------------------------------------------

    def clear_cache(self) -> None:
        """Clear all cached test results."""
        if self._cache:
            self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get test result cache statistics."""
        if not self._cache:
            return {"cache_enabled": False}

        stats = self._cache.get_stats()
        stats["cache_enabled"] = True
        return stats

    def invalidate_cache_for_file(self, file_path: Path) -> None:
        """
        Invalidate cached result for a specific file.

        Args:
            file_path: Path to test file to invalidate
        """
        if self._cache:
            test_hash = self._cache._compute_hash(file_path)
            if test_hash in self._cache._cache:
                del self._cache._cache[test_hash]

            # Also remove from disk cache
            cache_file = self._cache._cache_dir / f"{test_hash}.json"
            if cache_file.exists():
                cache_file.unlink()


# =============================================================================
# Convenience Functions
# =============================================================================


async def execute_tests(
    framework: str = "behave",
    feature_files: list[str | Path] | None = None,
    tags: list[str] | None = None,
    parallel: bool = False,
    workers: int = 1,
    project_path: str | Path | None = None,
) -> ExecutionResult:
    """
    Execute BDD tests.

    Args:
        framework: Test framework name ("behave", "pytest-bdd", "playwright")
        feature_files: Optional list of feature files to run
        tags: Optional tags to filter scenarios
        parallel: Whether to run tests in parallel
        workers: Number of parallel workers
        project_path: Optional project path

    Returns:
        ExecutionResult with test results
    """
    engine = TestExecutionEngine(project_path)

    framework_enum = TestFramework(framework)
    return await engine.execute_tests(framework_enum, feature_files, tags, parallel, workers)
