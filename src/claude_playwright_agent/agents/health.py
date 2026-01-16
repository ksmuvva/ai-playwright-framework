"""
Agent Health Monitoring Module for Claude Playwright Agent.

This module provides health monitoring and diagnostic capabilities:
- Agent health checks
- Heartbeat monitoring
- Resource usage tracking
- Agent lifecycle events
- Health status reporting
"""

import asyncio
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from pathlib import Path


class HealthStatus(str, Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    response_time_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
        }


@dataclass
class AgentHealth:
    """Overall health of an agent."""
    agent_id: str
    agent_type: str
    status: HealthStatus
    checks: list[HealthCheckResult] = field(default_factory=list)
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "checks": [check.to_dict() for check in self.checks],
        }


class HealthChecker:
    """Health check executor."""

    def __init__(self) -> None:
        """Initialize health checker."""
        self.checks: dict[str, Callable[[], HealthCheckResult]] = {}

    def register_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
    ) -> None:
        """Register a health check."""
        self.checks[name] = check_func

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found",
            )

        try:
            start_time = datetime.now()
            result = self.checks[name]()
            end_time = datetime.now()
            result.response_time_ms = (end_time - start_time).total_seconds() * 1000
            return result
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.ERROR,
                message=f"Health check failed: {e}",
            )

    async def run_all_checks(self) -> list[HealthCheckResult]:
        """Run all registered health checks."""
        tasks = [self.run_check(name) for name in self.checks]
        return await asyncio.gather(*tasks)


class AgentHealthMonitor:
    """Monitor health of running agents."""

    def __init__(self) -> None:
        """Initialize health monitor."""
        self.agent_health: dict[str, AgentHealth] = {}
        self.health_checker = HealthChecker()
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.health_checker.register_check(
            "memory",
            self._check_memory,
        )
        self.health_checker.register_check(
            "cpu",
            self._check_cpu,
        )
        self.health_checker.register_check(
            "disk",
            self._check_disk,
        )

    def _check_memory(self) -> HealthCheckResult:
        """Check memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()

        status = HealthStatus.HEALTHY
        message = f"Memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)"

        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
        elif memory_percent > 70:
            status = HealthStatus.DEGRADED

        return HealthCheckResult(
            name="memory",
            status=status,
            message=message,
            details={
                "memory_mb": memory_mb,
                "memory_percent": memory_percent,
            },
        )

    def _check_cpu(self) -> HealthCheckResult:
        """Check CPU usage."""
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)

        status = HealthStatus.HEALTHY
        message = f"CPU usage: {cpu_percent:.1f}%"

        if cpu_percent > 90:
            status = HealthStatus.UNHEALTHY
        elif cpu_percent > 70:
            status = HealthStatus.DEGRADED

        return HealthCheckResult(
            name="cpu",
            status=status,
            message=message,
            details={
                "cpu_percent": cpu_percent,
            },
        )

    def _check_disk(self) -> HealthCheckResult:
        """Check disk usage."""
        disk = psutil.disk_usage('/')
        used_percent = disk.used / disk.total * 100

        status = HealthStatus.HEALTHY
        message = f"Disk usage: {used_percent:.1f}%"

        if used_percent > 90:
            status = HealthStatus.UNHEALTHY
        elif used_percent > 80:
            status = HealthStatus.DEGRADED

        return HealthCheckResult(
            name="disk",
            status=status,
            message=message,
            details={
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_percent": used_percent,
            },
        )

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        start_time: datetime | None = None,
    ) -> None:
        """Register an agent for monitoring."""
        self.agent_health[agent_id] = AgentHealth(
            agent_id=agent_id,
            agent_type=agent_type,
            status=HealthStatus.HEALTHY,
            last_heartbeat=datetime.now().isoformat(),
            uptime_seconds=0.0,
        )

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from monitoring."""
        if agent_id in self.agent_health:
            self.agent_health[agent_id].status = HealthStatus.STOPPED

    def update_heartbeat(self, agent_id: str) -> None:
        """Update agent heartbeat timestamp."""
        if agent_id in self.agent_health:
            self.agent_health[agent_id].last_heartbeat = datetime.now().isoformat()

    async def check_agent_health(
        self,
        agent_id: str,
    ) -> AgentHealth:
        """Check health of a specific agent."""
        if agent_id not in self.agent_health:
            return AgentHealth(
                agent_id=agent_id,
                agent_type="unknown",
                status=HealthStatus.UNKNOWN,
            )

        health = self.agent_health[agent_id]

        # Run health checks
        check_results = await self.health_checker.run_all_checks()
        health.checks = check_results

        # Get resource usage
        try:
            process = psutil.Process()
            health.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            health.cpu_usage_percent = process.cpu_percent(interval=0.1)
        except Exception:
            pass

        # Determine overall status
        statuses = [check.status for check in check_results]
        if HealthStatus.UNHEALTHY in statuses or HealthStatus.ERROR in statuses:
            health.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            health.status = HealthStatus.DEGRADED
        else:
            health.status = HealthStatus.HEALTHY

        return health

    async def check_all_agents(self) -> dict[str, AgentHealth]:
        """Check health of all registered agents."""
        results = {}
        for agent_id in self.agent_health:
            results[agent_id] = await self.check_agent_health(agent_id)
        return results

    def get_health_summary(self) -> dict[str, Any]:
        """Get summary of all agent health."""
        summary = {
            "total_agents": len(self.agent_health),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "stopped": 0,
            "unknown": 0,
            "agents": {},
        }

        for agent_id, health in self.agent_health.items():
            status = health.status.value
            summary[status] = summary.get(status, 0) + 1
            summary["agents"][agent_id] = health.to_dict()

        return summary


class HealthCheckCommand:
    """Health check command for CLI."""

    @staticmethod
    async def run_health_checks(
        project_path: Path,
        output_format: str = "table",
    ) -> dict[str, Any]:
        """Run health checks and return results."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        monitor = AgentHealthMonitor()

        # Register the current process as an agent
        monitor.register_agent(
            agent_id="main",
            agent_type="cli",
            start_time=datetime.now(),
        )

        # Run health checks
        health = await monitor.check_agent_health("main")

        # Format output
        if output_format == "json":
            return health.to_dict()

        # Table format
        table = Table(title="Agent Health Status", show_header=True)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="green")
        table.add_column("Response Time", style="dim")

        for check in health.checks:
            status_style = {
                HealthStatus.HEALTHY: "green",
                HealthStatus.DEGRADED: "yellow",
                HealthStatus.UNHEALTHY: "red",
                HealthStatus.ERROR: "bold red",
                HealthStatus.UNKNOWN: "dim",
            }.get(check.status, "white")

            table.add_row(
                check.name,
                f"[{status_style}]{check.status.value}[/]",
                check.message,
                f"{check.response_time_ms:.1f}ms",
            )

        console.print(table)

        return health.to_dict()


# Singleton instance
_global_monitor: Optional[AgentHealthMonitor] = None


def get_health_monitor() -> AgentHealthMonitor:
    """Get the global health monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = AgentHealthMonitor()
    return _global_monitor


__all__ = [
    "HealthStatus",
    "HealthCheckResult",
    "AgentHealth",
    "HealthChecker",
    "AgentHealthMonitor",
    "HealthCheckCommand",
    "get_health_monitor",
]
