"""
Step definition generation for BDD frameworks.

This module provides:
- Python step definition generation
- Reusable step templates
- Framework-specific code generation (Behave, pytest-bdd)
- Context-aware parameter handling
"""

from pathlib import Path
from textwrap import dedent, indent
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.bdd.gherkin import GherkinScenario, GherkinStep, StepKeyword


# =============================================================================
# Generation Configuration
# =============================================================================


class StepGenConfig(BaseModel):
    """Configuration for step definition generation."""

    framework: str = Field(default="behave", description="BDD framework (behave or pytest-bdd)")
    use_async: bool = Field(default=True, description="Use async/await")
    include_type_hints: bool = Field(default=True, description="Include type hints")
    include_docstrings: bool = Field(default=True, description="Include docstrings")
    page_object_import: str = Field(default="", description="Page object import path")
    indent_size: int = Field(default=4, description="Indentation size")

    class Config:
        """Pydantic config."""
        use_enum_values = True


# =============================================================================
# Step Definition Models
# =============================================================================


class StepDefinition(BaseModel):
    """A generated step definition."""

    step_text: str = Field(..., description="Step text pattern")
    function_name: str = Field(..., description="Generated function name")
    code: str = Field(..., description="Generated Python code")
    parameters: list[str] = Field(default_factory=list, description="Step parameters")

    class Config:
        """Pydantic config."""
        use_enum_values = True


# =============================================================================
# Step Definition Generator
# =============================================================================


class StepDefinitionGenerator:
    """
    Generate Python step definitions from Gherkin scenarios.

    Features:
    - Behave and pytest-bdd support
    - Parameter extraction from step text
    - Page object integration
    - Reusable step detection
    """

    # Common step templates
    STEP_PATTERNS = {
        "navigation": "the user navigates to {url}",
        "click": "the user clicks {element}",
        "fill": "the user enters {value} into {element}",
        "type": "the user types {value} into {element}",
        "check": "the user checks {element}",
        "uncheck": "the user unchecks {element}",
        "hover": "the user hovers over {element}",
        "press": "the user presses {key}",
        "wait": "the user waits for {element}",
        "see": "the user should see {element}",
        "screenshot": "the user takes a screenshot",
    }

    def __init__(self, config: StepGenConfig | None = None) -> None:
        """
        Initialize the generator.

        Args:
            config: Generation configuration
        """
        self.config = config or StepGenConfig()
        self._generated_steps: dict[str, StepDefinition] = {}
        self._reusable_steps: list[str] = []

    # =========================================================================
    # Step Pattern Generation
    # =========================================================================

    def generate_step_pattern(
        self,
        step: GherkinStep,
    ) -> str:
        """
        Generate a regex pattern for the step.

        Args:
            step: Gherkin step to patternize

        Returns:
            Regex pattern string
        """
        pattern = step.text

        # Replace parameters with regex capture groups
        # URLs
        pattern = pattern.replace("https://", r"https?://")
        pattern = pattern.replace("http://", r"http?://")

        # Generic parameters (quoted values)
        import re

        pattern = re.sub(r'"([^"]*)"', r'"([^"]*)"', pattern)
        pattern = re.sub(r"'([^']*)'", r"'([^']*)'", pattern)

        # Element names (become named groups)
        pattern = re.sub(r'the (\w+) button', r'the "\1" button', pattern)
        pattern = re.sub(r'the (\w+) field', r'the "\1" field', pattern)
        pattern = re.sub(r'the (\w+) placeholder', r'the "\1" placeholder', pattern)

        return f"^{pattern}$"

    def extract_parameters(self, step_text: str) -> list[dict[str, str]]:
        """
        Extract parameters from step text.

        Args:
            step_text: The step text

        Returns:
            List of parameter dictionaries
        """
        params = []

        # Find quoted strings
        import re

        for match in re.finditer(r'"([^"]*)"', step_text):
            params.append({
                "name": f"param_{len(params) + 1}",
                "value": match.group(1),
                "type": "string",
            })

        # Find URLs
        if "http" in step_text:
            for match in re.finditer(r'(https?://[^\s]+)', step_text):
                params.append({
                    "name": "url",
                    "value": match.group(1),
                    "type": "url",
                })

        return params

    # =========================================================================
    # Code Generation
    # =========================================================================

    def generate_step_code(
        self,
        step: GherkinStep,
        function_name: str,
    ) -> str:
        """
        Generate Python code for a step definition.

        Args:
            step: Gherkin step
            function_name: Function name to use

        Returns:
            Generated Python code
        """
        indent_str = " " * self.config.indent_size
        lines = []

        # Determine step type from action
        action = step.original_action

        # Generate code based on framework
        if self.config.framework == "behave":
            lines.extend(self._generate_behave_step(step, function_name, indent_str))
        else:  # pytest-bdd
            lines.extend(self._generate_pytest_bdd_step(step, function_name, indent_str))

        return "\n".join(lines)

    def _generate_behave_step(
        self,
        step: GherkinStep,
        function_name: str,
        indent_str: str,
    ) -> list[str]:
        """Generate Behave-style step definition."""
        lines = []

        pattern = self.generate_step_pattern(step)

        # Async wrapper if needed
        if self.config.use_async:
            type_hint = " -> None" if self.config.include_type_hints else ""
            lines.append(f"@when('{pattern}')")
            lines.append(f"def {function_name}(context{type_hint}):")
        else:
            lines.append(f"@when('{pattern}')")
            lines.append(f"def {function_name}(context):")

        # Docstring
        if self.config.include_docstrings:
            lines.append(f'{indent_str}"""Step definition: {step.text}"""')

        # Implementation
        action = step.original_action

        if action == "goto":
            if self.config.use_async:
                lines.append(f"{indent_str}await context.page.goto({self._get_param_code(step, 'url')})")
            else:
                lines.append(f"{indent_str}context.page.goto({self._get_param_code(step, 'url')})")

        elif action == "click":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.click()")
            else:
                lines.append(f"{indent_str}{elem}.click()")

        elif action == "fill":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.fill({self._get_param_code(step, 'value')})")
            else:
                lines.append(f"{indent_str}{elem}.fill({self._get_param_code(step, 'value')})")

        elif action == "check":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.check()")
            else:
                lines.append(f"{indent_str}{elem}.check()")

        elif action == "uncheck":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.uncheck()")
            else:
                lines.append(f"{indent_str}{elem}.uncheck()")

        elif action == "wait":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.wait_for()")
            else:
                lines.append(f"{indent_str}{elem}.wait_for()")

        elif action == "expect":
            # Assertion
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}assert await {elem}.is_visible()")
            else:
                lines.append(f"{indent_str}assert {elem}.is_visible()")

        else:
            # Generic action - add TODO comment
            lines.append(f"{indent_str}# TODO: Implement {action} action")

        return lines

    def _generate_pytest_bdd_step(
        self,
        step: GherkinStep,
        function_name: str,
        indent_str: str,
    ) -> list[str]:
        """Generate pytest-bdd-style step definition."""
        lines = []

        pattern = self.generate_step_pattern(step)

        # pytest-bdd uses scenario context instead of behave context
        lines.append(f"@scenario('{pattern}')")

        # Async wrapper
        if self.config.use_async:
            type_hint = " -> None" if self.config.include_type_hints else ""
            lines.append(f"async def {function_name}(page{type_hint}):")
        else:
            lines.append(f"def {function_name}(page):")

        # Docstring
        if self.config.include_docstrings:
            lines.append(f'{indent_str}"""Step definition: {step.text}"""')

        # Implementation (similar to behave but uses 'page' instead of 'context.page')
        action = step.original_action

        if action == "goto":
            if self.config.use_async:
                lines.append(f"{indent_str}await page.goto({self._get_param_code(step, 'url')})")
            else:
                lines.append(f"{indent_str}page.goto({self._get_param_code(step, 'url')})")

        elif action == "click":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.click()")
            else:
                lines.append(f"{indent_str}{elem}.click()")

        elif action == "fill":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}await {elem}.fill({self._get_param_code(step, 'value')})")
            else:
                lines.append(f"{indent_str}{elem}.fill({self._get_param_code(step, 'value')})")

        elif action == "expect":
            elem = self._get_element_code(step)
            if self.config.use_async:
                lines.append(f"{indent_str}assert await {elem}.is_visible()")
            else:
                lines.append(f"{indent_str}assert {elem}.is_visible()")

        else:
            lines.append(f"{indent_str}# TODO: Implement {action} action")

        return lines

    def _get_element_code(self, step: GherkinStep) -> str:
        """
        Get page object/locator code for an element.

        Args:
            step: Gherkin step

        Returns:
            Code string for accessing the element
        """
        # If element name is known, use it
        if step.element_name:
            if self.config.page_object_import:
                # Assuming page object is available as 'page' or 'context.page'
                return f"page.{step.element_name}"
            else:
                # Use locator directly
                return f"page.{step._get_locator_from_selector()}"

        # Generate locator from selector
        return self._get_locator_from_selector(step)

    def _get_locator_from_selector(self, step: GherkinStep) -> str:
        """Generate Playwright locator code from selector."""
        selector = step.element_selector

        if not selector:
            return "page.locator('body')"  # Fallback

        # Parse selector and generate locator code
        if "getByRole" in selector:
            # Extract role and name
            import re
            match = re.search(r'getByRole\("([^,]+)",\s*{\s*name:\s*"([^"]+)"', selector)
            if match:
                role = match.group(1).strip('"')
                name = match.group(2)
                return f'page.get_by_role("{role}", name="{name}")'

        elif "getByLabel" in selector:
            import re
            match = re.search(r'getByLabel\("([^"]+)"', selector)
            if match:
                label = match.group(1)
                return f'page.get_by_label("{label}")'

        elif "getByText" in selector:
            import re
            match = re.search(r'getByText\("([^"]+)"', selector)
            if match:
                text = match.group(1)
                return f'page.get_by_text("{text}")'

        elif "locator" in selector:
            import re
            match = re.search(r'locator\("([^"]+)"', selector)
            if match:
                loc = match.group(1)
                return f'page.locator("{loc}")'

        # Fallback
        return f'page.locator("{selector}")'

    def _get_param_code(self, step: GherkinStep, param_type: str) -> str:
        """
        Get parameter code for a step.

        Args:
            step: Gherkin step
            param_type: Type of parameter (url, value, etc.)

        Returns:
            Code string for the parameter
        """
        params = self.extract_parameters(step.text)

        for param in params:
            if param["type"] == param_type or param["name"] == param_type:
                return param["value"]

        return '""'

    # =========================================================================
    # Batch Generation
    # =========================================================================

    def generate_from_scenario(
        self,
        scenario: GherkinScenario,
        output_file: Path,
    ) -> list[StepDefinition]:
        """
        Generate step definitions from a scenario.

        Args:
            scenario: Gherkin scenario
            output_file: File to write definitions to

        Returns:
            List of generated step definitions
        """
        step_defs = []

        for step in scenario.steps:
            # Generate function name
            function_name = self._generate_function_name(step)

            # Generate code
            code = self.generate_step_code(step, function_name)

            # Create step definition
            step_def = StepDefinition(
                step_text=self.generate_step_pattern(step),
                function_name=function_name,
                code=code,
                parameters=self.extract_parameters(step.text),
            )

            step_defs.append(step_def)

            # Cache for reuse detection
            self._generated_steps[step_def.step_text] = step_def

        # Write to file
        self._write_step_definitions(step_defs, output_file)

        return step_defs

    def _generate_function_name(self, step: GherkinStep) -> str:
        """Generate a function name from a step."""
        action = step.original_action

        # Clean up step text to create function name
        import re

        # Remove special characters
        clean_text = re.sub(r'[^\w\s]', '', step.text)
        clean_text = clean_text.strip()

        # Convert to snake_case
        words = clean_text.split()
        if len(words) > 5:
            words = words[:5]  # Limit length

        function_name = "_".join(words).lower()

        # Add action prefix if not clear
        if not function_name.startswith(action):
            function_name = f"{action}_{function_name}"

        # Ensure it starts with a letter
        if not function_name[0].isalpha():
            function_name = f"step_{function_name}"

        return function_name

    def _write_step_definitions(
        self,
        step_defs: list[StepDefinition],
        output_file: Path,
    ) -> None:
        """
        Write step definitions to a file.

        Args:
            step_defs: Step definitions to write
            output_file: Output file path
        """
        lines = []

        # Add imports
        if self.config.use_async:
            lines.append("from playwright.async_api import Page, Locator, expect")
        else:
            lines.append("from playwright.sync_api import Page, Locator, expect")

        if self.config.page_object_import:
            lines.append(f"from {self.config.page_object_import} import *")
            lines.append("")

        # Add each step definition
        for step_def in step_defs:
            lines.append("")
            lines.append(step_def.code)

        # Write file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

    # =========================================================================
    # Reusable Step Detection
    # =========================================================================

    def find_reusable_steps(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, list[GherkinStep]]:
        """
        Find steps that can be reused across scenarios.

        Args:
            scenarios: List of scenarios to analyze

        Returns:
            Dictionary mapping step patterns to list of steps
        """
        step_map: dict[str, list[GherkinStep]] = {}

        for scenario in scenarios:
            for step in scenario.steps:
                pattern = self.generate_step_pattern(step)

                if pattern not in step_map:
                    step_map[pattern] = []
                step_map[pattern].append(step)

        # Filter to only steps used multiple times
        return {
            pattern: steps
            for pattern, steps in step_map.items()
            if len(steps) > 1
        }

    def generate_reusable_steps_file(
        self,
        scenarios: list[GherkinScenario],
        output_file: Path,
    ) -> None:
        """
        Generate a file with common reusable steps.

        Args:
            scenarios: Scenarios to analyze
            output_file: Output file path
        """
        reusable = self.find_reusable_steps(scenarios)

        lines = ["# Common reusable steps"]
        lines.append("")
        lines.append("from playwright.async_api import Page, Locator, expect")
        lines.append("")

        for pattern, steps in reusable.items():
            # Use first step as template
            step = steps[0]
            function_name = self._generate_function_name(step)
            code = self.generate_step_code(step, function_name)

            lines.append("")
            lines.append(f"# Used in {len(steps)} scenarios")
            lines.append(code)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_steps(
    scenario: GherkinScenario,
    output_file: Path,
    framework: str = "behave",
) -> list[StepDefinition]:
    """
    Generate step definitions from a scenario.

    Args:
        scenario: Gherkin scenario
        output_file: Output file path
        framework: BDD framework (behave or pytest-bdd)

    Returns:
        List of generated step definitions
    """
    config = StepGenConfig(framework=framework)
    generator = StepDefinitionGenerator(config)
    return generator.generate_from_scenario(scenario, output_file)
