"""
Recording Agent - End-to-end test recording workflow.

This agent provides:
- Recording session management
- Auto-convert to BDD after recording
- Page object generation from recordings
- Test data schema extraction
"""

from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.playwright_parser import parse_recording
from claude_playwright_agent.agents.bdd_conversion import (
    BDDConverter,
    StepDefinitionGenerator,
)
from claude_playwright_agent.agents.deduplication import (
    PageObjectGenerator,
)


class RecordingAgent(BaseAgent):
    """
    Agent for managing the complete recording workflow.

    Handles:
    - Recording session setup and cleanup
    - Auto-convert recordings to BDD
    - Page object generation
    - Test data extraction
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        """
        Initialize the recording agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._converter = BDDConverter()
        self._step_gen = StepDefinitionGenerator()
        self._page_object_gen = PageObjectGenerator()

        system_prompt = """You are the Recording Agent for Claude Playwright Agent.

Your role is to:
1. Manage complete recording workflows
2. Convert recordings to BDD scenarios automatically
3. Generate page objects from recorded interactions
4. Extract test data schemas from recordings
5. Optimize selectors based on recording patterns

You provide:
- End-to-end recording workflow management
- Smart selector recommendations
- Page object templates
- Test data generation
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a recording with the complete workflow.

        Args:
            input_data: Input with recording_path and workflow options

        Returns:
            Complete workflow results
        """
        recording_path = input_data.get("recording_path", "")
        path = Path(recording_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Recording file not found: {recording_path}",
            }

        options = input_data.get("options", {})
        auto_convert = options.get("auto_convert", True)
        generate_page_objects = options.get("generate_page_objects", True)
        generate_data = options.get("generate_data", False)

        try:
            # Step 1: Parse the recording
            parsed = parse_recording(path)

            result = {
                "success": True,
                "recording_path": str(path),
                "recording_summary": {
                    "test_name": parsed.test_name,
                    "total_actions": len(parsed.actions),
                    "unique_selectors": len(parsed.selectors_used),
                    "urls_visited": len(parsed.urls_visited),
                },
                "generated_files": [],
            }

            # Step 2: Auto-convert to BDD if requested
            if auto_convert:
                bdd_result = await self._convert_to_bdd(parsed, options)
                result["bdd"] = bdd_result
                result["generated_files"].extend(bdd_result.get("files_generated", []))

            # Step 3: Generate page objects if requested
            if generate_page_objects:
                po_result = await self._generate_page_objects(parsed, options)
                result["page_objects"] = po_result
                result["generated_files"].extend(po_result.get("files_generated", []))

            # Step 4: Generate test data if requested
            if generate_data:
                data_result = await self._generate_test_data(parsed, options)
                result["test_data"] = data_result
                result["generated_files"].extend(data_result.get("files_generated", []))

            # Store in memory for future reference
            await self.remember(
                key=f"recording_{path.stem}",
                value=result,
                memory_type="episodic",
                priority="medium",
                tags=["recording", path.stem],
            )

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Recording workflow failed: {e}",
            }

    async def _convert_to_bdd(self, parsed: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Convert recording to BDD format."""
        feature_name = options.get("feature_name", parsed.test_name)

        try:
            feature = self._converter.convert_recording(parsed, feature_name)
            step_defs = self._step_gen.generate_for_feature(feature)

            output_path = options.get("output_path", self._project_path / "features")
            if isinstance(output_path, (str, Path)):
                Path(output_path).mkdir(parents=True, exist_ok=True)
                feature_file = (
                    Path(output_path) / f"{feature_name.lower().replace(' ', '_')}.feature"
                )
                step_file = (
                    Path(output_path).parent
                    / "steps"
                    / f"{feature_name.lower().replace(' ', '_')}_steps.py"
                )

                # Save feature file
                feature_content = feature.to_gherkin()
                feature_file.write_text(feature_content)

                # Save step definitions
                step_file.parent.mkdir(parents=True, exist_ok=True)
                step_file.write_text(step_defs)

                return {
                    "success": True,
                    "feature_file": str(feature_file),
                    "step_file": str(step_file),
                    "feature_content": feature_content,
                    "step_definitions": step_defs,
                    "scenario_count": len(feature.scenarios),
                    "step_count": sum(len(s.steps) for s in feature.scenarios),
                    "files_generated": [str(feature_file), str(step_file)],
                }

            return {
                "success": True,
                "feature_content": feature.to_gherkin(),
                "step_definitions": step_defs,
                "scenario_count": len(feature.scenarios),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"BDD conversion failed: {e}",
            }

    async def _generate_page_objects(self, parsed: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Generate page objects from recording."""
        output_path = options.get("output_path", self._project_path / "pages")
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            page_objects = self._page_object_gen.generate_from_recording(parsed)

            files_generated = []
            for po in page_objects:
                po_file = output_path / f"{po.name.lower()}_page.py"
                po_file.write_text(po.content)
                files_generated.append(str(po_file))

            return {
                "success": True,
                "page_objects": [{"name": po.name, "file": str(po_file)} for po in page_objects],
                "files_generated": files_generated,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Page object generation failed: {e}",
            }

    async def _generate_test_data(self, parsed: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Extract test data schema from recording."""
        output_path = options.get("output_path", self._project_path / "fixtures")
        output_file = Path(output_path) / "test_data.json"

        try:
            schema = self._extract_data_schema(parsed)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            import json

            output_file.write_text(json.dumps(schema, indent=2))

            return {
                "success": True,
                "data_schema": schema,
                "file": str(output_file),
                "files_generated": [str(output_file)],
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Test data generation failed: {e}",
            }

    def _extract_data_schema(self, parsed: Any) -> dict[str, Any]:
        """Extract test data schema from recording actions."""
        schema = {
            "description": "Auto-generated test data schema from recording",
            "generated": datetime.now().isoformat(),
            "entities": {},
        }

        inputs = []
        for action in parsed.actions:
            if hasattr(action, "type") and action.type in ["fill", "check", "select_option"]:
                selector = getattr(action, "selector", "") or ""
                value = getattr(action, "value", "") or ""

                field_type = "string"
                field_name = selector.split(".")[-1] if "." in selector else selector
                field_name = field_name.split("#")[-1] if "#" in field_name else field_name

                if "email" in selector.lower() or "@" in value:
                    field_type = "email"
                elif "password" in selector.lower():
                    field_type = "password"
                elif "phone" in selector.lower():
                    field_type = "phone"
                elif value.isdigit():
                    field_type = "integer"
                elif "." in value and value.replace(".", "").isdigit():
                    field_type = "number"

                inputs.append(
                    {
                        "name": field_name,
                        "type": field_type,
                        "example": value,
                        "selector": selector,
                    }
                )

        if inputs:
            schema["entities"]["form_data"] = {
                "fields": inputs,
                "description": "Form input fields extracted from recording",
            }

        return schema

    async def analyze_recording(self, recording_path: str) -> dict[str, Any]:
        """
        Analyze a recording and provide insights.

        Args:
            recording_path: Path to recording file

        Returns:
            Analysis results with recommendations
        """
        path = Path(recording_path)
        if not path.exists():
            return {"error": "Recording file not found"}

        parsed = parse_recording(path)

        analysis = {
            "recording_path": str(path),
            "test_name": parsed.test_name,
            "metrics": {
                "total_actions": len(parsed.actions),
                "unique_selectors": len(parsed.selectors_used),
                "urls_visited": len(parsed.urls_visited),
                "forms_filled": sum(1 for a in parsed.actions if getattr(a, "type", "") == "fill"),
                "clicks": sum(1 for a in parsed.actions if getattr(a, "type", "") == "click"),
                "assertions": sum(1 for a in parsed.actions if getattr(a, "type", "") == "expect"),
            },
            "selectors": {
                "fragile": [],
                "stable": [],
                "recommendations": [],
            },
        }

        # Analyze selector quality
        for selector in parsed.selectors_used:
            fragility = getattr(selector, "fragility", "unknown")
            if fragility in ["high", "very_high"]:
                analysis["selectors"]["fragile"].append(
                    {
                        "selector": getattr(selector, "selector", str(selector)),
                        "fragility": fragility,
                        "reason": getattr(selector, "reason", ""),
                    }
                )
            else:
                analysis["selectors"]["stable"].append(
                    {
                        "selector": getattr(selector, "selector", str(selector)),
                        "fragility": fragility,
                    }
                )

        # Generate recommendations
        if len(analysis["selectors"]["fragile"]) > 0:
            analysis["selectors"]["recommendations"].append(
                "Consider using data-testid attributes for more stable selectors"
            )

        if analysis["metrics"]["assertions"] == 0:
            analysis["selectors"]["recommendations"].append(
                "Add assertions to validate expected outcomes"
            )

        return analysis
