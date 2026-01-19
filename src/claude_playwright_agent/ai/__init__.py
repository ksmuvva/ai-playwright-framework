"""
AI Package - AI-powered components for test automation.

Modules:
- locator_healer: AI-powered selector recovery
- scenario_analyzer: Test scenario analysis and optimization
- wait_optimizer: Intelligent wait management optimization
"""

from .locator_healer import LocatorHealer, HealingStrategy, HealingAttempt, LocatorHealth
from .scenario_analyzer import ScenarioAnalyzer, ScenarioPattern, ScenarioAnalysis
from .wait_optimizer import WaitOptimizer, WaitMetrics, OptimizationRecommendation

__all__ = [
    "LocatorHealer",
    "HealingStrategy",
    "HealingAttempt",
    "LocatorHealth",
    "ScenarioAnalyzer",
    "ScenarioPattern",
    "ScenarioAnalysis",
    "WaitOptimizer",
    "WaitMetrics",
    "OptimizationRecommendation",
]
