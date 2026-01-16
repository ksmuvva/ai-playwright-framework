"""
State Management Module for Claude Playwright Agent.

This module provides state management for the framework including:
- State persistence (state.json)
- Thread-safe operations
- Event logging
- Query interface
- Atomic writes and automatic backups
"""

from claude_playwright_agent.state.manager import (
    NotInitializedError,
    StateEvent,
    StateError,
    StateLockError,
    StateManager,
    StateValidationError,
)
from claude_playwright_agent.state.models import (
    AgentStatus,
    AgentTask,
    ComponentElement,
    FrameworkState,
    FrameworkType,
    PageObject,
    ProjectMetadata,
    Recording,
    RecordingStatus,
    Scenario,
    ExecutionRun,
    UIComponent,
)

__all__ = [
    # Manager
    "StateManager",
    "StateEvent",
    "StateError",
    "StateLockError",
    "StateValidationError",
    "NotInitializedError",
    # Models
    "FrameworkState",
    "ProjectMetadata",
    "Recording",
    "RecordingStatus",
    "Scenario",
    "ExecutionRun",
    "AgentTask",
    "AgentStatus",
    "ComponentElement",
    "UIComponent",
    "PageObject",
    "FrameworkType",
]
