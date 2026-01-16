"""
LLM provider exceptions.

Custom exceptions for LLM provider operations.
"""

from typing import Any, Optional


class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize LLM error.

        Args:
            message: Error message
            provider: Provider name where error occurred
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.details = details or {}

    def __str__(self) -> str:
        if self.provider:
            return f"[{self.provider}] {self.message}"
        return self.message


class ProviderNotFoundError(LLMError):
    """Raised when attempting to use an unregistered provider."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' is not registered", provider=provider)


class ProviderConfigError(LLMError):
    """Raised when provider configuration is invalid."""

    def __init__(self, message: str, provider: Optional[str] = None, config_key: Optional[str] = None) -> None:
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, provider=provider, details=details)


class ProviderAPIError(LLMError):
    """Raised when provider API returns an error."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if status_code is not None:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        super().__init__(message, provider=provider, details=details)


class ProviderTimeoutError(LLMError):
    """Raised when provider request times out."""

    def __init__(self, message: str, provider: Optional[str] = None, timeout: Optional[int] = None) -> None:
        details = {"timeout": timeout} if timeout else {}
        super().__init__(message, provider=provider, details=details)


class ProviderConnectionError(LLMError):
    """Raised when unable to connect to provider API."""

    def __init__(self, message: str, provider: Optional[str] = None, endpoint: Optional[str] = None) -> None:
        details = {"endpoint": endpoint} if endpoint else {}
        super().__init__(message, provider=provider, details=details)


class RateLimitError(ProviderAPIError):
    """Raised when provider rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, provider=provider, details=details)


class TokenLimitError(ProviderAPIError):
    """Raised when request exceeds provider token limits."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        limit: Optional[int] = None,
        requested: Optional[int] = None,
    ) -> None:
        details = {}
        if limit is not None:
            details["limit"] = limit
        if requested is not None:
            details["requested"] = requested
        super().__init__(message, provider=provider, details=details)
