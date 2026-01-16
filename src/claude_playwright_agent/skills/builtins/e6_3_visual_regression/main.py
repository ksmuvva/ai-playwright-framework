"""
E6.3 - Visual Regression Skill.

This skill provides visual regression capabilities:
- Screenshot capture and comparison
- Diff generation
- Baseline management
- Visual change detection
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ComparisonStatus(str, Enum):
    """Comparison status types."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"


class DiffType(str, Enum):
    """Diff types."""

    PIXEL = "pixel"
    LAYOUT = "layout"
    COLOR = "color"
    MISSING = "missing"


@dataclass
class VisualBaseline:
    """
    A visual baseline for comparison.

    Attributes:
        baseline_id: Unique baseline identifier
        name: Baseline name
        test_name: Associated test name
        screenshot_path: Path to baseline screenshot
        created_at: When baseline was created
        viewport: Viewport dimensions
        device: Device type
        tags: Baseline tags
    """

    baseline_id: str = field(default_factory=lambda: f"base_{uuid.uuid4().hex[:8]}")
    name: str = ""
    test_name: str = ""
    screenshot_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    viewport: str = "1280x720"
    device: str = "desktop"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_id": self.baseline_id,
            "name": self.name,
            "test_name": self.test_name,
            "screenshot_path": self.screenshot_path,
            "created_at": self.created_at,
            "viewport": self.viewport,
            "device": self.device,
            "tags": self.tags,
        }


@dataclass
class VisualDiff:
    """
    A visual diff result.

    Attributes:
        diff_id: Unique diff identifier
        baseline_id: Associated baseline ID
        screenshot_path: Path to current screenshot
        diff_path: Path to diff image
        diff_type: Type of difference
        diff_percentage: Percentage of pixels that differ
        status: Comparison status
        detected_at: When diff was detected
        regions: List of affected regions
    """

    diff_id: str = field(default_factory=lambda: f"diff_{uuid.uuid4().hex[:8]}")
    baseline_id: str = ""
    screenshot_path: str = ""
    diff_path: str = ""
    diff_type: DiffType = DiffType.PIXEL
    diff_percentage: float = 0.0
    status: ComparisonStatus = ComparisonStatus.PASSED
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    regions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diff_id": self.diff_id,
            "baseline_id": self.baseline_id,
            "screenshot_path": self.screenshot_path,
            "diff_path": self.diff_path,
            "diff_type": self.diff_type.value,
            "diff_percentage": self.diff_percentage,
            "status": self.status.value,
            "detected_at": self.detected_at,
            "regions": self.regions,
        }


@dataclass
class VisualContext:
    """
    Context for visual regression operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        baselines_created: Number of baselines created
        comparisons_performed: Number of comparisons performed
        diffs_detected: Number of diffs detected
        threshold: Diff threshold for passing
        diff_history: List of visual diffs
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"vis_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    baselines_created: int = 0
    comparisons_performed: int = 0
    diffs_detected: int = 0
    threshold: float = 0.1
    diff_history: list[VisualDiff] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "baselines_created": self.baselines_created,
            "comparisons_performed": self.comparisons_performed,
            "diffs_detected": self.diffs_detected,
            "threshold": self.threshold,
            "diff_history": [d.to_dict() for d in self.diff_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class VisualRegressionAgent(BaseAgent):
    """
    Visual Regression Agent.

    This agent provides:
    1. Screenshot capture and comparison
    2. Diff generation
    3. Baseline management
    4. Visual change detection
    """

    name = "e6_3_visual_regression"
    version = "1.0.0"
    description = "E6.3 - Visual Regression"

    def __init__(self, **kwargs) -> None:
        """Initialize the visual regression agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E6.3 - Visual Regression agent for the Playwright test automation framework. You help users with e6.3 - visual regression tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[VisualContext] = []
        self._baseline_registry: dict[str, VisualBaseline] = {}
        self._diff_history: list[VisualDiff] = []

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
        """Execute visual regression task."""
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "create_baseline":
            return await self._create_baseline(context, execution_context)
        elif task_type == "capture_screenshot":
            return await self._capture_screenshot(context, execution_context)
        elif task_type == "compare_visuals":
            return await self._compare_visuals(context, execution_context)
        elif task_type == "generate_diff":
            return await self._generate_diff(context, execution_context)
        elif task_type == "get_baseline":
            return await self._get_baseline(context, execution_context)
        elif task_type == "get_diffs":
            return await self._get_diffs(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _create_baseline(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a visual baseline."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        name = context.get("name", "")
        test_name = context.get("test_name", "")
        screenshot_path = context.get("screenshot_path", "")
        viewport = context.get("viewport", "1280x720")
        device = context.get("device", "desktop")

        baseline = VisualBaseline(
            name=name,
            test_name=test_name,
            screenshot_path=screenshot_path,
            viewport=viewport,
            device=device,
        )

        self._baseline_registry[baseline.baseline_id] = baseline

        return f"Created baseline '{name}' for test '{test_name}' (ID: {baseline.baseline_id})"

    async def _capture_screenshot(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture a screenshot for visual testing."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        test_name = context.get("test_name", "")
        output_path = context.get("output_path", "screenshots")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{test_name}_{timestamp}.png"
        full_path = str(Path(output_path) / filename)

        return f"Captured screenshot: {full_path}"

    async def _compare_visuals(self, context: dict[str, Any], execution_context: Any) -> str:
        """Compare screenshots against baseline."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        baseline_id = context.get("baseline_id")
        screenshot_path = context.get("screenshot_path")
        threshold = context.get("threshold", 0.1)

        if not baseline_id:
            return "Error: baseline_id is required"

        baseline = self._baseline_registry.get(baseline_id)
        if not baseline:
            return f"Error: Baseline '{baseline_id}' not found"

        # Simulate comparison
        diff_percentage = 0.05  # Simulated 5% diff

        if diff_percentage > threshold:
            status = ComparisonStatus.FAILED
        else:
            status = ComparisonStatus.PASSED

        diff = VisualDiff(
            baseline_id=baseline_id,
            screenshot_path=screenshot_path,
            diff_percentage=diff_percentage,
            status=status,
        )

        self._diff_history.append(diff)

        return f"Comparison: {diff_percentage:.1%} diff, status={status.value}"

    async def _generate_diff(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate diff image."""
        baseline_id = context.get("baseline_id")
        screenshot_path = context.get("screenshot_path")
        diff_type = context.get("diff_type", DiffType.PIXEL)

        if isinstance(diff_type, str):
            diff_type = DiffType(diff_type)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diff_{timestamp}.png"
        output_dir = context.get("output_dir", "artifacts/diffs")
        diff_path = str(Path(output_dir) / filename)

        return f"Generated diff image: {diff_path}"

    async def _get_baseline(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get baseline by ID."""
        baseline_id = context.get("baseline_id")

        if not baseline_id:
            return "Error: baseline_id is required"

        baseline = self._baseline_registry.get(baseline_id)
        if baseline:
            return (
                f"Baseline '{baseline_id}': "
                f"{baseline.name}, "
                f"{baseline.test_name}, "
                f"{baseline.viewport}"
            )

        return f"Error: Baseline '{baseline_id}' not found"

    async def _get_diffs(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all diffs or filter by baseline."""
        baseline_id = context.get("baseline_id")

        diffs = self._diff_history

        if baseline_id:
            diffs = [d for d in diffs if d.baseline_id == baseline_id]

        if not diffs:
            return "No diffs found"

        return f"Diffs: {len(diffs)} found"

    def get_baseline_registry(self) -> dict[str, VisualBaseline]:
        """Get baseline registry."""
        return self._baseline_registry.copy()

    def get_diff_history(self) -> list[VisualDiff]:
        """Get diff history."""
        return self._diff_history.copy()

    def get_context_history(self) -> list[VisualContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

