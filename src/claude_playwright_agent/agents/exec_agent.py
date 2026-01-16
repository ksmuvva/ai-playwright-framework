"""
Test Execution Agent for Claude Playwright Agent.

This agent handles:
- Running BDD tests with Playwright
- Capturing test results
- Handling test failures and retries
- Supporting multiple test frameworks
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.execution import (
    TestExecutionEngine,
    TestFramework,
    execute_tests,
)


class ExecutionAgent(BaseAgent):
    """
    Agent for executing BDD tests with Playwright.

    Supports behave, pytest-bdd, and Playwright test runners.
    Captures results and handles failures.
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the execution agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._engine = TestExecutionEngine(self._project_path)

        system_prompt = """You are the Test Execution Agent for Claude Playwright Agent.

Your role is to:
1. Execute BDD tests using the appropriate framework
2. Capture test results and metrics
3. Handle failures and retries
4. Generate execution reports

Supported frameworks:
- behave: Python BDD framework
- pytest-bdd: pytest with BDD plugin
- playwright: Playwright test runner
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute tests based on input parameters.

        Args:
            input_data: Input with framework, feature files, and options

        Returns:
            Execution results
        """
        framework_str = input_data.get("framework", "behave")
        feature_files = input_data.get("feature_files", [])
        tags = input_data.get("tags", [])
        parallel = input_data.get("parallel", False)
        workers = input_data.get("workers", 1)

        try:
            framework = TestFramework(framework_str)
            result = await self._engine.execute_tests(
                framework,
                feature_files,
                tags,
                parallel,
                workers,
            )

            return {
                "success": True,
                "result": result.to_dict(),
            }
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown framework: {framework_str}. Use behave, pytest-bdd, or playwright.",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {e}",
            }

    async def run_tests(
        self,
        framework: str = "behave",
        feature_files: list[str | Path] | None = None,
        tags: list[str] | None = None,
        parallel: bool = False,
        workers: int = 1,
    ) -> dict[str, Any]:
        """
        Run BDD tests.

        Args:
            framework: Test framework to use
            feature_files: Optional list of feature files
            tags: Optional tags to filter scenarios
            parallel: Whether to run in parallel
            workers: Number of parallel workers

        Returns:
            Execution results
        """
        return await self.process({
            "framework": framework,
            "feature_files": feature_files,
            "tags": tags,
            "parallel": parallel,
            "workers": workers,
        })

    async def run_all_tests(
        self,
        framework: str = "behave",
        parallel: bool = False,
        workers: int = 1,
    ) -> dict[str, Any]:
        """
        Run all tests in the project.

        Args:
            framework: Test framework to use
            parallel: Whether to run in parallel
            workers: Number of parallel workers

        Returns:
            Execution results
        """
        return await self.run_tests(
            framework=framework,
            feature_files=None,  # Run all
            parallel=parallel,
            workers=workers,
        )

    async def run_tagged_tests(
        self,
        tags: list[str],
        framework: str = "behave",
        parallel: bool = False,
        workers: int = 1,
    ) -> dict[str, Any]:
        """
        Run tests matching specific tags.

        Args:
            tags: List of tags to match
            framework: Test framework to use
            parallel: Whether to run in parallel
            workers: Number of parallel workers

        Returns:
            Execution results
        """
        return await self.run_tests(
            framework=framework,
            feature_files=None,
            tags=tags,
            parallel=parallel,
            workers=workers,
        )
