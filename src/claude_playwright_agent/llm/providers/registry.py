"""
Provider registry for dynamic provider loading.

Allows registration and retrieval of LLM provider implementations.
"""

from typing import Dict, Type

from ..base import BaseLLMProvider, LLMProviderType
from ..exceptions import ProviderNotFoundError


class ProviderRegistry:
    """
    Registry for available LLM providers.

    Similar pattern to SkillLoader - allows dynamic discovery
    and registration of providers.

    Example:
        # Register a custom provider
        ProviderRegistry.register(
            LLMProviderType.CUSTOM,
            MyCustomProvider
        )

        # Get a provider class
        provider_class = ProviderRegistry.get(LLMProviderType.ANTHROPIC)

        # List all providers
        providers = ProviderRegistry.list_providers()
    """

    _providers: Dict[LLMProviderType, Type[BaseLLMProvider]] = {}

    @classmethod
    def register(
        cls,
        provider_type: LLMProviderType,
        provider_class: Type[BaseLLMProvider],
    ) -> None:
        """
        Register a new provider type.

        Args:
            provider_type: Provider type identifier
            provider_class: Provider class (must inherit from BaseLLMProvider)

        Raises:
            TypeError: If provider_class doesn't inherit from BaseLLMProvider
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise TypeError(f"{provider_class.__name__} must inherit from BaseLLMProvider")

        cls._providers[provider_type] = provider_class

    @classmethod
    def unregister(cls, provider_type: LLMProviderType) -> None:
        """
        Unregister a provider type.

        Args:
            provider_type: Provider type to unregister
        """
        cls._providers.pop(provider_type, None)

    @classmethod
    def get(cls, provider_type: LLMProviderType) -> Type[BaseLLMProvider]:
        """
        Get a provider class by type.

        Args:
            provider_type: Provider type

        Returns:
            Provider class

        Raises:
            ProviderNotFoundError: If provider type not registered
        """
        if provider_type not in cls._providers:
            available = ", ".join(p.value for p in cls._providers.keys())
            raise ProviderNotFoundError(
                f"Provider '{provider_type.value}' not registered. "
                f"Available providers: {available or 'none'}"
            )
        return cls._providers[provider_type]

    @classmethod
    def is_registered(cls, provider_type: LLMProviderType) -> bool:
        """
        Check if a provider type is registered.

        Args:
            provider_type: Provider type to check

        Returns:
            True if provider is registered
        """
        return provider_type in cls._providers

    @classmethod
    def list_providers(cls) -> list[LLMProviderType]:
        """
        List all registered provider types.

        Returns:
            List of provider types
        """
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (mainly for testing)."""
        cls._providers.clear()
