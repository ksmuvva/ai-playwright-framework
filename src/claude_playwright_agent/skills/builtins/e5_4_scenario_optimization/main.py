"""
E5.4 - Scenario Optimization Skill.

This skill provides scenario optimization functionality:
- Step consolidation
- Duplicate detection
- Scenario refactoring
- Optimization tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class OptimizationType(str, Enum):
    """Types of optimizations."""

    CONSOLIDATE_STEPS = "consolidate_steps"
    REMOVE_DUPLICATES = "remove_duplicates"
    SIMPLIFY_STEPS = "simplify_steps"
    EXTRACT_BACKGROUND = "extract_background"
    REORDER_STEPS = "reorder_steps"


@dataclass
class OptimizationSuggestion:
    """
    A suggestion for scenario optimization.

    Attributes:
        suggestion_id: Unique suggestion identifier
        optimization_type: Type of optimization
        description: Suggestion description
        affected_steps: List of affected step IDs
        suggested_steps: Suggested replacement steps
        confidence: Confidence in suggestion
        reason: Reason for suggestion
        suggestion_context: Context at suggestion time
    """

    suggestion_id: str = field(default_factory=lambda: f"sugg_{uuid.uuid4().hex[:8]}")
    optimization_type: OptimizationType = OptimizationType.CONSOLIDATE_STEPS
    description: str = ""
    affected_steps: list[str] = field(default_factory=list)
    suggested_steps: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""
    suggestion_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion_id": self.suggestion_id,
            "optimization_type": self.optimization_type.value,
            "description": self.description,
            "affected_steps": self.affected_steps,
            "suggested_steps": self.suggested_steps,
            "confidence": self.confidence,
            "reason": self.reason,
            "suggestion_context": self.suggestion_context,
        }


@dataclass
class OptimizedScenario:
    """
    An optimized scenario with context tracking.

    Attributes:
        scenario_id: Unique scenario identifier
        original_scenario_id: Original scenario ID before optimization
        name: Scenario name
        steps: Optimized steps
        background_steps: Background steps
        applied_optimizations: List of applied optimizations
        optimization_context: Context from optimization
        improvement_metrics: Metrics showing improvement
        optimized_at: When scenario was optimized
    """

    scenario_id: str = field(default_factory=lambda: f"opt_scenario_{uuid.uuid4().hex[:8]}")
    original_scenario_id: str = ""
    name: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    background_steps: list[dict[str, Any]] = field(default_factory=list)
    applied_optimizations: list[str] = field(default_factory=list)
    optimization_context: dict[str, Any] = field(default_factory=dict)
    improvement_metrics: dict[str, Any] = field(default_factory=dict)
    optimized_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "original_scenario_id": self.original_scenario_id,
            "name": self.name,
            "steps": self.steps,
            "background_steps": self.background_steps,
            "applied_optimizations": self.applied_optimizations,
            "optimization_context": self.optimization_context,
            "improvement_metrics": self.improvement_metrics,
            "optimized_at": self.optimized_at,
        }


@dataclass
class OptimizationContext:
    """
    Context for scenario optimization.

    Attributes:
        optimization_id: Unique optimization identifier
        workflow_id: Associated workflow ID
        scenarios_optimized: Number of scenarios optimized
        optimizations_applied: Total optimizations applied
        improvement_summary: Summary of improvements
        optimization_started: When optimization started
        optimization_completed: When optimization completed
        context_preserved: Whether context was preserved
    """

    optimization_id: str = field(default_factory=lambda: f"opt_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    scenarios_optimized: int = 0
    optimizations_applied: int = 0
    improvement_summary: dict[str, Any] = field(default_factory=dict)
    optimization_started: str = field(default_factory=lambda: datetime.now().isoformat())
    optimization_completed: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "optimization_id": self.optimization_id,
            "workflow_id": self.workflow_id,
            "scenarios_optimized": self.scenarios_optimized,
            "optimizations_applied": self.optimizations_applied,
            "improvement_summary": self.improvement_summary,
            "optimization_started": self.optimization_started,
            "optimization_completed": self.optimization_completed,
            "context_preserved": self.context_preserved,
        }


class ScenarioOptimizationAgent(BaseAgent):
    """
    Scenario Optimization Agent.

    This agent provides:
    1. Step consolidation
    2. Duplicate detection
    3. Scenario refactoring
    4. Optimization tracking
    """

    name = "e5_4_scenario_optimization"
    version = "1.0.0"
    description = "E5.4 - Scenario Optimization"

    DUPLICATE_THRESHOLD = 0.9

    def __init__(self, **kwargs) -> None:
        """Initialize the scenario optimization agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E5.4 - Scenario Optimization agent for the Playwright test automation framework. You help users with e5.4 - scenario optimization tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._optimization_history: list[OptimizationContext] = []
        self._scenario_registry: dict[str, OptimizedScenario] = {}
        self._suggestions: list[OptimizationSuggestion] = []

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
        Execute scenario optimization task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the optimization operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "optimize_scenario":
            return await self._optimize_scenario(context, execution_context)
        elif task_type == "consolidate_steps":
            return await self._consolidate_steps(context, execution_context)
        elif task_type == "detect_duplicates":
            return await self._detect_duplicates(context, execution_context)
        elif task_type == "simplify_steps":
            return await self._simplify_steps(context, execution_context)
        elif task_type == "extract_background":
            return await self._extract_background(context, execution_context)
        elif task_type == "get_optimization_context":
            return await self._get_optimization_context(context, execution_context)
        elif task_type == "get_suggestions":
            return await self._get_suggestions(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _optimize_scenario(self, context: dict[str, Any], execution_context: Any) -> str:
        """Optimize a scenario with full context tracking."""
        scenario = context.get("scenario")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        optimizations = context.get("optimizations", [])

        if not scenario:
            return "Error: scenario is required"

        # Create optimized scenario
        optimized = OptimizedScenario(
            original_scenario_id=scenario.get("scenario_id", ""),
            name=scenario.get("name", "Scenario"),
            steps=scenario.get("steps", []).copy(),
            optimization_context={
                "workflow_id": workflow_id,
                "original_step_count": len(scenario.get("steps", [])),
            },
        )

        original_step_count = len(optimized.steps)

        # Apply optimizations
        for opt_type in optimizations:
            if opt_type == "consolidate_steps":
                optimized.steps = self._consolidate_adjacent_steps(optimized.steps)
                optimized.applied_optimizations.append(opt_type)
            elif opt_type == "simplify":
                optimized.steps = self._simplify_step_texts(optimized.steps)
                optimized.applied_optimizations.append(opt_type)
            elif opt_type == "remove_duplicates":
                optimized.steps = self._remove_duplicate_steps(optimized.steps)
                optimized.applied_optimizations.append(opt_type)

        # Calculate improvement metrics
        optimized.improvement_metrics = {
            "original_step_count": original_step_count,
            "optimized_step_count": len(optimized.steps),
            "steps_removed": original_step_count - len(optimized.steps),
            "improvement_ratio": (original_step_count - len(optimized.steps)) / original_step_count if original_step_count > 0 else 0,
        }

        self._scenario_registry[optimized.scenario_id] = optimized

        return (
            f"Optimized scenario: {original_step_count} -> {len(optimized.steps)} steps "
            f"({optimized.improvement_metrics['steps_removed']} removed)"
        )

    async def _consolidate_steps(self, context: dict[str, Any], execution_context: Any) -> str:
        """Consolidate adjacent steps."""
        steps = context.get("steps", [])

        if not steps:
            return "Error: steps list is required"

        consolidated = self._consolidate_adjacent_steps(steps)

        return f"Consolidated {len(steps)} steps to {len(consolidated)}"

    async def _detect_duplicates(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect duplicate steps."""
        steps = context.get("steps", [])

        if not steps:
            return "Error: steps list is required"

        duplicates = self._find_duplicate_steps(steps)

        return f"Found {len(duplicates)} duplicate step pair(s)"

    async def _simplify_steps(self, context: dict[str, Any], execution_context: Any) -> str:
        """Simplify step texts."""
        steps = context.get("steps", [])

        if not steps:
            return "Error: steps list is required"

        simplified = self._simplify_step_texts(steps)

        return f"Simplified {len(steps)} step(s)"

    async def _extract_background(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract common steps as background."""
        scenarios = context.get("scenarios", [])

        if not scenarios:
            return "Error: scenarios list is required"

        # Find common prefix steps
        if len(scenarios) < 2:
            return "Need at least 2 scenarios to extract background"

        first_steps = [s.get("text", "") for s in scenarios[0].get("steps", [])]
        common_steps = []

        for i, step_text in enumerate(first_steps):
            is_common = True
            for scenario in scenarios[1:]:
                steps = scenario.get("steps", [])
                if i >= len(steps):
                    is_common = False
                    break
                if steps[i].get("text", "") != step_text:
                    is_common = False
                    break

            if is_common:
                common_steps.append(step_text)
            else:
                break

        return f"Extracted {len(common_steps)} common step(s) as background"

    async def _get_optimization_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get optimization context."""
        optimization_id = context.get("optimization_id")

        if not optimization_id:
            return "Error: optimization_id is required"

        for optimization_context in self._optimization_history:
            if optimization_context.optimization_id == optimization_id:
                return (
                    f"Optimization '{optimization_id}': "
                    f"{optimization_context.scenarios_optimized} scenario(s), "
                    f"{optimization_context.optimizations_applied} optimization(s)"
                )

        return f"Error: Optimization context '{optimization_id}' not found"

    async def _get_suggestions(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get optimization suggestions."""
        scenario_id = context.get("scenario_id")

        if not scenario_id:
            return "Error: scenario_id is required"

        suggestions = [s for s in self._suggestions if scenario_id in s.suggestion_context.get("scenario_id", "")]

        return f"Found {len(suggestions)} suggestion(s) for scenario"

    def _consolidate_adjacent_steps(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Consolidate adjacent steps with same keyword."""
        if not steps:
            return []

        consolidated = []
        prev_keyword = None

        for step in steps:
            keyword = step.get("keyword", "")

            if keyword == prev_keyword and keyword in ("When", "And"):
                # Change to And
                step_copy = step.copy()
                step_copy["keyword"] = "And"
                consolidated.append(step_copy)
            else:
                consolidated.append(step.copy())

            prev_keyword = consolidated[-1]["keyword"]

        return consolidated

    def _find_duplicate_steps(self, steps: list[dict[str, Any]]) -> list[tuple[int, int]]:
        """Find duplicate steps."""
        duplicates = []
        seen = {}

        for i, step in enumerate(steps):
            step_text = step.get("text", "")
            step_key = (step.get("keyword", ""), step_text)

            if step_key in seen:
                duplicates.append((seen[step_key], i))
            else:
                seen[step_key] = i

        return duplicates

    def _remove_duplicate_steps(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate steps."""
        seen = set()
        unique = []

        for step in steps:
            step_key = (step.get("keyword", ""), step.get("text", ""))
            if step_key not in seen:
                seen.add(step_key)
                unique.append(step)

        return unique

    def _simplify_step_texts(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Simplify step texts."""
        simplified = []

        for step in steps:
            step_copy = step.copy()
            step_text = step.get("text", "")

            # Remove redundant words
            step_text = step_text.replace("the user ", "")
            step_text = step_text.replace("the ", "")

            step_copy["text"] = step_text
            simplified.append(step_copy)

        return simplified

    def get_optimization_history(self) -> list[OptimizationContext]:
        """Get optimization history."""
        return self._optimization_history.copy()

    def get_scenario_registry(self) -> dict[str, OptimizedScenario]:
        """Get scenario registry."""
        return self._scenario_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

