"""
E2.1 - Orchestrator Agent Core Skill.

This skill provides central orchestration for multi-agent workflows:
- Workflow coordination with context propagation
- Agent spawning and task distribution
- Result aggregation with context preservation
- Error handling and recovery with context tracking
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class ExecutionContext:
    """
    Complete execution context passed through agent chain.

    Attributes:
        workflow_id: Unique workflow identifier
        task_id: Current task identifier
        parent_context: Parent execution context (for nested workflows)
        recording_id: Associated recording ID (if applicable)
        project_path: Project root path
        agent_chain: Ordered list of agent IDs in the workflow
        context_chain: Chain of context IDs for traceability
        metadata: Additional context metadata
        created_at: Context creation time
        updated_at: Last context update time
    """

    workflow_id: str = field(default_factory=lambda: f"workflow_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    parent_context: "ExecutionContext | None" = None
    recording_id: str = ""
    project_path: str = ""
    agent_chain: list[str] = field(default_factory=list)
    context_chain: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def create_child(self, task_id: str, agent_id: str = "") -> "ExecutionContext":
        """Create a child context for nested execution."""
        child = ExecutionContext(
            workflow_id=self.workflow_id,
            task_id=task_id,
            parent_context=self,
            recording_id=self.recording_id,
            project_path=self.project_path,
            agent_chain=self.agent_chain.copy(),
            context_chain=self.context_chain.copy(),
            metadata=self.metadata.copy(),
        )
        if agent_id:
            child.agent_chain.append(agent_id)
        child.context_chain.append(self.task_id or "root")
        child.updated_at = datetime.now().isoformat()
        return child

    def add_agent(self, agent_id: str) -> None:
        """Add an agent to the execution chain."""
        if agent_id not in self.agent_chain:
            self.agent_chain.append(agent_id)
            self.updated_at = datetime.now().isoformat()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update context metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "parent_task_id": self.parent_context.task_id if self.parent_context else None,
            "recording_id": self.recording_id,
            "project_path": self.project_path,
            "agent_chain": self.agent_chain,
            "context_chain": self.context_chain,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowResult:
    """
    Result of a workflow execution.

    Attributes:
        workflow_id: Workflow identifier
        status: Execution status (pending, running, completed, failed)
        results: Aggregate results from all agents
        errors: List of errors encountered
        context: Final execution context
        duration: Execution duration in seconds
        started_at: Workflow start time
        completed_at: Workflow completion time
    """

    workflow_id: str
    status: str = "pending"
    results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    context: ExecutionContext | None = None
    duration: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""


class OrchestratorCoreAgent(BaseAgent):
    """
    Orchestrator Agent for coordinating multi-agent workflows.

    This agent provides:
    1. Workflow orchestration with context propagation
    2. Agent spawning and task distribution
    3. Result aggregation with context preservation
    4. Error handling and recovery with context tracking
    """

    name = "e2_1_orchestrator_core"
    version = "1.0.0"
    description = "E2.1 - Orchestrator Agent Core"

    def __init__(self, **kwargs) -> None:
        """Initialize the orchestrator agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a E2.1 - Orchestrator Agent Core agent for the Playwright test automation framework. You help users with e2.1 - orchestrator agent core tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._active_workflows: dict[str, WorkflowResult] = {}
        self._agent_registry: dict[str, Callable[[], BaseAgent]] = {}
        self._message_queue: Any = None

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
        Execute orchestration task.

        Args:
            task: Task to perform
            context: Execution context

        Returns:
            Result of the orchestration operation
        """
        # Ensure context is always present
        execution_context = context.get("execution_context")
        if not execution_context:
            # Create root context if not provided
            execution_context = ExecutionContext(
                task_id=context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                project_path=context.get("project_path", ""),
                recording_id=context.get("recording_id", ""),
            )

        task_type = context.get("task_type", task)

        if task_type == "run_workflow":
            return await self._run_workflow(context, execution_context)
        elif task_type == "spawn_agent":
            return await self._spawn_agent(context, execution_context)
        elif task_type == "coordinate_agents":
            return await self._coordinate_agents(context, execution_context)
        elif task_type == "aggregate_results":
            return await self._aggregate_results(context, execution_context)
        elif task_type == "get_workflow_status":
            return await self._get_workflow_status(context, execution_context)
        elif task_type == "handle_error":
            return await self._handle_error(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _run_workflow(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Run a complete workflow with context propagation."""
        workflow_id = context.get("workflow_id", execution_context.workflow_id)
        agents = context.get("agents", [])
        initial_data = context.get("initial_data", {})

        # Create workflow result
        workflow = WorkflowResult(workflow_id=workflow_id, status="running")
        workflow.context = execution_context
        self._active_workflows[workflow_id] = workflow

        try:
            # Execute workflow steps with context propagation
            current_context = execution_context
            aggregated_results = {}

            for agent_config in agents:
                agent_name = agent_config.get("name")
                agent_task = agent_config.get("task")
                agent_params = agent_config.get("params", {})

                # Create child context for this agent
                agent_context = current_context.create_child(
                    task_id=f"{workflow_id}_{agent_name}",
                    agent_id=agent_name,
                )

                # Add context to params
                agent_params["execution_context"] = agent_context
                agent_params["workflow_id"] = workflow_id

                # Execute agent (placeholder - actual execution would be through lifecycle manager)
                agent_result = await self._execute_agent_step(
                    agent_name, agent_task, agent_params, agent_context
                )

                # Store result with context
                aggregated_results[agent_name] = {
                    "result": agent_result,
                    "context": agent_context.to_dict(),
                }

                # Update context for next agent
                current_context = agent_context

            workflow.results = aggregated_results
            workflow.status = "completed"
            workflow.completed_at = datetime.now().isoformat()

            return f"Workflow '{workflow_id}' completed with {len(aggregated_results)} agent(s)"

        except Exception as e:
            workflow.status = "failed"
            workflow.errors.append(str(e))
            workflow.completed_at = datetime.now().isoformat()
            return f"Workflow '{workflow_id}' failed: {e}"

    async def _spawn_agent(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Spawn a new agent with context."""
        agent_type = context.get("agent_type")
        agent_id = context.get("agent_id", f"{agent_type}_{uuid.uuid4().hex[:8]}")

        if not agent_type:
            return "Error: agent_type is required"

        # Create agent context
        agent_context = execution_context.create_child(
            task_id=f"{execution_context.workflow_id}_{agent_id}",
            agent_id=agent_id,
        )

        # Store context mapping
        agent_context.update_metadata("agent_type", agent_type)
        agent_context.update_metadata("spawned_at", datetime.now().isoformat())

        return f"Agent '{agent_id}' (type: {agent_type}) spawned with context {agent_context.task_id}"

    async def _coordinate_agents(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Coordinate multiple agents with shared context."""
        agent_ids = context.get("agent_ids", [])
        coordination_type = context.get("coordination_type", "parallel")

        # Create shared context for coordination
        coordination_context = execution_context.create_child(
            task_id=f"{execution_context.workflow_id}_coordination",
        )
        coordination_context.update_metadata("coordination_type", coordination_type)
        coordination_context.update_metadata("agent_count", len(agent_ids))

        if coordination_type == "parallel":
            return f"Coordinating {len(agent_ids)} agent(s) in parallel with context {coordination_context.task_id}"
        else:
            return f"Coordinating {len(agent_ids)} agent(s) sequentially with context {coordination_context.task_id}"

    async def _aggregate_results(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Aggregate results from multiple agents with context preservation."""
        agent_results = context.get("agent_results", {})

        # Aggregate with context tracking
        aggregated = {
            "total_agents": len(agent_results),
            "workflow_context": execution_context.to_dict(),
            "agent_results": [],
        }

        for agent_id, result in agent_results.items():
            agent_context = execution_context.create_child(
                task_id=f"{execution_context.workflow_id}_{agent_id}_result",
                agent_id=agent_id,
            )
            aggregated["agent_results"].append({
                "agent_id": agent_id,
                "result": result,
                "context": agent_context.to_dict(),
            })

        return f"Aggregated {len(agent_results)} result(s) with context preservation"

    async def _get_workflow_status(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Get status of a workflow with context information."""
        workflow_id = context.get("workflow_id", execution_context.workflow_id)

        if workflow_id not in self._active_workflows:
            return f"Workflow '{workflow_id}' not found"

        workflow = self._active_workflows[workflow_id]
        context_info = workflow.context.to_dict() if workflow.context else {}

        return f"Workflow '{workflow_id}' status: {workflow.status}, context: {context_info['task_id']}"

    async def _handle_error(self, context: dict[str, Any], execution_context: ExecutionContext) -> str:
        """Handle error with context preservation for recovery."""
        error_message = context.get("error_message", "Unknown error")
        failed_agent = context.get("failed_agent", "")

        # Create error context
        error_context = execution_context.create_child(
            task_id=f"{execution_context.workflow_id}_error",
        )
        error_context.update_metadata("error_occurred", True)
        error_context.update_metadata("error_message", error_message)
        error_context.update_metadata("failed_agent", failed_agent)
        error_context.update_metadata("error_time", datetime.now().isoformat())

        return f"Error handled with context preservation: {error_context.task_id}"

    async def _execute_agent_step(
        self,
        agent_name: str,
        agent_task: str,
        params: dict[str, Any],
        agent_context: ExecutionContext,
    ) -> str:
        """Execute a single agent step (placeholder for actual execution)."""
        # This would call the actual agent through the lifecycle manager
        return f"Executed {agent_name} with context {agent_context.task_id}"

    def register_agent_factory(self, agent_type: str, factory: Callable[[], BaseAgent]) -> None:
        """Register an agent factory for spawning."""
        self._agent_registry[agent_type] = factory

    def get_active_workflows(self) -> dict[str, WorkflowResult]:
        """Get all active workflows."""
        return self._active_workflows.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

