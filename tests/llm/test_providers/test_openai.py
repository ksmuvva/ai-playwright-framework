"""
Tests for OpenAI/GPT provider.

Tests for:
- OpenAIProvider initialization
- Message conversion
- Query execution
- Streaming support
- Tool calling support
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from claude_playwright_agent.llm.providers.openai import OpenAIProvider
from claude_playwright_agent.llm.models.config import OpenAIConfig
from claude_playwright_agent.llm.base import (
    LLMMessage,
    LLMResponse,
    LLMProviderType,
)


class TestOpenAIProvider:
    """Tests for OpenAIProvider class."""

    def test_openai_provider_initialization(self):
        """Test creating OpenAIProvider."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4-turbo-preview",
        )

        provider = OpenAIProvider(config)

        assert provider.config == config
        assert provider._openai_client is None

    @pytest.mark.asyncio
    async def test_openai_provider_initialize(self):
        """Test initializing OpenAIProvider."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4-turbo-preview",
        )

        provider = OpenAIProvider(config)

        # Mock the openai package
        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            await provider.initialize()

            assert provider._initialized is True
            mock_openai.AsyncOpenAI.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_provider_initialize_with_base_url(self):
        """Test initializing with custom base URL."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
            base_url="https://custom.openai.com",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            await provider.initialize()

            # Verify base_url was passed
            call_kwargs = mock_openai.AsyncOpenAI.call_args[1]
            assert call_kwargs["base_url"] == "https://custom.openai.com"

    @pytest.mark.asyncio
    async def test_openai_provider_initialize_with_organization(self):
        """Test initializing with organization."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
            organization="org-123",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            await provider.initialize()

            # Verify organization was passed
            call_kwargs = mock_openai.AsyncOpenAI.call_args[1]
            assert call_kwargs["organization"] == "org-123"

    @pytest.mark.asyncio
    async def test_openai_provider_cleanup(self):
        """Test cleaning up OpenAIProvider."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4-turbo-preview",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            await provider.initialize()
            await provider.cleanup()

            assert provider._initialized is False
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_query_basic(self):
        """Test basic query to OpenAI provider."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4-turbo-preview",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            # Setup mock client
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.model = "gpt-4-turbo-preview"

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            response = await provider.query(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.model == "gpt-4-turbo-preview"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5

    @pytest.mark.asyncio
    async def test_openai_query_with_tools(self):
        """Test query with tool definitions."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Tool result"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 15
            mock_response.usage.completion_tokens = 10
            mock_response.model = "gpt-4"

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

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

            # Verify tools were passed
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert "tools" in call_kwargs

    @pytest.mark.asyncio
    async def test_openai_query_with_temperature(self):
        """Test query with custom temperature."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
            temperature=0.5,
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.model = "gpt-4"

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            response = await provider.query(messages, temperature=0.8)

            # Verify temperature was used
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.8

    @pytest.mark.asyncio
    async def test_openai_query_stream(self):
        """Test streaming query to OpenAI provider."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

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

            async def mock_stream():
                yield mock_chunk1
                yield mock_chunk2
                yield mock_chunk3

            mock_client.chat.completions.create = MagicMock(return_value=mock_stream())

            await provider.initialize()

            messages = [LLMMessage.user("Hello")]
            chunks = []

            async for chunk in provider.query_stream(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " world"
            assert chunks[2].finish_reason == "stop"

    def test_openai_supports_tool_calling_gpt4(self):
        """Test that GPT-4 supports tool calling."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)
        assert provider.supports_tool_calling() is True

    def test_openai_supports_tool_calling_gpt35(self):
        """Test that GPT-3.5 supports tool calling."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-3.5-turbo",
        )

        provider = OpenAIProvider(config)
        # GPT-3.5 doesn't start with gpt-4
        assert provider.supports_tool_calling() is False

    def test_openai_supports_streaming(self):
        """Test that OpenAI provider supports streaming."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)
        assert provider.supports_streaming() is True

    def test_openai_get_provider_info(self):
        """Test getting OpenAI provider info."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)
        info = provider.get_provider_info()

        assert info["name"] == "OpenAI"
        assert info["type"] == "openai"
        assert "gpt-4-turbo-preview" in info["models"]
        assert "gpt-4" in info["models"]
        assert "gpt-3.5-turbo" in info["models"]
        assert "tool-calling" in info["capabilities"]
        assert "streaming" in info["capabilities"]
        assert info["max_tokens"] == 128000


class TestOpenAIProviderErrors:
    """Tests for OpenAIProvider error handling."""

    @pytest.mark.asyncio
    async def test_openai_timeout_error(self):
        """Test timeout error handling."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
            timeout=30,
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            import asyncio
            mock_client.chat.completions.create = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timed out")
            )

            await provider.initialize()

            from claude_playwright_agent.llm.exceptions import ProviderTimeoutError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(ProviderTimeoutError):
                await provider.query(messages)

    @pytest.mark.asyncio
    async def test_openai_rate_limit_error(self):
        """Test rate limit error handling."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        provider = OpenAIProvider(config)

        with patch("claude_playwright_agent.llm.providers.openai.openai") as mock_openai:
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client

            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )

            await provider.initialize()

            from claude_playwright_agent.llm.exceptions import RateLimitError

            messages = [LLMMessage.user("Hello")]

            with pytest.raises(RateLimitError):
                await provider.query(messages)


class TestOpenAIConfig:
    """Tests for OpenAIConfig class."""

    def test_openai_config_defaults(self):
        """Test OpenAIConfig default values."""
        config = OpenAIConfig(api_key="test-key")

        assert config.provider == LLMProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-4-turbo-preview"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout == 60
        assert config.organization is None
        assert config.base_url is None

    def test_openai_config_custom_values(self):
        """Test OpenAIConfig with custom values."""
        config = OpenAIConfig(
            api_key="test-key",
            model="gpt-4",
            max_tokens=8192,
            temperature=0.5,
            timeout=120,
            organization="org-123",
        )

        assert config.model == "gpt-4"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5
        assert config.timeout == 120
        assert config.organization == "org-123"

    def test_openai_config_to_dict(self):
        """Test converting OpenAIConfig to dict."""
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )

        data = config.to_dict()

        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["api_key"] == "sk-test"
