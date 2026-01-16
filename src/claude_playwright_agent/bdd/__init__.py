"""
BDD Conversion module for converting actions to executable tests.

This module provides:
- BDD Conversion Agent with dedup data loading
- Gherkin scenario generation
- Step definition creation
- Scenario optimization
- Feature file management
"""

from claude_playwright_agent.bdd.agent import (
    BDDConversionAgent,
    BDDConversionConfig,
    BDDConversionResult,
)
from claude_playwright_agent.bdd.gherkin import (
    GherkinGenerator,
    GherkinScenario,
    GherkinStep,
    ScenarioOutline,
)
from claude_playwright_agent.bdd.steps import StepDefinitionGenerator
from claude_playwright_agent.bdd.optimization import ScenarioOptimizer
from claude_playwright_agent.bdd.features import FeatureFileManager

__all__ = [
    "BDDConversionAgent",
    "BDDConversionConfig",
    "BDDConversionResult",
    "GherkinGenerator",
    "GherkinScenario",
    "GherkinStep",
    "ScenarioOutline",
    "StepDefinitionGenerator",
    "ScenarioOptimizer",
    "FeatureFileManager",
]
