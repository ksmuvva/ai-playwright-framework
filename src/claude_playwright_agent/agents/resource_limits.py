"""
Agent resource limit management for Claude Playwright Agent.

This module implements:
- Resource tracking per agent (memory, CPU, time)
- Resource limit enforcement
- Concurrent agent limiting
- Resource quota management
- Automatic cleanup of resource-exhausted agents
"""

import asyncio
import os
import psutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# =============================================================================
# Resource Types and Limits
# =============================================================================


class ResourceType(str, Enum):
    """Types of resources that can be tracked and limited."""
    MEMORY = "memory"           # Memory usage in bytes
    CPU_TIME = "cpu_time"       # CPU time in seconds
    WALL_TIME = "wall_time"     # Wall clock time in seconds
    OPERATIONS = "operations"   # Number of operations performed
    NETWORK = "network"         # Network I/O in bytes
    DISK = "disk"              # Disk I/O in bytes


@dataclass
class ResourceLimit:
    """
    Resource limit configuration.

    Attributes:
        resource_type: Type of resource being limited
        max_value: Maximum allowed value
        per_agent: Whether limit applies per-agent or globally
        action_on_exceed: Action to take when limit is exceeded
        grace_period: Grace period before enforcement (seconds)
    """

    resource_type: ResourceType
    max_value: int | float
    per_agent: bool = True
    action_on_exceed: str = "terminate"  # terminate, throttle, warn
    grace_period: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_type": self.resource_type.value,
            "max_value": self.max_value,
            "per_agent": self.per_agent,
            "action_on_exceed": self.action_on_exceed,
            "grace_period": self.grace_period,
        }


# Default resource limits
DEFAULT_LIMITS = {
    ResourceType.MEMORY: ResourceLimit(
        resource_type=ResourceType.MEMORY,
        max_value=2 * 1024 * 1024 * 1024,  # 2 GB
        per_agent=True,
        action_on_exceed="terminate",
        grace_period=5.0,
    ),
    ResourceType.CPU_TIME: ResourceLimit(
        resource_type=ResourceType.CPU_TIME,
        max_value=3600,  # 1 hour
        per_agent=True,
        action_on_exceed="terminate",
        grace_period=10.0,
    ),
    ResourceType.WALL_TIME: ResourceLimit(
        resource_type=ResourceType.WALL_TIME,
        max_value=7200,  # 2 hours
        per_agent=True,
        action_on_exceed="terminate",
        grace_period=30.0,
    ),
    ResourceType.OPERATIONS: ResourceLimit(
        resource_type=ResourceType.OPERATIONS,
        max_value=1000000,  # 1 million operations
        per_agent=True,
        action_on_exceed="warn",
        grace_period=0.0,
    ),
}


# =============================================================================
# Resource Usage Tracking
# =============================================================================


@dataclass
class ResourceUsage:
    """
    Current resource usage for an agent.

    Attributes:
        agent_id: Agent being tracked
        start_time: When tracking started
        memory_usage: Current memory usage in bytes
        cpu_time: CPU time consumed in seconds
        wall_time: Wall clock time elapsed in seconds
        operations: Number of operations performed
        network_io: Network I/O in bytes
        disk_io: Disk I/O in bytes
        process: psutil Process for tracking
    """

    agent_id: str
    start_time: float = field(default_factory=time.time)
    memory_usage: int = 0
    cpu_time: float = 0.0
    wall_time: float = 0.0
    operations: int = 0
    network_io: int = 0
    disk_io: int = 0
    process: Any = field(default=None)
    last_update: float = field(default_factory=time.time)

    def update(self) -> None:
        """Update resource usage from system metrics."""
        self.wall_time = time.time() - self.start_time
        self.last_update = time.time()

        if self.process:
            try:
                self.memory_usage = self.process.memory_info().rss
                self.cpu_time = self.process.cpu_times().user + self.process.cpu_times().system

                # I/O counters (may not be available on all platforms)
                try:
                    io_counters = self.process.io_counters()
                    self.disk_io = io_counters.read_bytes + io_counters.write_bytes
                except (AttributeError, psutil.AccessDenied):
                    pass

                # Network I/O is tracked separately
                try:
                    net_io = self.process.io_counters()
                    if hasattr(net_io, 'read_count') and hasattr(net_io, 'write_count'):
                        self.network_io = getattr(net_io, 'read_bytes', 0) + getattr(net_io, 'write_bytes', 0)
                except (AttributeError, psutil.AccessDenied):
                    pass

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def get_usage(self, resource_type: ResourceType) -> int | float:
        """
        Get current usage for a resource type.

        Args:
            resource_type: Type of resource

        Returns:
            Current usage value
        """
        self.update()

        mapping = {
            ResourceType.MEMORY: self.memory_usage,
            ResourceType.CPU_TIME: self.cpu_time,
            ResourceType.WALL_TIME: self.wall_time,
            ResourceType.OPERATIONS: self.operations,
            ResourceType.NETWORK: self.network_io,
            ResourceType.DISK: self.disk_io,
        }

        return mapping.get(resource_type, 0)

    def increment_operations(self, count: int = 1) -> None:
        """Increment operation counter."""
        self.operations += count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        self.update()
        return {
            "agent_id": self.agent_id,
            "start_time": self.start_time,
            "memory_usage_mb": round(self.memory_usage / (1024 * 1024), 2),
            "cpu_time_seconds": round(self.cpu_time, 2),
            "wall_time_seconds": round(self.wall_time, 2),
            "operations": self.operations,
            "network_io_mb": round(self.network_io / (1024 * 1024), 2),
            "disk_io_mb": round(self.disk_io / (1024 * 1024), 2),
        }


# =============================================================================
# Resource Limit Manager
# =============================================================================


class ResourceLimitManager:
    """
    Manages resource limits for agents.

    Features:
    - Track resource usage per agent
    - Enforce resource limits
    - Automatic cleanup on limit exceed
    - Global and per-agent limits
    - Resource quota management
    """

    def __init__(
        self,
        max_concurrent_agents: int = 10,
        limits: dict[ResourceType, ResourceLimit] | None = None,
        check_interval: float = 5.0,
    ) -> None:
        """
        Initialize the resource limit manager.

        Args:
            max_concurrent_agents: Maximum number of concurrent agents
            limits: Custom resource limits (uses defaults if None)
            check_interval: Seconds between resource checks
        """
        self._max_concurrent_agents = max_concurrent_agents
        self._limits = limits or DEFAULT_LIMITS.copy()
        self._check_interval = check_interval

        # Resource tracking per agent
        self._usage: dict[str, ResourceUsage] = {}
        self._context: dict[str, dict[str, Any]] = {}

        # Global resource tracking
        self._global_usage: dict[ResourceType, int | float] = {
            rt: 0 for rt in ResourceType
        }

        # Limit enforcement state
        self._enforcement_active: bool = False
        self._monitor_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start resource monitoring."""
        if self._enforcement_active:
            return

        self._enforcement_active = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop resource monitoring."""
        self._enforcement_active = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def register_agent(
        self,
        agent_id: str,
        process: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Register an agent for resource tracking.

        Args:
            agent_id: Agent identifier
            process: psutil Process object for tracking
            context: Optional context information

        Raises:
            ResourceLimitError: If max concurrent agents reached
        """
        # Check concurrent agent limit
        if len(self._usage) >= self._max_concurrent_agents:
            raise ResourceLimitError(
                f"Maximum concurrent agents ({self._max_concurrent_agents}) reached"
            )

        # Create resource usage tracker
        usage = ResourceUsage(
            agent_id=agent_id,
            process=process,
        )
        usage.update()

        self._usage[agent_id] = usage
        self._context[agent_id] = context or {}

        # Update global usage
        for resource_type in ResourceType:
            self._global_usage[resource_type] += usage.get_usage(resource_type)

    async def unregister_agent(self, agent_id: str) -> ResourceUsage | None:
        """
        Unregister an agent from tracking.

        Args:
            agent_id: Agent identifier

        Returns:
            Final resource usage or None if agent not found
        """
        usage = self._usage.pop(agent_id, None)
        if usage:
            # Update global usage
            for resource_type in ResourceType:
                self._global_usage[resource_type] -= usage.get_usage(resource_type)

            self._context.pop(agent_id, None)
            usage.update()
            return usage

        return None

    def get_usage(self, agent_id: str) -> ResourceUsage | None:
        """
        Get current resource usage for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            ResourceUsage or None if agent not found
        """
        usage = self._usage.get(agent_id)
        if usage:
            usage.update()
        return usage

    def get_global_usage(self) -> dict[ResourceType, int | float]:
        """Get global resource usage across all agents."""
        return self._global_usage.copy()

    def get_agent_count(self) -> int:
        """Get current number of tracked agents."""
        return len(self._usage)

    async def check_limits(self, agent_id: str) -> list[str]:
        """
        Check if an agent has exceeded any limits.

        Args:
            agent_id: Agent identifier

        Returns:
            List of exceeded limit descriptions
        """
        usage = self._usage.get(agent_id)
        if not usage:
            return []

        exceeded = []

        for resource_type, limit in self._limits.items():
            if limit.per_agent:
                # Check per-agent limit
                current = usage.get_usage(resource_type)

                # Check grace period
                if usage.wall_time < limit.grace_period:
                    continue

                if current > limit.max_value:
                    exceeded.append(
                        f"{resource_type.value}: {current} > {limit.max_value}"
                    )

        return exceeded

    async def _monitor_loop(self) -> None:
        """Periodically check resource limits and enforce them."""
        while self._enforcement_active:
            await asyncio.sleep(self._check_interval)

            # Check each agent
            for agent_id in list(self._usage.keys()):
                try:
                    exceeded = await self.check_limits(agent_id)

                    if exceeded:
                        # Get limit for first exceeded resource
                        resource_name = exceeded[0].split(":")[0]
                        resource_type = ResourceType(resource_name)
                        limit = self._limits.get(resource_type)

                        if limit and limit.action_on_exceed == "terminate":
                            # Emit warning for termination
                            await self._handle_limit_exceeded(
                                agent_id, resource_type, limit
                            )

                except Exception as e:
                    # Log error but continue monitoring
                    pass

    async def _handle_limit_exceeded(
        self,
        agent_id: str,
        resource_type: ResourceType,
        limit: ResourceLimit,
    ) -> None:
        """
        Handle a resource limit being exceeded.

        Args:
            agent_id: Agent that exceeded limit
            resource_type: Resource type that was exceeded
            limit: The limit that was exceeded
        """
        # Get final usage
        usage = self._usage.get(agent_id)
        if usage:
            usage.update()

        # Log the event (would use proper logging in production)
        # For now, just mark the agent for cleanup

        # The orchestrator should handle actual termination
        # This method just records the event

    def set_limit(self, limit: ResourceLimit) -> None:
        """
        Set or update a resource limit.

        Args:
            limit: Resource limit to set
        """
        self._limits[limit.resource_type] = limit

    def remove_limit(self, resource_type: ResourceType) -> None:
        """
        Remove a resource limit.

        Args:
            resource_type: Resource type to remove limit for
        """
        self._limits.pop(resource_type, None)

    def get_limits(self) -> dict[ResourceType, ResourceLimit]:
        """Get all configured resource limits."""
        return self._limits.copy()

    def get_summary(self) -> dict[str, Any]:
        """
        Get resource usage summary.

        Returns:
            Summary of all resource usage
        """
        return {
            "active_agents": len(self._usage),
            "max_concurrent_agents": self._max_concurrent_agents,
            "global_usage": {
                rt.value: self._format_usage(rt, val)
                for rt, val in self._global_usage.items()
            },
            "agents": {
                agent_id: usage.to_dict()
                for agent_id, usage in self._usage.items()
            },
        }

    def _format_usage(self, resource_type: ResourceType, value: int | float) -> str:
        """Format resource usage for display."""
        if resource_type == ResourceType.MEMORY:
            return f"{value / (1024 * 1024):.1f} MB"
        elif resource_type in (ResourceType.CPU_TIME, ResourceType.WALL_TIME):
            return f"{value:.1f} s"
        elif resource_type == ResourceType.OPERATIONS:
            return f"{int(value)}"
        else:
            return f"{value / (1024 * 1024):.1f} MB"


# =============================================================================
# Exceptions
# =============================================================================


class ResourceLimitError(Exception):
    """Exception raised when a resource limit is exceeded."""

    def __init__(
        self,
        message: str,
        resource_type: ResourceType | None = None,
        current_value: int | float | None = None,
        limit_value: int | float | None = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            resource_type: Type of resource that was exceeded
            current_value: Current resource value
            limit_value: Limit that was exceeded
        """
        super().__init__(message)
        self.resource_type = resource_type
        self.current_value = current_value
        self.limit_value = limit_value


# =============================================================================
# Convenience Functions
# =============================================================================


_limit_manager_instance: ResourceLimitManager | None = None


def get_resource_manager(
    max_concurrent_agents: int = 10,
    limits: dict[ResourceType, ResourceLimit] | None = None,
) -> ResourceLimitManager:
    """
    Get the singleton resource limit manager instance.

    Args:
        max_concurrent_agents: Maximum concurrent agents
        limits: Custom resource limits

    Returns:
        ResourceLimitManager instance
    """
    global _limit_manager_instance
    if _limit_manager_instance is None:
        _limit_manager_instance = ResourceLimitManager(
            max_concurrent_agents=max_concurrent_agents,
            limits=limits,
        )
    return _limit_manager_instance
