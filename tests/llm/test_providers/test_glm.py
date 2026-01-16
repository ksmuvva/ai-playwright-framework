"""
Tests for Zhipu AI/GLM provider.

Tests for:
- GLMProvider initialization
- Message conversion
- Query execution
- Streaming support
- Tool calling support
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from claude_playwright_agent.llm.providers.glm import GLMProvider
from claude_playwright_agent.llm.models.config import GLMConfig
from claude_playwright_agent.llm.base import (
    LLMMessage,
    LLMResponse,
    LLMProviderType,
)


class TestGLMProvider:
    """Tests for GLMProvider class."""

    def test_glm_provider_initialization(self):
        """Test creating GLMProvider."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4-plus",
        )

        provider = GLMProvider(config)

        assert provider.config == config
        assert provider._zhipu_client is None

    @pytest.mark.asyncio
    async def test_glm_provider_initialize(self):
        """Test initializing GLMProvider."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4-plus",
        )

        provider = GLMProvider(config)

        # Mock the zhipuai package
        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            await provider.initialize()

            assert provider._initialized is True
            mock_zhipuai.ZhipuAI.assert_called_once_with(api_key="test-key")

    @pytest.mark.asyncio
    async def test_glm_provider_cleanup(self):
        """Test cleaning up GLMProvider."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4-plus",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            await provider.initialize()
            await provider.cleanup()

            assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_glm_query_basic(self):
        """Test basic query to GLM provider."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4-plus",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.model = "glm-4-plus"

            mock_client.chat.completions.create = MagicMock(return_value=mock_response)

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            response = await provider.query(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.model == "glm-4-plus"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5

    @pytest.mark.asyncio
    async def test_glm_query_with_tools(self):
        """Test query with tool definitions."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Tool result"
            mock_response.choices[0].finish_reason = "tool_calls"
            mock_response.choices[0].message.tool_calls = []
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 15
            mock_response.usage.completion_tokens = 10
            mock_response.model = "glm-4"

            mock_client.chat.completions.create = MagicMock(return_value=mock_response)

            await provider.initialize()

            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "parameters": {}
                    }
                }
            ]

            messages = [LLMMessage.user("What's the weather?")]
            response = await provider.query(messages, tools=tools)

            assert response.content == "Tool result"
            assert response.extra["tool_calls"] == []

    @pytest.mark.asyncio
    async def test_glm_query_with_temperature(self):
        """Test query with custom temperature."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
            temperature=0.5,
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.model = "glm-4"

            mock_client.chat.completions.create = MagicMock(return_value=mock_response)

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            response = await provider.query(messages, temperature=0.8)

            # Verify temperature was used
            import asyncio
            asyncio.to_thread = AsyncMock(return_value=mock_response)
            call_kwargs = asyncio.to_thread.call_args[1]
            assert call_kwargs["temperature"] == 0.8

    @pytest.mark.asyncio
    async def test_glm_query_stream(self):
        """Test streaming query to GLM provider."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            # Mock stream response
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [MagicMock()]
            mock_chunk1.choices[0].delta.content = "Hello"
            mock_chunk1.choices[0].finish_reason = None

            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [MagicMock()]
            mock_chunk2.choices[0].delta.content = " world"
            mock_chunk2.choices[0].finish_reason = None

            mock_chunk3 = MagicMock()
            mock_chunk3.choices = [MagicMock()]
            mock_chunk3.choices[0].delta.content = None
            mock_chunk3.choices[0].finish_reason = "stop"

            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([mock_chunk1, mock_chunk2, mock_chunk3])

            import asyncio
            asyncio.to_thread = AsyncMock(return_value=mock_response)

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            chunks = []

            async for chunk in provider.query_stream(messages):
                chunks.append(chunk)

            assert len(chunks) >= 1
            if len(chunks) > 0:
                assert chunks[0].content in ["Hello", "Hello world", ""]

    def test_glm_supports_tool_calling_glm4(self):
        """Test that GLM-4 supports tool calling."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)
        assert provider.supports_tool_calling() is True

    def test_glm_supports_tool_calling_glm3(self):
        """Test that GLM-3 doesn't support tool calling."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-3-turbo",
        )

        provider = GLMProvider(config)
        assert provider.supports_tool_calling() is False

    def test_glm_supports_streaming(self):
        """Test that GLM provider supports streaming."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)
        assert provider.supports_streaming() is True

    def test_glm_get_provider_info(self):
        """Test getting GLM provider info."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)
        info = provider.get_provider_info()

        assert info["name"] == "Zhipu AI"
        assert info["type"] == "glm"
        assert "glm-4-plus" in info["models"]
        assert "glm-4" in info["models"]
        assert "glm-3-turbo" in info["models"]
        assert "tool-calling" in info["capabilities"]
        assert "streaming" in info["capabilities"]
        assert info["max_tokens"] == 128000


class TestGLMProviderErrors:
    """Tests for GLMProvider error handling."""

    @pytest.mark.asyncio
    async def test_glm_timeout_error(self):
        """Test timeout error handling."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
            timeout=30,
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            import asyncio
            asyncio.to_thread = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))

            await provider.initialize()

            from claude_playwright_agent.llm.exceptions import ProviderTimeoutError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(ProviderTimeoutError):
                await provider.query(messages)

    @pytest.mark.asyncio
    async def test_glm_rate_limit_error(self):
        """Test rate limit error handling."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            import asyncio
            asyncio.to_thread = AsyncMock(
                side_effect=Exception("Rate limit exceeded: 429")
            )

            await provider.initialize()

            from claude_playwright_agent.llm.exceptions import RateLimitError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(RateLimitError):
                await provider.query(messages)

    @pytest.mark.asyncio
    async def test_glm_token_limit_error(self):
        """Test token limit error handling."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        with patch("claude_playwright_agent.llm.providers.glm.zhipuai") as mock_zhipuai:
            mock_client = MagicMock()
            mock_zhipuai.ZhipuAI.return_value = mock_client

            import asyncio
            asyncio.to_thread = AsyncMock(
                side_effect=Exception("Token limit exceeded")
            )

            await provider.initialize()

            from claude_playwright_agent.llm.exceptions import TokenLimitError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(TokenLimitError):
                await provider.query(messages)


class TestGLMConfig:
    """Tests for GLMConfig class."""

    def test_glm_config_defaults(self):
        """Test GLMConfig default values."""
        config = GLMConfig(api_key="test-key")

        assert config.provider == LLMProviderType.GLM
        assert config.api_key == "test-key"
        assert config.model == "glm-4-plus"
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout == 120

    def test_glm_config_custom_values(self):
        """Test GLMConfig with custom values."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
            max_tokens=4096,
            temperature=0.5,
            timeout=60,
        )

        assert config.model == "glm-4"
        assert config.max_tokens == 4096
        assert config.temperature == 0.5
        assert config.timeout == 60

    def test_glm_config_to_dict(self):
        """Test converting GLMConfig to dict."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        data = config.to_dict()

        assert data["provider"] == "glm"
        assert data["model"] == "glm-4"
        assert data["api_key"] == "test-key"


class TestGLMMessageConversion:
    """Tests for GLM message conversion."""

    @pytest.mark.asyncio
    async def test_convert_messages_to_glm_format(self):
        """Test converting LLMMessage to GLM format."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        messages = [
            LLMMessage.system("You are helpful."),
            LLMMessage.user("Hello"),
            LLMMessage.assistant("Hi there!"),
        ]

        glm_messages = provider._convert_messages(messages)

        assert len(glm_messages) == 3
        assert glm_messages[0]["role"] == "system"
        assert glm_messages[0]["content"] == "You are helpful."
        assert glm_messages[1]["role"] == "user"
        assert glm_messages[1]["content"] == "Hello"
        assert glm_messages[2]["role"] == "assistant"
        assert glm_messages[2]["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_parse_glm_response(self):
        """Test parsing GLM response to LLMResponse."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        # Mock GLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.model = "glm-4"

        llm_response = provider._parse_response(mock_response)

        assert llm_response.content == "Test response"
        assert llm_response.finish_reason == "stop"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 5
        assert llm_response.model == "glm-4"

    @pytest.mark.asyncio
    async def test_parse_glm_response_with_tool_calls(self):
        """Test parsing GLM response with tool calls."""
        config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )

        provider = GLMProvider(config)

        # Mock GLM response with tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_function"
        mock_tool_call.function.arguments = '{"arg": "value"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.model = "glm-4"

        llm_response = provider._parse_response(mock_response)

        assert llm_response.content == ""
        assert llm_response.extra["tool_calls"][0]["id"] == "call_123"
        assert llm_response.extra["tool_calls"][0]["name"] == "test_function"
        assert llm_response.extra["tool_calls"][0]["arguments"] == '{"arg": "value"}'
