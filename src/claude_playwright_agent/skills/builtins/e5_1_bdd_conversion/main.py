"""
E5.1 - BDD Conversion Agent Skill.

This skill provides BDD conversion functionality:
- Recording to BDD scenario conversion
- Context-aware action mapping
- Conversion tracking
- Step keyword assignment
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class StepKeyword(str, Enum):
    """Gherkin step keywords."""

    GIVEN = "Given"
    WHEN = "When"
    THEN = "Then"
    AND = "And"
    BUT = "But"


class ConversionStage(str, Enum):
    """BDD conversion stages."""

    INITIALIZED = "initialized"
    PARSING = "parsing"
    MAPPING = "mapping"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConversionContext:
    """
    Context for BDD conversion operation.

    Attributes:
        conversion_id: Unique conversion identifier
        workflow_id: Associated workflow ID
        recording_id: Source recording ID
        feature_name: Generated feature name
        scenario_count: Number of scenarios generated
        step_count: Total steps generated
        conversion_stage: Current conversion stage
        action_mappings: List of action-to-step mappings
        started_at: When conversion started
        completed_at: When conversion completed
        context_preserved: Whether context was preserved
    """

    conversion_id: str = field(default_factory=lambda: f"conv_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_id: str = ""
    feature_name: str = ""
    scenario_count: int = 0
    step_count: int = 0
    conversion_stage: ConversionStage = ConversionStage.INITIALIZED
    action_mappings: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conversion_id": self.conversion_id,
            "workflow_id": self.workflow_id,
            "recording_id": self.recording_id,
            "feature_name": self.feature_name,
            "scenario_count": self.scenario_count,
            "step_count": self.step_count,
            "conversion_stage": self.conversion_stage.value,
            "action_mappings": self.action_mappings,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


@dataclass
class GherkinStep:
    """
    A Gherkin step with context.

    Attributes:
        step_id: Unique step identifier
        keyword: Step keyword (Given/When/Then/And)
        text: Step text
        source_action: Source action that generated this step
        step_context: Context at step creation
        line_number: Line number in scenario
        table: Data table for step
        docstring: Docstring for step
    """

    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    keyword: StepKeyword = StepKeyword.WHEN
    text: str = ""
    source_action: dict[str, Any] = field(default_factory=dict)
    step_context: dict[str, Any] = field(default_factory=dict)
    line_number: int = 0
    table: list[dict[str, str]] = field(default_factory=list)
    docstring: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "keyword": self.keyword.value,
            "text": self.text,
            "source_action": self.source_action,
            "step_context": self.step_context,
            "line_number": self.line_number,
            "table": self.table,
            "docstring": self.docstring,
        }


@dataclass
class GherkinScenario:
    """
    A Gherkin scenario with context.

    Attributes:
        scenario_id: Unique scenario identifier
        name: Scenario name
        steps: List of steps
        tags: Scenario tags
        scenario_context: Context at scenario creation
        source_recording: Source recording info
        description: Scenario description
    """

    scenario_id: str = field(default_factory=lambda: f"scenario_{uuid.uuid4().hex[:8]}")
    name: str = ""
    steps: list[GherkinStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    scenario_context: dict[str, Any] = field(default_factory=dict)
    source_recording: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "steps": [s.to_dict() for s in self.steps],
            "tags": self.tags,
            "scenario_context": self.scenario_context,
            "source_recording": self.source_recording,
            "description": self.description,
        }

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        lines = []

        # Tags
        for tag in self.tags:
            lines.append(f"@{tag}")

        # Scenario line
        lines.append(f"Scenario: {self.name}")

        # Steps
        for step in self.steps:
            prefix = "  "
            keyword = step.keyword.value
            lines.append(f"{prefix}{keyword} {step.text}")

        return "\n".join(lines)


@dataclass
class GherkinFeature:
    """
    A Gherkin feature with context.

    Attributes:
        feature_id: Unique feature identifier
        name: Feature name
        description: Feature description
        scenarios: List of scenarios
        tags: Feature tags
        feature_context: Context at feature creation
        generated_at: When feature was generated
    """

    feature_id: str = field(default_factory=lambda: f"feature_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    scenarios: list[GherkinScenario] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    feature_context: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "description": self.description,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "tags": self.tags,
            "feature_context": self.feature_context,
            "generated_at": self.generated_at,
        }

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        lines = []

        # Feature tags
        for tag in self.tags:
            lines.append(f"@{tag}")

        # Feature line
        lines.append(f"Feature: {self.name}")

        # Description
        if self.description:
            for line in self.description.split("\n"):
                lines.append(f"  {line}")

        lines.append("")

        # Scenarios
        for i, scenario in enumerate(self.scenarios):
            lines.append(scenario.to_gherkin())
            if i < len(self.scenarios) - 1:
                lines.append("")

        return "\n".join(lines)


class BDDConversionAgent(BaseAgent):
    """
    BDD Conversion Agent.

    This agent provides:
    1. Recording to BDD scenario conversion
    2. Context-aware action mapping
    3. Conversion tracking
    4. Step keyword assignment
    """

    name = "e5_1_bdd_conversion"
    version = "1.0.0"
    description = "E5.1 - BDD Conversion Agent"

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
        "assert": StepKeyword.THEN,
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the BDD conversion agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E5.1 - BDD Conversion Agent agent for the Playwright test automation framework. You help users with e5.1 - bdd conversion agent tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._conversion_history: list[ConversionContext] = []
        self._feature_registry: dict[str, GherkinFeature] = {}

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute BDD conversion task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the conversion operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "convert_recording":
            return await self._convert_recording(context, execution_context)
        elif task_type == "map_action_to_step":
            return await self._map_action_to_step(context, execution_context)
        elif task_type == "assign_keyword":
            return await self._assign_keyword(context, execution_context)
        elif task_type == "create_feature":
            return await self._create_feature(context, execution_context)
        elif task_type == "get_conversion_context":
            return await self._get_conversion_context(context, execution_context)
        elif task_type == "get_feature":
            return await self._get_feature(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _convert_recording(self, context: dict[str, Any], execution_context: Any) -> str:
        """Convert recording to BDD with full context tracking."""
        recording = context.get("recording")
        feature_name = context.get("feature_name", "")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not recording:
            return "Error: recording is required"

        # Create conversion context
        conversion_context = ConversionContext(
            workflow_id=workflow_id,
            recording_id=recording.get("recording_id", recording.get("test_name", "")),
            feature_name=feature_name or self._generate_feature_name(recording),
        )

        conversion_context.conversion_stage = ConversionStage.PARSING

        # Extract actions
        actions = recording.get("actions", [])

        conversion_context.conversion_stage = ConversionStage.MAPPING

        # Create scenario
        scenario = GherkinScenario(
            name=recording.get("test_name", "Test Scenario"),
            source_recording={
                "recording_id": conversion_context.recording_id,
                "workflow_id": workflow_id,
            },
            scenario_context={
                "conversion_id": conversion_context.conversion_id,
            },
        )

        # Convert actions to steps
        steps = []
        last_keyword = None

        for action in actions:
            step = self._action_to_step(action, last_keyword, conversion_context.conversion_id)
            if step:
                steps.append(step)
                last_keyword = step.keyword

                # Track mapping
                conversion_context.action_mappings.append({
                    "action_type": action.get("action_type", ""),
                    "step_id": step.step_id,
                    "keyword": step.keyword.value,
                    "step_text": step.text,
                })

        scenario.steps = steps

        # Create feature
        conversion_context.conversion_stage = ConversionStage.GENERATING

        feature = GherkinFeature(
            name=conversion_context.feature_name,
            description=f"Auto-generated from recording: {conversion_context.recording_id}",
            scenarios=[scenario],
            feature_context={
                "conversion_id": conversion_context.conversion_id,
                "workflow_id": workflow_id,
            },
        )

        # Complete conversion
        conversion_context.scenario_count = len(feature.scenarios)
        conversion_context.step_count = sum(len(s.steps) for s in feature.scenarios)
        conversion_context.conversion_stage = ConversionStage.COMPLETED
        conversion_context.completed_at = datetime.now().isoformat()

        self._feature_registry[feature.feature_id] = feature
        self._conversion_history.append(conversion_context)

        return f"Converted recording to BDD: {conversion_context.scenario_count} scenario(s), {conversion_context.step_count} step(s)"

    async def _map_action_to_step(self, context: dict[str, Any], execution_context: Any) -> str:
        """Map action to step with context."""
        action = context.get("action")
        conversion_id = context.get("conversion_id", "")

        if not action:
            return "Error: action is required"

        step = self._action_to_step(action, None, conversion_id)

        if step:
            return f"Mapped action to step: {step.keyword.value} {step.text}"

        return "Failed to map action to step"

    async def _assign_keyword(self, context: dict[str, Any], execution_context: Any) -> str:
        """Assign keyword to action type."""
        action_type = context.get("action_type", "")

        if not action_type:
            return "Error: action_type is required"

        keyword = self.ACTION_KEYWORD_MAP.get(action_type, StepKeyword.WHEN)
        return f"Keyword for '{action_type}': {keyword.value}"

    async def _create_feature(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create feature from scenarios."""
        feature_name = context.get("feature_name", "Feature")
        scenarios_data = context.get("scenarios", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        feature = GherkinFeature(
            name=feature_name,
            feature_context={"workflow_id": workflow_id},
        )

        for scenario_data in scenarios_data:
            scenario = GherkinScenario(
                name=scenario_data.get("name", "Scenario"),
                scenario_context=scenario_data.get("context", {}),
            )

            for step_data in scenario_data.get("steps", []):
                step = GherkinStep(
                    keyword=StepKeyword(step_data.get("keyword", "When")),
                    text=step_data.get("text", ""),
                    step_context=step_data.get("context", {}),
                )
                scenario.steps.append(step)

            feature.scenarios.append(scenario)

        self._feature_registry[feature.feature_id] = feature

        return f"Created feature: {feature.feature_id}"

    async def _get_conversion_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get conversion context."""
        conversion_id = context.get("conversion_id")

        if not conversion_id:
            return "Error: conversion_id is required"

        for conversion_context in self._conversion_history:
            if conversion_context.conversion_id == conversion_id:
                return (
                    f"Conversion '{conversion_id}': "
                    f"{conversion_context.scenario_count} scenario(s), "
                    f"{conversion_context.step_count} step(s)"
                )

        return f"Error: Conversion context '{conversion_id}' not found"

    async def _get_feature(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get feature by ID."""
        feature_id = context.get("feature_id")

        if not feature_id:
            return "Error: feature_id is required"

        feature = self._feature_registry.get(feature_id)
        if feature:
            return f"Feature '{feature.name}': {len(feature.scenarios)} scenario(s)"

        return f"Error: Feature '{feature_id}' not found"

    def _action_to_step(
        self,
        action: dict[str, Any],
        last_keyword: StepKeyword | None,
        conversion_id: str,
    ) -> GherkinStep | None:
        """Convert action to Gherkin step."""
        action_type = action.get("action_type", "")
        selector = action.get("selector", {})
        value = action.get("value", "")

        # Get base keyword
        base_keyword = self.ACTION_KEYWORD_MAP.get(action_type, StepKeyword.WHEN)

        # Use And if same as previous
        keyword = base_keyword
        if last_keyword == base_keyword:
            keyword = StepKeyword.AND

        # Generate step text
        step_text = self._generate_step_text(action_type, selector, value)

        return GherkinStep(
            keyword=keyword,
            text=step_text,
            source_action=action,
            step_context={
                "conversion_id": conversion_id,
                "action_type": action_type,
            },
        )

    def _generate_step_text(self, action_type: str, selector: dict[str, Any], value: str) -> str:
        """Generate step text from action."""
        if action_type == "goto":
            return f'the user navigates to "{value}"'
        elif action_type == "click":
            element_desc = self._describe_element(selector)
            return f'the user clicks on {element_desc}'
        elif action_type in ("fill", "type"):
            element_desc = self._describe_element(selector)
            return f'the user enters "{value}" into {element_desc}'
        elif action_type == "check":
            element_desc = self._describe_element(selector)
            return f'the user checks {element_desc}'
        elif action_type == "uncheck":
            element_desc = self._describe_element(selector)
            return f'the user unchecks {element_desc}'
        elif action_type == "select_option":
            element_desc = self._describe_element(selector)
            return f'the user selects "{value}" from {element_desc}'
        elif action_type == "expect":
            element_desc = self._describe_element(selector)
            return f'{element_desc} should be visible'
        else:
            return f'the user performs action "{action_type}"'

    def _describe_element(self, selector: dict[str, Any]) -> str:
        """Generate element description."""
        if not selector:
            return "the element"

        selector_type = selector.get("type", "")
        selector_value = selector.get("value", "")

        if selector_type == "getByRole":
            role = selector_value or "element"
            name = selector.get("attributes", {}).get("name", "")
            if name:
                return f'the {role} named "{name}"'
            return f'the {role}'
        elif selector_type == "getByLabel":
            return f'the field labeled "{selector_value}"'
        elif selector_type == "getByPlaceholder":
            return f'the field with placeholder "{selector_value}"'
        elif selector_type == "getByText":
            return f'the element with text "{selector_value}"'
        elif selector_type == "getByTestId":
            return f'the element with test ID "{selector_value}"'
        else:
            return "the element"

    def _generate_feature_name(self, recording: dict[str, Any]) -> str:
        """Generate feature name from recording."""
        test_name = recording.get("test_name", "Test")
        return " ".join(word.capitalize() for word in test_name.replace("_", " ").replace("-", " ").split())

    def get_conversion_history(self) -> list[ConversionContext]:
        """Get conversion history."""
        return self._conversion_history.copy()

    def get_feature_registry(self) -> dict[str, GherkinFeature]:
        """Get feature registry."""
        return self._feature_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

