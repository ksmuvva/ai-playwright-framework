"""
E4.3 - Component Extraction Skill.
"""

from .main import (
    ComponentElement,
    ComponentExtractionAgent,
    ComponentType,
    ExtractionContext,
    ReusableComponent,
)

# Aliases for test compatibility
Component = ComponentElement

__all__ = [
    "ComponentElement",
    "ComponentExtractionAgent",
    "ComponentType",
    "ExtractionContext",
    "ReusableComponent",
    # Alias
    "Component",
]
