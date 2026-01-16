"""
Unit tests for LLM provider factory and registry.

Tests for:
- ProviderRegistry class
- LLMProviderFactory class
- ProviderConfig creation
- FallbackProvider class
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from claude_playwright_agent.llm.factory import (
    LLMProviderFactory,
    FallbackProvider,
)
from claude_playwright_agent.llm.providers.registry import (
    ProviderRegistry,
    ProviderNotFoundError,
)
from claude_playwright_agent.llm.base import (
    LLMProviderType,
    LLMMessage,
    LLMResponse,
    StreamChunk,
)
from claude_playwright_agent.llm.models.config import (
    ProviderConfig,
    AnthropicConfig,
    OpenAIConfig,
    GLMConfig,
)
from claude_playwright_agent.llm.exceptions import (
    LLMError,
    ProviderAPIError,
)


class TestProviderRegistry:
    """Tests for ProviderRegistry class."""

    def test_registry_initially_empty(self):
        """Test that registry starts with built-in providers."""
        registered = ProviderRegistry.list_providers()
        # Should have anthropic, openai, glm from module imports
        assert len(registered) >= 3

    def test_list_providers(self):
        """Test listing all registered providers."""
        providers = ProviderRegistry.list_providers()
        assert LLMProviderType.ANTHROPIC in providers
        assert LLMProviderType.OPENAI in providers
        assert LLMProviderType.GLM in providers

    def test_get_registered_provider(self):
        """Test getting a registered provider class."""
        provider_class = ProviderRegistry.get(LLMProviderType.ANTHROPIC)
        assert provider_class is not None

    def test_get_unregistered_provider_raises_error(self):
        """Test that getting unregistered provider raises error."""
        # Temporarily unregister GLM provider for testing
        ProviderRegistry.unregister(LLMProviderType.GLM)

        try:
            # Try to get the unregistered provider
            with pytest.raises(ProviderNotFoundError):
                ProviderRegistry.get(LLMProviderType.GLM)
        finally:
            # Re-register GLM provider
            from claude_playwright_agent.llm.providers.glm import GLMProvider
            ProviderRegistry.register(LLMProviderType.GLM, GLMProvider)

    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        # Create a mock provider class that inherits from BaseLLMProvider
        from claude_playwright_agent.llm.base import BaseLLMProvider

        class CustomProvider(BaseLLMProvider):
            async def initialize(self) -> None:
                pass

            async def cleanup(self) -> None:
                pass

            async def query(self, messages, tools=None, **kwargs):
                from claude_playwright_agent.llm.base import LLMResponse
                return LLMResponse(content="Custom response")

            async def query_stream(self, messages, tools=None, **kwargs):
                from claude_playwright_agent.llm.base import StreamChunk
                yield StreamChunk(content="Custom response")
                return

            def supports_tool_calling(self) -> bool:
                return False

            def supports_streaming(self) -> bool:
                return False

            def get_provider_info(self) -> dict:
                return {"name": "Custom", "type": "custom"}

        # Register it (using a temp type - we'll create a new enum-like approach)
        # Actually, let's just test with a valid provider registration
        # by registering to a new provider type
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Save original
        original_provider = ProviderRegistry._providers.get(LLMProviderType.OPENAI)

        try:
            # Register custom provider
            ProviderRegistry.register(LLMProviderType.OPENAI, CustomProvider)

            # Verify it's registered
            retrieved = ProviderRegistry.get(LLMProviderType.OPENAI)
            assert retrieved is CustomProvider
        finally:
            # Restore original provider
            if original_provider:
                ProviderRegistry.register(LLMProviderType.OPENAI, original_provider)

    def test_register_invalid_provider_raises_error(self):
        """Test that registering invalid provider raises error."""
        class InvalidProvider:
            pass

        with pytest.raises(TypeError):
            ProviderRegistry.register(LLMProviderType.ANTHROPIC, InvalidProvider)


class TestProviderConfig:
    """Tests for ProviderConfig classes."""

    def test_anthropic_config_creation(self):
        """Test creating AnthropicConfig."""
        config = AnthropicConfig(
            api_key="test-key",
            model="claude-3-5-sonnet",
            max_tokens=4096,
            temperature=0.7,
        )
        assert config.provider == LLMProviderType.ANTHROPIC
        assert config.api_key == "test-key"
        assert config.model == "claude-3-5-sonnet"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_openai_config_creation(self):
        """Test creating OpenAIConfig."""
        config = OpenAIConfig(
            api_key="test-key",
            model="gpt-4",
            organization="org-123",
        )
        assert config.provider == LLMProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.organization == "org-123"

    def test_glm_config_creation(self):
        """Test creating GLMConfig."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )
        assert config.provider == LLMProviderType.GLM
        assert config.api_key == "test-key"
        assert config.model == "glm-4"

    def test_provider_config_to_dict(self):
        """Test converting provider config to dict."""
        config = AnthropicConfig(
            api_key="test-key",
            model="claude-3-5-sonnet",
        )
        data = config.to_dict()
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3-5-sonnet"

    def test_anthropic_config_get_headers(self):
        """Test AnthropicConfig.get_headers method."""
        config = AnthropicConfig(api_key="sk-ant-test", model="claude-3")
        headers = config.get_headers()
        assert "anthropic-version" in headers
        assert headers["x-api-key"] == "sk-ant-test"

    def test_config_default_values(self):
        """Test that config has sensible defaults."""
        config = AnthropicConfig(api_key="test")
        assert config.max_tokens > 0
        assert 0 <= config.temperature <= 1
        assert config.timeout > 0


class TestLLMProviderFactory:
    """Tests for LLMProviderFactory class."""

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = ProviderConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet",
        )

        provider = LLMProviderFactory.create_provider(config)
        assert provider is not None
        assert provider.config.provider == LLMProviderType.ANTHROPIC

    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = ProviderConfig(
            provider=LLMProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4",
        )

        provider = LLMProviderFactory.create_provider(config)
        assert provider is not None
        assert provider.config.provider == LLMProviderType.OPENAI

    def test_create_glm_provider(self):
        """Test creating GLM provider."""
        config = ProviderConfig(
            provider=LLMProviderType.GLM,
            api_key="test-key",
            model="glm-4",
        )

        provider = LLMProviderFactory.create_provider(config)
        assert provider is not None
        assert provider.config.provider == LLMProviderType.GLM

    def test_create_provider_from_dict(self):
        """Test creating provider from dictionary config."""
        config_dict = {
            "provider": "anthropic",
            "api_key": "test-key",
            "model": "claude-3-5-sonnet",
            "max_tokens": 4096,
        }

        provider = LLMProviderFactory.create_from_dict(config_dict)
        assert provider is not None
        assert provider.config.provider == LLMProviderType.ANTHROPIC

    def test_create_provider_from_dict_invalid_provider(self):
        """Test that invalid provider in dict raises error."""
        config_dict = {
            "provider": "invalid",
            "api_key": "test-key",
            "model": "test-model",
        }

        with pytest.raises((ValueError, ProviderNotFoundError)):
            LLMProviderFactory.create_from_dict(config_dict)

    def test_create_provider_from_env(self):
        """Test creating provider from environment variables."""
        with patch.dict("os.environ", {
            "ANTHROPIC_API_KEY": "env-key",
            "CPA_AI__PROVIDER": "anthropic",
            "CPA_AI__ANTHROPIC__MODEL": "claude-3-5-sonnet",
        }):
            # This functionality is not yet implemented
            # It would read from environment variables and create a provider
            provider = LLMProviderFactory.create_provider_from_env()
            assert provider is not None
            assert provider.config.provider == LLMProviderType.ANTHROPIC


class TestFallbackProvider:
    """Tests for FallbackProvider class."""

    @pytest.mark.asyncio
    async def test_fallback_provider_uses_first_successful(self):
        """Test that fallback provider uses first successful provider."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Create mock providers
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(return_value=LLMResponse(content="Success"))

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")

        # Create fallback provider
        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Query should succeed with first provider
        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success"
        assert response.extra.get("fallback_used") is False
        mock_provider1.query.assert_called_once()
        mock_provider2.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_provider_falls_back_on_error(self):
        """Test that fallback provider tries next provider on error."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Create mock providers
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Fallback success")
        )

        # Create fallback provider
        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Query should fall back to second provider
        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Fallback success"
        assert response.extra.get("fallback_used") is True
        assert response.extra.get("fallback_provider") == "anthropic"
        mock_provider1.query.assert_called_once()
        mock_provider2.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_provider_all_providers_fail(self):
        """Test that fallback provider fails when all providers fail."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Create mock providers that all fail
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="openai")
        )

        # Create fallback provider
        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Query should fail
        with pytest.raises(LLMError):
            await fallback.query([LLMMessage.user("Test")])

    @pytest.mark.asyncio
    async def test_fallback_provider_initialize_all(self):
        """Test that fallback provider initializes all providers."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Create mock providers
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.initialize = AsyncMock()
        mock_provider1.is_initialized = Mock(return_value=False)

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2.initialize = AsyncMock()
        mock_provider2.is_initialized = Mock(return_value=False)

        # Create fallback provider
        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Initialize
        await fallback.initialize()

        # Both providers should be initialized
        mock_provider1.initialize.assert_called_once()
        mock_provider2.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_provider_cleanup_all(self):
        """Test that fallback provider cleans up all providers."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        # Create mock providers
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.cleanup = AsyncMock()
        mock_provider1._initialized = True

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2.cleanup = AsyncMock()
        mock_provider2._initialized = True

        # Create fallback provider
        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Cleanup
        await fallback.cleanup()

        # Both providers should be cleaned up
        mock_provider1.cleanup.assert_called_once()
        mock_provider2.cleanup.assert_called_once()

    def test_fallback_provider_supports_tool_calling(self):
        """Test that fallback provider reports tool calling support."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.supports_tool_calling = Mock(return_value=True)

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2.supports_tool_calling = Mock(return_value=False)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Should report True if any provider supports it
        assert fallback.supports_tool_calling() is True

    def test_fallback_provider_supports_streaming(self):
        """Test that fallback provider reports streaming support."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.supports_streaming = Mock(return_value=True)

        mock_provider2 = Mock()
        mock_provider2.config = AnthropicConfig(api_key="key2", model="model2")
        mock_provider2.supports_streaming = Mock(return_value=True)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Should report True if all providers support it
        assert fallback.supports_streaming() is True


class TestFactoryIntegration:
    """Integration tests for factory patterns."""

    def test_create_with_fallback(self):
        """Test creating provider with fallback chain."""
        configs = [
            ProviderConfig(
                provider=LLMProviderType.ANTHROPIC,
                api_key="key1",
                model="model1",
            ),
            ProviderConfig(
                provider=LLMProviderType.OPENAI,
                api_key="key2",
                model="model2",
            ),
        ]

        fallback_provider = LLMProviderFactory.create_with_fallback(configs)

        assert isinstance(fallback_provider, FallbackProvider)
        assert len(fallback_provider._providers) == 2

    def test_create_with_fallback_single_provider(self):
        """Test that single provider fallback still works."""
        configs = [
            ProviderConfig(
                provider=LLMProviderType.ANTHROPIC,
                api_key="key1",
                model="model1",
            ),
        ]

        fallback_provider = LLMProviderFactory.create_with_fallback(configs)

        assert isinstance(fallback_provider, FallbackProvider)
        assert len(fallback_provider._providers) == 1

    def test_create_with_fallback_empty_list_raises_error(self):
        """Test that empty fallback list raises error."""
        with pytest.raises(ValueError):
            LLMProviderFactory.create_with_fallback([])

    @pytest.mark.asyncio
    async def test_factory_context_manager(self):
        """Test using provider as async context manager."""
        from claude_playwright_agent.llm.models.config import ProviderConfig

        config = ProviderConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3",
        )

        # Note: This would require actual provider initialization
        # For testing, we just verify the interface exists
        provider = LLMProviderFactory.create_provider(config)

        assert hasattr(provider, "initialize")
        assert hasattr(provider, "cleanup")
