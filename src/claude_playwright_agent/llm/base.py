"""
Base abstractions for LLM providers.

Defines the unified interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional

from .exceptions import LLMError


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GLM = "glm"

    def __str__(self) -> str:
        return self.value


@dataclass
class LLMMessage:
    """
    Unified message format across providers.

    Attributes:
        role: Message role ("system", "user", "assistant", "tool")
        content: Message content (text or structured content)
        extra: Provider-specific extra data (images, tool calls, etc.)
    """

    role: str
    content: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"role": self.role, "content": self.content}
        if self.extra:
            result.update(self.extra)
        return result

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create a system message."""
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        """Create a user message."""
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        """Create an assistant message."""
        return cls(role="assistant", content=content)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMMessage":
        """
        Create message from dictionary.

        Args:
            data: Dictionary with role, content, and optional extra fields

        Returns:
            LLMMessage instance
        """
        role = data.get("role", "user")
        content = data.get("content", "")
        extra = {k: v for k, v in data.items() if k not in ("role", "content")}
        return cls(role=role, content=content, extra=extra)


@dataclass
class LLMResponse:
    """
    Unified response format across providers.

    Attributes:
        content: Generated text content
        finish_reason: Reason the generation finished
        usage: Token usage statistics
        model: Model identifier used
        extra: Provider-specific metadata (tool calls, etc.)
    """

    content: str
    finish_reason: Optional[str] = None
    usage: dict[str, int] = field(default_factory=dict)
    model: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def prompt_tokens(self) -> int:
        """Get number of prompt tokens used."""
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        """Get number of completion tokens used."""
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        """Get total number of tokens used."""
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "model": self.model,
            "extra": self.extra,
        }


@dataclass
class LLMConfig:
    """
    Base configuration for LLM providers.

    Attributes:
        provider: Provider type
        model: Model identifier (provider-specific)
        api_key: API key for the provider
        base_url: Custom API endpoint URL
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds
    """

    provider: LLMProviderType = LLMProviderType.ANTHROPIC
    model: str = "claude-3-5-sonnet-20241022"
    api_key: str = ""
    base_url: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout: int = 120

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            # Allow empty api_key for testing purposes
            pass
        if self.temperature < 0 or self.temperature > 1:
            raise LLMError("Temperature must be between 0 and 1")
        if self.max_tokens < 1:
            raise LLMError("max_tokens must be at least 1")

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Content-Type": "application/json",
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
        }


@dataclass
class StreamChunk:
    """
    A chunk of streaming response.

    Attributes:
        content: Text content chunk
        delta: New content since last chunk
        finish_reason: Finish reason if this is the final chunk
    """

    content: str
    delta: str = None  # type: ignore[assignment]
    finish_reason: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize delta to content if not provided."""
        if self.delta is None:
            self.delta = self.content

    def is_complete(self) -> bool:
        """Check if this is the final chunk."""
        return self.finish_reason is not None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement this interface to ensure
    consistent behavior across different LLM backends.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._client: Any = None
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the provider client.

        This should create the underlying API client and
        prepare it for making requests.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up provider resources.

        This should close any open connections and release resources.
        """
        pass

    @abstractmethod
    async def query(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send a query to the LLM and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool/function definitions
            **kwargs: Provider-specific options (e.g., stop sequences, top_p)

        Returns:
            LLMResponse with the generated content

        Raises:
            ProviderAPIError: If the API returns an error
            ProviderTimeoutError: If the request times out
            RateLimitError: If rate limit is exceeded
        """
        pass

    @abstractmethod
    async def query_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming query to the LLM.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool/function definitions
            **kwargs: Provider-specific options

        Yields:
            StreamChunk objects as they arrive

        Raises:
            ProviderAPIError: If the API returns an error
            ProviderTimeoutError: If the request times out
        """
        pass

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """
        Check if provider supports function/tool calling.

        Returns:
            True if provider supports tool calling
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if provider supports streaming responses.

        Returns:
            True if provider supports streaming
        """
        pass

    @abstractmethod
    def get_provider_info(self) -> dict[str, Any]:
        """
        Get provider metadata and capabilities.

        Returns:
            Dictionary with provider info including:
            - name: Provider name
            - models: List of supported models
            - capabilities: List of supported features
            - max_tokens: Maximum tokens supported
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        if not self._initialized:
            await self.initialize()
            self._initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def is_initialized(self) -> bool:
        """Check if provider has been initialized."""
        return self._initialized
