"""
Test Execution Module

Provides test discovery and execution capabilities.
"""

from .test_discovery import (
    TestDiscovery,
    DiscoveredTest,
    TestType,
    TestFramework,
)

from .test_execution_engine import (
    TestExecutionEngine,
    TestExecutionResult,
    ExecutionStatus,
    ExecutionConfig,
)

__all__ = [
    "TestDiscovery",
    "DiscoveredTest",
    "TestType",
    "TestFramework",
    "TestExecutionEngine",
    "TestExecutionResult",
    "ExecutionStatus",
    "ExecutionConfig",
]
