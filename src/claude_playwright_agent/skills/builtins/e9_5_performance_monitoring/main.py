"""
E9.5 - Performance Monitoring Skill.

This skill provides performance monitoring capabilities:
- Test execution performance tracking
- Resource usage monitoring
- Bottleneck detection
- Performance reporting
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class MetricType(str, Enum):
    """Performance metric types."""

    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    NETWORK_LATENCY = "network_latency"
    THROUGHPUT = "throughput"
    CUSTOM = "custom"


class PerformanceLevel(str, Enum):
    """Performance levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """
    A performance metric measurement.

    Attributes:
        metric_id: Unique metric identifier
        metric_type: Type of metric
        name: Metric name
        value: Metric value
        unit: Unit of measurement
        timestamp: When metric was recorded
        tags: Metric tags for grouping
        metadata: Additional metadata
    """

    metric_id: str = field(default_factory=lambda: f"metric_{uuid.uuid4().hex[:8]}")
    metric_type: MetricType = MetricType.EXECUTION_TIME
    name: str = ""
    value: float = 0.0
    unit: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type.value,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class PerformanceSnapshot:
    """
    A snapshot of system performance at a point in time.

    Attributes:
        snapshot_id: Unique snapshot identifier
        workflow_id: Associated workflow ID
        timestamp: When snapshot was taken
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in MB
        memory_percent: Memory usage percentage
        disk_io_mb: Disk I/O in MB
        network_io_mb: Network I/O in MB
        active_threads: Number of active threads
        open_files: Number of open files
        metrics: List of metrics in this snapshot
    """

    snapshot_id: str = field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_io_mb: float = 0.0
    network_io_mb: float = 0.0
    active_threads: int = 0
    open_files: int = 0
    metrics: list[PerformanceMetric] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "disk_io_mb": self.disk_io_mb,
            "network_io_mb": self.network_io_mb,
            "active_threads": self.active_threads,
            "open_files": self.open_files,
            "metrics": [m.to_dict() for m in self.metrics],
        }


@dataclass
class BottleneckInfo:
    """
    Information about a performance bottleneck.

    Attributes:
        bottleneck_id: Unique bottleneck identifier
        name: Bottleneck name
        description: Bottleneck description
        severity: Bottleneck severity
        location: Where bottleneck occurs
        impact_ms: Performance impact in milliseconds
        detected_at: When bottleneck was detected
        suggestions: List of suggestions to fix
        resolved: Whether bottleneck is resolved
    """

    bottleneck_id: str = field(default_factory=lambda: f"bottleneck_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    severity: PerformanceLevel = PerformanceLevel.FAIR
    location: str = ""
    impact_ms: float = 0.0
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    suggestions: list[str] = field(default_factory=list)
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bottleneck_id": self.bottleneck_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "location": self.location,
            "impact_ms": self.impact_ms,
            "detected_at": self.detected_at,
            "suggestions": self.suggestions,
            "resolved": self.resolved,
        }


@dataclass
class PerformanceReport:
    """
    A performance report for a workflow execution.

    Attributes:
        report_id: Unique report identifier
        workflow_id: Associated workflow ID
        execution_id: Associated execution ID
        started_at: When monitoring started
        completed_at: When monitoring completed
        total_duration_ms: Total execution duration
        avg_cpu_percent: Average CPU usage
        avg_memory_mb: Average memory usage
        peak_memory_mb: Peak memory usage
        bottlenecks: List of bottlenecks detected
        snapshots: List of performance snapshots
        overall_score: Overall performance score
        recommendations: List of recommendations
    """

    report_id: str = field(default_factory=lambda: f"report_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    execution_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    total_duration_ms: float = 0.0
    avg_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    bottlenecks: list[BottleneckInfo] = field(default_factory=list)
    snapshots: list[PerformanceSnapshot] = field(default_factory=list)
    overall_score: PerformanceLevel = PerformanceLevel.GOOD
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "avg_cpu_percent": self.avg_cpu_percent,
            "avg_memory_mb": self.avg_memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "snapshots": [s.to_dict() for s in self.snapshots],
            "overall_score": self.overall_score.value,
            "recommendations": self.recommendations,
        }


@dataclass
class MonitoringContext:
    """
    Context for performance monitoring operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        reports_generated: Number of reports generated
        bottlenecks_detected: Number of bottlenecks detected
        metrics_collected: Number of metrics collected
        monitoring_history: List of performance reports
        started_at: When monitoring started
        completed_at: When monitoring completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"mon_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    reports_generated: int = 0
    bottlenecks_detected: int = 0
    metrics_collected: int = 0
    monitoring_history: list[PerformanceReport] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "reports_generated": self.reports_generated,
            "bottlenecks_detected": self.bottlenecks_detected,
            "metrics_collected": self.metrics_collected,
            "monitoring_history": [r.to_dict() for r in self.monitoring_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class PerformanceMonitoringAgent(BaseAgent):
    """
    Performance Monitoring Agent.

    This agent provides:
    1. Test execution performance tracking
    2. Resource usage monitoring
    3. Bottleneck detection
    4. Performance reporting
    """

    name = "e9_5_performance_monitoring"
    version = "1.0.0"
    description = "E9.5 - Performance Monitoring"

    def __init__(self, **kwargs) -> None:
        """Initialize the performance monitoring agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E9.5 - Performance Monitoring agent for the Playwright test automation framework. You help users with e9.5 - performance monitoring tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[MonitoringContext] = []
        self._report_registry: dict[str, PerformanceReport] = {}
        self._snapshot_history: list[PerformanceSnapshot] = []
        self._bottleneck_registry: dict[str, BottleneckInfo] = {}

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
        Execute performance monitoring task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the monitoring operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "start_monitoring":
            return await self._start_monitoring(context, execution_context)
        elif task_type == "record_metric":
            return await self._record_metric(context, execution_context)
        elif task_type == "take_snapshot":
            return await self._take_snapshot(context, execution_context)
        elif task_type == "detect_bottlenecks":
            return await self._detect_bottlenecks(context, execution_context)
        elif task_type == "generate_report":
            return await self._generate_report(context, execution_context)
        elif task_type == "get_report":
            return await self._get_report(context, execution_context)
        elif task_type == "get_bottlenecks":
            return await self._get_bottlenecks(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _start_monitoring(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start performance monitoring for a workflow."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        execution_id = context.get("execution_id", "")

        # Create initial snapshot
        snapshot = PerformanceSnapshot(
            workflow_id=workflow_id,
        )

        # Simulate system metrics
        snapshot.cpu_percent = 25.0
        snapshot.memory_mb = 512.0
        snapshot.memory_percent = 12.5
        snapshot.active_threads = 4
        snapshot.open_files = 128

        self._snapshot_history.append(snapshot)

        return f"Started monitoring for workflow '{workflow_id}' (execution: {execution_id})"

    async def _record_metric(self, context: dict[str, Any], execution_context: Any) -> str:
        """Record a performance metric."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        metric_type = context.get("metric_type", MetricType.EXECUTION_TIME)
        name = context.get("name", "")
        value = context.get("value", 0.0)
        unit = context.get("unit", "ms")
        tags = context.get("tags", {})

        if isinstance(metric_type, str):
            metric_type = MetricType(metric_type)

        metric = PerformanceMetric(
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            tags={"workflow_id": workflow_id, **tags},
        )

        # Add to latest snapshot if available
        if self._snapshot_history:
            self._snapshot_history[-1].metrics.append(metric)

        return f"Recorded metric '{name}': {value} {unit}"

    async def _take_snapshot(self, context: dict[str, Any], execution_context: Any) -> str:
        """Take a performance snapshot."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        snapshot = PerformanceSnapshot(
            workflow_id=workflow_id,
        )

        # Simulate system metrics
        snapshot.cpu_percent = 30.0 + (hash(snapshot.snapshot_id) % 50)
        snapshot.memory_mb = 512.0 + (hash(snapshot.snapshot_id) % 256)
        snapshot.memory_percent = snapshot.memory_mb / 4096 * 100
        snapshot.active_threads = 4 + (hash(snapshot.snapshot_id) % 4)
        snapshot.open_files = 128 + (hash(snapshot.snapshot_id) % 64)

        self._snapshot_history.append(snapshot)

        return f"Snapshot '{snapshot.snapshot_id}': CPU={snapshot.cpu_percent:.1f}%, Memory={snapshot.memory_mb:.1f}MB"

    async def _detect_bottlenecks(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect performance bottlenecks."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        bottlenecks = []

        # Analyze snapshots for bottlenecks
        if self._snapshot_history:
            avg_cpu = sum(s.cpu_percent for s in self._snapshot_history) / len(self._snapshot_history)
            avg_memory = sum(s.memory_mb for s in self._snapshot_history) / len(self._snapshot_history)

            # High CPU usage
            if avg_cpu > 80:
                bottleneck = BottleneckInfo(
                    name="High CPU Usage",
                    description=f"Average CPU usage is {avg_cpu:.1f}%",
                    severity=PerformanceLevel.CRITICAL,
                    location="system",
                    impact_ms=avg_cpu * 10,
                    suggestions=[
                        "Reduce parallel test execution",
                        "Optimize test logic",
                        "Add delays between heavy operations",
                    ],
                )
                bottlenecks.append(bottleneck)

            # High memory usage
            if avg_memory > 2048:
                bottleneck = BottleneckInfo(
                    name="High Memory Usage",
                    description=f"Average memory usage is {avg_memory:.1f}MB",
                    severity=PerformanceLevel.POOR,
                    location="system",
                    impact_ms=avg_memory / 10,
                    suggestions=[
                        "Reduce test data size",
                        "Clean up resources after tests",
                        "Use pagination for large data sets",
                    ],
                )
                bottlenecks.append(bottleneck)

        # Check for slow operations
        for snapshot in self._snapshot_history:
            for metric in snapshot.metrics:
                if metric.metric_type == MetricType.EXECUTION_TIME and metric.value > 5000:
                    bottleneck = BottleneckInfo(
                        name=f"Slow {metric.name}",
                        description=f"Operation took {metric.value:.0f}ms",
                        severity=PerformanceLevel.FAIR,
                        location=metric.name,
                        impact_ms=metric.value,
                        suggestions=[
                            "Optimize operation logic",
                            "Add caching",
                            "Consider parallel execution",
                        ],
                    )
                    bottlenecks.append(bottleneck)

        # Register bottlenecks
        for bottleneck in bottlenecks:
            self._bottleneck_registry[bottleneck.bottleneck_id] = bottleneck

        if bottlenecks:
            return f"Detected {len(bottlenecks)} bottleneck(s)"

        return "No bottlenecks detected"

    async def _generate_report(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate a performance report."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        execution_id = context.get("execution_id", "")

        # Calculate metrics from snapshots
        if self._snapshot_history:
            avg_cpu = sum(s.cpu_percent for s in self._snapshot_history) / len(self._snapshot_history)
            avg_memory = sum(s.memory_mb for s in self._snapshot_history) / len(self._snapshot_history)
            peak_memory = max(s.memory_mb for s in self._snapshot_history)
            total_duration = len(self._snapshot_history) * 1000  # Simulated
        else:
            avg_cpu = 0.0
            avg_memory = 0.0
            peak_memory = 0.0
            total_duration = 0.0

        # Determine overall score
        if avg_cpu < 50 and avg_memory < 1024:
            overall_score = PerformanceLevel.EXCELLENT
        elif avg_cpu < 70 and avg_memory < 1536:
            overall_score = PerformanceLevel.GOOD
        elif avg_cpu < 85 and avg_memory < 2048:
            overall_score = PerformanceLevel.FAIR
        else:
            overall_score = PerformanceLevel.POOR

        # Get bottlenecks
        bottlenecks = list(self._bottleneck_registry.values())

        # Generate recommendations
        recommendations = []
        if avg_cpu > 70:
            recommendations.append("Consider reducing parallel execution to lower CPU usage")
        if avg_memory > 1536:
            recommendations.append("Implement memory cleanup between test operations")
        if total_duration > 30000:
            recommendations.append("Optimize test execution to reduce total duration")

        report = PerformanceReport(
            workflow_id=workflow_id,
            execution_id=execution_id,
            completed_at=datetime.now().isoformat(),
            total_duration_ms=total_duration,
            avg_cpu_percent=avg_cpu,
            avg_memory_mb=avg_memory,
            peak_memory_mb=peak_memory,
            bottlenecks=bottlenecks,
            snapshots=self._snapshot_history.copy(),
            overall_score=overall_score,
            recommendations=recommendations,
        )

        self._report_registry[report.report_id] = report

        return f"Generated report '{report.report_id}': Score={overall_score.value}, {len(bottlenecks)} bottleneck(s)"

    async def _get_report(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get performance report by ID."""
        report_id = context.get("report_id")

        if not report_id:
            return "Error: report_id is required"

        report = self._report_registry.get(report_id)
        if report:
            return (
                f"Report '{report_id}': "
                f"score={report.overall_score.value}, "
                f"duration={report.total_duration_ms:.0f}ms, "
                f"avg_cpu={report.avg_cpu_percent:.1f}%, "
                f"avg_mem={report.avg_memory_mb:.1f}MB"
            )

        return f"Error: Report '{report_id}' not found"

    async def _get_bottlenecks(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all bottlenecks or filter by workflow."""
        workflow_id = context.get("workflow_id")

        bottlenecks = list(self._bottleneck_registry.values())

        if workflow_id:
            # Filter by workflow (would need to track workflow in bottleneck)
            pass

        if not bottlenecks:
            return "No bottlenecks detected"

        output = f"Bottlenecks ({len(bottlenecks)}):\n"
        for bottleneck in bottlenecks:
            output += f"- {bottleneck.name}: {bottleneck.severity.value}, {bottleneck.impact_ms:.0f}ms impact\n"

        return output

    def get_report_registry(self) -> dict[str, PerformanceReport]:
        """Get report registry."""
        return self._report_registry.copy()

    def get_snapshot_history(self) -> list[PerformanceSnapshot]:
        """Get snapshot history."""
        return self._snapshot_history.copy()

    def get_bottleneck_registry(self) -> dict[str, BottleneckInfo]:
        """Get bottleneck registry."""
        return self._bottleneck_registry.copy()

    def get_context_history(self) -> list[MonitoringContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

