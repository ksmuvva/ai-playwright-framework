"""
OpenAI/GPT provider implementation.

Uses the openai package to provide GPT-4 and other OpenAI models.
"""

import asyncio
from typing import Any, AsyncIterator, List, Optional

from ..base import BaseLLMProvider, LLMConfig, LLMMessage, LLMProviderType, StreamChunk
from ..exceptions import ProviderAPIError, ProviderTimeoutError, RateLimitError, TokenLimitError
from ..models.config import OpenAIConfig


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI/GPT provider implementation.

    Uses the official openai package to provide access to GPT-4, GPT-3.5 Turbo, etc.

    Example:
        config = OpenAIConfig(
            model="gpt-4-turbo-preview",
            api_key="sk-...",
        )
        provider = OpenAIProvider(config)
        async with provider:
            response = await provider.query(messages)
    """

    def __init__(self, config: OpenAIConfig) -> None:
        """
        Initialize the OpenAI provider.

        Args:
            config: OpenAI-specific configuration
        """
        super().__init__(config)
        self._openai_client = None

    async def initialize(self) -> None:
        """
        Initialize the OpenAI client.

        Creates an openai.AsyncOpenAI client instance.
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI provider requires the 'openai' package. "
                "Install it with: pip install openai>=1.10.0"
            )

        client_kwargs = {
            "api_key": self.config.api_key,
            "timeout": self.config.timeout,
        }

        if self.config.base_url:
            client_kwargs["base_url"] = self.config.base_url

        if self.config.organization:
            client_kwargs["organization"] = self.config.organization

        self._openai_client = openai.AsyncOpenAI(**client_kwargs)
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the OpenAI client."""
        if self._openai_client:
            await self._openai_client.close()
            self._openai_client = None
        self._initialized = False

    async def query(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LLMResponse":
        """
        Send a query to OpenAI and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool/function definitions
            **kwargs: Additional options (max_tokens, temperature, top_p, stop, etc.)

        Returns:
            LLMResponse with OpenAI's response

        Raises:
            ProviderAPIError: If the API returns an error
            ProviderTimeoutError: If the request times out
            RateLimitError: If rate limit is exceeded
            TokenLimitError: If request exceeds token limits
        """
        if not self._openai_client:
            await self.initialize()

        # Convert LLMMessage to OpenAI format
        openai_messages = self._convert_messages(messages)

        # Build request parameters
        request_params = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        # Add optional parameters
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            request_params["stop"] = kwargs["stop"]
        if "presence_penalty" in kwargs:
            request_params["presence_penalty"] = kwargs["presence_penalty"]
        if "frequency_penalty" in kwargs:
            request_params["frequency_penalty"] = kwargs["frequency_penalty"]

        # Add tools if provided
        if tools:
            openai_tools = self._convert_tools(tools)
            request_params["tools"] = openai_tools

        try:
            response = await self._openai_client.chat.completions.create(
                **request_params,
            )

            return self._parse_response(response)

        except asyncio.TimeoutError as e:
            raise ProviderTimeoutError(
                f"Request to {self.config.provider} timed out",
                provider=self.config.provider.value,
                timeout=self.config.timeout,
            ) from e
        except ImportError as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(
                    f"OpenAI rate limit exceeded",
                    provider=self.config.provider.value,
                ) from e
            elif "maximum context length" in str(e).lower():
                raise TokenLimitError(
                    f"Request exceeds OpenAI's token limit",
                    provider=self.config.provider.value,
                ) from e
            raise ProviderAPIError(
                f"Error from {self.config.provider} API: {str(e)}",
                provider=self.config.provider.value,
            ) from e
        except Exception as e:
            raise ProviderAPIError(
                f"Error from {self.config.provider} API: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    async def query_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming query to OpenAI.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Additional options

        Yields:
            StreamChunk objects as they arrive
        """
        if not self._openai_client:
            await self.initialize()

        openai_messages = self._convert_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }

        if tools:
            request_params["tools"] = self._convert_tools(tools)

        try:
            stream = await self._openai_client.chat.completions.create(
                **request_params,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        delta=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                    )

                if chunk.choices[0].finish_reason:
                    yield StreamChunk(
                        content="",
                        delta="",
                        finish_reason=chunk.choices[0].finish_reason,
                    )
                    break

        except Exception as e:
            raise ProviderAPIError(
                f"Streaming error from {self.config.provider}: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    def _convert_messages(self, messages: List[LLMMessage]) -> List[dict]:
        """Convert LLMMessage to OpenAI format."""
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        return openai_messages

    def _convert_tools(self, tools: List[dict]) -> List[dict]:
        """Convert tools to OpenAI format."""
        return tools  # OpenAI format is compatible

    def _parse_response(self, response) -> "LLMResponse":
        """Parse OpenAI response to LLMResponse."""
        from ..base import LLMResponse

        choice = response.choices[0]
        message = choice.message

        # Extract content
        content = message.content or ""

        # Handle tool calls if present
        extra = {}
        if hasattr(message, "tool_calls") and message.tool_calls:
            extra["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in message.tool_calls
            ]

        # Extract usage
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=content,
            finish_reason=choice.finish_reason,
            usage=usage,
            model=response.model,
            extra=extra,
        )

    def supports_tool_calling(self) -> bool:
        """Check if OpenAI supports tool calling (yes, for GPT-4+)."""
        return self.config.model.startswith("gpt-4")

    def supports_streaming(self) -> bool:
        """Check if OpenAI supports streaming (yes, it does)."""
        return True

    def get_provider_info(self) -> dict[str, Any]:
        """Get OpenAI provider information."""
        return {
            "name": "OpenAI",
            "type": self.config.provider.value,
            "models": [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo",
            ],
            "capabilities": ["tool-calling", "streaming", "function-calling"],
            "max_tokens": 128000,
            "website": "https://platform.openai.com",
        }
