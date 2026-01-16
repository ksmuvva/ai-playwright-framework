"""
Tests for Anthropic/Claude provider.

Tests for:
- AnthropicProvider initialization
- Message conversion
- Query execution
- Streaming support
- Tool calling support
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from claude_playwright_agent.llm.providers.anthropic import AnthropicProvider
from claude_playwright_agent.llm.models.config import AnthropicConfig
from claude_playwright_agent.llm.base import (
    LLMMessage,
    LLMResponse,
    LLMProviderType,
)


class TestAnthropicProvider:
    """Tests for AnthropicProvider class."""

    def test_anthropic_provider_initialization(self):
        """Test creating AnthropicProvider."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        assert provider.config == config
        assert provider._claude_client is None
        assert provider._sdk_options is None

    @pytest.mark.asyncio
    async def test_anthropic_provider_initialize(self):
        """Test initializing AnthropicProvider."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        # Mock the ClaudeSDKClient
        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()
            assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_anthropic_provider_cleanup(self):
        """Test cleaning up AnthropicProvider."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()
            await provider.cleanup()
            assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_anthropic_query_basic(self):
        """Test basic query to Anthropic provider."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        # Mock the ClaudeSDKClient
        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()

            # Mock the query response
            provider._simulate_claude_request = AsyncMock(
                return_value="Test response"
            )

            messages = [LLMMessage.user("Hello")]
            response = await provider.query(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_anthropic_query_with_system_prompt(self):
        """Test query with system prompt extraction."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()

            provider._simulate_claude_request = AsyncMock(
                return_value="Response"
            )

            messages = [
                LLMMessage.system("You are helpful."),
                LLMMessage.user("Hello"),
            ]

            response = await provider.query(messages)

            assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_anthropic_query_stream(self):
        """Test streaming query to Anthropic provider."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()

            # Mock streaming response
            provider.query = AsyncMock(
                return_value=LLMResponse(content="Stream response")
            )

            messages = [LLMMessage.user("Hello")]
            chunks = []

            async for chunk in provider.query_stream(messages):
                chunks.append(chunk)

            # Should get at least one chunk
            assert len(chunks) > 0

    def test_anthropic_supports_tool_calling(self):
        """Test that Anthropic provider supports tool calling."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)
        assert provider.supports_tool_calling() is True

    def test_anthropic_supports_streaming(self):
        """Test that Anthropic provider supports streaming."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)
        assert provider.supports_streaming() is True

    def test_anthropic_get_provider_info(self):
        """Test getting Anthropic provider info."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)
        info = provider.get_provider_info()

        assert info["name"] == "Anthropic"
        assert info["type"] == "anthropic"
        assert "claude-3-5-sonnet-20241022" in info["models"]
        assert "tool-calling" in info["capabilities"]
        assert "streaming" in info["capabilities"]
        assert info["max_tokens"] == 200000


class TestAnthropicProviderErrors:
    """Tests for AnthropicProvider error handling."""

    @pytest.mark.asyncio
    async def test_anthropic_timeout_error(self):
        """Test timeout error handling."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()

            import asyncio
            provider._simulate_claude_request = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timed out")
            )

            from claude_playwright_agent.llm.exceptions import ProviderTimeoutError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(ProviderTimeoutError):
                await provider.query(messages)

    @pytest.mark.asyncio
    async def test_anthropic_api_error(self):
        """Test API error handling."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )

        provider = AnthropicProvider(config)

        with patch("claude_playwright_agent.llm.providers.anthropic.ClaudeSDKClient"):
            await provider.initialize()

            provider._simulate_claude_request = AsyncMock(
                side_effect=Exception("API Error")
            )

            from claude_playwright_agent.llm.exceptions import ProviderAPIError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(ProviderAPIError):
                await provider.query(messages)


class TestAnthropicConfig:
    """Tests for AnthropicConfig class."""

    def test_anthropic_config_defaults(self):
        """Test AnthropicConfig default values."""
        config = AnthropicConfig(api_key="test-key")

        assert config.provider == LLMProviderType.ANTHROPIC
        assert config.api_key == "test-key"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.enable_caching is True
        assert config.version == "2023-06-01"
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout == 120

    def test_anthropic_config_custom_values(self):
        """Test AnthropicConfig with custom values."""
        config = AnthropicConfig(
            api_key="test-key",
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.5,
            timeout=60,
        )

        assert config.model == "claude-3-opus-20240229"
        assert config.max_tokens == 4096
        assert config.temperature == 0.5
        assert config.timeout == 60

    def test_anthropic_config_get_headers(self):
        """Test AnthropicConfig.get_headers method."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet",
        )

        headers = config.get_headers()

        assert headers["x-api-key"] == "sk-ant-test"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_anthropic_config_to_dict(self):
        """Test converting AnthropicConfig to dict."""
        config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet",
        )

        data = config.to_dict()

        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3-5-sonnet"
        assert data["api_key"] == "sk-ant-test"
