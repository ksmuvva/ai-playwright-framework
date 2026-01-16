"""
E4.4 - Page Object Generation Skill.
"""

from .main import (
    GeneratedPageObject,
    GenerationContext,
    GenerationFormat,
    PageObjectElement,
    PageObjectGenerationAgent,
    PageObjectMethod,
)

# Aliases for test compatibility
PageObject = GeneratedPageObject

__all__ = [
    "GeneratedPageObject",
    "GenerationContext",
    "GenerationFormat",
    "PageObjectElement",
    "PageObjectGenerationAgent",
    "PageObjectMethod",
    # Alias
    "PageObject",
]
