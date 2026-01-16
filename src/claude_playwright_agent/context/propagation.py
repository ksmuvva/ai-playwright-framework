"""
Context propagation system for agent workflows.

This module provides the ContextPropagator class which manages
context creation, validation, and propagation through the agent chain.
"""

import logging
from pathlib import Path
from typing import Any

from claude_playwright_agent.context.models import (
    ExecutionContext,
    TaskContext,
    ContextChain,
    create_task_context,
    create_execution_context,
)
from claude_playwright_agent.state import StateManager

logger = logging.getLogger(__name__)


# =============================================================================
# Context Propagator
# =============================================================================


class ContextPropagator:
    """
    Propagate context through agent chain.

    The ContextPropagator ensures that:
    1. Context is preserved through the entire agent pipeline
    2. Child contexts are created with proper parent references
    3. Context chain integrity is maintained
    4. Context loss is detected and reported

    Usage:
        propagator = ContextPropagator(project_path)

        # Create root context
        task_ctx = propagator.create_root_context(
            workflow_id="wf_001",
            recording_id="rec_001",
        )

        # Create child context for first agent
        exec_ctx = propagator.create_child_context(
            parent_context=task_ctx,
            agent_id="parser_agent",
        )

        # Validate context before passing to agent
        if propagator.validate_context(exec_ctx):
            # Pass context to agent
            result = await agent.process_with_context(exec_ctx)
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the context propagator.

        Args:
            project_path: Path to project root for state management
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._state = StateManager(self._project_path)
        self._active_contexts: dict[str, ExecutionContext] = {}

    # ========================================================================
    # Context Creation
    # ========================================================================

    def create_root_context(
        self,
        workflow_id: str = "",
        recording_id: str = "",
        project_path: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskContext:
        """
        Create a root task context.

        This is the entry point for a new workflow. The root context
        tracks the entire workflow from start to finish.

        Args:
            workflow_id: Unique workflow identifier
            recording_id: Source recording ID (if applicable)
            project_path: Path to the project
            tags: Optional workflow tags
            metadata: Optional workflow metadata

        Returns:
            New TaskContext instance
        """
        from datetime import datetime

        task_ctx = create_task_context(
            workflow_id=workflow_id or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            recording_id=recording_id,
            project_path=project_path or str(self._project_path),
            tags=tags or [],
            metadata=metadata or {},
        )

        # Store in state for persistence
        self._state.update_workflow_context(
            task_ctx.task_id,
            task_ctx.to_dict(),
        )
        self._state.save()

        logger.info(
            f"Created root context: task_id={task_ctx.task_id}, "
            f"workflow_id={task_ctx.workflow_id}, "
            f"recording_id={recording_id}"
        )

        return task_ctx

    def create_child_context(
        self,
        parent_context: TaskContext,
        agent_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        """
        Create a child execution context for an agent.

        The child context inherits all data from the parent and
        adds the agent to the execution chain.

        Args:
            parent_context: Parent TaskContext
            agent_id: ID of the agent that will use this context
            metadata: Optional metadata for this agent execution

        Returns:
            New ExecutionContext instance
        """
        # Create execution context
        exec_ctx = create_execution_context(parent_context)

        # Set current agent
        exec_ctx.current_agent = agent_id

        # Add agent to chain
        exec_ctx.context_chain.add_agent(agent_id, metadata)

        # Store in active contexts
        self._active_contexts[agent_id] = exec_ctx

        # Update state with chain information
        self._state.update_agent_chain(
            parent_context.task_id,
            exec_ctx.context_chain.to_dict(),
        )
        self._state.save()

        logger.info(
            f"Created child context: agent_id={agent_id}, "
            f"task_id={parent_context.task_id}, "
            f"chain_position={len(exec_ctx.context_chain.chain)}"
        )

        return exec_ctx

    # ========================================================================
    # Context Validation
    # ========================================================================

    def validate_context(self, context: ExecutionContext) -> bool:
        """
        Validate context completeness and integrity.

        Checks:
        1. Parent context exists and is valid
        2. Context chain is not broken
        3. Required fields are present
        4. No context loss detected

        Args:
            context: ExecutionContext to validate

        Returns:
            True if context is valid
        """
        # Check parent context
        if not context.parent_context.task_id:
            logger.error("Context validation failed: missing task_id")
            return False

        # Check context chain
        if not context.context_chain.chain:
            logger.warning("Context validation: empty chain (may be intentional)")

        # Check current agent is in chain
        if context.current_agent:
            if not context.context_chain.contains(context.current_agent):
                logger.error(
                    f"Context validation failed: current_agent '{context.current_agent}' "
                    f"not in chain"
                )
                return False

        # Check for context loss (compare with state)
        stored_chain = self._state.get_agent_chain(
            context.parent_context.task_id
        )
        if stored_chain:
            stored_chain_obj = ContextChain.from_dict(stored_chain)
            if len(context.context_chain.chain) < len(stored_chain_obj.chain):
                logger.error(
                    f"Context validation failed: context loss detected. "
                    f"Current chain length: {len(context.context_chain.chain)}, "
                    f"Stored chain length: {len(stored_chain_obj.chain)}"
                )
                return False

        logger.debug(f"Context validated: task_id={context.parent_context.task_id}")
        return True

    def validate_chain_integrity(
        self,
        context: ExecutionContext,
        expected_agents: list[str],
    ) -> bool:
        """
        Validate that the expected agents are in the execution chain.

        Args:
            context: ExecutionContext to validate
            expected_agents: List of expected agent IDs in order

        Returns:
            True if chain integrity is valid
        """
        actual_chain = context.context_chain.chain

        # Check if all expected agents are present
        for agent in expected_agents:
            if agent not in actual_chain:
                logger.error(
                    f"Chain integrity failed: expected agent '{agent}' not in chain"
                )
                return False

        # Check order (optional - can be strict or loose)
        # For now, just check presence, not order
        logger.debug(
            f"Chain integrity validated: expected={expected_agents}, "
            f"actual={actual_chain}"
        )
        return True

    # ========================================================================
    # Context Retrieval
    # ========================================================================

    def get_context(self, task_id: str) -> ExecutionContext | None:
        """
        Retrieve execution context by task ID.

        Args:
            task_id: Task identifier

        Returns:
            ExecutionContext if found, None otherwise
        """
        # Try to get from state
        context_data = self._state.get_workflow_context(task_id)
        if context_data:
            parent_context = TaskContext.from_dict(context_data)
            chain_data = self._state.get_agent_chain(task_id)
            context_chain = ContextChain.from_dict(chain_data) if chain_data else ContextChain()

            return ExecutionContext(
                parent_context=parent_context,
                context_chain=context_chain,
            )

        logger.warning(f"Context not found for task_id: {task_id}")
        return None

    def get_active_context(self, agent_id: str) -> ExecutionContext | None:
        """
        Get the active context for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            ExecutionContext if found, None otherwise
        """
        return self._active_contexts.get(agent_id)

    # ========================================================================
    # Context Cleanup
    # ========================================================================

    def release_context(self, agent_id: str) -> None:
        """
        Release an agent's active context.

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._active_contexts:
            del self._active_contexts[agent_id]
            logger.debug(f"Released context for agent: {agent_id}")

    def cleanup_task_context(self, task_id: str) -> None:
        """
        Clean up all contexts associated with a task.

        Args:
            task_id: Task identifier
        """
        # Remove from active contexts
        to_remove = [
            agent_id
            for agent_id, ctx in self._active_contexts.items()
            if ctx.parent_context.task_id == task_id
        ]
        for agent_id in to_remove:
            self.release_context(agent_id)

        # Mark task as completed in state
        context = self.get_context(task_id)
        if context:
            context.parent_context.complete()
            self._state.update_workflow_context(
                task_id,
                context.parent_context.to_dict(),
            )
            self._state.save()

        logger.info(f"Cleaned up context for task: {task_id}")


# =============================================================================
# Singleton Instance
# =============================================================================


_propagator_instance: ContextPropagator | None = None


def get_context_propagator(project_path: Path | str | None = None) -> ContextPropagator:
    """
    Get the singleton context propagator instance.

    Args:
        project_path: Optional path to project root

    Returns:
        ContextPropagator instance
    """
    global _propagator_instance

    if _propagator_instance is None:
        if project_path:
            _propagator_instance = ContextPropagator(Path(project_path))
        else:
            _propagator_instance = ContextPropagator()

    return _propagator_instance
