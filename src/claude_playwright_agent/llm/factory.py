"""
Factory for creating LLM provider instances.

Handles provider instantiation, configuration loading, and fallback chains.
"""

import asyncio
from typing import Any, AsyncIterator, List, Optional

from claude_playwright_agent.llm.base import (
    BaseLLMProvider,
    LLMConfig,
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    StreamChunk,
)
from claude_playwright_agent.llm.exceptions import (
    LLMError,
    ProviderAPIError,
    ProviderConnectionError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    RateLimitError,
)
from claude_playwright_agent.llm.models.config import ProviderConfig
from claude_playwright_agent.llm.providers.registry import ProviderRegistry


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Example:
        # Create from config dict
        config = ProviderConfig.from_dict({
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-..."
        })
        provider = LLMProviderFactory.create_provider(config)

        # Create with fallback
        provider = LLMProviderFactory.create_with_fallback([
            primary_config,
            fallback_config,
        ])
    """

    @staticmethod
    def create_provider(config: ProviderConfig) -> BaseLLMProvider:
        """
        Create a provider instance from configuration.

        Args:
            config: Provider configuration (ProviderConfig or LLMConfig subclass)

        Returns:
            Initialized provider instance

        Raises:
            ProviderNotFoundError: If provider type not registered
            LLMError: If configuration is invalid
        """
        # Handle both ProviderConfig and LLMConfig subclasses
        from claude_playwright_agent.llm.models.config import (
            AnthropicConfig,
            GLMConfig,
            OpenAIConfig,
            ProviderConfig,
        )

        if isinstance(config, ProviderConfig) and not isinstance(
            config, (AnthropicConfig, OpenAIConfig, GLMConfig)
        ):
            # It's a generic ProviderConfig, convert to specific config
            llm_config = config.to_llm_config()
        else:
            # It's already a specific config (AnthropicConfig, OpenAIConfig, GLMConfig)
            llm_config = config

        provider_class = ProviderRegistry.get(llm_config.provider)
        return provider_class(llm_config)

    @staticmethod
    def create_from_dict(data: dict[str, Any]) -> BaseLLMProvider:
        """
        Create a provider from a dictionary.

        Args:
            data: Provider configuration dictionary

        Returns:
            Provider instance
        """
        config = ProviderConfig.from_dict(data)
        return LLMProviderFactory.create_provider(config)

    @staticmethod
    def create_provider_from_env() -> BaseLLMProvider:
        """
        Create a provider from environment variables.

        Reads the following environment variables:
        - CPA_AI__PROVIDER: Provider type (anthropic, openai, glm)
        - ANTHROPIC_API_KEY: Anthropic API key
        - OPENAI_API_KEY: OpenAI API key
        - ZHIPUAI_API_KEY: Zhipu AI API key
        - CPA_AI__MODEL: Model name (optional, uses provider default)
        - CPA_AI__ANTHROPIC__MODEL: Anthropic-specific model (optional)
        - CPA_AI__OPENAI__MODEL: OpenAI-specific model (optional)
        - CPA_AI__GLM__MODEL: GLM-specific model (optional)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not specified or API key is missing
        """
        import os

        from claude_playwright_agent.llm.models.config import (
            AnthropicConfig,
            GLMConfig,
            OpenAIConfig,
        )

        provider_str = os.environ.get("CPA_AI__PROVIDER", "anthropic")
        provider_type = LLMProviderType(provider_str)

        api_key: str | None = None
        model: str | None = None

        if provider_type == LLMProviderType.ANTHROPIC:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
                )
            # Check provider-specific model first, then generic model
            model = os.environ.get("CPA_AI__ANTHROPIC__MODEL") or os.environ.get("CPA_AI__MODEL")
            config = AnthropicConfig(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022",
            )
        elif provider_type == LLMProviderType.OPENAI:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required for OpenAI provider"
                )
            # Check provider-specific model first, then generic model
            model = os.environ.get("CPA_AI__OPENAI__MODEL") or os.environ.get("CPA_AI__MODEL")
            config = OpenAIConfig(
                api_key=api_key,
                model=model or "gpt-4-turbo-preview",
            )
        elif provider_type == LLMProviderType.GLM:
            api_key = os.environ.get("ZHIPUAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "ZHIPUAI_API_KEY environment variable is required for GLM provider"
                )
            # Check provider-specific model first, then generic model
            model = os.environ.get("CPA_AI__GLM__MODEL") or os.environ.get("CPA_AI__MODEL")
            config = GLMConfig(
                api_key=api_key,
                model=model or "glm-4-plus",
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        return LLMProviderFactory.create_provider(config)

    @staticmethod
    def create_with_fallback(
        providers: List[ProviderConfig],
    ) -> "FallbackProvider":
        """
        Create a provider with fallback chain.

        Args:
            providers: List of provider configs in priority order

        Returns:
            FallbackProvider that tries each in sequence

        Raises:
            ValueError: If providers list is empty
        """
        if not providers:
            raise ValueError("At least one provider config is required")

        provider_instances = []
        for config in providers:
            provider = LLMProviderFactory.create_provider(config)
            provider_instances.append(provider)

        return FallbackProvider(provider_instances)

    @staticmethod
    async def test_provider(provider: BaseLLMProvider) -> dict[str, Any]:
        """
        Test a provider by making a simple query.

        Args:
            provider: Provider to test

        Returns:
            Test results with success status and metadata
        """
        try:
            async with provider:
                messages = [LLMMessage.user("Hello")]
                response = await provider.query(messages)

                return {
                    "success": True,
                    "provider": provider.config.provider.value,
                    "model": response.model,
                    "response_length": len(response.content),
                    "tokens": response.total_tokens,
                }
        except Exception as e:
            return {
                "success": False,
                "provider": provider.config.provider.value,
                "error": str(e),
            }


class FallbackProvider(BaseLLMProvider):
    """
    Provider with automatic fallback to alternate providers.

    Attempts queries in order through the fallback chain until
    one succeeds. Useful for high-availability scenarios.

    Example:
        fallback = FallbackProvider([primary, backup1, backup2])
        response = await fallback.query(messages)
        # If primary fails, automatically tries backup1, then backup2
    """

    def __init__(
        self,
        providers: List[BaseLLMProvider],
    ) -> None:
        """
        Initialize fallback provider.

        Args:
            providers: List of providers in fallback priority order

        Raises:
            ValueError: If providers list is empty
        """
        if not providers:
            raise ValueError("At least one provider is required for fallback")

        # Use first provider's config as the "primary" config
        super().__init__(providers[0].config)
        self._providers = providers

    async def initialize(self) -> None:
        """Initialize all providers in the fallback chain."""
        for provider in self._providers:
            if not provider.is_initialized():
                await provider.initialize()

    async def cleanup(self) -> None:
        """Clean up all providers."""
        for provider in self._providers:
            try:
                await provider.cleanup()
            except Exception:
                pass  # Ignore cleanup errors for fallback providers

    async def query(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send query to providers in order until one succeeds.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Provider-specific options

        Returns:
            LLMResponse from first successful provider

        Raises:
            LLMError: If all providers fail
        """
        last_error = None

        for i, provider in enumerate(self._providers):
            try:
                response = await provider.query(messages, tools, **kwargs)
                # Add fallback metadata to response
                response.extra["fallback_used"] = i > 0
                response.extra["fallback_provider"] = provider.config.provider.value
                response.extra["attempted_providers"] = i
                return response
            except (ProviderAPIError, ProviderTimeoutError, RateLimitError, ProviderConnectionError) as e:
                last_error = e
                continue  # Try next provider
            except Exception as e:
                last_error = e
                break  # Don't continue on non-API errors

        # All providers failed
        raise LLMError(
            f"All {len(self._providers)} providers in fallback chain failed",
            provider=self.config.provider.value,
            details={"last_error": str(last_error)} if last_error else {},
        )

    async def query_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send streaming query to providers in order.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Provider-specific options

        Yields:
            StreamChunk objects from first successful provider

        Raises:
            LLMError: If all providers fail
        """
        last_error = None

        for i, provider in enumerate(self._providers):
            if not provider.supports_streaming():
                continue

            try:
                async for chunk in provider.query_stream(messages, tools, **kwargs):
                    chunk.extra["fallback_used"] = i > 0
                    chunk.extra["fallback_provider"] = provider.config.provider.value
                    yield chunk
                return  # Success - exit iteration
            except Exception as e:
                last_error = e
                continue  # Try next provider

        # All streaming providers failed
        raise LLMError(
            f"All providers in fallback chain failed to stream",
            provider=self.config.provider.value,
            details={"last_error": str(last_error)} if last_error else {},
        )

    def supports_tool_calling(self) -> bool:
        """Check if primary provider supports tool calling."""
        return self._providers[0].supports_tool_calling()

    def supports_streaming(self) -> bool:
        """Check if all providers support streaming."""
        return all(p.supports_streaming() for p in self._providers)

    def get_provider_info(self) -> dict[str, Any]:
        """Get info about all providers in fallback chain."""
        return {
            "type": "fallback",
            "primary": self._providers[0].config.provider.value,
            "providers": [p.get_provider_info() for p in self._providers],
        }

    def get_providers(self) -> List[BaseLLMProvider]:
        """Get all providers in the fallback chain."""
        return self._providers.copy()
