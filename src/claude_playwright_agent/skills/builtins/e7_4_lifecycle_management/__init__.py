"""
E7.4 - Skill Lifecycle Management Skill.
"""

from .main import (
    LifecycleContext,
    LifecycleEvent,
    LifecycleEventRecord,
    LifecycleState,
    SkillLifecycle,
    SkillLifecycleManagementAgent,
)

# Alias for test compatibility
SkillLifecycleAgent = SkillLifecycleManagementAgent

__all__ = [
    "LifecycleContext",
    "LifecycleEvent",
    "LifecycleEventRecord",
    "LifecycleState",
    "SkillLifecycle",
    "SkillLifecycleManagementAgent",
    "SkillLifecycleAgent",
]
