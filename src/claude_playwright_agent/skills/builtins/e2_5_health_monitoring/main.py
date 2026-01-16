"""
E2.5 - Agent Health Monitoring Skill.

This skill provides agent health monitoring:
- Heartbeat monitoring with context tracking
- Timeout detection and recovery
- Health status tracking
- Failure recovery with context preservation
- Performance metrics collection
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class HealthStatus(str, Enum):
    """Agent health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HealthMetrics:
    """
    Health metrics for an agent.

    Attributes:
        agent_id: Agent identifier
        heartbeat_count: Number of heartbeats received
        last_heartbeat: Last heartbeat timestamp
        heartbeat_interval: Average interval between heartbeats
        response_time: Last response time in seconds
        error_count: Number of errors detected
        timeout_count: Number of timeouts detected
        restart_count: Number of restarts
        uptime_seconds: Agent uptime in seconds
        resource_usage: Resource usage metrics
        context_preserved: Whether context was preserved on restart
    """

    agent_id: str
    heartbeat_count: int = 0
    last_heartbeat: str = ""
    heartbeat_interval: float = 0.0
    response_time: float = 0.0
    error_count: int = 0
    timeout_count: int = 0
    restart_count: int = 0
    uptime_seconds: float = 0.0
    resource_usage: dict[str, Any] = field(default_factory=dict)
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "heartbeat_count": self.heartbeat_count,
            "last_heartbeat": self.last_heartbeat,
            "heartbeat_interval": self.heartbeat_interval,
            "response_time": self.response_time,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "restart_count": self.restart_count,
            "uptime_seconds": self.uptime_seconds,
            "resource_usage": self.resource_usage,
            "context_preserved": self.context_preserved,
        }


@dataclass
class HealthSnapshot:
    """
    Snapshot of agent health at a point in time.

    Attributes:
        agent_id: Agent identifier
        status: Current health status
        metrics: Health metrics
        context_snapshot: Agent context snapshot
        timestamp: Snapshot timestamp
        recovery_action: Suggested recovery action
    """

    agent_id: str
    status: HealthStatus
    metrics: HealthMetrics
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    recovery_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "context_snapshot": self.context_snapshot,
            "timestamp": self.timestamp,
            "recovery_action": self.recovery_action,
        }


class AgentHealthMonitoringAgent(BaseAgent):
    """
    Agent Health Monitoring Agent.

    This agent provides:
    1. Heartbeat monitoring with context tracking
    2. Timeout detection and recovery
    3. Health status tracking
    4. Failure recovery with context preservation
    5. Performance metrics collection
    """

    name = "e2_5_health_monitoring"
    version = "1.0.0"
    description = "E2.5 - Agent Health Monitoring"

    def __init__(self, **kwargs) -> None:
        """Initialize the health monitoring agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E2.5 - Agent Health Monitoring agent for the Playwright test automation framework. You help users with e2.5 - agent health monitoring tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._health_metrics: dict[str, HealthMetrics] = {}
        self._health_snapshots: dict[str, list[HealthSnapshot]] = {}
        self._last_heartbeat: dict[str, float] = {}
        self._agent_start_times: dict[str, float] = {}
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_interval = 30.0
        self._agent_timeout = 300.0

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
        Execute health monitoring task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the health monitoring operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context", {})
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "register_agent":
            return await self._register_agent(context, execution_context)
        elif task_type == "record_heartbeat":
            return await self._record_heartbeat(context, execution_context)
        elif task_type == "check_health":
            return await self._check_health(context, execution_context)
        elif task_type == "get_health_status":
            return await self._get_health_status(context, execution_context)
        elif task_type == "detect_timeout":
            return await self._detect_timeout(context, execution_context)
        elif task_type == "handle_failure":
            return await self._handle_failure(context, execution_context)
        elif task_type == "take_snapshot":
            return await self._take_snapshot(context, execution_context)
        elif task_type == "get_health_history":
            return await self._get_health_history(context, execution_context)
        elif task_type == "start_monitoring":
            return await self._start_monitoring(context, execution_context)
        elif task_type == "stop_monitoring":
            return await self._stop_monitoring(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _register_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Register an agent for health monitoring."""
        agent_id = context.get("agent_id")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not agent_id:
            return "Error: agent_id is required"

        async with self._lock:
            # Initialize health metrics
            self._health_metrics[agent_id] = HealthMetrics(agent_id=agent_id)
            self._health_snapshots[agent_id] = []
            self._last_heartbeat[agent_id] = time.time()
            self._agent_start_times[agent_id] = time.time()

        return f"Agent '{agent_id}' registered for health monitoring"

    async def _record_heartbeat(self, context: dict[str, Any], execution_context: Any) -> str:
        """Record a heartbeat from an agent with context."""
        agent_id = context.get("agent_id")
        response_time = context.get("response_time", 0.0)
        agent_context = context.get("agent_context", {})

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id not in self._health_metrics:
            await self._register_agent(context, execution_context)

        async with self._lock:
            metrics = self._health_metrics[agent_id]

            # Update heartbeat metrics
            current_time = time.time()
            if self._last_heartbeat[agent_id]:
                interval = current_time - self._last_heartbeat[agent_id]
                # Update average interval
                if metrics.heartbeat_count == 0:
                    metrics.heartbeat_interval = interval
                else:
                    metrics.heartbeat_interval = (
                        metrics.heartbeat_interval * 0.9 + interval * 0.1
                    )

            self._last_heartbeat[agent_id] = current_time
            metrics.last_heartbeat = datetime.now().isoformat()
            metrics.heartbeat_count += 1
            metrics.response_time = response_time
            metrics.uptime_seconds = current_time - self._agent_start_times[agent_id]

            # Store context for recovery
            if agent_context:
                metrics.context_snapshot = agent_context

        return f"Heartbeat recorded for agent '{agent_id}' (count: {metrics.heartbeat_count})"

    async def _check_health(self, context: dict[str, Any], execution_context: Any) -> str:
        """Check health of an agent."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id not in self._health_metrics:
            return f"Error: Agent '{agent_id}' not registered"

        metrics = self._health_metrics[agent_id]
        current_time = time.time()
        time_since_heartbeat = current_time - self._last_heartbeat.get(agent_id, current_time)

        # Determine health status
        status = HealthStatus.HEALTHY
        recovery_action = ""

        if time_since_heartbeat > self._agent_timeout:
            status = HealthStatus.TIMEOUT
            recovery_action = "restart_agent"
        elif time_since_heartbeat > self._heartbeat_interval * 2:
            status = HealthStatus.DEGRADED
            recovery_action = "send_ping"
        elif metrics.error_count > 5:
            status = HealthStatus.UNHEALTHY
            recovery_action = "investigate_errors"

        return f"Agent '{agent_id}' health: {status.value}, action: {recovery_action or 'none'}"

    async def _get_health_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get detailed health status for an agent."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._health_metrics:
            return f"Error: Agent '{agent_id}' not found"

        metrics = self._health_metrics[agent_id]
        current_time = time.time()
        time_since_heartbeat = current_time - self._last_heartbeat.get(agent_id, current_time)

        return (
            f"Agent '{agent_id}' status: "
            f"heartbeats={metrics.heartbeat_count}, "
            f"last_heartbeat={time_since_heartbeat:.1f}s ago, "
            f"errors={metrics.error_count}, "
            f"context_preserved={metrics.context_preserved}"
        )

    async def _detect_timeout(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect and handle agent timeouts."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id not in self._health_metrics:
            return f"Error: Agent '{agent_id}' not registered"

        metrics = self._health_metrics[agent_id]
        current_time = time.time()
        time_since_heartbeat = current_time - self._last_heartbeat.get(agent_id, current_time)

        if time_since_heartbeat > self._agent_timeout:
            metrics.timeout_count += 1
            metrics.context_preserved = False  # Context may be lost on timeout

            # Create health snapshot
            snapshot = HealthSnapshot(
                agent_id=agent_id,
                status=HealthStatus.TIMEOUT,
                metrics=metrics,
                context_snapshot=getattr(metrics, "context_snapshot", {}),
                recovery_action="restart_agent_with_context_restore",
            )
            self._health_snapshots[agent_id].append(snapshot)

            return f"Timeout detected for agent '{agent_id}', context snapshot taken"

        return f"No timeout for agent '{agent_id}'"

    async def _handle_failure(self, context: dict[str, Any], execution_context: Any) -> str:
        """Handle agent failure with context preservation."""
        agent_id = context.get("agent_id")
        error_message = context.get("error_message", "Unknown error")
        preserve_context = context.get("preserve_context", True)

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id not in self._health_metrics:
            return f"Error: Agent '{agent_id}' not registered"

        metrics = self._health_metrics[agent_id]
        metrics.error_count += 1

        # Create failure snapshot with context
        snapshot = HealthSnapshot(
            agent_id=agent_id,
            status=HealthStatus.FAILED,
            metrics=metrics,
            context_snapshot=getattr(metrics, "context_snapshot", {}) if preserve_context else {},
            recovery_action="restart_agent_with_context_restore" if preserve_context else "restart_agent_clean",
        )
        self._health_snapshots[agent_id].append(snapshot)

        return f"Failure handled for agent '{agent_id}', context preserved: {preserve_context}"

    async def _take_snapshot(self, context: dict[str, Any], execution_context: Any) -> str:
        """Take a health snapshot for an agent."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._health_metrics:
            return f"Error: Agent '{agent_id}' not found"

        metrics = self._health_metrics[agent_id]

        # Determine current status
        current_time = time.time()
        time_since_heartbeat = current_time - self._last_heartbeat.get(agent_id, current_time)

        status = HealthStatus.HEALTHY
        if time_since_heartbeat > self._agent_timeout:
            status = HealthStatus.TIMEOUT
        elif time_since_heartbeat > self._heartbeat_interval * 2:
            status = HealthStatus.DEGRADED
        elif metrics.error_count > 5:
            status = HealthStatus.UNHEALTHY

        snapshot = HealthSnapshot(
            agent_id=agent_id,
            status=status,
            metrics=metrics,
            context_snapshot=getattr(metrics, "context_snapshot", {}),
        )

        self._health_snapshots[agent_id].append(snapshot)

        return f"Health snapshot taken for agent '{agent_id}': {status.value}"

    async def _get_health_history(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get health history for an agent."""
        agent_id = context.get("agent_id")
        limit = context.get("limit", 10)

        if not agent_id or agent_id not in self._health_snapshots:
            return f"Error: No health history for agent '{agent_id}'"

        snapshots = self._health_snapshots[agent_id][-limit:]

        return f"Health history for '{agent_id}': {len(snapshots)} snapshot(s)"

    async def _start_monitoring(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start background health monitoring for an agent."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id in self._monitoring_tasks:
            return f"Already monitoring agent '{agent_id}'"

        # Start monitoring task
        async def monitor_agent():
            while True:
                try:
                    check_context = {
                        "agent_id": agent_id,
                        "execution_context": execution_context,
                    }
                    await self._check_health(check_context, execution_context)
                    await asyncio.sleep(self._heartbeat_interval)
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(self._heartbeat_interval)

        self._monitoring_tasks[agent_id] = asyncio.create_task(monitor_agent())

        return f"Started monitoring agent '{agent_id}'"

    async def _stop_monitoring(self, context: dict[str, Any], execution_context: Any) -> str:
        """Stop health monitoring for an agent."""
        agent_id = context.get("agent_id")

        if not agent_id:
            return "Error: agent_id is required"

        if agent_id in self._monitoring_tasks:
            self._monitoring_tasks[agent_id].cancel()
            del self._monitoring_tasks[agent_id]
            return f"Stopped monitoring agent '{agent_id}'"

        return f"Agent '{agent_id}' is not being monitored"

    def get_health_metrics(self, agent_id: str) -> HealthMetrics | None:
        """Get health metrics for an agent."""
        return self._health_metrics.get(agent_id)

    def get_all_health_metrics(self) -> dict[str, HealthMetrics]:
        """Get health metrics for all agents."""
        return self._health_metrics.copy()

    def get_latest_snapshot(self, agent_id: str) -> HealthSnapshot | None:
        """Get latest health snapshot for an agent."""
        snapshots = self._health_snapshots.get(agent_id, [])
        return snapshots[-1] if snapshots else None

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

