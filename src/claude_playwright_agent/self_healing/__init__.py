"""
Self-Healing Module

Provides automatic selector recovery and healing capabilities for test automation.
Includes analytics, code updating, strategy implementations, and memory integration.

Components:
- HealingAnalytics: Track and analyze healing effectiveness
- CodeUpdater: Automatically update page objects with healed selectors
- SelfHealingEngine: Main healing engine with multiple strategies
- MemoryPoweredSelfHealingEngine: Memory-integrated healing engine
"""

from .analytics import HealingAnalytics, HealingAttempt, StrategyStats
from .updater import CodeUpdater
from .engine import (
    MemoryPoweredSelfHealingEngine,
    create_memory_powered_healing_engine,
)

__all__ = [
    "HealingAnalytics",
    "HealingAttempt",
    "StrategyStats",
    "CodeUpdater",
    "MemoryPoweredSelfHealingEngine",
    "create_memory_powered_healing_engine",
]

__version__ = "1.0.0"
