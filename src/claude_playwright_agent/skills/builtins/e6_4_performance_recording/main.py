"""
E6.4 - Performance Recording Skill.

This skill provides performance recording capabilities:
- Timing capture
- Resource tracking
- Bottleneck detection
- Performance metrics recording
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class MetricCategory(str, Enum):
    """Performance metric categories."""

    TIMING = "timing"
    RESOURCE = "resource"
    NETWORK = "network"
    RENDERING = "rendering"
    CUSTOM = "custom"


@dataclass
class PerformanceMetric:
    """
    A performance metric recorded during execution.

    Attributes:
        metric_id: Unique metric identifier
        category: Metric category
        name: Metric name
        value: Metric value
        unit: Unit of measurement
        timestamp: When metric was recorded
        url: Associated URL
        element: Associated element selector
        metadata: Additional metadata
    """

    metric_id: str = field(default_factory=lambda: f"metric_{uuid.uuid4().hex[:8]}")
    category: MetricCategory = MetricCategory.TIMING
    name: str = ""
    value: float = 0.0
    unit: str = "ms"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    url: str = ""
    element: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_id": self.metric_id,
            "category": self.category.value,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "url": self.url,
            "element": self.element,
            "metadata": self.metadata,
        }


@dataclass
class ResourceTiming:
    """
    Resource timing information.

    Attributes:
        timing_id: Unique timing identifier
        url: Resource URL
        resource_type: Type of resource
        start_time: Start time in ms
        duration: Duration in ms
        size_bytes: Resource size in bytes
        cached: Whether resource was cached
        timestamp: When timing was recorded
    """

    timing_id: str = field(default_factory=lambda: f"timing_{uuid.uuid4().hex[:8]}")
    url: str = ""
    resource_type: str = ""
    start_time: float = 0.0
    duration: float = 0.0
    size_bytes: int = 0
    cached: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timing_id": self.timing_id,
            "url": self.url,
            "resource_type": self.resource_type,
            "start_time": self.start_time,
            "duration": self.duration,
            "size_bytes": self.size_bytes,
            "cached": self.cached,
            "timestamp": self.timestamp,
        }


@dataclass
class PerformanceRecording:
    """
    A performance recording session.

    Attributes:
        recording_id: Unique recording identifier
        workflow_id: Associated workflow ID
        test_name: Test name
        started_at: When recording started
        completed_at: When recording completed
        metrics: List of recorded metrics
        resource_timings: List of resource timings
        total_duration_ms: Total recording duration
    """

    recording_id: str = field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    test_name: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    metrics: list[PerformanceMetric] = field(default_factory=list)
    resource_timings: list[ResourceTiming] = field(default_factory=list)
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recording_id": self.recording_id,
            "workflow_id": self.workflow_id,
            "test_name": self.test_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metrics": [m.to_dict() for m in self.metrics],
            "resource_timings": [t.to_dict() for t in self.resource_timings],
            "total_duration_ms": self.total_duration_ms,
        }


@dataclass
class RecordingContext:
    """
    Context for performance recording operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        recordings_created: Number of recordings created
        metrics_captured: Number of metrics captured
        bottlenecks_detected: Number of bottlenecks detected
        recording_history: List of performance recordings
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"perf_rec_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recordings_created: int = 0
    metrics_captured: int = 0
    bottlenecks_detected: int = 0
    recording_history: list[PerformanceRecording] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "recordings_created": self.recordings_created,
            "metrics_captured": self.metrics_captured,
            "bottlenecks_detected": self.bottlenecks_detected,
            "recording_history": [r.to_dict() for r in self.recording_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class PerformanceRecordingAgent(BaseAgent):
    """
    Performance Recording Agent.

    This agent provides:
    1. Timing capture
    2. Resource tracking
    3. Bottleneck detection
    4. Performance metrics recording
    """

    name = "e6_4_performance_recording"
    version = "1.0.0"
    description = "E6.4 - Performance Recording"

    def __init__(self, **kwargs) -> None:
        """Initialize the performance recording agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E6.4 - Performance Recording agent for the Playwright test automation framework. You help users with e6.4 - performance recording tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[RecordingContext] = []
        self._recording_registry: dict[str, PerformanceRecording] = {}
        self._metric_history: list[PerformanceMetric] = []

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
        """Execute performance recording task."""
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "start_recording":
            return await self._start_recording(context, execution_context)
        elif task_type == "stop_recording":
            return await self._stop_recording(context, execution_context)
        elif task_type == "record_metric":
            return await self._record_metric(context, execution_context)
        elif task_type == "record_resource_timing":
            return await self._record_resource_timing(context, execution_context)
        elif task_type == "get_recording":
            return await self._get_recording(context, execution_context)
        elif task_type == "get_metrics":
            return await self._get_metrics(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _start_recording(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start a performance recording."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        test_name = context.get("test_name", "")

        recording = PerformanceRecording(
            workflow_id=workflow_id,
            test_name=test_name,
        )

        self._recording_registry[recording.recording_id] = recording

        return f"Started performance recording '{recording.recording_id}' for '{test_name}'"

    async def _stop_recording(self, context: dict[str, Any], execution_context: Any) -> str:
        """Stop a performance recording."""
        recording_id = context.get("recording_id")

        if not recording_id:
            return "Error: recording_id is required"

        recording = self._recording_registry.get(recording_id)
        if not recording:
            return f"Error: Recording '{recording_id}' not found"

        recording.completed_at = datetime.now().isoformat()
        metric_count = len(recording.metrics)
        resource_count = len(recording.resource_timings)

        return f"Stopped recording '{recording_id}': {metric_count} metrics, {resource_count} resources"

    async def _record_metric(self, context: dict[str, Any], execution_context: Any) -> str:
        """Record a performance metric."""
        recording_id = context.get("recording_id")
        category = context.get("category", MetricCategory.TIMING)
        name = context.get("name", "")
        value = context.get("value", 0.0)
        unit = context.get("unit", "ms")

        if isinstance(category, str):
            category = MetricCategory(category)

        metric = PerformanceMetric(
            category=category,
            name=name,
            value=value,
            unit=unit,
        )

        self._metric_history.append(metric)

        # Add to recording if provided
        if recording_id:
            recording = self._recording_registry.get(recording_id)
            if recording:
                recording.metrics.append(metric)

        return f"Recorded metric '{name}': {value} {unit}"

    async def _record_resource_timing(self, context: dict[str, Any], execution_context: Any) -> str:
        """Record resource timing."""
        recording_id = context.get("recording_id")
        url = context.get("url", "")
        resource_type = context.get("resource_type", "")
        duration = context.get("duration", 0.0)
        size_bytes = context.get("size_bytes", 0)
        cached = context.get("cached", False)

        timing = ResourceTiming(
            url=url,
            resource_type=resource_type,
            duration=duration,
            size_bytes=size_bytes,
            cached=cached,
        )

        # Add to recording if provided
        if recording_id:
            recording = self._recording_registry.get(recording_id)
            if recording:
                recording.resource_timings.append(timing)

        return f"Recorded resource timing: {url} ({duration:.0f}ms)"

    async def _get_recording(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get recording by ID."""
        recording_id = context.get("recording_id")

        if not recording_id:
            return "Error: recording_id is required"

        recording = self._recording_registry.get(recording_id)
        if recording:
            return (
                f"Recording '{recording_id}': "
                f"{recording.test_name}, "
                f"{len(recording.metrics)} metrics, "
                f"{len(recording.resource_timings)} resources"
            )

        return f"Error: Recording '{recording_id}' not found"

    async def _get_metrics(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all metrics or filter by recording."""
        recording_id = context.get("recording_id")
        category = context.get("category")

        metrics = self._metric_history

        if recording_id:
            recording = self._recording_registry.get(recording_id)
            if recording:
                metrics = recording.metrics

        if category:
            if isinstance(category, str):
                category = MetricCategory(category)
            metrics = [m for m in metrics if m.category == category]

        return f"Metrics: {len(metrics)} found"

    def get_recording_registry(self) -> dict[str, PerformanceRecording]:
        """Get recording registry."""
        return self._recording_registry.copy()

    def get_metric_history(self) -> list[PerformanceMetric]:
        """Get metric history."""
        return self._metric_history.copy()

    def get_context_history(self) -> list[RecordingContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

