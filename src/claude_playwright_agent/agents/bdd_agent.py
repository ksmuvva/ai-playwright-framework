"""
BDD Conversion Agent for Claude Playwright Agent.

This agent handles:
- Converting parsed recordings to Gherkin scenarios
- Generating feature files with proper formatting
- Creating step definition templates
- AI-enhanced scenario generation
"""

from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.bdd_conversion import (
    BDDConverter,
    StepDefinitionGenerator,
    convert_to_gherkin,
    save_feature_file,
    GherkinFeature,
)


class ScenarioTemplate(str, Enum):
    """Pre-defined scenario templates."""

    BASIC = "basic"
    LOGIN = "login"
    SEARCH = "search"
    FORM = "form"
    CRUD = "crud"
    NAVIGATION = "navigation"


@dataclass
class ConversionOptions:
    """Options for BDD conversion."""

    feature_name: str = ""
    include_background: bool = True
    add_tags: bool = True
    use_scenario_outline: bool = False
    template: ScenarioTemplate = ScenarioTemplate.BASIC
    add_examples: bool = False
    include_assertions: bool = True
    generate_page_objects: bool = True


class BDDConversionAgent(BaseAgent):
    """
    Agent for converting Playwright recordings to BDD scenarios.

    Takes parsed recording data and generates Gherkin feature files
    with proper Given/When/Then steps. Provides AI-enhanced scenario
    generation with templates and best practices.
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
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
5. Apply best practices for BDD scenario design
6. Suggest appropriate tags and backgrounds

Your output includes:
- Gherkin feature files with proper syntax
- Step definition templates in Python
- Suggestions for improvements
- Alternative scenario formulations

Follow BDD best practices:
- Use business language, not technical details
- One scenario per behavior
- Include assertions for validation
- Use tags for organization
- Keep scenarios focused and atomic
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

        options = ConversionOptions(
            feature_name=input_data.get("feature_name", ""),
            include_background=input_data.get("include_background", True),
            add_tags=input_data.get("add_tags", True),
            use_scenario_outline=input_data.get("use_scenario_outline", False),
            template=ScenarioTemplate(input_data.get("template", "basic")),
            add_examples=input_data.get("add_examples", False),
            include_assertions=input_data.get("include_assertions", True),
            generate_page_objects=input_data.get("generate_page_objects", True),
        )

        try:
            # Convert to Gherkin
            feature = self._converter.convert_recording(
                parsed_recording,
                options.feature_name or parsed_recording.get("test_name", "Feature"),
            )

            # Apply template-based enhancements
            if options.template != ScenarioTemplate.BASIC:
                feature = self._apply_template(feature, options.template)

            # Generate step definitions
            step_defs = self._step_gen.generate_for_feature(feature)

            # Add background if requested
            if options.include_background:
                feature = self._add_background(feature, parsed_recording)

            # Get file path if provided
            output_path = input_data.get("output_path", "")
            if output_path:
                save_feature_file(parsed_recording, output_path, options.feature_name)

            result = {
                "success": True,
                "feature_file": feature.to_gherkin(),
                "step_definitions": step_defs,
                "summary": {
                    "feature_name": feature.name,
                    "scenario_count": len(feature.scenarios),
                    "step_count": sum(len(s.steps) for s in feature.scenarios),
                    "test_name": parsed_recording.get("test_name", ""),
                    "template_used": options.template.value,
                },
                "suggestions": await self._generate_suggestions(feature, parsed_recording),
            }

            # Store conversion result in memory
            await self.remember(
                key=f"bdd_conversion_{feature.name}",
                value=result["summary"],
                memory_type="semantic",
                priority="medium",
                tags=["bdd", "conversion", feature.name],
            )

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"BDD conversion failed: {e}",
            }

    def _apply_template(
        self, feature: GherkinFeature, template: ScenarioTemplate
    ) -> GherkinFeature:
        """Apply a scenario template to enhance the feature."""
        if template == ScenarioTemplate.LOGIN:
            for scenario in feature.scenarios:
                if "login" in scenario.name.lower():
                    scenario.name = f"Successful login with valid credentials"
                    if not any("Given" in s.text for s in scenario.steps):
                        scenario.steps.insert(
                            0, type(scenario.steps[0])("Given", "I am on the login page")
                        )
                    if not any("Then" in s.text for s in scenario.steps):
                        scenario.steps.append(
                            type(scenario.steps[0])("Then", "I should be logged in successfully")
                        )

        elif template == ScenarioTemplate.SEARCH:
            for scenario in feature.scenarios:
                if "search" in scenario.name.lower():
                    scenario.name = f"Search for and find results"

        elif template == ScenarioTemplate.FORM:
            for scenario in feature.scenarios:
                if not any("form" in s.text.lower() for s in scenario.steps):
                    if not any("submit" in s.text.lower() for s in scenario.steps):
                        scenario.steps.append(type(scenario.steps[0])("When", "I submit the form"))

        return feature

    def _add_background(self, feature: GherkinFeature, parsed_recording: dict) -> GherkinFeature:
        """Add a background section to the feature."""
        urls = parsed_recording.get("urls_visited", [])
        if urls:
            # Add background with navigation to first URL
            feature.background = "  Given I navigate to the application"

        return feature

    async def _generate_suggestions(
        self, feature: GherkinFeature, parsed_recording: dict
    ) -> list[str]:
        """Generate improvement suggestions for the feature."""
        suggestions = []
        scenarios = feature.scenarios

        # Check for missing assertions
        has_assertions = any(
            "Then" in s.text or "expect" in s.text.lower()
            for scenario in scenarios
            for s in scenario.steps
        )
        if not has_assertions:
            suggestions.append(
                "Consider adding assertion steps (Then) to validate expected outcomes"
            )

        # Check for long scenarios
        for scenario in scenarios:
            if len(scenario.steps) > 10:
                suggestions.append(
                    f"Scenario '{scenario.name}' has {len(scenario.steps)} steps. "
                    "Consider splitting into smaller scenarios"
                )

        # Check for missing tags
        if not feature.tags:
            suggestions.append("Add tags (@smoke, @regression) for better test organization")

        # Check for form handling
        if any(
            "fill" in s.text.lower() or "form" in s.text.lower()
            for scenario in scenarios
            for s in scenario.steps
        ):
            suggestions.append(
                "Consider using page objects for form handling to improve maintainability"
            )

        return suggestions

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
        return await self.process(
            {
                "parsed_recording": parsed_recording,
                "output_path": str(output_path),
                "feature_name": feature_name,
            }
        )

    async def generate_scenario_outline(
        self,
        parsed_recording: dict[str, Any],
        examples: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a scenario outline with examples table.

        Args:
            parsed_recording: Parsed recording data
            examples: List of example data dictionaries

        Returns:
            Scenario outline with examples
        """
        options = ConversionOptions(
            feature_name=parsed_recording.get("test_name", "Feature"),
            use_scenario_outline=True,
            add_examples=True,
        )

        result = await self.process(
            {
                "parsed_recording": parsed_recording,
                "options": options.__dict__,
            }
        )

        if result["success"]:
            result["examples_table"] = self._format_examples_table(examples)

        return result

    def _format_examples_table(self, examples: list[dict]) -> str:
        """Format examples as a Gherkin table."""
        if not examples:
            return ""

        headers = list(examples[0].keys())
        lines = ["      | " + " | ".join(headers) + " |"]

        for example in examples:
            values = [str(example.get(h, "")) for h in headers]
            lines.append("      | " + " | ".join(values) + " |")

        return "\n".join(lines)
