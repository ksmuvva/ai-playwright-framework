"""
E7.3 - Custom Skill Support Skill.
"""

from .main import (
    CustomSkillSupportAgent,
    ScaffoldContext,
    SkillScaffold,
    SkillTemplate,
    TemplateType,
)

# Alias for test compatibility
CustomSkillAgent = CustomSkillSupportAgent

__all__ = [
    "CustomSkillSupportAgent",
    "ScaffoldContext",
    "SkillScaffold",
    "SkillTemplate",
    "TemplateType",
    "CustomSkillAgent",
]
