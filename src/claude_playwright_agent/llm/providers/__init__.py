"""
LLM provider implementations.

Includes Anthropic (Claude), OpenAI (GPT), and Zhipu AI (GLM) providers.
"""

from .anthropic import AnthropicProvider
from .glm import GLMProvider
from .openai import OpenAIProvider
from .registry import ProviderRegistry

# Import base types for registration
from claude_playwright_agent.llm.base import LLMProviderType

# Register built-in providers
ProviderRegistry.register(LLMProviderType.ANTHROPIC, AnthropicProvider)
ProviderRegistry.register(LLMProviderType.OPENAI, OpenAIProvider)
ProviderRegistry.register(LLMProviderType.GLM, GLMProvider)

__all__ = [
    "AnthropicProvider",
    "OpenAIProvider",
    "GLMProvider",
    "ProviderRegistry",
]
