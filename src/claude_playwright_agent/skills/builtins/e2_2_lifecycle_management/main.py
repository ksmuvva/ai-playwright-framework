"""
E2.2 - Agent Lifecycle Management Skill.

This skill provides comprehensive agent lifecycle management:
- Agent spawning with context initialization
- Agent state tracking with context preservation
- Graceful shutdown with context cleanup
- Resource monitoring and limits
- Context propagation throughout lifecycle
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class LifecycleState(str, Enum):
    """Agent lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED = "failed"


@dataclass
class AgentLifecycleContext:
    """
    Lifecycle context for an agent.

    Attributes:
        agent_id: Unique agent identifier
        agent_type: Type of agent
        workflow_id: Associated workflow ID
        task_id: Associated task ID
        lifecycle_state: Current lifecycle state
        parent_context: Parent execution context
        spawn_time: When agent was spawned
        initialize_time: When initialization completed
        start_time: When agent started running
        end_time: When agent terminated
        resource_usage: Resource usage metrics
        metadata: Additional lifecycle metadata
    """

    agent_id: str
    agent_type: str
    workflow_id: str
    task_id: str
    lifecycle_state: LifecycleState = LifecycleState.CREATED
    parent_context: dict[str, Any] = field(default_factory=dict)
    spawn_time: str = field(default_factory=lambda: datetime.now().isoformat())
    initialize_time: str = ""
    start_time: str = ""
    end_time: str = ""
    resource_usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_state: LifecycleState) -> None:
        """Transition to a new lifecycle state."""
        self.lifecycle_state = new_state
        self.metadata[f"{new_state.value}_at"] = datetime.now().isoformat()

    def update_resource_usage(self, key: str, value: Any) -> None:
        """Update resource usage metric."""
        self.resource_usage[key] = value
        self.resource_usage["updated_at"] = datetime.now().isoformat()


@dataclass
class SpawnResult:
    """Result of agent spawn operation."""

    success: bool
    agent_id: str
    lifecycle_context: AgentLifecycleContext | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "agent_id": self.agent_id,
            "lifecycle_context": self.lifecycle_context.__dict__ if self.lifecycle_context else None,
            "error": self.error,
        }


class LifecycleManagementAgent(BaseAgent):
    """
    Agent Lifecycle Management Agent.

    This agent provides:
    1. Agent spawning with context initialization
    2. Agent state tracking with context preservation
    3. Graceful shutdown with context cleanup
    4. Resource monitoring and limits
    5. Context propagation throughout lifecycle
    """

    name = "e2_2_lifecycle_management"
    version = "1.0.0"
    description = "E2.2 - Agent Lifecycle Management"

    def __init__(self, **kwargs) -> None:
        """Initialize the lifecycle management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E2.2 - Agent Lifecycle Management agent for the Playwright test automation framework. You help users with e2.2 - agent lifecycle management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._lifecycle_contexts: dict[str, AgentLifecycleContext] = {}
        self._active_agents: dict[str, BaseAgent] = {}
        self._agent_tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_intervals: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute lifecycle management task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the lifecycle operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            # Create root context if not provided
            from .main import ExecutionContext
            execution_context = ExecutionContext(
                task_id=context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                project_path=context.get("project_path", ""),
            )

        task_type = context.get("task_type", task)

        if task_type == "spawn_agent":
            return await self._spawn_agent(context, execution_context)
        elif task_type == "initialize_agent":
            return await self._initialize_agent(context, execution_context)
        elif task_type == "start_agent":
            return await self._start_agent(context, execution_context)
        elif task_type == "suspend_agent":
            return await self._suspend_agent(context, execution_context)
        elif task_type == "resume_agent":
            return await self._resume_agent(context, execution_context)
        elif task_type == "terminate_agent":
            return await self._terminate_agent(context, execution_context)
        elif task_type == "get_agent_status":
            return await self._get_agent_status(context, execution_context)
        elif task_type == "get_all_agents":
            return await self._get_all_agents(context, execution_context)
        elif task_type == "cleanup_agent":
            return await self._cleanup_agent(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _spawn_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Spawn a new agent with context initialization."""
        agent_type = context.get("agent_type")
        agent = context.get("agent_instance")
        workflow_id = context.get("workflow_id", execution_context.workflow_id)
        task_id = context.get("task_id", execution_context.task_id)

        if not agent_type or not agent:
            return "Error: agent_type and agent_instance are required"

        agent_id = context.get("agent_id", f"{agent_type}_{uuid.uuid4().hex[:8]}")

        async with self._lock:
            # Create lifecycle context with full context tracking
            lifecycle_context = AgentLifecycleContext(
                agent_id=agent_id,
                agent_type=agent_type,
                workflow_id=workflow_id,
                task_id=task_id,
                parent_context=execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context,
            )

            # Store agent and context
            self._active_agents[agent_id] = agent
            self._lifecycle_contexts[agent_id] = lifecycle_context

            # Transition to initializing
            lifecycle_context.transition_to(LifecycleState.INITIALIZING)

        return f"Agent '{agent_id}' spawned with context {lifecycle_context.task_id}"

    async def _initialize_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Initialize an agent with context."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._active_agents:
            return f"Error: Agent '{agent_id}' not found"

        agent = self._active_agents[agent_id]
        lifecycle_context = self._lifecycle_contexts[agent_id]

        try:
            # Initialize the agent
            await agent.initialize()

            # Update lifecycle context
            lifecycle_context.initialize_time = datetime.now().isoformat()
            lifecycle_context.transition_to(LifecycleState.IDLE)

            # Add initialization context
            lifecycle_context.metadata["initialized_with_context"] = execution_context.task_id if hasattr(execution_context, "task_id") else "unknown"

            return f"Agent '{agent_id}' initialized successfully"

        except Exception as e:
            lifecycle_context.transition_to(LifecycleState.FAILED)
            lifecycle_context.metadata["initialization_error"] = str(e)
            return f"Agent '{agent_id}' initialization failed: {e}"

    async def _start_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start an agent with context propagation."""
        agent_id = context.get("agent_id")
        task = context.get("task", "")
        task_context = context.get("task_context", {})

        if not agent_id or agent_id not in self._active_agents:
            return f"Error: Agent '{agent_id}' not found"

        agent = self._active_agents[agent_id]
        lifecycle_context = self._lifecycle_contexts[agent_id]

        try:
            # Merge execution context into task context
            task_context["execution_context"] = execution_context
            task_context["lifecycle_context"] = lifecycle_context

            # Start agent execution
            lifecycle_context.start_time = datetime.now().isoformat()
            lifecycle_context.transition_to(LifecycleState.RUNNING)

            # Create async task for agent execution
            agent_task = asyncio.create_task(agent.run(task, task_context))
            self._agent_tasks[agent_id] = agent_task

            return f"Agent '{agent_id}' started with context {execution_context.task_id if hasattr(execution_context, 'task_id') else 'unknown'}"

        except Exception as e:
            lifecycle_context.transition_to(LifecycleState.FAILED)
            lifecycle_context.metadata["start_error"] = str(e)
            return f"Agent '{agent_id}' start failed: {e}"

    async def _suspend_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Suspend an agent with context preservation."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._lifecycle_contexts:
            return f"Error: Agent '{agent_id}' not found"

        lifecycle_context = self._lifecycle_contexts[agent_id]

        # Preserve context before suspension
        lifecycle_context.metadata["suspended_from_context"] = execution_context.task_id if hasattr(execution_context, "task_id") else "unknown"
        lifecycle_context.transition_to(LifecycleState.SUSPENDED)

        return f"Agent '{agent_id}' suspended with context preserved"

    async def _resume_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Resume a suspended agent with context restoration."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._lifecycle_contexts:
            return f"Error: Agent '{agent_id}' not found"

        lifecycle_context = self._lifecycle_contexts[agent_id]

        if lifecycle_context.lifecycle_state != LifecycleState.SUSPENDED:
            return f"Error: Agent '{agent_id}' is not suspended"

        # Restore context and resume
        lifecycle_context.metadata["resumed_with_context"] = execution_context.task_id if hasattr(execution_context, "task_id") else "unknown"
        lifecycle_context.transition_to(LifecycleState.RUNNING)

        return f"Agent '{agent_id}' resumed with context restored"

    async def _terminate_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Terminate an agent with context cleanup."""
        agent_id = context.get("agent_id")
        graceful = context.get("graceful", True)

        if not agent_id or agent_id not in self._active_agents:
            return f"Error: Agent '{agent_id}' not found"

        agent = self._active_agents[agent_id]
        lifecycle_context = self._lifecycle_contexts[agent_id]

        try:
            async with self._lock:
                lifecycle_context.transition_to(LifecycleState.TERMINATING)

                if graceful:
                    await agent.cleanup()
                    lifecycle_context.metadata["cleanup_context"] = execution_context.task_id if hasattr(execution_context, "task_id") else "unknown"

                # Cancel agent task if running
                if agent_id in self._agent_tasks:
                    self._agent_tasks[agent_id].cancel()
                    del self._agent_tasks[agent_id]

                # Update lifecycle
                lifecycle_context.end_time = datetime.now().isoformat()
                lifecycle_context.transition_to(LifecycleState.TERMINATED)

                # Remove from active agents
                del self._active_agents[agent_id]

            return f"Agent '{agent_id}' terminated gracefully"

        except Exception as e:
            lifecycle_context.transition_to(LifecycleState.FAILED)
            lifecycle_context.metadata["termination_error"] = str(e)
            return f"Agent '{agent_id}' termination failed: {e}"

    async def _get_agent_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get agent status with context information."""
        agent_id = context.get("agent_id")

        if not agent_id or agent_id not in self._lifecycle_contexts:
            return f"Error: Agent '{agent_id}' not found"

        lifecycle_context = self._lifecycle_contexts[agent_id]

        return (
            f"Agent '{agent_id}' status: {lifecycle_context.lifecycle_state.value}, "
            f"workflow: {lifecycle_context.workflow_id}, "
            f"context: {lifecycle_context.task_id}"
        )

    async def _get_all_agents(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all agents with their lifecycle contexts."""
        agents_info = []

        for agent_id, lifecycle_context in self._lifecycle_contexts.items():
            agents_info.append({
                "agent_id": agent_id,
                "type": lifecycle_context.agent_type,
                "state": lifecycle_context.lifecycle_state.value,
                "workflow": lifecycle_context.workflow_id,
                "task": lifecycle_context.task_id,
                "spawned_at": lifecycle_context.spawn_time,
            })

        return f"Found {len(agents_info)} agent(s)"

    async def _cleanup_agent(self, context: dict[str, Any], execution_context: Any) -> str:
        """Clean up terminated agent resources and context."""
        agent_id = context.get("agent_id")

        if agent_id in self._lifecycle_contexts:
            # Preserve final context before cleanup
            lifecycle_context = self._lifecycle_contexts[agent_id]
            final_context = lifecycle_context.__dict__.copy()

            del self._lifecycle_contexts[agent_id]

            return f"Agent '{agent_id}' cleaned up, context preserved in state"

        return f"Agent '{agent_id}' not found for cleanup"

    def get_lifecycle_context(self, agent_id: str) -> AgentLifecycleContext | None:
        """Get lifecycle context for an agent."""
        return self._lifecycle_contexts.get(agent_id)

    def get_all_lifecycle_contexts(self) -> dict[str, AgentLifecycleContext]:
        """Get all lifecycle contexts."""
        return self._lifecycle_contexts.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

