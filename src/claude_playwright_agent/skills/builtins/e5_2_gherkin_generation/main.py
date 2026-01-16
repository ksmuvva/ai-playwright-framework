"""
E5.2 - Gherkin Scenario Generation Skill.

This skill provides Gherkin scenario generation functionality:
- Scenario generation from actions
- Step creation with context
- Tag generation
- Background step handling
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ScenarioType(str, Enum):
    """Types of scenarios."""

    HAPPY_PATH = "happy_path"
    SAD_PATH = "sad_path"
    EDGE_CASE = "edge_case"
    REGRESSION = "regression"
    SMOKE = "smoke"


@dataclass
class ScenarioTemplate:
    """
    Template for scenario generation.

    Attributes:
        template_id: Unique template identifier
        name: Template name
        scenario_type: Type of scenario
        step_pattern: Pattern for steps
        tags: Default tags
        description: Template description
        created_at: When template was created
    """

    template_id: str = field(default_factory=lambda: f"tpl_{uuid.uuid4().hex[:8]}")
    name: str = ""
    scenario_type: ScenarioType = ScenarioType.HAPPY_PATH
    step_pattern: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "scenario_type": self.scenario_type.value,
            "step_pattern": self.step_pattern,
            "tags": self.tags,
            "description": self.description,
            "created_at": self.created_at,
        }


@dataclass
class GeneratedScenario:
    """
    A generated scenario with full context.

    Attributes:
        scenario_id: Unique scenario identifier
        name: Scenario name
        scenario_type: Type of scenario
        steps: List of generated steps
        tags: Scenario tags
        background_steps: Background steps
        generation_context: Context at generation time
        source_actions: Source action data
        data_table: Data table for scenario
        examples: Examples for scenario outline
        generated_at: When scenario was generated
    """

    scenario_id: str = field(default_factory=lambda: f"gen_scenario_{uuid.uuid4().hex[:8]}")
    name: str = ""
    scenario_type: ScenarioType = ScenarioType.HAPPY_PATH
    steps: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    background_steps: list[dict[str, Any]] = field(default_factory=list)
    generation_context: dict[str, Any] = field(default_factory=dict)
    source_actions: list[dict[str, Any]] = field(default_factory=list)
    data_table: list[dict[str, str]] = field(default_factory=list)
    examples: list[dict[str, str]] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "scenario_type": self.scenario_type.value,
            "steps": self.steps,
            "tags": self.tags,
            "background_steps": self.background_steps,
            "generation_context": self.generation_context,
            "source_actions": self.source_actions,
            "data_table": self.data_table,
            "examples": self.examples,
            "generated_at": self.generated_at,
        }


@dataclass
class GenerationContext:
    """
    Context for scenario generation.

    Attributes:
        generation_id: Unique generation identifier
        workflow_id: Associated workflow ID
        recording_id: Source recording ID
        scenarios_generated: Number of scenarios generated
        scenario_types: Breakdown by type
        total_steps: Total steps across all scenarios
        generation_started: When generation started
        generation_completed: When generation completed
        context_preserved: Whether context was preserved
    """

    generation_id: str = field(default_factory=lambda: f"gen_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_id: str = ""
    scenarios_generated: int = 0
    scenario_types: dict[str, int] = field(default_factory=dict)
    total_steps: int = 0
    generation_started: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_completed: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generation_id": self.generation_id,
            "workflow_id": self.workflow_id,
            "recording_id": self.recording_id,
            "scenarios_generated": self.scenarios_generated,
            "scenario_types": self.scenario_types,
            "total_steps": self.total_steps,
            "generation_started": self.generation_started,
            "generation_completed": self.generation_completed,
            "context_preserved": self.context_preserved,
        }


class GherkinGenerationAgent(BaseAgent):
    """
    Gherkin Scenario Generation Agent.

    This agent provides:
    1. Scenario generation from actions
    2. Step creation with context
    3. Tag generation
    4. Background step handling
    """

    name = "e5_2_gherkin_generation"
    version = "1.0.0"
    description = "E5.2 - Gherkin Scenario Generation"

    def __init__(self, **kwargs) -> None:
        """Initialize the Gherkin generation agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E5.2 - Gherkin Scenario Generation agent for the Playwright test automation framework. You help users with e5.2 - gherkin scenario generation tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._generation_history: list[GenerationContext] = []
        self._scenario_registry: dict[str, GeneratedScenario] = {}
        self._template_registry: dict[str, ScenarioTemplate] = {}

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
        Execute Gherkin generation task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the generation operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "generate_scenario":
            return await self._generate_scenario(context, execution_context)
        elif task_type == "generate_scenarios_from_actions":
            return await self._generate_scenarios_from_actions(context, execution_context)
        elif task_type == "create_step":
            return await self._create_step(context, execution_context)
        elif task_type == "generate_tags":
            return await self._generate_tags(context, execution_context)
        elif task_type == "add_background":
            return await self._add_background(context, execution_context)
        elif task_type == "get_generation_context":
            return await self._get_generation_context(context, execution_context)
        elif task_type == "get_scenario":
            return await self._get_scenario(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _generate_scenario(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate a single scenario with context."""
        actions = context.get("actions", [])
        scenario_name = context.get("scenario_name", "Test Scenario")
        scenario_type = context.get("scenario_type", ScenarioType.HAPPY_PATH)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not actions:
            return "Error: actions list is required"

        # Generate scenario
        scenario = GeneratedScenario(
            name=scenario_name,
            scenario_type=scenario_type if isinstance(scenario_type, ScenarioType) else ScenarioType(scenario_type),
            source_actions=actions,
            generation_context={
                "workflow_id": workflow_id,
                "action_count": len(actions),
            },
        )

        # Generate steps from actions
        for i, action in enumerate(actions):
            step = {
                "step_id": f"step_{uuid.uuid4().hex[:8]}",
                "keyword": self._infer_keyword(action),
                "text": self._generate_step_text(action),
                "line_number": i + 1,
                "source_action": action,
                "step_context": {
                    "action_index": i,
                    "scenario_id": scenario.scenario_id,
                },
            }
            scenario.steps.append(step)

        # Generate tags
        scenario.tags = self._generate_tags_for_scenario(scenario)

        self._scenario_registry[scenario.scenario_id] = scenario

        return f"Generated scenario '{scenario.name}': {len(scenario.steps)} step(s)"

    async def _generate_scenarios_from_actions(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate multiple scenarios from action groups."""
        action_groups = context.get("action_groups", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not action_groups:
            return "Error: action_groups list is required"

        # Create generation context
        generation_context = GenerationContext(
            workflow_id=workflow_id,
        )

        scenarios = []

        for group in action_groups:
            scenario = GeneratedScenario(
                name=group.get("name", "Scenario"),
                scenario_type=ScenarioType(group.get("type", ScenarioType.HAPPY_PATH)),
                source_actions=group.get("actions", []),
                generation_context={
                    "workflow_id": workflow_id,
                    "generation_id": generation_context.generation_id,
                },
            )

            # Generate steps
            for i, action in enumerate(group.get("actions", [])):
                step = {
                    "step_id": f"step_{uuid.uuid4().hex[:8]}",
                    "keyword": self._infer_keyword(action),
                    "text": self._generate_step_text(action),
                    "source_action": action,
                }
                scenario.steps.append(step)

            # Generate tags
            scenario.tags = self._generate_tags_for_scenario(scenario)

            scenarios.append(scenario)
            self._scenario_registry[scenario.scenario_id] = scenario

        generation_context.scenarios_generated = len(scenarios)
        generation_context.total_steps = sum(len(s.steps) for s in scenarios)

        # Type breakdown
        for scenario in scenarios:
            scenario_type = scenario.scenario_type.value
            generation_context.scenario_types[scenario_type] = generation_context.scenario_types.get(scenario_type, 0) + 1

        generation_context.generation_completed = datetime.now().isoformat()
        self._generation_history.append(generation_context)

        return f"Generated {len(scenarios)} scenario(s) with {generation_context.total_steps} total step(s)"

    async def _create_step(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a step with context."""
        action = context.get("action")
        keyword = context.get("keyword", "")
        step_text = context.get("step_text", "")

        if not action:
            return "Error: action is required"

        if not keyword:
            keyword = self._infer_keyword(action)

        if not step_text:
            step_text = self._generate_step_text(action)

        step = {
            "step_id": f"step_{uuid.uuid4().hex[:8]}",
            "keyword": keyword,
            "text": step_text,
            "source_action": action,
            "step_context": {
                "created_at": datetime.now().isoformat(),
            },
        }

        return f"Created step: {keyword} {step_text}"

    async def _generate_tags(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate tags for scenario."""
        scenario_type = context.get("scenario_type", ScenarioType.HAPPY_PATH)
        custom_tags = context.get("custom_tags", [])

        tags = []

        # Add type-based tag
        if isinstance(scenario_type, str):
            scenario_type = ScenarioType(scenario_type)

        tags.append(scenario_type.value)

        # Add custom tags
        tags.extend(custom_tags)

        return f"Generated tags: {tags}"

    async def _add_background(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add background steps to scenario."""
        scenario_id = context.get("scenario_id")
        background_steps = context.get("background_steps", [])

        if not scenario_id:
            return "Error: scenario_id is required"

        scenario = self._scenario_registry.get(scenario_id)
        if not scenario:
            return f"Error: Scenario '{scenario_id}' not found"

        for step_data in background_steps:
            step = {
                "step_id": f"bg_step_{uuid.uuid4().hex[:8]}",
                "keyword": step_data.get("keyword", "Given"),
                "text": step_data.get("text", ""),
                "step_context": {
                    "background": True,
                },
            }
            scenario.background_steps.append(step)

        return f"Added {len(background_steps)} background step(s)"

    async def _get_generation_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get generation context."""
        generation_id = context.get("generation_id")

        if not generation_id:
            return "Error: generation_id is required"

        for generation_context in self._generation_history:
            if generation_context.generation_id == generation_id:
                return (
                    f"Generation '{generation_id}': "
                    f"{generation_context.scenarios_generated} scenario(s), "
                    f"{generation_context.total_steps} step(s)"
                )

        return f"Error: Generation context '{generation_id}' not found"

    async def _get_scenario(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get scenario by ID."""
        scenario_id = context.get("scenario_id")

        if not scenario_id:
            return "Error: scenario_id is required"

        scenario = self._scenario_registry.get(scenario_id)
        if scenario:
            return f"Scenario '{scenario.name}': {len(scenario.steps)} step(s), type={scenario.scenario_type.value}"

        return f"Error: Scenario '{scenario_id}' not found"

    def _infer_keyword(self, action: dict[str, Any]) -> str:
        """Infer keyword from action type."""
        action_type = action.get("action_type", "")

        if action_type in ("goto", "navigate"):
            return "Given"
        elif action_type in ("expect", "assert", "screenshot"):
            return "Then"
        else:
            return "When"

    def _generate_step_text(self, action: dict[str, Any]) -> str:
        """Generate step text from action."""
        action_type = action.get("action_type", "")
        selector = action.get("selector", {})
        value = action.get("value", "")

        if action_type == "goto":
            return f'the user navigates to "{value}"'
        elif action_type == "click":
            return f'the user clicks on the element'
        elif action_type in ("fill", "type"):
            return f'the user enters "{value}" into the field'
        elif action_type == "expect":
            return f'the element should be visible'
        else:
            return f'the user performs {action_type}'

    def _generate_tags_for_scenario(self, scenario: GeneratedScenario) -> list[str]:
        """Generate tags for a scenario."""
        tags = [scenario.scenario_type.value]

        # Add additional tags based on scenario
        if "login" in scenario.name.lower():
            tags.append("auth")
        if "search" in scenario.name.lower():
            tags.append("search")

        return tags

    def get_generation_history(self) -> list[GenerationContext]:
        """Get generation history."""
        return self._generation_history.copy()

    def get_scenario_registry(self) -> dict[str, GeneratedScenario]:
        """Get scenario registry."""
        return self._scenario_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

