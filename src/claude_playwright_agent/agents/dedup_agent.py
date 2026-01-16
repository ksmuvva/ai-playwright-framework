"""
Deduplication Agent for Claude Playwright Agent.

This agent handles:
- Finding repeated patterns across recordings
- Creating reusable page object models
- Merging similar scenarios
- Identifying common test flows
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.deduplication import (
    PageObjectGenerator,
    analyze_patterns,
    generate_page_objects,
)


class DeduplicationAgent(BaseAgent):
    """
    Agent for deduplicating patterns and creating page objects.

    Analyzes multiple recordings to find repeated selectors and patterns,
    then generates reusable page object models.
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the deduplication agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._generator = PageObjectGenerator()

        system_prompt = """You are the Deduplication Agent for Claude Playwright Agent.

Your role is to:
1. Analyze multiple recordings for repeated patterns
2. Find common selectors and page elements
3. Create reusable page object models
4. Identify opportunities for test consolidation

Your output includes:
- Repeated selector patterns
- Page object models (Python code)
- Deduplication statistics
- Recommendations for test consolidation
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process recordings for deduplication.

        Args:
            input_data: Input with 'recordings' key containing list of parsed recordings

        Returns:
            Deduplication results with page objects
        """
        recordings = input_data.get("recordings", [])
        output_dir = input_data.get("output_dir", "")

        if not recordings:
            return {
                "success": False,
                "error": "No recordings provided for analysis",
            }

        try:
            # Analyze patterns
            result = analyze_patterns(recordings)

            # Generate page objects if output directory specified
            files_created = []
            if output_dir:
                gen_result = generate_page_objects(recordings, output_dir)
                files_created = gen_result.get("files_created", [])

            return {
                "success": True,
                "selector_patterns": [p.to_dict() for p in result.selector_patterns],
                "page_objects": [p.to_dict() for p in result.page_objects],
                "page_objects_code": [p.to_python_code() for p in result.page_objects],
                "statistics": result.statistics,
                "files_created": files_created,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Deduplication analysis failed: {e}",
            }

    async def analyze_patterns(
        self,
        recordings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze recordings for repeated patterns.

        Args:
            recordings: List of parsed recording dictionaries

        Returns:
            Pattern analysis results
        """
        return await self.process({"recordings": recordings})

    async def generate_page_objects(
        self,
        recordings: list[dict[str, Any]],
        output_dir: str | Path,
    ) -> dict[str, Any]:
        """
        Generate page object files.

        Args:
            recordings: List of parsed recording dictionaries
            output_dir: Directory to save page object files

        Returns:
            Generation results
        """
        return await self.process({
            "recordings": recordings,
            "output_dir": str(output_dir),
        })
