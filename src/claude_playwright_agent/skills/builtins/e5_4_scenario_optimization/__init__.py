"""
E5.4 - Scenario Optimization Skill.
"""

from .main import (
    OptimizedScenario,
    OptimizationContext,
    OptimizationSuggestion,
    OptimizationType,
    ScenarioOptimizationAgent,
)

# Aliases for test compatibility
OptimizationResult = OptimizedScenario

__all__ = [
    "OptimizedScenario",
    "OptimizationContext",
    "OptimizationSuggestion",
    "OptimizationType",
    "ScenarioOptimizationAgent",
    # Alias
    "OptimizationResult",
]
