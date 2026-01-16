"""
E7.5 - Skill Discovery & Documentation Skill.
"""

from .main import (
    DiscoveryContext,
    DiscoveryScope,
    SkillDiscoveryAgent,
    SkillDocumentation,
    SkillMetadata,
)

# Alias for test compatibility
DiscoveryAgent = SkillDiscoveryAgent

__all__ = [
    "DiscoveryContext",
    "DiscoveryScope",
    "SkillDiscoveryAgent",
    "SkillDocumentation",
    "SkillMetadata",
    "DiscoveryAgent",
]
