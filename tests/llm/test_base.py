"""
Unit tests for LLM base abstractions.

Tests for:
- LLMProviderType enum
- LLMMessage dataclass
- LLMResponse dataclass
- StreamChunk dataclass
- BaseLLMProvider abstract class
"""

import pytest
from dataclasses import asdict
from typing import AsyncIterator

from claude_playwright_agent.llm.base import (
    LLMProviderType,
    LLMMessage,
    LLMResponse,
    StreamChunk,
    BaseLLMProvider,
)


class TestLLMProviderType:
    """Tests for LLMProviderType enum."""

    def test_provider_type_values(self):
        """Test that provider type enum has correct values."""
        assert LLMProviderType.ANTHROPIC == "anthropic"
        assert LLMProviderType.OPENAI == "openai"
        assert LLMProviderType.GLM == "glm"

    def test_provider_type_comparison(self):
        """Test provider type string comparison."""
        assert LLMProviderType.ANTHROPIC == "anthropic"
        assert "openai" == LLMProviderType.OPENAI


class TestLLMMessage:
    """Tests for LLMMessage dataclass."""

    def test_create_message_with_role_string(self):
        """Test creating a message with string role."""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.extra == {}

    def test_create_message_with_extra(self):
        """Test creating a message with extra metadata."""
        msg = LLMMessage(
            role="user",
            content="Hello",
            extra={"timestamp": "2024-01-01"}
        )
        assert msg.extra == {"timestamp": "2024-01-01"}

    def test_system_message_factory(self):
        """Test the system message classmethod factory."""
        msg = LLMMessage.system("You are a helpful assistant.")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant."

    def test_user_message_factory(self):
        """Test the user message classmethod factory."""
        msg = LLMMessage.user("What is the weather?")
        assert msg.role == "user"
        assert msg.content == "What is the weather?"

    def test_assistant_message_factory(self):
        """Test the assistant message classmethod factory."""
        msg = LLMMessage.assistant("It's sunny today.")
        assert msg.role == "assistant"
        assert msg.content == "It's sunny today."

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = LLMMessage(role="user", content="Hello")
        result = msg.to_dict()
        assert result == {"role": "user", "content": "Hello"}

    def test_message_to_dict_with_extra(self):
        """Test converting message with extra fields to dictionary."""
        msg = LLMMessage(
            role="user",
            content="Hello",
            extra={"name": "John"}
        )
        result = msg.to_dict()
        assert result == {
            "role": "user",
            "content": "Hello",
            "name": "John"
        }

    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {"role": "user", "content": "Hello"}
        msg = LLMMessage.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_from_dict_with_extra(self):
        """Test creating message from dictionary with extra fields."""
        data = {"role": "user", "content": "Hello", "name": "John"}
        msg = LLMMessage.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.extra == {"name": "John"}


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_basic_response(self):
        """Test creating a basic response."""
        response = LLMResponse(content="Hello!")
        assert response.content == "Hello!"
        assert response.finish_reason is None
        assert response.usage == {}
        assert response.model is None
        assert response.extra == {}

    def test_create_response_with_all_fields(self):
        """Test creating a response with all fields."""
        response = LLMResponse(
            content="Hello!",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            model="claude-3-5-sonnet",
            extra={"latency_ms": 100}
        )
        assert response.content == "Hello!"
        assert response.finish_reason == "stop"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}
        assert response.model == "claude-3-5-sonnet"
        assert response.extra == {"latency_ms": 100}

    def test_response_total_tokens(self):
        """Test calculating total tokens."""
        response = LLMResponse(
            content="Hello!",
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert response.total_tokens == 15

    def test_response_total_tokens_with_missing_fields(self):
        """Test total tokens with missing usage fields."""
        response = LLMResponse(content="Hello!", usage={})
        assert response.total_tokens == 0

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = LLMResponse(
            content="Hello!",
            finish_reason="stop",
            model="claude-3-5-sonnet"
        )
        result = response.to_dict()
        assert result == {
            "content": "Hello!",
            "finish_reason": "stop",
            "usage": {},
            "model": "claude-3-5-sonnet",
            "extra": {}
        }


class TestStreamChunk:
    """Tests for StreamChunk dataclass."""

    def test_create_basic_chunk(self):
        """Test creating a basic stream chunk."""
        chunk = StreamChunk(content="Hello")
        assert chunk.content == "Hello"
        assert chunk.delta == "Hello"
        assert chunk.finish_reason is None

    def test_create_final_chunk(self):
        """Test creating the final stream chunk."""
        chunk = StreamChunk(
            content="",
            delta="",
            finish_reason="stop"
        )
        assert chunk.content == ""
        assert chunk.delta == ""
        assert chunk.finish_reason == "stop"

    def test_is_complete(self):
        """Test checking if chunk is complete."""
        incomplete_chunk = StreamChunk(content="Hello")
        complete_chunk = StreamChunk(
            content="",
            delta="",
            finish_reason="stop"
        )
        assert not incomplete_chunk.is_complete()
        assert complete_chunk.is_complete()


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for testing BaseLLMProvider."""

    async def initialize(self) -> None:
        """Initialize the mock provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the mock provider."""
        self._initialized = False

    async def query(self, messages, tools=None, **kwargs):
        """Query the mock provider."""
        from claude_playwright_agent.llm.base import LLMResponse
        return LLMResponse(content="Mock response")

    async def query_stream(self, messages, tools=None, **kwargs):
        """Query stream mock provider."""
        yield StreamChunk(content="Mock response")

    def supports_tool_calling(self) -> bool:
        """Check if tool calling is supported."""
        return True

    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return True

    def get_provider_info(self) -> dict:
        """Get provider info."""
        return {
            "name": "Mock Provider",
            "type": "mock",
            "models": ["mock-model"],
            "capabilities": []
        }


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract class."""

    def test_provider_requires_initialization(self):
        """Test that provider requires initialize implementation."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        # Provider should not be initialized initially
        assert not getattr(provider, "_initialized", False)

    @pytest.mark.asyncio
    async def test_provider_initialization(self):
        """Test provider initialization."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        await provider.initialize()
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_provider_cleanup(self):
        """Test provider cleanup."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        await provider.initialize()
        await provider.cleanup()
        assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_provider_query(self):
        """Test provider query method."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        await provider.initialize()
        response = await provider.query([LLMMessage.user("Hello")])

        assert response.content == "Mock response"

    @pytest.mark.asyncio
    async def test_provider_query_stream(self):
        """Test provider query_stream method."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        await provider.initialize()
        chunks = []
        async for chunk in provider.query_stream([LLMMessage.user("Hello")]):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].content == "Mock response"

    def test_provider_config_attribute(self):
        """Test that provider has config attribute."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        assert provider.config == config

    def test_supports_tool_calling(self):
        """Test supports_tool_calling method."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        assert provider.supports_tool_calling() is True

    def test_supports_streaming(self):
        """Test supports_streaming method."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        assert provider.supports_streaming() is True

    def test_get_provider_info(self):
        """Test get_provider_info method."""
        from claude_playwright_agent.llm.models.config import AnthropicConfig

        config = AnthropicConfig(api_key="test", model="test-model")
        provider = MockLLMProvider(config)

        info = provider.get_provider_info()
        assert info["name"] == "Mock Provider"
        assert info["type"] == "mock"


class TestLLMMessageBatch:
    """Tests for working with batches of messages."""

    def test_create_conversation(self):
        """Test creating a conversation with multiple messages."""
        messages = [
            LLMMessage.system("You are helpful."),
            LLMMessage.user("What is 2+2?"),
            LLMMessage.assistant("It is 4."),
        ]

        assert len(messages) == 3
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert messages[2].role == "assistant"

    def test_messages_to_list_of_dicts(self):
        """Test converting messages to list of dictionaries."""
        messages = [
            LLMMessage.system("You are helpful."),
            LLMMessage.user("What is 2+2?"),
        ]

        result = [msg.to_dict() for msg in messages]
        assert result == [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is 2+2?"},
        ]

    def test_messages_from_list_of_dicts(self):
        """Test creating messages from list of dictionaries."""
        data = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is 2+2?"},
        ]

        messages = [LLMMessage.from_dict(d) for d in data]
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"


class TestLLMErrorHandling:
    """Tests for error handling in base abstractions."""

    def test_message_with_empty_content(self):
        """Test that message can have empty content."""
        msg = LLMMessage(role="user", content="")
        assert msg.content == ""

    def test_response_with_empty_content(self):
        """Test that response can have empty content."""
        response = LLMResponse(content="")
        assert response.content == ""

    def test_response_with_none_finish_reason(self):
        """Test that response can have None finish reason."""
        response = LLMResponse(content="Hello", finish_reason=None)
        assert response.finish_reason is None

    def test_stream_chunk_with_none_finish_reason(self):
        """Test that stream chunk can have None finish reason."""
        chunk = StreamChunk(content="Hello", finish_reason=None)
        assert chunk.finish_reason is None
        assert not chunk.is_complete()
