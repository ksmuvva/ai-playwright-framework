"""
Debug Agent - Agent for analyzing and fixing test failures.
"""

from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class DebugAgent(BaseAgent):
    """
    Agent for debugging test failures.

    Handles:
    - Root cause analysis
    - Suggesting fixes
    - Applying auto-fixes
    - Interactive debugging
    """

    def __init__(
        self,
        mcp_servers: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize the Debug Agent."""
        system_prompt = """You are a test debugging expert specializing in Playwright test failures.

Your responsibilities:
1. Analyze test failures and identify root causes
2. Suggest specific code fixes
3. Explain why failures occurred
4. Recommend preventive measures
5. Help improve test reliability

When analyzing failures:
- Check for timing issues (race conditions, slow loads)
- Verify selectors are correct and elements exist
- Look for network/API failures
- Check for environment differences
- Identify flaky test patterns

When suggesting fixes:
- Provide exact code changes
- Explain the reasoning
- Include error handling if needed
- Consider edge cases"""

        default_tools = [
            "Read",
            "Write",
            "Bash",
            "analyze_failure",
            "suggest_fix",
        ]

        super().__init__(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools or default_tools,
        )

    async def analyze_failure(
        self,
        test_name: str,
        error_message: str,
        stack_trace: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze a test failure.

        Args:
            test_name: Name of the failed test
            error_message: Error message from the failure
            stack_trace: Stack trace if available
            context: Additional context (screenshots, page state, etc.)

        Returns:
            Failure analysis with root cause and suggestions
        """
        await self.initialize()

        prompt = f"""Analyze this test failure:

Test: {test_name}
Error: {error_message}
Stack Trace:
{stack_trace}

Context:
{context}

Please provide:
1. Root cause analysis
2. Confidence in your assessment (0-1)
3. Suggested fix with code
4. Explanation of why this happened
5. How to prevent similar failures"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "test_name": test_name,
                "analysis": "\n".join(response_parts),
                "error_message": error_message,
            }

    async def suggest_fix(
        self,
        test_file: str,
        failure_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Suggest a fix for a failed test.

        Args:
            test_file: Path to the test file
            failure_analysis: Results from analyze_failure

        Returns:
            Suggested fix with code diff
        """
        prompt = f"""Based on this failure analysis, suggest a fix:

Test File: {test_file}
Analysis:
{failure_analysis}

Please provide:
1. Exact code changes needed (diff format)
2. Which line(s) to change
3. The new code
4. Why this fix works"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "test_file": test_file,
                "suggestion": "\n".join(response_parts),
            }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "analyze_failure")

        if action == "analyze_failure":
            return await self.analyze_failure(
                test_name=input_data["test_name"],
                error_message=input_data["error_message"],
                stack_trace=input_data.get("stack_trace", ""),
                context=input_data.get("context", {}),
            )
        elif action == "suggest_fix":
            return await self.suggest_fix(
                test_file=input_data["test_file"],
                failure_analysis=input_data["failure_analysis"],
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
