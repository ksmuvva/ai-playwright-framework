"""
Zhipu AI/GLM provider implementation.

Supports both the legacy zhipuai package and the new OpenAI-compatible API.
GLM-4.7 uses the new endpoint: https://api.z.ai/api/paas/v4/
"""

import asyncio
import json
from typing import Any, AsyncIterator, List, Optional

from ..base import BaseLLMProvider, LLMConfig, LLMMessage, LLMProviderType, StreamChunk
from ..exceptions import ProviderAPIError, ProviderTimeoutError, RateLimitError
from ..models.config import GLMConfig


class GLMProvider(BaseLLMProvider):
    """
    Zhipu AI/GLM provider implementation.

    GLM-4.7 uses the OpenAI-compatible API with custom base_url.
    Older GLM models can use the zhipuai package.

    Example:
        config = GLMConfig(
            model="glm-4.7",
            api_key="...",
            base_url="https://api.z.ai/api/paas/v4/",
        )
        provider = GLMProvider(config)
        async with provider:
            response = await provider.query(messages)
    """

    def __init__(self, config: GLMConfig) -> None:
        """
        Initialize the GLM provider.

        Args:
            config: GLM-specific configuration
        """
        super().__init__(config)
        self._openai_client = None
        self._zhipu_client = None
        self._use_openai_compat = self._is_glm47_or_newer()

    def _is_glm47_or_newer(self) -> bool:
        """Check if using GLM-4.7 or newer (requires OpenAI-compatible API)."""
        model = self.config.model.lower()
        return "glm-4.7" in model or model.startswith("glm-4-7")

    async def initialize(self) -> None:
        """
        Initialize the appropriate client.

        For GLM-4.7+: Uses OpenAI SDK with custom base_url
        For older GLM: Uses zhipuai package
        """
        if self._use_openai_compat:
            await self._init_openai_client()
        else:
            await self._init_zhipu_client()
        self._initialized = True

    async def _init_openai_client(self) -> None:
        """Initialize OpenAI-compatible client for GLM-4.7+"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "GLM-4.7 provider requires the 'openai' package. "
                "Install it with: pip install 'openai>=1.0'"
            )

        self._openai_client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    async def _init_zhipu_client(self) -> None:
        """Initialize legacy zhipuai client for older GLM models"""
        try:
            import zhipuai
        except ImportError:
            raise ImportError(
                "GLM provider requires the 'zhipuai' package. "
                "Install it with: pip install zhipuai>=2.0.0"
            )

        self._zhipu_client = zhipuai.ZhipuAI(
            api_key=self.config.api_key,
        )

    async def cleanup(self) -> None:
        """Clean up the client."""
        self._openai_client = None
        self._zhipu_client = None
        self._initialized = False

    async def query(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LLMResponse":
        """
        Send a query to Zhipu AI and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Additional options (max_tokens, temperature, top_p, etc.)

        Returns:
            LLMResponse with GLM's response

        Raises:
            ProviderAPIError: If the API returns an error
            ProviderTimeoutError: If the request times out
            RateLimitError: If rate limit is exceeded
        """
        if self._use_openai_compat:
            return await self._query_openai(messages, tools, **kwargs)
        else:
            return await self._query_zhipu(messages, tools, **kwargs)

    async def _query_openai(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LLMResponse":
        """Query using OpenAI-compatible API for GLM-4.7+"""
        if not self._openai_client:
            await self.initialize()

        glm_messages = self._convert_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": glm_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if tools:
            request_params["tools"] = tools

        try:
            response = await self._openai_client.chat.completions.create(
                **request_params,
            )
            return self._parse_response(response)
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                raise RateLimitError(
                    f"GLM rate limit exceeded",
                    provider=self.config.provider.value,
                ) from e
            raise ProviderAPIError(
                f"Error from GLM API: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    async def _query_zhipu(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LLMResponse":
        """Query using legacy zhipuai API"""
        if not self._zhipu_client:
            await self.initialize()

        glm_messages = self._convert_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": glm_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        try:
            response = await asyncio.to_thread(
                self._zhipu_client.chat.completions.create,
                **request_params,
            )
            return self._parse_response(response)
        except asyncio.TimeoutError as e:
            raise ProviderTimeoutError(
                f"Request to {self.config.provider} timed out",
                provider=self.config.provider.value,
                timeout=self.config.timeout,
            ) from e
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                raise RateLimitError(
                    f"Zhipu AI rate limit exceeded",
                    provider=self.config.provider.value,
                ) from e
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
        Send a streaming query to Zhipu AI.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Additional options

        Yields:
            StreamChunk objects as they arrive
        """
        if self._use_openai_compat:
            async for chunk in self._stream_openai(messages, tools, **kwargs):
                yield chunk
        else:
            async for chunk in self._stream_zhipu(messages, tools, **kwargs):
                yield chunk

    async def _stream_openai(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream using OpenAI-compatible API for GLM-4.7+"""
        if not self._openai_client:
            await self.initialize()

        glm_messages = self._convert_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": glm_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }

        try:
            stream = await self._openai_client.chat.completions.create(
                **request_params,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        delta=chunk.choices[0].delta.content,
                        finish_reason=None,
                    )
                if chunk.choices and chunk.choices[0].finish_reason:
                    yield StreamChunk(
                        content="",
                        delta="",
                        finish_reason=chunk.choices[0].finish_reason,
                    )
                    break
        except Exception as e:
            raise ProviderAPIError(
                f"Streaming error from GLM API: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    async def _stream_zhipu(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream using legacy zhipuai API"""
        if not self._zhipu_client:
            await self.initialize()

        glm_messages = self._convert_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": glm_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }

        try:
            response = await asyncio.to_thread(
                self._zhipu_client.chat.completions.create,
                **request_params,
            )

            for chunk in response:
                if hasattr(chunk, "choices") and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                        content = choice.delta.content or ""
                        if content:
                            yield StreamChunk(
                                content=content,
                                delta=content,
                                finish_reason=None,
                            )

                    if hasattr(choice, "finish_reason") and choice.finish_reason:
                        yield StreamChunk(
                            content="",
                            delta="",
                            finish_reason=choice.finish_reason,
                        )
                        break

        except Exception as e:
            raise ProviderAPIError(
                f"Streaming error from {self.config.provider}: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    def _convert_messages(self, messages: List[LLMMessage]) -> List[dict]:
        """Convert LLMMessage to GLM format."""
        glm_messages = []
        for msg in messages:
            glm_messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        return glm_messages

    def _parse_response(self, response) -> "LLMResponse":
        """Parse GLM response to LLMResponse."""
        from ..base import LLMResponse

        choice = response.choices[0]
        message = choice.message

        # Extract content
        content = message.content or ""

        # Extract usage
        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

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

        return LLMResponse(
            content=content,
            finish_reason=choice.finish_reason,
            usage=usage,
            model=response.model,
            extra=extra,
        )

    def supports_tool_calling(self) -> bool:
        """Check if GLM supports tool calling (yes, for GLM-4)."""
        return self.config.model.startswith("glm-4")

    def supports_streaming(self) -> bool:
        """Check if GLM supports streaming (yes, it does)."""
        return True

    def get_provider_info(self) -> dict[str, Any]:
        """Get GLM provider information."""
        return {
            "name": "Zhipu AI",
            "type": self.config.provider.value,
            "models": [
                "glm-4.7",
                "glm-4.7-flashx",
                "glm-4.7-flash",
                "glm-4-plus",
                "glm-4",
                "glm-3-turbo",
            ],
            "capabilities": ["tool-calling", "streaming", "function-calling", "thinking"],
            "max_tokens": 128000,
            "website": "https://open.bigmodel.cn",
            "docs": "https://docs.z.ai/guides/llm/glm-4.7",
            "api_endpoint": "https://api.z.ai/api/paas/v4/",
        }
