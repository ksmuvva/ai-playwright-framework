"""
Gherkin scenario generation with context tracking.

This module provides:
- Action to Gherkin step mapping
- Scenario generation with proper structure
- Scenario outline support for data-driven testing
- Context preservation throughout generation
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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


@dataclass
class GherkinStep:
    """
    A single Gherkin step with full context.

    Maintains:
    - Original action context
    - Step keyword
    - Step text
    - Arguments (docstring, table)
    """

    keyword: StepKeyword
    text: str
    line_number: int = 0

    # Context tracking
    recording_id: str = ""
    page_url: str = ""
    original_action: str = ""
    element_name: str = ""
    element_selector: str = ""

    # Step arguments
    docstring: str = ""
    table: list[dict[str, str]] | None = None

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        line = f"    {self.keyword.value} {self.text}"

        if self.docstring:
            line += f' """{self.docstring}"""'

        if self.table:
            line += "\n"
            if self.table:
                headers = " | ".join(self.table[0].keys())
                line += f"      | {headers} |\n"

                for row in self.table:
                    values = " | ".join(str(v) for v in row.values())
                    line += f"      | {values} |\n"

        return line

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "keyword": self.keyword.value,
            "text": self.text,
            "line_number": self.line_number,
            "recording_id": self.recording_id,
            "page_url": self.page_url,
            "original_action": self.original_action,
            "element_name": self.element_name,
            "element_selector": self.element_selector,
            "docstring": self.docstring,
            "table": self.table,
        }


@dataclass
class GherkinScenario:
    """
    A complete Gherkin scenario with context.

    Contains:
    - Scenario name and tags
    - All steps with context
    - Original recording source
    """

    name: str
    scenario_id: str
    steps: list[GherkinStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Context tracking
    recording_id: str = ""
    feature_file: str = ""
    line_number: int = 0

    # Metadata
    description: str = ""
    is_outline: bool = False
    background_steps: list[GherkinStep] = field(default_factory=list)

    def add_step(self, step: GherkinStep) -> None:
        """Add a step to the scenario."""
        self.steps.append(step)

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        lines = []

        # Tags
        for tag in self.tags:
            lines.append(f"  {tag}")

        # Scenario header
        scenario_type = "Scenario Outline" if self.is_outline else "Scenario"
        lines.append(f"  {scenario_type}: {self.name}")

        # Steps
        for step in self.steps:
            lines.append(step.to_gherkin())

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "scenario_id": self.scenario_id,
            "steps": [s.to_dict() for s in self.steps],
            "tags": self.tags,
            "recording_id": self.recording_id,
            "feature_file": self.feature_file,
            "line_number": self.line_number,
            "description": self.description,
            "is_outline": self.is_outline,
        }


@dataclass
class ScenarioOutline:
    """
    A scenario outline with examples table.

    Used for data-driven testing with multiple data sets.
    """

    base_scenario: GherkinScenario
    examples: list[dict[str, str]] = field(default_factory=list)
    parameter_names: list[str] = field(default_factory=list)

    def to_gherkin(self) -> str:
        """Convert to Gherkin format with examples."""
        lines = [self.base_scenario.to_gherkin()]

        # Add examples table
        if self.examples:
            lines.append("\n  Examples:")
            header = " | ".join(self.parameter_names)
            lines.append(f"    | {header} |")

            for example in self.examples:
                values = " | ".join(example.get(param, "") for param in self.parameter_names)
                lines.append(f"    | {values} |")

        return "\n".join(lines)


# =============================================================================
# Action to Step Mapping
# =============================================================================


class ActionStepMapper:
    """
    Maps Playwright actions to Gherkin steps.

    Maintains context throughout the mapping process:
    - Page URL context
    - Element context
    - Action context
    """

    # Step templates for different action types
    STEP_TEMPLATES = {
        "goto": "the user navigates to {url}",
        "click": "the user clicks {element}",
        "fill": "the user enters {value} into {element}",
        "type": "the user types {value} into {element}",
        "check": "the user checks {element}",
        "uncheck": "the user unchecks {element}",
        "select": "the user selects {value} from {element}",
        "hover": "the user hovers over {element}",
        "press": "the user presses {key}",
        "upload": "the user uploads {file} to {element}",
        "wait_for": "the user waits for {element}",
        "expect": "the user should see {element}",
        "screenshot": "the user takes a screenshot",
    }

    def __init__(self) -> None:
        """Initialize the mapper."""
        self._element_name_cache: dict[str, str] = {}

    def map_action_to_step(
        self,
        action_type: str,
        selector: dict[str, Any] | None = None,
        value: str | None = None,
        page_url: str = "",
        element_name: str = "",
        recording_id: str = "",
        line_number: int = 0,
    ) -> GherkinStep:
        """
        Map an action to a Gherkin step.

        Args:
            action_type: Type of action (goto, click, etc.)
            selector: Selector information
            value: Value for the action
            page_url: Current page URL
            element_name: Name of the element
            recording_id: Source recording ID
            line_number: Line number in recording

        Returns:
            GherkinStep with full context
        """
        # Determine element description
        element_desc = element_name or self._describe_selector(selector) if selector else "the element"

        # Get step template
        template = self.STEP_TEMPLATES.get(action_type, "the user performs {action} on {element}")

        # Fill in the template
        step_text = template.format(
            url=value or page_url,
            element=element_desc,
            value=value or "",
            key=value or "",
            file=value or "",
            action=action_type,
        )

        # Determine keyword (first step is Given, rest are When)
        # This will be adjusted at scenario level
        keyword = StepKeyword.WHEN

        return GherkinStep(
            keyword=keyword,
            text=step_text,
            line_number=line_number,
            recording_id=recording_id,
            page_url=page_url,
            original_action=action_type,
            element_name=element_name,
            element_selector=selector.get("raw", "") if selector else "",
        )

    def _describe_selector(self, selector: dict[str, Any]) -> str:
        """
        Generate a human-readable description for a selector.

        Args:
            selector: Selector information

        Returns:
            Human-readable description
        """
        selector_type = selector.get("type", "")
        value = selector.get("value", "")

        if selector_type == "getByRole":
            return f"the {value} button"
        elif selector_type == "getByLabel":
            return f"the field labeled {value}"
        elif selector_type == "getByPlaceholder":
            return f"the {value} placeholder"
        elif selector_type == "getByTestId":
            return f"the element with test id {value}"
        elif selector_type == "getByText":
            return f"the element containing text {value}"
        elif selector_type == "getByTitle":
            return f"the element with title {value}"
        else:
            return f"the element"

    def set_element_name(self, selector_hash: str, element_name: str) -> None:
        """
        Cache an element name for a selector.

        Args:
            selector_hash: Hash of the selector
            element_name: Name to use
        """
        self._element_name_cache[selector_hash] = element_name

    def get_element_name(self, selector_hash: str) -> str | None:
        """Get cached element name for a selector."""
        return self._element_name_cache.get(selector_hash)


# =============================================================================
# Gherkin Generator
# =============================================================================


class GherkinGenerator:
    """
    Generate Gherkin scenarios from actions with context tracking.

    Features:
    - Action to step conversion
    - Scenario structure generation
    - Scenario outline support
    - Context preservation
    """

    def __init__(self) -> None:
        """Initialize the generator."""
        self.mapper = ActionStepMapper()
        self._scenarios: list[GherkinScenario] = []

    def generate_scenario(
        self,
        name: str,
        actions: list[dict[str, Any]],
        recording_id: str = "",
        page_url: str = "",
        tags: list[str] | None = None,
        element_names: dict[str, str] | None = None,
    ) -> GherkinScenario:
        """
        Generate a Gherkin scenario from actions.

        Args:
            name: Scenario name
            actions: List of action dictionaries
            recording_id: Source recording ID
            page_url: Starting page URL
            tags: Optional tags
            element_names: Mapping of selector hashes to names

        Returns:
            GherkinScenario with steps and context
        """
        scenario = GherkinScenario(
            name=name,
            scenario_id=f"scenario_{hash(name)}",
            tags=tags or [],
            recording_id=recording_id,
        )

        # Cache element names
        if element_names:
            for sel_hash, elem_name in element_names.items():
                self.mapper.set_element_name(sel_hash, elem_name)

        # Convert actions to steps
        for i, action in enumerate(actions):
            action_type = action.get("action_type", "")
            selector = action.get("selector")
            value = action.get("value")
            line_number = action.get("line_number", i)

            # Get element name from cache if available
            element_name = ""
            if selector:
                import hashlib
                sel_hash = hashlib.sha256(selector.get("raw", "").encode()).hexdigest()[:16]
                element_name = self.mapper.get_element_name(sel_hash) or ""

            step = self.mapper.map_action_to_step(
                action_type=action_type,
                selector=selector,
                value=value,
                page_url=page_url,
                element_name=element_name,
                recording_id=recording_id,
                line_number=line_number,
            )

            scenario.add_step(step)

        # Set proper keywords (first step is Given/When, rest are And)
        self._adjust_step_keywords(scenario)

        self._scenarios.append(scenario)
        return scenario

    def _adjust_step_keywords(self, scenario: GherkinScenario) -> None:
        """
        Adjust step keywords for proper Gherkin syntax.

        First Given/When step followed by And/But keywords.
        """
        if not scenario.steps:
            return

        # First step
        first_step = scenario.steps[0]
        if first_step.keyword in (StepKeyword.WHEN, StepKeyword.THEN):
            first_step.keyword = StepKeyword.GIVEN
        elif first_step.keyword == StepKeyword.AND:
            first_step.keyword = StepKeyword.GIVEN

        # Subsequent steps
        for i in range(1, len(scenario.steps)):
            step = scenario.steps[i]
            if step.keyword in (StepKeyword.GIVEN, StepKeyword.WHEN, StepKeyword.THEN):
                step.keyword = StepKeyword.AND

    def generate_scenario_outline(
        self,
        base_scenario: GherkinScenario,
        examples: list[dict[str, str]],
        parameter_names: list[str],
    ) -> ScenarioOutline:
        """
        Generate a scenario outline from a base scenario.

        Args:
            base_scenario: Base scenario with parameterized steps
            examples: Example data sets
            parameter_names: Parameter names for examples table

        Returns:
            ScenarioOutline with examples
        """
        return ScenarioOutline(
            base_scenario=base_scenario,
            examples=examples,
            parameter_names=parameter_names,
        )

    def get_all_scenarios(self) -> list[GherkinScenario]:
        """Get all generated scenarios."""
        return self._scenarios.copy()

    def clear(self) -> None:
        """Clear all generated scenarios."""
        self._scenarios.clear()


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_scenario(
    name: str,
    actions: list[dict[str, Any]],
    recording_id: str = "",
    page_url: str = "",
    tags: list[str] | None = None,
) -> GherkinScenario:
    """
    Generate a Gherkin scenario from actions.

    Args:
        name: Scenario name
        actions: List of action dictionaries
        recording_id: Source recording ID
        page_url: Starting page URL
        tags: Optional tags

    Returns:
        GherkinScenario with steps
    """
    generator = GherkinGenerator()
    return generator.generate_scenario(name, actions, recording_id, page_url, tags)


def actions_to_gherkin(
    actions: list[dict[str, Any]],
    scenario_name: str = "Test Scenario",
) -> str:
    """
    Convert actions to Gherkin format string.

    Args:
        actions: List of action dictionaries
        scenario_name: Name for the scenario

    Returns:
        Gherkin format string
    """
    scenario = generate_scenario(scenario_name, actions)
    return scenario.to_gherkin()
