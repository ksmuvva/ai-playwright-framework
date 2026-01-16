"""
BDD Conversion Agent for Claude Playwright Agent.

This agent handles:
- Converting parsed recordings to Gherkin scenarios
- Generating feature files
- Creating step definition templates
"""

from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.bdd_conversion import (
    BDDConverter,
    StepDefinitionGenerator,
    convert_to_gherkin,
    save_feature_file,
)


class BDDConversionAgent(BaseAgent):
    """
    Agent for converting Playwright recordings to BDD scenarios.

    Takes parsed recording data and generates Gherkin feature files
    with proper Given/When/Then steps.
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the BDD conversion agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._converter = BDDConverter()
        self._step_gen = StepDefinitionGenerator()

        system_prompt = """You are the BDD Conversion Agent for Claude Playwright Agent.

Your role is to:
1. Convert parsed Playwright recordings to Gherkin BDD scenarios
2. Transform actions into Given/When/Then steps
3. Generate feature files with proper formatting
4. Create step definition templates

Your output includes:
- Gherkin feature files
- Step definition templates
- Conversion summaries
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a parsed recording and convert to BDD.

        Args:
            input_data: Input with 'parsed_recording' key containing parsed data

        Returns:
            Conversion results with Gherkin content
        """
        parsed_recording = input_data.get("parsed_recording")
        if not parsed_recording:
            return {
                "success": False,
                "error": "No parsed_recording provided in input",
            }

        feature_name = input_data.get("feature_name", "")

        try:
            # Convert to Gherkin
            feature = self._converter.convert_recording(
                parsed_recording,
                feature_name,
            )

            # Generate step definitions
            step_defs = self._step_gen.generate_for_feature(feature)

            # Get file path if provided
            output_path = input_data.get("output_path", "")
            if output_path:
                save_feature_file(parsed_recording, output_path, feature_name)

            return {
                "success": True,
                "feature_file": feature.to_gherkin(),
                "step_definitions": step_defs,
                "summary": {
                    "feature_name": feature.name,
                    "scenario_count": len(feature.scenarios),
                    "step_count": sum(len(s.steps) for s in feature.scenarios),
                    "test_name": parsed_recording.get("test_name", ""),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"BDD conversion failed: {e}",
            }

    async def convert_recording_to_file(
        self,
        parsed_recording: dict[str, Any],
        output_path: str | Path,
        feature_name: str = "",
    ) -> dict[str, Any]:
        """
        Convert a recording and save to file.

        Args:
            parsed_recording: Parsed recording data
            output_path: Path to save the feature file
            feature_name: Optional feature name

        Returns:
            Conversion results
        """
        return await self.process({
            "parsed_recording": parsed_recording,
            "output_path": str(output_path),
            "feature_name": feature_name,
        })
