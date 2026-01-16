"""
Report Agent - Agent for generating intelligent test reports.
"""

from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    """
    Agent for generating intelligent test reports.

    Handles:
    - Failure clustering
    - Executive summaries
    - Trend analysis
    - AI insights
    """

    def __init__(
        self,
        mcp_servers: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize the Report Agent."""
        system_prompt = """You are a test reporting expert specializing in making test results actionable.

Your responsibilities:
1. Cluster similar failures to identify patterns
2. Generate executive summaries for stakeholders
3. Provide actionable insights
4. Identify trends over time
5. Highlight flaky tests

When creating reports:
- Focus on business impact
- Highlight high-priority issues
- Provide clear next steps
- Use visualizations when helpful
- Be concise and actionable

For clustering:
- Group failures by root cause
- Identify systemic issues
- Flag patterns that need attention

For summaries:
- Use business language
- Quantify impact
- Suggest priorities"""

        default_tools = [
            "Read",
            "analyze_results",
            "cluster_failures",
            "generate_summary",
        ]

        super().__init__(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools or default_tools,
        )

    async def analyze_results(
        self,
        results_path: str,
    ) -> dict[str, Any]:
        """
        Analyze test results.

        Args:
            results_path: Path to test results JSON

        Returns:
            Analysis with insights and patterns
        """
        await self.initialize()

        prompt = f"""Analyze these test results from: {results_path}

Please provide:
1. Overall health assessment
2. Key failure patterns
3. Flaky tests identified
4. Recommendations for improvement
5. Priority issues to address"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "results_path": results_path,
                "analysis": "\n".join(response_parts),
            }

    async def cluster_failures(
        self,
        test_results: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Cluster similar failures.

        Args:
            test_results: Test results dictionary

        Returns:
            Failure clusters with common themes
        """
        prompt = f"""Cluster these test failures by root cause:

{test_results}

Please provide:
1. Failure clusters (group by similar root causes)
2. Cluster names and descriptions
3. Number of failures in each cluster
4. Affected tests
5. Suggested fix approach for each cluster"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "clusters": "\n".join(response_parts),
            }

    async def generate_executive_summary(
        self,
        analysis: dict[str, Any],
        format: str = "markdown",
    ) -> dict[str, Any]:
        """
        Generate executive summary.

        Args:
            analysis: Results analysis
            format: Output format (markdown or html)

        Returns:
            Executive summary in specified format
        """
        prompt = f"""Generate an executive summary from this analysis:

{analysis}

The summary should:
- Be suitable for non-technical stakeholders
- Focus on business impact
- Quantify risk and coverage
- Provide clear next steps
- Be concise (under 300 words)"""

        async with self.client:
            await self.client.query(prompt)
            response_parts = []

            async for msg in self.client.receive_response():
                response_parts.append(str(msg))

            return {
                "summary": "\n".join(response_parts),
                "format": format,
            }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "analyze_results")

        if action == "analyze_results":
            return await self.analyze_results(
                results_path=input_data["results_path"],
            )
        elif action == "cluster_failures":
            return await self.cluster_failures(
                test_results=input_data["test_results"],
            )
        elif action == "generate_executive_summary":
            return await self.generate_executive_summary(
                analysis=input_data["analysis"],
                format=input_data.get("format", "markdown"),
            )
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
