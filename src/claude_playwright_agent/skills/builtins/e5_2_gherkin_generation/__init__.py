"""
E5.2 - Gherkin Scenario Generation Skill.
"""

from .main import (
    GeneratedScenario,
    GenerationContext,
    GherkinGenerationAgent,
    ScenarioTemplate,
    ScenarioType,
)

# Aliases for test compatibility
GherkinDocument = GeneratedScenario

__all__ = [
    "GeneratedScenario",
    "GenerationContext",
    "GherkinGenerationAgent",
    "ScenarioTemplate",
    "ScenarioType",
    # Alias
    "GherkinDocument",
]
