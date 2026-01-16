"""
E2.5 - Agent Health Monitoring Skill.
"""

from .main import (
    AgentHealthMonitoringAgent,
    HealthMetrics,
    HealthSnapshot,
    HealthStatus,
)

# Aliases for test compatibility
AgentHealthStatus = HealthStatus
HealthMonitoringAgent = AgentHealthMonitoringAgent
HealthCheckResult = HealthSnapshot
SystemMetrics = HealthMetrics

__all__ = [
    "AgentHealthMonitoringAgent",
    "HealthMetrics",
    "HealthSnapshot",
    "HealthStatus",
    # Aliases
    "AgentHealthStatus",
    "HealthMonitoringAgent",
    "HealthCheckResult",
    "SystemMetrics",
]
