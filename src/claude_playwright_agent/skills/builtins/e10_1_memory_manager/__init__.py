"""
Memory Management Skill Package

This skill provides a multi-layered memory system for AI agents:
- Short-term memory: Session-based working memory (ephemeral)
- Long-term memory: Persistent knowledge across sessions
- Semantic memory: Concepts, patterns, and general knowledge
- Episodic memory: Specific events and test executions
- Working memory: Current task context and state

Example usage:
    from skills.builtins.e10_1_memory_manager import (
        MemoryManager,
        MemoryType,
        MemoryPriority,
        remember_test_execution,
        recall_similar_failures
    )

    # Create memory manager
    manager = MemoryManager(persist_to_disk=True)

    # Store a memory
    await manager.store(
        key="test_result",
        value={"status": "passed"},
        type=MemoryType.EPISODIC,
        tags=["test", "passed"]
    )

    # Retrieve a memory
    memory = await manager.retrieve("test_result")

    # Remember test execution
    await remember_test_execution(
        manager,
        test_name="login_test",
        outcome="passed",
        duration_ms=1500
    )

    # Get statistics
    stats = manager.get_statistics()
"""

from .main import (
    MemoryType,
    MemoryPriority,
    MemoryEntry,
    MemoryQuery,
    MemoryManager,
    memory_skill,
    remember_test_execution,
    remember_selector_failure,
    recall_similar_failures,
)

__all__ = [
    "MemoryType",
    "MemoryPriority",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryManager",
    "memory_skill",
    "remember_test_execution",
    "remember_selector_failure",
    "recall_similar_failures",
]

__version__ = "1.0.0"
__author__ = "Claude Playwright Agent"
