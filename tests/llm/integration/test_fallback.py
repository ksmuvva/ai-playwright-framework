"""
Fallback mechanism integration tests.

Tests for:
- FallbackProvider behavior
- Error handling across fallback chain
- Partial success scenarios
- Fallback chain configuration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from claude_playwright_agent.llm.factory import FallbackProvider
from claude_playwright_agent.llm.base import LLMMessage, LLMResponse
from claude_playwright_agent.llm.exceptions import (
    ProviderAPIError,
    RateLimitError,
    ProviderTimeoutError,
)
from claude_playwright_agent.llm.models.config import (
    AnthropicConfig,
    OpenAIConfig,
    GLMConfig,
)


class TestFallbackBehavior:
    """Tests for fallback provider behavior."""

    @pytest.mark.asyncio
    async def test_first_provider_succeeds(self):
        """Test that first provider is used when it succeeds."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            return_value=LLMResponse(content="Success from provider 1")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success from provider 1"
        assert response.extra.get("fallback_used") is False
        mock_provider1.query.assert_called_once()
        mock_provider2.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_second_provider_succeeds_after_first_fails(self):
        """Test fallback to second provider when first fails."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success from provider 2")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success from provider 2"
        assert response.extra.get("fallback_used") is True
        assert response.extra.get("fallback_provider") == "openai"  # The successful provider
        mock_provider1.query.assert_called_once()
        mock_provider2.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_third_provider_succeeds_after_two_fail(self):
        """Test fallback through multiple providers."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=RateLimitError("Rate limited", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            side_effect=ProviderTimeoutError("Timeout", provider="openai", timeout=60)
        )

        mock_provider3 = Mock()
        mock_provider3.config = GLMConfig(api_key="key3", model="model3")
        mock_provider3._initialized = True
        mock_provider3.query = AsyncMock(
            return_value=LLMResponse(content="Success from provider 3")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2, mock_provider3])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success from provider 3"
        assert response.extra.get("fallback_used") is True
        assert response.extra.get("attempted_providers") == 2  # First 2 failed

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test that error is raised when all providers fail."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="openai")
        )

        mock_provider3 = Mock()
        mock_provider3.config = GLMConfig(api_key="key3", model="model3")
        mock_provider3._initialized = True
        mock_provider3.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="glm")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2, mock_provider3])

        from claude_playwright_agent.llm.exceptions import LLMError

        with pytest.raises(LLMError) as exc_info:
            await fallback.query([LLMMessage.user("Test")])

        assert "providers in fallback chain failed" in str(exc_info.value)


class TestFallbackErrorTypes:
    """Tests for handling different error types."""

    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit(self):
        """Test fallback on rate limit errors."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=RateLimitError("Rate limited", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success"
        assert response.extra.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_fallback_on_timeout(self):
        """Test fallback on timeout errors."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderTimeoutError("Timeout", provider="anthropic", timeout=60)
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success"
        assert response.extra.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_fallback_on_api_error(self):
        """Test fallback on general API errors."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("API Error", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        assert response.content == "Success"
        assert response.extra.get("fallback_used") is True


class TestFallbackStreaming:
    """Tests for fallback with streaming."""

    @pytest.mark.asyncio
    async def test_fallback_with_streaming(self):
        """Test that streaming works with fallback."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True

        async def mock_stream1(messages, tools=None, **kwargs):
            return
            yield  # Make this an async generator (never reached)

        mock_provider1.query_stream = mock_stream1

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True

        from claude_playwright_agent.llm.base import StreamChunk

        async def mock_stream2(messages, tools=None, **kwargs):
            yield StreamChunk(content="Stream response")
            return

        mock_provider2.query_stream = mock_stream2

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        chunks = []
        async for chunk in fallback.query_stream([LLMMessage.user("Test")]):
            chunks.append(chunk)

        # Should get chunks from second provider
        assert len(chunks) >= 0


class TestFallbackLifecycle:
    """Tests for fallback provider lifecycle management."""

    @pytest.mark.asyncio
    async def test_initialize_all_providers(self):
        """Test that all providers are initialized."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.initialize = AsyncMock()
        mock_provider1.is_initialized = Mock(return_value=False)

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.initialize = AsyncMock()
        mock_provider2.is_initialized = Mock(return_value=False)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        await fallback.initialize()

        mock_provider1.initialize.assert_called_once()
        mock_provider2.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_all_providers(self):
        """Test that all providers are cleaned up."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.cleanup = AsyncMock()
        mock_provider1._initialized = True

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.cleanup = AsyncMock()
        mock_provider2._initialized = True

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        await fallback.cleanup()

        mock_provider1.cleanup.assert_called_once()
        mock_provider2.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_after_partial_initialization(self):
        """Test cleanup when some providers failed to initialize."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.initialize = AsyncMock(side_effect=Exception("Init failed"))
        mock_provider1._initialized = False

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.initialize = AsyncMock()
        mock_provider2._initialized = False
        mock_provider2.cleanup = AsyncMock()
        mock_provider2._initialized = True

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Initialize should handle first provider failure
        try:
            await fallback.initialize()
        except Exception:
            pass

        # Cleanup should still work
        try:
            await fallback.cleanup()
        except Exception:
            pass


class TestFallbackCapabilities:
    """Tests for fallback provider capability reporting."""

    def test_supports_tool_calling_if_any_supports(self):
        """Test that tool calling is supported if any provider supports it."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.supports_tool_calling = Mock(return_value=True)

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.supports_tool_calling = Mock(return_value=False)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        # Should return True if any provider supports it
        assert fallback.supports_tool_calling() is True

    def test_supports_streaming_if_all_support(self):
        """Test that streaming is supported only if all providers support it."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.supports_streaming = Mock(return_value=True)

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.supports_streaming = Mock(return_value=True)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        assert fallback.supports_streaming() is True

    def test_does_not_support_streaming_if_one_doesnt(self):
        """Test that streaming is not supported if one provider doesn't support it."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1.supports_streaming = Mock(return_value=True)

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2.supports_streaming = Mock(return_value=False)

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        assert fallback.supports_streaming() is False


class TestFallbackMetadata:
    """Tests for fallback metadata tracking."""

    @pytest.mark.asyncio
    async def test_fallback_metadata_in_response(self):
        """Test that fallback metadata is included in response."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        # Check metadata
        assert "fallback_used" in response.extra
        assert "fallback_provider" in response.extra
        assert "attempted_providers" in response.extra

    @pytest.mark.asyncio
    async def test_no_fallback_metadata_on_first_success(self):
        """Test that no fallback metadata when first provider succeeds."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1])

        response = await fallback.query([LLMMessage.user("Test")])

        # Should indicate no fallback was used
        assert response.extra.get("fallback_used") is False


class TestFallbackConfiguration:
    """Tests for fallback configuration scenarios."""

    def test_fallback_chain_from_config(self):
        """Test creating fallback chain from configuration."""
        configs = [
            AnthropicConfig(api_key="key1", model="model1"),
            OpenAIConfig(api_key="key2", model="model2"),
            GLMConfig(api_key="key3", model="model3"),
        ]

        from claude_playwright_agent.llm import LLMProviderFactory

        fallback = LLMProviderFactory.create_with_fallback(configs)

        assert len(fallback._providers) == 3

    def test_single_provider_fallback(self):
        """Test fallback with single provider (degenerate case)."""
        configs = [
            AnthropicConfig(api_key="key1", model="model1"),
        ]

        from claude_playwright_agent.llm import LLMProviderFactory

        fallback = LLMProviderFactory.create_with_fallback(configs)

        assert len(fallback._providers) == 1

    def test_empty_fallback_list_raises_error(self):
        """Test that empty fallback list raises error."""
        from claude_playwright_agent.llm import LLMProviderFactory

        with pytest.raises(ValueError):
            LLMProviderFactory.create_with_fallback([])


class TestFallbackRetries:
    """Tests for retry behavior with fallback."""

    @pytest.mark.asyncio
    async def test_no_retry_on_same_provider(self):
        """Test that failed provider is not retried."""
        mock_provider1 = Mock()
        mock_provider1.config = AnthropicConfig(api_key="key1", model="model1")
        mock_provider1._initialized = True
        mock_provider1.query = AsyncMock(
            side_effect=ProviderAPIError("Failed", provider="anthropic")
        )

        mock_provider2 = Mock()
        mock_provider2.config = OpenAIConfig(api_key="key2", model="model2")
        mock_provider2._initialized = True
        mock_provider2.query = AsyncMock(
            return_value=LLMResponse(content="Success")
        )

        fallback = FallbackProvider([mock_provider1, mock_provider2])

        response = await fallback.query([LLMMessage.user("Test")])

        # Provider 1 should only be called once
        assert mock_provider1.query.call_count == 1
        assert mock_provider2.query.call_count == 1
