"""
LLM provider abstraction layer.

Provides a unified interface for multiple LLM providers (Anthropic, OpenAI, GLM).

Example:
    from claude_playwright_agent.llm import (
        LLMProviderFactory,
        LLMProviderType,
        LLMMessage,
    )

    # Create a provider
    config = {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "sk-...",
    }
    provider = LLMProviderFactory.create_from_dict(config)

    # Use the provider
    async with provider:
        messages = [LLMMessage.user("Hello!")]
        response = await provider.query(messages)
        print(response.content)
"""

# Base abstractions
from .base import (
    BaseLLMProvider,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    LLMProviderType,
    StreamChunk,
)

# Factory
from .factory import FallbackProvider, LLMProviderFactory

# Exceptions
from .exceptions import (
    LLMError,
    ProviderAPIError,
    ProviderConfigError,
    ProviderConnectionError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    RateLimitError,
    TokenLimitError,
)

# Models
from .models import (
    AnthropicConfig,
    GLMConfig,
    MODEL_ALIASES,
    OpenAIConfig,
    ProviderConfig,
    resolve_model_alias,
)

# Registry
from .providers.registry import ProviderRegistry

__all__ = [
    # Base
    "BaseLLMProvider",
    "LLMConfig",
    "LLMMessage",
    "LLMResponse",
    "LLMProviderType",
    "StreamChunk",
    # Factory
    "LLMProviderFactory",
    "FallbackProvider",
    # Exceptions
    "LLMError",
    "ProviderNotFoundError",
    "ProviderConfigError",
    "ProviderAPIError",
    "ProviderTimeoutError",
    "ProviderConnectionError",
    "RateLimitError",
    "TokenLimitError",
    # Models
    "AnthropicConfig",
    "OpenAIConfig",
    "GLMConfig",
    "ProviderConfig",
    "MODEL_ALIASES",
    "resolve_model_alias",
    # Registry
    "ProviderRegistry",
]

# Version info
__version__ = "1.0.0"
