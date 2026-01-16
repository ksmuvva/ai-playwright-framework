"""
Test Agent - Primary agent for test generation and execution.
"""

from typing import Any, Literal

from claude_playwright_agent.agents.base import BaseAgent


class TestAgent(BaseAgent):
    """
    Primary agent for generating and executing tests.

    Handles:
    - BDD scenario generation from recordings
    - Test execution with self-healing
    - Locator healing
    - Test data generation
    """

    def __init__(
        self,
        mcp_servers: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize the Test Agent."""
        system_prompt = """You are an expert test automation engineer specializing in BDD testing with Playwright.

Your responsibilities:
1. Generate clear, maintainable Gherkin feature files from recordings or requirements
2. Create robust Python step definitions using Playwright
3. Implement self-healing locators with multiple fallback strategies
4. Generate realistic test data when needed
5. Suggest improvements for test reliability

Always follow best practices:
- Use given-when-then format appropriately
- Create reusable step definitions
- Add wait strategies for dynamic content
- Include clear assertions
- Generate self-documenting tests"""

        default_tools = [
            "Read",
            "Write",
            "Bash",
            "playwright_record",
            "playwright_playback",
            "generate_feature",
            "generate_steps",
            "heal_locator",
            "generate_test_data",
        ]

        super().__init__(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools or default_tools,
        )

    async def generate_tests(
        self,
        source: str,
        source_type: Literal["recording", "requirements", "video"] = "recording",
        output_format: Literal["bdd", "python"] = "bdd",
    ) -> dict[str, Any]:
        """
        Generate tests from source data.

        Args:
            source: Path to source file or source content
            source_type: Type of source data
            output_format: Output format for tests

        Returns:
            Dictionary with generated test content and metadata
        """
        await self.initialize()

        prompt = f"""Generate {output_format} tests from the following {source_type}:

{source}

Please provide:
1. Well-structured feature file with scenarios
2. Step definitions in Python
3. Page object classes if applicable
4. Any test data fixtures needed"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "success": True,
                "content": "\n".join(response_parts),
                "format": output_format,
            }

    async def heal_locator(
        self,
        failed_locator: str,
        page_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Heal a failed locator.

        Args:
            failed_locator: The locator that failed
            page_state: Current page state/DOM snapshot

        Returns:
            Healed locator with confidence score
        """
        prompt = f"""The following locator failed: {failed_locator}

Page state:
{page_state}

Please analyze and suggest a healed locator with:
1. Primary locator (most robust)
2. Fallback locators (in order of preference)
3. Confidence score for each
4. Reasoning for your choices"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "original_locator": failed_locator,
                "healed_content": "\n".join(response_parts),
            }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "generate_tests")

        if action == "generate_tests":
            return await self.generate_tests(
                source=input_data["source"],
                source_type=input_data.get("source_type", "recording"),
                output_format=input_data.get("output_format", "bdd"),
            )
        elif action == "heal_locator":
            return await self.heal_locator(
                failed_locator=input_data["failed_locator"],
                page_state=input_data["page_state"],
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
