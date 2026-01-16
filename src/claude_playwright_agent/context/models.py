"""
Context data models for tracking execution through agent workflows.

These models ensure complete traceability from the original recording
through all processing stages (parse, deduplicate, BDD, execute).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# =============================================================================
# Context Models
# =============================================================================


@dataclass
class TaskContext:
    """
    Complete task execution context.

    This context tracks a task from creation through completion,
    maintaining all metadata needed for traceability and debugging.

    Attributes:
        task_id: Unique task identifier
        workflow_id: Parent workflow identifier
        recording_id: Source recording ID (if applicable)
        project_path: Path to the project
        created_at: Task creation timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        status: Current task status
        metadata: Additional task metadata
        tags: Task tags for filtering
        parent_task_id: Parent task ID if this is a subtask
    """

    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex}")
    workflow_id: str = ""
    recording_id: str = ""
    project_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    completed_at: str = ""
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    parent_task_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "recording_id": self.recording_id,
            "project_path": self.project_path,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "metadata": self.metadata,
            "tags": self.tags,
            "parent_task_id": self.parent_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskContext":
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", f"task_{uuid.uuid4().hex}"),
            workflow_id=data.get("workflow_id", ""),
            recording_id=data.get("recording_id", ""),
            project_path=data.get("project_path", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            status=data.get("status", "pending"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            parent_task_id=data.get("parent_task_id", ""),
        )

    def start(self) -> None:
        """Mark task as started."""
        self.started_at = datetime.now().isoformat()
        self.status = "running"

    def complete(self) -> None:
        """Mark task as completed."""
        self.completed_at = datetime.now().isoformat()
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.completed_at = datetime.now().isoformat()
        self.status = "failed"
        self.metadata["error"] = error


@dataclass
class ContextChain:
    """
    Chain of execution contexts through agent pipeline.

    Maintains the complete history of which agents processed
    the task, in what order, with timestamps.

    Attributes:
        chain: List of agent IDs in execution order
        timestamps: Entry timestamps for each agent
        metadata: Additional chain metadata
    """

    chain: list[str] = field(default_factory=list)
    timestamps: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_agent(self, agent_id: str, metadata: dict[str, Any] | None = None) -> None:
        """
        Add an agent to the execution chain.

        Args:
            agent_id: Agent identifier
            metadata: Optional metadata for this agent execution
        """
        if agent_id not in self.chain:
            self.chain.append(agent_id)
            self.timestamps[agent_id] = datetime.now().isoformat()
            if metadata:
                self.metadata[agent_id] = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chain": self.chain,
            "timestamps": self.timestamps,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextChain":
        """Create from dictionary."""
        return cls(
            chain=data.get("chain", []),
            timestamps=data.get("timestamps", {}),
            metadata=data.get("metadata", {}),
        )

    def contains(self, agent_id: str) -> bool:
        """Check if an agent is in the chain."""
        return agent_id in self.chain

    def get_position(self, agent_id: str) -> int:
        """Get the position of an agent in the chain."""
        try:
            return self.chain.index(agent_id)
        except ValueError:
            return -1


@dataclass
class ExecutionContext:
    """
    Execution context passed between agents.

    This context is propagated through the agent pipeline,
    ensuring all agents have access to the same foundational
    information while tracking their individual contributions.

    Attributes:
        parent_context: Parent TaskContext
        context_chain: Chain of agent executions
        current_agent: Currently executing agent ID
        start_time: Context creation time
        updated_time: Last update time
        data: Shared data dictionary
        agent_data: Per-agent data storage
    """

    parent_context: TaskContext
    context_chain: ContextChain = field(default_factory=ContextChain)
    current_agent: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_time: str = field(default_factory=lambda: datetime.now().isoformat())
    data: dict[str, Any] = field(default_factory=dict)
    agent_data: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "parent_context": self.parent_context.to_dict(),
            "context_chain": self.context_chain.to_dict(),
            "current_agent": self.current_agent,
            "start_time": self.start_time,
            "updated_time": self.updated_time,
            "data": self.data,
            "agent_data": self.agent_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContext":
        """Create from dictionary."""
        parent_context = TaskContext.from_dict(
            data.get("parent_context", {})
        )
        context_chain = ContextChain.from_dict(
            data.get("context_chain", {})
        )
        return cls(
            parent_context=parent_context,
            context_chain=context_chain,
            current_agent=data.get("current_agent", ""),
            start_time=data.get("start_time", datetime.now().isoformat()),
            updated_time=data.get("updated_time", datetime.now().isoformat()),
            data=data.get("data", {}),
            agent_data=data.get("agent_data", {}),
        )

    def update_timestamp(self) -> None:
        """Update the timestamp."""
        self.updated_time = datetime.now().isoformat()

    def get_agent_data(self, agent_id: str) -> dict[str, Any]:
        """Get data stored by a specific agent."""
        return self.agent_data.get(agent_id, {})

    def set_agent_data(self, agent_id: str, data: dict[str, Any]) -> None:
        """Store data for a specific agent."""
        self.agent_data[agent_id] = data
        self.update_timestamp()

    def merge_agent_data(self, agent_id: str, data: dict[str, Any]) -> None:
        """Merge data into existing agent data."""
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {}
        self.agent_data[agent_id].update(data)
        self.update_timestamp()

    def set_shared_data(self, key: str, value: Any) -> None:
        """Store data shared between all agents."""
        self.data[key] = value
        self.update_timestamp()

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data."""
        return self.data.get(key, default)


# =============================================================================
# Convenience Functions
# =============================================================================


def create_task_context(
    workflow_id: str = "",
    recording_id: str = "",
    project_path: str = "",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TaskContext:
    """
    Create a new TaskContext with common parameters.

    Args:
        workflow_id: Parent workflow identifier
        recording_id: Source recording ID
        project_path: Path to the project
        tags: Optional task tags
        metadata: Optional task metadata

    Returns:
        New TaskContext instance
    """
    return TaskContext(
        workflow_id=workflow_id,
        recording_id=recording_id,
        project_path=project_path,
        tags=tags or [],
        metadata=metadata or {},
    )


def create_execution_context(
    task_context: TaskContext | None = None,
) -> ExecutionContext:
    """
    Create a new ExecutionContext from a TaskContext.

    Args:
        task_context: Optional parent TaskContext (creates new if not provided)

    Returns:
        New ExecutionContext instance
    """
    if task_context is None:
        task_context = create_task_context()

    return ExecutionContext(
        parent_context=task_context,
        context_chain=ContextChain(),
    )
