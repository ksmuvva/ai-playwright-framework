"""
Base agent class for all Claude Playwright Agent implementations.

Supports both legacy ClaudeSDKClient and new multi-provider LLM abstraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
import logging

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)


def get_settings() -> dict[str, Any]:
    """
    Get agent settings from configuration.

    Returns:
        Dictionary of agent settings including provider information
    """
    # Import here to avoid circular dependency
    from claude_playwright_agent.config import ConfigManager

    config = ConfigManager()
    return {
        "model": config.ai.model,
        "max_tokens": config.ai.max_tokens,
        "temperature": config.ai.temperature,
        "enable_caching": config.ai.enable_caching,
        "timeout": config.ai.timeout,
        # NEW: Multi-provider support
        "provider": config.ai.provider,
        "fallback_providers": config.ai.fallback_providers,
        "provider_settings": config.ai.provider_settings,
    }


class BaseAgent(ABC):
    """
    Base class for all agents in the Claude Playwright Agent system.

    Provides common functionality for initializing and interacting with
    LLM providers. Supports both legacy ClaudeSDKClient and new
    multi-provider abstraction for backward compatibility.
    """

    def __init__(
        self,
        system_prompt: str,
        mcp_servers: Optional[dict] = None,
        allowed_tools: Optional[list[str]] = None,
        # NEW: Allow explicit LLM provider override
        llm_provider: Optional[Any] = None,  # BaseLLMProvider | None
        # NEW: Memory system integration
        enable_memory: bool = True,
        memory_db_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the base agent.

        Args:
            system_prompt: The system prompt for the agent
            mcp_servers: Optional MCP servers to attach
            allowed_tools: List of allowed tool names
            llm_provider: Optional explicit LLM provider (BaseLLMProvider instance)
                         If provided, overrides the provider from config
            enable_memory: Whether to enable memory system (default: True)
            memory_db_path: Optional custom path for memory database
        """
        self.settings = get_settings()
        self.system_prompt = system_prompt
        self.mcp_servers = mcp_servers or {}
        self.allowed_tools = allowed_tools or []

        # NEW: Support both legacy and new client types
        self.client: Optional[Union[ClaudeSDKClient, Any]] = None  # ClaudeSDKClient | BaseLLMProvider
        self._explicit_provider = llm_provider

        # Detect if we should use legacy path (default Anthropic, no override)
        self._use_legacy = (
            self.settings.get("provider") == "anthropic"
            and llm_provider is None
            and not self.settings.get("fallback_providers")
        )

        # NEW: Initialize memory system
        self.enable_memory = enable_memory
        self._memory_manager = None
        if self.enable_memory:
            try:
                from claude_playwright_agent.skills.builtins.e10_1_memory_manager import (
                    MemoryManager,
                    MemoryType,
                    MemoryPriority,
                )

                db_path = memory_db_path or ".cpa/memory.db"
                self._memory_manager = MemoryManager(
                    persist_to_disk=True,
                    memory_db_path=db_path,
                )
                self.MemoryType = MemoryType
                self.MemoryPriority = MemoryPriority
                logger.info(f"Memory system initialized for {self.__class__.__name__}")
            except ImportError as e:
                logger.warning(f"Failed to initialize memory system: {e}")
                self.enable_memory = False

    def _create_options(self) -> ClaudeAgentOptions:
        """
        Create ClaudeAgentOptions for the SDK client.

        Returns:
            Configured ClaudeAgentOptions instance
        """
        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            mcp_servers=self.mcp_servers,
            allowed_tools=self.allowed_tools,
        )

    async def initialize(self) -> None:
        """
        Initialize the LLM client.

        Uses legacy ClaudeSDKClient for backward compatibility when:
        - Provider is "anthropic" (default)
        - No explicit provider override is given
        - No fallback providers are configured

        Otherwise uses the new LLMProviderFactory to create a provider.
        """
        if self.client is not None:
            return  # Already initialized

        if self._explicit_provider:
            # Use explicitly provided provider
            self.client = self._explicit_provider
            if hasattr(self.client, "initialize") and not getattr(self.client, "_initialized", False):
                await self.client.initialize()
        elif self._use_legacy:
            # Use legacy ClaudeSDKClient for backward compatibility
            options = self._create_options()
            self.client = ClaudeSDKClient(options=options)
        else:
            # Use new LLMProviderFactory
            from claude_playwright_agent.llm import LLMProviderFactory
            from claude_playwright_agent.llm.models import ProviderConfig

            # Create provider config from settings
            provider_config = ProviderConfig(
                provider=self.settings["provider"],
                model=self.settings["model"],
                api_key="",  # Loaded from environment by provider
                max_tokens=self.settings["max_tokens"],
                temperature=self.settings["temperature"],
                timeout=self.settings["timeout"],
            )

            # Check for fallback providers
            fallback_providers = self.settings.get("fallback_providers", [])
            if fallback_providers:
                # Create fallback provider chain
                provider = LLMProviderFactory.create_with_fallback([provider_config])
            else:
                # Create single provider
                provider = LLMProviderFactory.create_provider(provider_config)

            # Initialize the provider
            await provider.initialize()
            self.client = provider

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client is not None:
            # Handle both ClaudeSDKClient and BaseLLMProvider cleanup
            if hasattr(self.client, "__aexit__"):
                # ClaudeSDKClient has __aexit__
                await self.client.__aexit__(None, None, None)
            elif hasattr(self.client, "cleanup"):
                # BaseLLMProvider has cleanup()
                await self.client.cleanup()
            self.client = None

        # NEW: Cleanup memory manager
        if self._memory_manager is not None:
            await self._memory_manager.close()
            self._memory_manager = None

    # NEW: Memory helper methods

    async def remember(
        self,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        priority: str = "medium",
        context: Optional[dict] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """
        Store information in memory.

        Args:
            key: Unique identifier for the memory
            value: Data to store
            memory_type: Type of memory (short_term, long_term, semantic, episodic, working)
            priority: Priority level (critical, high, medium, low)
            context: Additional context information
            tags: Optional tags for categorization

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.enable_memory or self._memory_manager is None:
            return False

        try:
            await self._memory_manager.store(
                key=key,
                value=value,
                type=self.MemoryType(memory_type),
                priority=self.MemoryPriority(priority),
                context=context,
                tags=tags,
            )
            logger.debug(f"Stored memory: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory {key}: {e}")
            return False

    async def recall(
        self,
        key: str,
        memory_type: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Retrieve information from memory.

        Args:
            key: The memory key to retrieve
            memory_type: Optional memory type filter

        Returns:
            The stored value if found, None otherwise
        """
        if not self.enable_memory or self._memory_manager is None:
            return None

        try:
            entry = await self._memory_manager.retrieve(
                key=key,
                type=self.MemoryType(memory_type) if memory_type else None,
            )
            return entry.value if entry else None
        except Exception as e:
            logger.error(f"Failed to recall memory {key}: {e}")
            return None

    async def search_memories(
        self,
        tags: Optional[list[str]] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search memories by tags or type.

        Args:
            tags: Optional list of tags to filter by
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of memory dictionaries
        """
        if not self.enable_memory or self._memory_manager is None:
            return []

        try:
            from claude_playwright_agent.skills.builtins.e10_1_memory_manager import MemoryQuery

            query = MemoryQuery(
                tags=tags or [],
                type=self.MemoryType(memory_type) if memory_type else None,
                limit=limit,
            )
            results = await self._memory_manager.search(query)
            return [entry.to_dict() for entry in results]
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def forget(self, key: str, memory_type: Optional[str] = None) -> bool:
        """
        Remove a memory from storage.

        Args:
            key: The memory key to remove
            memory_type: Optional memory type filter

        Returns:
            True if memory was removed, False otherwise
        """
        if not self.enable_memory or self._memory_manager is None:
            return False

        try:
            return await self._memory_manager.forget(
                key=key,
                type=self.MemoryType(memory_type) if memory_type else None,
            )
        except Exception as e:
            logger.error(f"Failed to forget memory {key}: {e}")
            return False

    def get_memory_stats(self) -> dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dictionary with memory statistics
        """
        if not self.enable_memory or self._memory_manager is None:
            return {"enabled": False}

        return self._memory_manager.get_statistics()

    @property
    def memory(self) -> Optional[Any]:
        """
        Get the memory manager instance.

        Returns:
            MemoryManager instance or None
        """
        return self._memory_manager

    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        ...

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
