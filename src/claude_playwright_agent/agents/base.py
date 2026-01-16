"""
Base agent class for all Claude Playwright Agent implementations.

Supports both legacy ClaudeSDKClient and new multi-provider LLM abstraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient


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
    ) -> None:
        """
        Initialize the base agent.

        Args:
            system_prompt: The system prompt for the agent
            mcp_servers: Optional MCP servers to attach
            allowed_tools: List of allowed tool names
            llm_provider: Optional explicit LLM provider (BaseLLMProvider instance)
                         If provided, overrides the provider from config
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
