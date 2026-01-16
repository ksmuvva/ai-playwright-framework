"""
Anthropic/Claude provider implementation.

Wraps the existing ClaudeSDKClient to provide a unified interface.
"""

import asyncio
from typing import Any, AsyncIterator, List, Optional

from ..base import BaseLLMProvider, LLMConfig, LLMMessage, LLMProviderType, StreamChunk
from ..exceptions import ProviderAPIError, ProviderTimeoutError
from ..models.config import AnthropicConfig


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic/Claude provider implementation.

    Wraps the existing claude_agent_sdk.ClaudeSDKClient to provide
    a unified interface compatible with other LLM providers.

    This provider maintains backward compatibility with the existing
    Claude-based implementation while enabling multi-provider support.
    """

    def __init__(self, config: AnthropicConfig) -> None:
        """
        Initialize the Anthropic provider.

        Args:
            config: Anthropic-specific configuration
        """
        super().__init__(config)
        self._claude_client = None
        self._sdk_options = None

    async def initialize(self) -> None:
        """
        Initialize the Claude SDK client.

        Creates a ClaudeSDKClient instance with the appropriate configuration.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        # Build system prompt from messages (will be passed in query)
        system_prompt = ""

        # Create SDK options
        self._sdk_options = ClaudeAgentOptions(
            system_prompt=system_prompt,
        )

        # Initialize the client
        self._claude_client = ClaudeSDKClient(options=self._sdk_options)
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the Claude SDK client."""
        if self._claude_client:
            # ClaudeSDKClient doesn't have explicit cleanup
            self._claude_client = None
        self._initialized = False

    async def query(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LLMResponse":
        """
        Send a query to Claude and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Additional options (max_tokens, temperature, etc.)

        Returns:
            LLMResponse with Claude's response

        Raises:
            ProviderAPIError: If the API returns an error
            ProviderTimeoutError: If the request times out
        """
        if not self._claude_client:
            await self.initialize()

        # Extract system prompt from messages
        system_prompt = ""
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # Update system prompt in SDK options
        self._sdk_options.system_prompt = system_prompt

        # Override max_tokens if provided
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        try:
            # Use the Claude SDK client
            # Note: This is a simplified implementation
            # In practice, we'd need to call the appropriate SDK method
            response_content = await self._simulate_claude_request(
                system_prompt,
                user_messages,
                max_tokens,
            )

            from ..base import LLMResponse
            return LLMResponse(
                content=response_content,
                finish_reason="stop",
                usage={
                    "prompt_tokens": 0,  # SDK would provide this
                    "completion_tokens": 0,
                },
                model=self.config.model,
            )

        except asyncio.TimeoutError as e:
            raise ProviderTimeoutError(
                f"Request to {self.config.provider} timed out",
                provider=self.config.provider.value,
                timeout=self.config.timeout,
            ) from e
        except Exception as e:
            raise ProviderAPIError(
                f"Error from {self.config.provider} API: {str(e)}",
                provider=self.config.provider.value,
            ) from e

    async def _simulate_claude_request(
        self,
        system_prompt: str,
        messages: List[dict],
        max_tokens: int,
    ) -> str:
        """
        Simulate a Claude API request.

        In production, this would use the actual ClaudeSDKClient.
        For now, this is a placeholder that demonstrates the interface.

        TODO: Integrate with actual ClaudeSDKClient API methods
        """
        # This is a placeholder - in production we'd use:
        # response = await self._claude_client.create_message(...)
        # For now, simulate a response
        return "This is a placeholder response from Claude. In production, this would use the actual ClaudeSDKClient."

    async def query_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming query to Claude.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            **kwargs: Additional options

        Yields:
            StreamChunk objects as they arrive

        TODO: Implement streaming using ClaudeSDKClient
        """
        response = await self.query(messages, tools, **kwargs)

        # Yield the full response as a single chunk for now
        # In production, we'd stream actual chunks
        yield StreamChunk(
            content=response.content,
            delta=response.content,
            finish_reason=response.finish_reason,
        )

    def supports_tool_calling(self) -> bool:
        """Check if Claude supports tool calling (yes, it does)."""
        return True

    def supports_streaming(self) -> bool:
        """Check if Claude supports streaming (yes, it does)."""
        return True

    def get_provider_info(self) -> dict[str, Any]:
        """Get Anthropic provider information."""
        return {
            "name": "Anthropic",
            "type": self.config.provider.value,
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307",
            ],
            "capabilities": ["tool-calling", "streaming", "prompt-caching"],
            "max_tokens": 200000,
            "website": "https://www.anthropic.com",
        }
