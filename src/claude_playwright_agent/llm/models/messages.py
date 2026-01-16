"""
Message and response models for LLM providers.

Unified data structures for messages and responses across providers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..base import LLMMessage, LLMResponse


class MessageRole(str, Enum):
    """Standard message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


class FinishReason(str, Enum):
    """Reasons why a generation finished."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_USES = "tool_calls"
    CONTENT_FILTER = "content_filter"
    RATE_LIMIT = "rate_limit"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ToolCall:
    """
    Represents a tool/function call from the LLM.

    Attributes:
        id: Unique identifier for this tool call
        name: Name of the function to call
        arguments: JSON string of function arguments
    """

    id: str
    name: str
    arguments: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class ToolResult:
    """
    Result of a tool/function execution.

    Attributes:
        tool_call_id: ID of the tool call this result is for
        content: Result content
        is_error: Whether the tool execution resulted in an error
    """

    tool_call_id: str
    content: str
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
        }


@dataclass
class TokenUsage:
    """
    Token usage statistics.

    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total number of tokens
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary format."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "TokenUsage":
        """Create from dictionary."""
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", data.get("prompt_tokens", 0) + data.get("completion_tokens", 0)),
        )


@dataclass
class ProviderResponseMetadata:
    """
    Provider-specific response metadata.

    Attributes:
        raw_response: Raw response from provider API
        headers: Response headers
        request_id: Unique request ID from provider
        extra: Additional provider-specific metadata
    """

    raw_response: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    request_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
