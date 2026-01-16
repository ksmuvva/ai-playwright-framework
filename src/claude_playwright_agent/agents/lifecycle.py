"""
Agent Lifecycle Manager

Manages the creation, initialization, and cleanup of agents.
Handles agent spawning, health monitoring, and resource management.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent in its lifecycle."""
    CREATING = "creating"
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for agent initialization."""
    agent_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    auto_start: bool = True
    timeout: int = 30000  # milliseconds


@dataclass
class AgentInstance:
    """Represents a running agent instance."""
    agent_id: str
    agent_type: str
    agent: Optional["BaseAgent"]
    status: AgentStatus
    created_at: str
    config: AgentConfig
    message_count: int = 0
    error_count: int = 0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentLifecycleManager:
    """
    Manage agent lifecycle from creation to cleanup.

    Example:
        >>> lifecycle = AgentLifecycleManager()
        >>> agent = await lifecycle.spawn_agent(
        ...     agent_type="IngestionAgent",
        ...     config={"project_path": "/path/to/project"}
        ... )
        >>> await lifecycle.stop_agent(agent.agent_id)
    """

    def __init__(self):
        """Initialize the lifecycle manager."""
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_counter = 0
        self._running = False

    async def start(self) -> None:
        """Start the lifecycle manager."""
        if self._running:
            logger.warning("AgentLifecycleManager already running")
            return

        self._running = True
        logger.info("AgentLifecycleManager started")

    async def stop(self) -> None:
        """Stop the lifecycle manager and all agents."""
        if not self._running:
            return

        self._running = False

        # Stop all agents
        tasks = []
        for agent_id in list(self.agents.keys()):
            tasks.append(self.stop_agent(agent_id))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("AgentLifecycleManager stopped")

    async def spawn_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AgentInstance:
        """
        Create and initialize a new agent instance.

        Args:
            agent_type: Type/class name of the agent to create
            config: Configuration dict for the agent

        Returns:
            AgentInstance with the created agent
        """
        agent_config = AgentConfig(
            agent_type=agent_type,
            config=config or {}
        )

        # Generate unique agent ID
        self.agent_counter += 1
        agent_id = f"{agent_type.lower()}_{self.agent_counter}"

        logger.info(f"Spawning agent: {agent_id} (type: {agent_type})")

        # Create agent instance
        instance = AgentInstance(
            agent_id=agent_id,
            agent_type=agent_type,
            agent=None,
            status=AgentStatus.CREATING,
            created_at=datetime.now().isoformat(),
            config=agent_config
        )

        self.agents[agent_id] = instance

        try:
            # Dynamically import and create agent
            agent_class = await self._load_agent_class(agent_type)
            instance.agent = agent_class(**agent_config.config)
            instance.status = AgentStatus.INITIALIZING

            # Initialize agent if it has async initialization
            if hasattr(instance.agent, 'initialize'):
                await instance.agent.initialize()

            instance.status = AgentStatus.IDLE
            logger.info(f"Agent spawned successfully: {agent_id}")

            return instance

        except Exception as e:
            logger.error(f"Failed to spawn agent {agent_id}: {e}")
            instance.status = AgentStatus.ERROR
            instance.error_count += 1
            raise

    async def _load_agent_class(self, agent_type: str) -> type:
        """
        Dynamically load agent class by type name.

        Args:
            agent_type: Name of the agent class

        Returns:
            Agent class
        """
        # Map of agent type names to their module paths
        agent_mappings = {
            "IngestionAgent": "src.claude_playwright_agent.agents.ingestion_agent",
            "DeduplicationAgent": "src.claude_playwright_agent.deduplication.agent",
            "BDDConversionAgent": "src.claude_playwright_agent.bdd.converter",
            "ExecutionAgent": "src.claude_playwright_agent.execution.executor",
            "AnalysisAgent": "src.claude_playwright_agent.agents.analysis_agent",
        }

        if agent_type not in agent_mappings:
            raise ValueError(f"Unknown agent type: {agent_type}")

        module_path = agent_mappings[agent_type]

        # Import module
        parts = module_path.split(".")
        module = __import__(module_path)

        # Navigate to the class
        for part in parts[1:]:
            module = getattr(module, part)

        agent_class = getattr(module, agent_type)
        return agent_class

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop and cleanup an agent.

        Args:
            agent_id: ID of the agent to stop

        Returns:
            True if stopped successfully
        """
        instance = self.agents.get(agent_id)

        if not instance:
            logger.warning(f"Agent not found: {agent_id}")
            return False

        logger.info(f"Stopping agent: {agent_id}")
        instance.status = AgentStatus.STOPPING

        try:
            # Cleanup agent if it has cleanup method
            if instance.agent and hasattr(instance.agent, 'cleanup'):
                await instance.agent.cleanup()

            instance.status = AgentStatus.STOPPED
            instance.agent = None

            logger.info(f"Agent stopped: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            instance.status = AgentStatus.ERROR
            return False

    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        """
        Get an agent instance by ID.

        Args:
            agent_id: Agent ID

        Returns:
            AgentInstance or None if not found
        """
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, AgentInstance]:
        """Get all agent instances."""
        return self.agents.copy()

    def get_active_agents(self) -> Dict[str, AgentInstance]:
        """Get all non-stopped agents."""
        return {
            agent_id: instance
            for agent_id, instance in self.agents.items()
            if instance.status not in [AgentStatus.STOPPED, AgentStatus.ERROR]
        }

    async def execute_on_agent(
        self,
        agent_id: str,
        method_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a method on an agent.

        Args:
            agent_id: Agent ID
            method_name: Method to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result
        """
        instance = self.get_agent(agent_id)

        if not instance or not instance.agent:
            raise ValueError(f"Agent not found or not initialized: {agent_id}")

        method = getattr(instance.agent, method_name, None)

        if not method:
            raise AttributeError(f"Agent {agent_id} has no method '{method_name}'")

        # Update activity tracking
        instance.last_activity = datetime.now().isoformat()
        instance.status = AgentStatus.RUNNING

        try:
            # Execute method
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)

            instance.status = AgentStatus.IDLE
            instance.message_count += 1

            return result

        except Exception as e:
            logger.error(f"Error executing {method_name} on {agent_id}: {e}")
            instance.status = AgentStatus.ERROR
            instance.error_count += 1
            raise

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Statistics dictionary
        """
        instance = self.get_agent(agent_id)

        if not instance:
            return {"error": "Agent not found"}

        return {
            "agent_id": instance.agent_id,
            "agent_type": instance.agent_type,
            "status": instance.status.value,
            "created_at": instance.created_at,
            "last_activity": instance.last_activity,
            "message_count": instance.message_count,
            "error_count": instance.error_count,
            "uptime_seconds": (
                datetime.now().timestamp() - datetime.fromisoformat(instance.created_at).timestamp()
            )
        }

    def cleanup_stopped_agents(self, max_age_seconds: int = 3600) -> int:
        """
        Remove stopped agents older than max age.

        Args:
            max_age_seconds: Maximum age in seconds before cleanup

        Returns:
            Number of agents cleaned up
        """
        now = datetime.now()
        cleaned = 0

        for agent_id, instance in list(self.agents.items()):
            if instance.status in [AgentStatus.STOPPED, AgentStatus.ERROR]:
                created = datetime.fromisoformat(instance.created_at)
                age_seconds = (now - created).total_seconds()

                if age_seconds > max_age_seconds:
                    logger.info(f"Cleaning up stopped agent: {agent_id}")
                    del self.agents[agent_id]
                    cleaned += 1

        return cleaned

    def __len__(self) -> int:
        """Return number of agents."""
        return len(self.agents)

    def __repr__(self) -> str:
        """String representation."""
        active = len(self.get_active_agents())
        return f"AgentLifecycleManager(agents={len(self)}, active={active})"


# Convenience function for quick agent spawning
async def spawn_agent(
    agent_type: str,
    config: Optional[Dict[str, Any]] = None
) -> AgentInstance:
    """
    Quick function to spawn an agent without managing lifecycle.

    Args:
        agent_type: Type of agent to spawn
        config: Configuration for the agent

    Returns:
        AgentInstance

    Example:
        >>> agent = await spawn_agent("IngestionAgent", {"project_path": "."})
    """
    lifecycle = AgentLifecycleManager()
    await lifecycle.start()
    return await lifecycle.spawn_agent(agent_type, config)
