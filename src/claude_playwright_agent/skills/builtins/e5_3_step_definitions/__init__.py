"""
E5.3 - Step Definition Creator Skill.
"""

from .main import (
    CreationContext,
    DefinitionFile,
    ImplementationStatus,
    StepDefinition,
    StepDefinitionCreatorAgent,
    StepFramework,
    StepParameter,
)

# Aliases for test compatibility
StepDefinitionsAgent = StepDefinitionCreatorAgent

__all__ = [
    "CreationContext",
    "DefinitionFile",
    "ImplementationStatus",
    "StepDefinition",
    "StepDefinitionCreatorAgent",
    "StepFramework",
    "StepParameter",
    # Alias
    "StepDefinitionsAgent",
]
