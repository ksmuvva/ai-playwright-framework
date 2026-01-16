"""
Context tracking and propagation for agent workflows.

This module provides:
- TaskContext: Complete task execution context with metadata
- ExecutionContext: Execution context passed between agents
- ContextPropagator: Context propagation through agent chain
- Context validation and chain tracking

Context tracking is critical for maintaining traceability from recordings
through deduplication, BDD conversion, and test execution.
"""

from claude_playwright_agent.context.models import (
    TaskContext,
    ExecutionContext,
    ContextChain,
)
from claude_playwright_agent.context.propagation import (
    ContextPropagator,
    get_context_propagator,
)

__all__ = [
    "TaskContext",
    "ExecutionContext",
    "ContextChain",
    "ContextPropagator",
    "get_context_propagator",
]
