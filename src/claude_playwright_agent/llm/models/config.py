"""
Configuration models for LLM providers.

Provider-specific configuration classes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ..base import LLMConfig, LLMProviderType


class ProviderType(str, Enum):
    """String enum for provider types (for serialization)."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GLM = "glm"

    @classmethod
    def from_llm_provider_type(cls, provider_type: LLMProviderType) -> "ProviderType":
        """Convert from LLMProviderType enum."""
        return cls(provider_type.value)

    def to_llm_provider_type(self) -> LLMProviderType:
        """Convert to LLMProviderType enum."""
        return LLMProviderType(self.value)


@dataclass
class AnthropicConfig(LLMConfig):
    """
    Anthropic/Claude provider configuration.

    Attributes:
        provider: Always ANTHROPIC
        model: Claude model identifier
        api_key: Anthropic API key
        base_url: Custom Anthropic API endpoint (default: https://api.anthropic.com)
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds
        enable_caching: Enable prompt caching
        version: API version (default: 2023-06-01)
    """

    provider: LLMProviderType = field(default=LLMProviderType.ANTHROPIC, repr=False)
    model: str = "claude-3-5-sonnet-20241022"
    enable_caching: bool = True
    version: str = "2023-06-01"

    def __post_init__(self) -> None:
        """Set default base_url for Anthropic if not provided."""
        if self.base_url is None:
            self.base_url = "https://api.anthropic.com"
        super().__post_init__()

    def get_headers(self) -> dict[str, str]:
        """Get Anthropic-specific headers."""
        headers = super().get_headers()
        headers.update({
            "x-api-key": self.api_key,
            "anthropic-version": self.version,
        })
        return headers


@dataclass
class OpenAIConfig(LLMConfig):
    """
    OpenAI/GPT provider configuration.

    Attributes:
        provider: Always OPENAI
        model: OpenAI model identifier (e.g., gpt-4, gpt-3.5-turbo)
        api_key: OpenAI API key
        base_url: Custom OpenAI API endpoint (default: https://api.openai.com/v1)
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds
        organization: OpenAI organization ID
    """

    provider: LLMProviderType = field(default=LLMProviderType.OPENAI, repr=False)
    model: str = "gpt-4-turbo-preview"
    organization: Optional[str] = None

    def __post_init__(self) -> None:
        """Set default base_url for OpenAI if not provided."""
        if self.base_url is None:
            self.base_url = "https://api.openai.com/v1"
        super().__post_init__()

    def get_headers(self) -> dict[str, str]:
        """Get OpenAI-specific headers."""
        headers = super().get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers


@dataclass
class GLMConfig(LLMConfig):
    """
    Zhipu AI/GLM provider configuration.

    Attributes:
        provider: Always GLM
        model: GLM model identifier (e.g., glm-4-plus, glm-4)
        api_key: Zhipu AI API key
        base_url: Custom Zhipu AI endpoint (default: https://open.bigmodel.cn/api/paas/v4)
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds
    """

    provider: LLMProviderType = field(default=LLMProviderType.GLM, repr=False)
    model: str = "glm-4-plus"

    def __post_init__(self) -> None:
        """Set default base_url for Zhipu AI if not provided."""
        if self.base_url is None:
            # GLM-4.7 uses the new z.ai endpoint
            self.base_url = "https://api.z.ai/api/paas/v4/"
        super().__post_init__()

    def get_headers(self) -> dict[str, str]:
        """Get GLM-specific headers."""
        headers = super().get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


@dataclass
class ProviderConfig:
    """
    Generic provider configuration factory.

    Creates provider-specific configs based on provider type.
    """

    provider: LLMProviderType
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout: int = 120
    extra: dict[str, Any] = field(default_factory=dict)

    def to_llm_config(self) -> LLMConfig:
        """
        Convert to provider-specific LLMConfig.

        Returns:
            AnthropicConfig, OpenAIConfig, or GLMConfig based on provider type
        """
        if self.provider == LLMProviderType.ANTHROPIC:
            return AnthropicConfig(
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                enable_caching=self.extra.get("enable_caching", True),
                version=self.extra.get("version", "2023-06-01"),
            )
        elif self.provider == LLMProviderType.OPENAI:
            return OpenAIConfig(
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                organization=self.extra.get("organization"),
            )
        elif self.provider == LLMProviderType.GLM:
            return GLMConfig(
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
            )
        else:
            raise ValueError(f"Unknown provider type: {self.provider}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        """Create from dictionary (e.g., from config file)."""
        provider_str = data.get("provider", "anthropic")
        provider = LLMProviderType(provider_str)

        return cls(
            provider=provider,
            model=data.get("model", "claude-3-5-sonnet-20241022"),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url"),
            max_tokens=data.get("max_tokens", 8192),
            temperature=data.get("temperature", 0.3),
            timeout=data.get("timeout", 120),
            extra=data.get("extra", {}),
        )


# Model name aliases for different providers
MODEL_ALIASES: dict[str, dict[LLMProviderType, str]] = {
    "claude-opus": {
        LLMProviderType.ANTHROPIC: "claude-3-opus-20240229",
        LLMProviderType.OPENAI: "gpt-4-turbo-preview",
        LLMProviderType.GLM: "glm-4-plus",
    },
    "claude-sonnet": {
        LLMProviderType.ANTHROPIC: "claude-3-5-sonnet-20241022",
        LLMProviderType.OPENAI: "gpt-4-turbo",
        LLMProviderType.GLM: "glm-4",
    },
    "claude-haiku": {
        LLMProviderType.ANTHROPIC: "claude-3-haiku-20240307",
        LLMProviderType.OPENAI: "gpt-3.5-turbo",
        LLMProviderType.GLM: "glm-3-turbo",
    },
}


def resolve_model_alias(alias: str, provider: LLMProviderType) -> str:
    """
    Resolve a model alias to provider-specific model name.

    Args:
        alias: Model alias (e.g., "claude-sonnet")
        provider: Target provider

    Returns:
        Provider-specific model name
    """
    if alias in MODEL_ALIASES:
        return MODEL_ALIASES[alias].get(provider, alias)
    return alias
