"""
BDD Conversion Module for Claude Playwright Agent.

This module converts parsed Playwright recordings into Gherkin BDD scenarios:
- Transform actions to Given/When/Then steps
- Generate feature files
- Create step definition templates
"""

import string
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Gherkin Models
# =============================================================================


class StepKeyword(str, Enum):
    """Gherkin step keywords."""

    GIVEN = "Given"
    WHEN = "When"
    THEN = "Then"
    AND = "And"
    BUT = "But"


class GherkinStep:
    """A single Gherkin step."""

    def __init__(
        self,
        keyword: str,
        text: str,
        docstring: str | None = None,
        table: list[dict[str, str]] | None = None,
    ) -> None:
        self.keyword = keyword
        self.text = text
        self.docstring = docstring
        self.table = table

    def to_gherkin(self, indent: int = 2) -> str:
        """Convert to Gherkin format."""
        prefix = " " * indent
        # Handle both string and Enum values
        keyword_str = self.keyword.value if hasattr(self.keyword, "value") else self.keyword
        line = f"{prefix}{keyword_str} {self.text}"
        result = [line]

        if self.docstring:
            result.append(f'{prefix}  """')
            result.append(prefix + self.docstring)
            result.append(f'{prefix}  """')

        if self.table:
            # Header row (keys from first dict)
            headers = " | ".join(self.table[0].keys())
            result.append(f"{prefix}  | {headers} |")
            # All data rows (values from each dict)
            for row in self.table:
                values = " | ".join(str(v) for v in row.values())
                result.append(f"{prefix}  | {values} |")

        return "\n".join(result)


class GherkinScenario:
    """A Gherkin scenario."""

    def __init__(
        self,
        name: str,
        steps: list[GherkinStep],
        tags: list[str] | None = None,
    ) -> None:
        self.name = name
        self.steps = steps
        self.tags = tags or []

    def to_gherkin(self, indent: int = 2) -> str:
        """Convert to Gherkin format."""
        prefix = " " * indent
        result = []

        # Tags
        if self.tags:
            for tag in self.tags:
                result.append(f"{tag}")
            result.append("")

        # Scenario line
        result.append(f"{prefix}Scenario: {self.name}")

        # Steps
        for i, step in enumerate(self.steps):
            result.append(step.to_gherkin(indent))

        return "\n".join(result)


class GherkinFeature:
    """A Gherkin feature file."""

    def __init__(
        self,
        name: str,
        description: str = "",
        scenarios: list[GherkinScenario] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.scenarios = scenarios or []
        self.tags = tags or []

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        result = []

        # Feature tags
        for tag in self.tags:
            result.append(tag)

        # Feature line
        result.append(f"Feature: {self.name}")

        # Description
        if self.description:
            for line in self.description.split("\n"):
                result.append(f"  {line}")

        result.append("")

        # Scenarios
        for i, scenario in enumerate(self.scenarios):
            result.append(scenario.to_gherkin())
            if i < len(self.scenarios) - 1:
                result.append("")

        return "\n".join(result)


# =============================================================================
# BDD Converter
# =============================================================================


class BDDConverter:
    """
    Convert Playwright recordings to Gherkin BDD scenarios.

    Features:
    - Action-to-step mapping
    - Scenario generation
    - Feature file creation
    - Step definition templates
    """

    # Action type to step keyword mapping
    ACTION_KEYWORD_MAP = {
        "goto": StepKeyword.GIVEN,
        "click": StepKeyword.WHEN,
        "fill": StepKeyword.WHEN,
        "type": StepKeyword.WHEN,
        "check": StepKeyword.WHEN,
        "uncheck": StepKeyword.WHEN,
        "select_option": StepKeyword.WHEN,
        "hover": StepKeyword.WHEN,
        "press": StepKeyword.WHEN,
        "upload": StepKeyword.WHEN,
        "wait_for": StepKeyword.WHEN,
        "expect": StepKeyword.THEN,
        "screenshot": StepKeyword.THEN,
    }

    def __init__(self) -> None:
        """Initialize the BDD converter."""
        self._step_counter = 0

    def convert_recording(
        self,
        parsed_recording: dict[str, Any],
        feature_name: str = "",
    ) -> GherkinFeature:
        """
        Convert a parsed recording to a Gherkin feature.

        Args:
            parsed_recording: Parsed recording data
            feature_name: Optional feature name

        Returns:
            GherkinFeature with scenarios
        """
        # Extract metadata
        test_name = parsed_recording.get("test_name", "Test Scenario")
        actions = parsed_recording.get("actions", [])
        urls_visited = parsed_recording.get("urls_visited", [])

        # Generate feature name
        if not feature_name:
            feature_name = self._generate_feature_name(test_name, urls_visited)

        # Create scenario from actions
        scenario = self._create_scenario(test_name, actions)

        # Create feature
        feature = GherkinFeature(
            name=feature_name,
            description=f"  Auto-generated from Playwright recording: {test_name}",
            scenarios=[scenario],
        )

        return feature

    def _generate_feature_name(self, test_name: str, urls: list[str]) -> str:
        """Generate a feature name from test metadata."""
        # Use test name as base, convert to title case
        name = test_name.replace("_", " ").replace("-", " ")
        return string.capwords(name)

    def _create_scenario(self, test_name: str, actions: list[dict[str, Any]]) -> GherkinScenario:
        """Create a scenario from a list of actions."""
        steps = []
        last_keyword = ""

        for action in actions:
            step = self._action_to_step(action, last_keyword)
            if step:
                steps.append(step)
                last_keyword = step.keyword

        # Add verification step if no explicit assertions
        if not any(s.keyword == StepKeyword.THEN for s in steps):
            steps.append(GherkinStep(
                keyword=StepKeyword.THEN,
                text="the action is completed successfully",
            ))

        return GherkinScenario(
            name=test_name,
            steps=steps,
        )

    def _action_to_step(
        self,
        action: dict[str, Any],
        last_keyword: str,
    ) -> GherkinStep | None:
        """Convert an action to a Gherkin step."""
        action_type = action.get("action_type", "")
        selector = action.get("selector", {})
        value = action.get("value", "")

        # Get the base keyword for this action type
        base_keyword = self.ACTION_KEYWORD_MAP.get(action_type, StepKeyword.WHEN)

        # Use "And" if same as previous keyword
        keyword = base_keyword
        if base_keyword == last_keyword:
            keyword = StepKeyword.AND

        # Generate step text based on action type
        step_text = self._generate_step_text(action_type, selector, value)

        return GherkinStep(keyword=keyword, text=step_text)

    def _generate_step_text(self, action_type: str, selector: dict[str, Any] | None, value: str) -> str:
        """Generate step text for an action."""
        selector_info = selector if selector else {}
        selector_type = selector_info.get("type", "")
        selector_value = selector_info.get("value", "")
        selector_attrs = selector_info.get("attributes", {})

        # goto action
        if action_type == "goto":
            return f'the user navigates to "{value}"'

        # click action
        if action_type == "click":
            element_desc = self._describe_element(selector_info)
            return f'the user clicks on {element_desc}'

        # fill/type action
        if action_type in ("fill", "type"):
            element_desc = self._describe_element(selector_info)
            return f'the user enters "{value}" into {element_desc}'

        # check action
        if action_type == "check":
            element_desc = self._describe_element(selector_info)
            return f'the user checks {element_desc}'

        # uncheck action
        if action_type == "uncheck":
            element_desc = self._describe_element(selector_info)
            return f'the user unchecks {element_desc}'

        # select_option action
        if action_type == "select_option":
            element_desc = self._describe_element(selector_info)
            if value:
                return f'the user selects "{value}" from {element_desc}'
            return f'the user selects an option from {element_desc}'

        # hover action
        if action_type == "hover":
            element_desc = self._describe_element(selector_info)
            return f'the user hovers over {element_desc}'

        # press action
        if action_type == "press":
            return f'the user presses the "{value}" key'

        # wait_for action
        if action_type == "wait_for":
            return 'the user waits for the element to be visible'

        # expect action
        if action_type == "expect":
            element_desc = self._describe_element(selector_info)
            return f'{element_desc} should be visible'

        # screenshot action
        if action_type == "screenshot":
            return 'a screenshot is captured'

        # upload action
        if action_type == "upload":
            element_desc = self._describe_element(selector_info)
            return f'the user uploads a file to {element_desc}'

        # Default/fallback
        return f'the user performs action "{action_type}"'

    def _describe_element(self, selector: dict[str, Any]) -> str:
        """Generate a human-readable description of an element."""
        if not selector:
            return "the element"

        selector_type = selector.get("type", "")
        selector_value = selector.get("value", "")
        selector_attrs = selector.get("attributes", {})

        # getByRole - e.g., "button named 'Sign in'"
        if selector_type == "getByRole":
            role = selector_value or "element"
            name = selector_attrs.get("name", "")
            if name:
                return f'the {role} named "{name}"'
            return f'the {role}'

        # getByLabel - e.g., "field labeled 'Email'"
        if selector_type == "getByLabel":
            label = selector_value or "field"
            return f'the field labeled "{label}"'

        # getByPlaceholder - e.g., "field with placeholder 'Enter email'"
        if selector_type == "getByPlaceholder":
            placeholder = selector_value or "field"
            return f'the field with placeholder "{placeholder}"'

        # getByText - e.g., "element with text 'Submit'"
        if selector_type == "getByText":
            text = selector_value or "element"
            return f'the element with text "{text}"'

        # getByTestId - e.g., "element with test ID 'submit-btn'"
        if selector_type == "getByTestId":
            test_id = selector_value or "element"
            return f'the element with test ID "{test_id}"'

        # locator - e.g., "element with selector '#submit'"
        if selector_type == "locator":
            return f'the element with selector "{selector_value}"'

        # CSS selector
        if selector_type == "css":
            return f'the element "{selector_value}"'

        # Default
        return f'the element'


# =============================================================================
# Step Definition Generator
# =============================================================================


class StepDefinitionGenerator:
    """Generate step definition templates for Gherkin steps."""

    def __init__(self) -> None:
        """Initialize the generator."""
        self._templates: dict[str, str] = {
            "navigate": '''
from playwright.sync_api import Page

@given('the user navigates to "{url}"')
def navigate_to_url(page: Page, url: str) -> None:
    """Navigate to the specified URL."""
    page.goto(url)
''',
            "click": '''
from playwright.sync_api import Page

@when('the user clicks on {element_desc}')
def click_element(page: Page, element_desc: str) -> None:
    """Click on the specified element."""
    # TODO: Implement selector logic for {element_desc}
    page.click("selector_here")
''',
            "fill": '''
from playwright.sync_api import Page

@when('the user enters "{text}" into {element_desc}')
def fill_input(page: Page, text: str, element_desc: str) -> None:
    """Enter text into the specified field."""
    # TODO: Implement selector logic for {element_desc}
    page.fill("selector_here", text)
''',
        }

    def generate_for_feature(self, feature: GherkinFeature) -> str:
        """Generate step definitions for all steps in a feature."""
        result = [
            '"""',
            f'Step definitions for {feature.name}',
            '"""',
            '',
            'from behave import given, when, then',
            'from playwright.sync_api import Page, expect',
            '',
        ]

        for scenario in feature.scenarios:
            for step in scenario.steps:
                result.append(self._generate_step_definition(step))
                result.append("")

        return "\n".join(result)

    def _generate_step_definition(self, step: GherkinStep) -> str:
        """Generate a step definition for a single step."""
        step_text = step.text
        # Convert step text to function name
        func_name = (step_text
            .lower()
            .replace('"', '')
            .replace("'", '')
            .replace(" ", "_")
            .replace("-", "_")
            .strip()[:50])

        # Determine decorator
        decorator = step.keyword.lower()

        return f'''
@{decorator}('{step_text}')
def step_{func_name}(context) -> None:
    """{step.text}"""
    # TODO: Implement step logic
    pass
'''


# =============================================================================
# Convenience Functions
# =============================================================================


def convert_to_gherkin(
    parsed_recording: dict[str, Any],
    feature_name: str = "",
) -> str:
    """
    Convert a parsed recording to Gherkin format.

    Args:
        parsed_recording: Parsed recording data
        feature_name: Optional feature name

    Returns:
        Gherkin feature file content as string
    """
    converter = BDDConverter()
    feature = converter.convert_recording(parsed_recording, feature_name)
    return feature.to_gherkin()


def save_feature_file(
    parsed_recording: dict[str, Any],
    output_path: str | Path,
    feature_name: str = "",
) -> None:
    """
    Convert a recording and save as a feature file.

    Args:
        parsed_recording: Parsed recording data
        output_path: Path to save the feature file
        feature_name: Optional feature name
    """
    gherkin_content = convert_to_gherkin(parsed_recording, feature_name)
    Path(output_path).write_text(gherkin_content, encoding="utf-8")
