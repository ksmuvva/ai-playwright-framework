"""
Self-Healing Module

Provides automatic selector recovery and healing capabilities for test automation.
Includes analytics, code updating, and strategy implementations.

Components:
- HealingAnalytics: Track and analyze healing effectiveness
- CodeUpdater: Automatically update page objects with healed selectors
- SelfHealingEngine: Main healing engine with multiple strategies
"""

from .analytics import HealingAnalytics, HealingAttempt, StrategyStats
from .updater import CodeUpdater

__all__ = [
    "HealingAnalytics",
    "HealingAttempt",
    "StrategyStats",
    "CodeUpdater"
]

__version__ = "1.0.0"
