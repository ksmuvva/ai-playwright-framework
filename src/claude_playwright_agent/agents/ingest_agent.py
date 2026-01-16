"""
Ingestion Agent for processing Playwright recordings.

This agent handles:
- Reading Playwright recording files
- Extracting actions and selectors
- Preparing data for further processing
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.playwright_parser import parse_recording


class IngestionAgent(BaseAgent):
    """
    Agent for ingesting Playwright recordings.

    Processes recorded test sessions and extracts structured data
    for conversion to BDD scenarios.
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the ingestion agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        system_prompt = """You are the Ingestion Agent for Claude Playwright Agent.

Your role is to:
1. Read Playwright recording files (.js files from codegen)
2. Extract test actions, selectors, and page interactions
3. Identify navigation patterns and user flows
4. Structure the data for BDD conversion

Provide detailed extraction results including:
- Action sequences
- Element selectors with fallbacks
- Page structure information
- Test data parameters
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a Playwright recording file.

        Args:
            input_data: Input with 'recording_path' key

        Returns:
            Extracted actions and metadata
        """
        recording_path = input_data.get("recording_path", "")
        path = Path(recording_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Recording file not found: {recording_path}",
            }

        try:
            # Parse the recording
            parsed = parse_recording(path)

            return {
                "success": True,
                "recording_path": recording_path,
                "parsed_recording": parsed.to_dict(),
                "summary": {
                    "test_name": parsed.test_name,
                    "total_actions": len(parsed.actions),
                    "unique_selectors": len(parsed.selectors_used),
                    "urls_visited": len(parsed.urls_visited),
                    "file_size": path.stat().st_size,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse recording: {e}",
            }
