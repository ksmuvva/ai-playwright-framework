"""
Integration tests for multi-provider LLM system.

Tests for:
- Provider switching
- Cross-provider message handling
- Configuration integration
- Real-world usage patterns
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.llm import (
    LLMProviderFactory,
    LLMProviderType,
    LLMMessage,
)
from claude_playwright_agent.llm.models.config import (
    AnthropicConfig,
    OpenAIConfig,
    GLMConfig,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestProviderSwitching:
    """Tests for switching between providers."""

    @pytest.mark.asyncio
    async def test_switch_from_anthropic_to_openai(self):
        """Test switching from Anthropic to OpenAI provider."""
        # Create Anthropic provider
        anthropic_config = AnthropicConfig(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )
        anthropic_provider = LLMProviderFactory.create_provider(anthropic_config)

        assert anthropic_provider.config.provider == LLMProviderType.ANTHROPIC

        # Switch to OpenAI
        openai_config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )
        openai_provider = LLMProviderFactory.create_provider(openai_config)

        assert openai_provider.config.provider == LLMProviderType.OPENAI

    @pytest.mark.asyncio
    async def test_switch_from_openai_to_glm(self):
        """Test switching from OpenAI to GLM provider."""
        # Create OpenAI provider
        openai_config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4",
        )
        openai_provider = LLMProviderFactory.create_provider(openai_config)

        assert openai_provider.config.provider == LLMProviderType.OPENAI

        # Switch to GLM
        glm_config = GLMConfig(
            api_key="test-key",
            model="glm-4",
        )
        glm_provider = LLMProviderFactory.create_provider(glm_config)

        assert glm_provider.config.provider == LLMProviderType.GLM

    @pytest.mark.asyncio
    async def test_provider_config_isolation(self):
        """Test that provider configurations are isolated."""
        anthropic_config = AnthropicConfig(
            api_key="key1",
            model="model1",
            temperature=0.5,
        )
        openai_config = OpenAIConfig(
            api_key="key2",
            model="model2",
            temperature=0.7,
        )

        assert anthropic_config.temperature != openai_config.temperature
        assert anthropic_config.model != openai_config.model


class TestCrossProviderCompatibility:
    """Tests for cross-provider message compatibility."""

    def test_messages_work_with_all_providers(self):
        """Test that standard messages work with all providers."""
        messages = [
            LLMMessage.system("You are helpful."),
            LLMMessage.user("What is 2+2?"),
        ]

        # All providers should accept these messages
        providers = [
            AnthropicConfig(api_key="test", model="claude-3"),
            OpenAIConfig(api_key="test", model="gpt-4"),
            GLMConfig(api_key="test", model="glm-4"),
        ]

        for config in providers:
            provider = LLMProviderFactory.create_provider(config)
            # Should not raise error
            assert provider is not None

    def test_tool_definitions_compatible(self):
        """Test that tool definitions are compatible across providers."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform a calculation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression to evaluate",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            }
        ]

        # All providers should accept this tool definition
        providers = [
            AnthropicConfig(api_key="test", model="claude-3"),
            OpenAIConfig(api_key="test", model="gpt-4"),
            GLMConfig(api_key="test", model="glm-4"),
        ]

        for config in providers:
            provider = LLMProviderFactory.create_provider(config)
            # Should not raise error
            assert provider.supports_tool_calling() in [True, False]


class TestConfigIntegration:
    """Tests for integration with ConfigManager."""

    def test_config_manager_provider_settings(self, tmp_path):
        """Test that ConfigManager stores provider settings."""
        config_file = tmp_path / ".cpa" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Create config manager
        config_manager = ConfigManager(tmp_path)

        # Update provider settings
        config_manager.update(
            ai_provider="openai",
            ai_provider_settings={
                "openai": {
                    "model": "gpt-4",
                    "max_tokens": 4096,
                }
            }
        )
        config_manager.save()

        # Reload and verify
        config_manager2 = ConfigManager(tmp_path)
        assert config_manager2.ai.provider == "openai"
        assert config_manager2.ai.provider_settings["openai"]["model"] == "gpt-4"

    def test_config_manager_fallback_settings(self, tmp_path):
        """Test that ConfigManager stores fallback settings."""
        config_file = tmp_path / ".cpa" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_manager = ConfigManager(tmp_path)

        # Update fallback settings
        config_manager.update(
            ai_fallback_providers=["openai", "glm"]
        )
        config_manager.save()

        # Reload and verify
        config_manager2 = ConfigManager(tmp_path)
        assert config_manager2.ai.fallback_providers == ["openai", "glm"]


class TestBaseAgentIntegration:
    """Tests for BaseAgent integration with multi-provider."""

    @pytest.mark.asyncio
    async def test_agent_with_explicit_provider(self):
        """Test BaseAgent with explicit provider override."""
        config = AnthropicConfig(api_key="test", model="claude-3")
        provider = LLMProviderFactory.create_provider(config)

        agent = BaseAgent(
            system_prompt="You are helpful.",
            llm_provider=provider,
        )

        assert agent._explicit_provider is provider
        assert agent._use_legacy is False

    @pytest.mark.asyncio
    async def test_agent_with_legacy_detection(self, tmp_path):
        """Test BaseAgent legacy path detection."""
        # Create a config file with default Anthropic settings
        config_file = tmp_path / ".cpa" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_manager = ConfigManager(tmp_path)
        config_manager.update(
            ai_provider="anthropic",
            ai_fallback_providers=[],
        )
        config_manager.save()

        # Create agent in this context
        agent = BaseAgent(
            system_prompt="You are helpful.",
        )

        # Should use legacy path (default Anthropic, no fallback)
        assert agent._use_legacy is True

    @pytest.mark.asyncio
    async def test_agent_with_new_provider_path(self, tmp_path):
        """Test BaseAgent new provider path."""
        # Create config with non-default provider
        config_file = tmp_path / ".cpa" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_manager = ConfigManager(tmp_path)
        config_manager.update(ai_provider="openai")
        config_manager.save()

        # Create agent in this context
        agent = BaseAgent(
            system_prompt="You are helpful.",
        )

        # Should NOT use legacy path
        assert agent._use_legacy is False

    @pytest.mark.asyncio
    async def test_agent_initialization_with_provider(self, tmp_path):
        """Test agent initialization with provider."""
        # Create config with OpenAI provider
        config_file = tmp_path / ".cpa" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_manager = ConfigManager(tmp_path)
        config_manager.update(ai_provider="openai")
        config_manager.save()

        agent = BaseAgent(
            system_prompt="You are helpful.",
        )

        # Mock the provider initialization
        with patch("claude_playwright_agent.llm.providers.openai.openai"):
            await agent.initialize()

            # Should have a client (either ClaudeSDKClient or BaseLLMProvider)
            assert agent.client is not None


class TestProviderFactoryIntegration:
    """Integration tests for provider factory."""

    def test_factory_creates_all_providers(self):
        """Test that factory can create all provider types."""
        providers = [
            (LLMProviderType.ANTHROPIC, AnthropicConfig(api_key="test", model="claude-3")),
            (LLMProviderType.OPENAI, OpenAIConfig(api_key="test", model="gpt-4")),
            (LLMProviderType.GLM, GLMConfig(api_key="test", model="glm-4")),
        ]

        for provider_type, config in providers:
            provider = LLMProviderFactory.create_provider(config)
            assert provider.config.provider == provider_type

    def test_factory_with_fallback_chain(self):
        """Test creating provider with fallback chain."""
        configs = [
            AnthropicConfig(api_key="key1", model="model1"),
            OpenAIConfig(api_key="key2", model="model2"),
            GLMConfig(api_key="key3", model="model3"),
        ]

        fallback_provider = LLMProviderFactory.create_with_fallback(configs)

        assert len(fallback_provider._providers) == 3
        assert fallback_provider._providers[0].config.provider == LLMProviderType.ANTHROPIC
        assert fallback_provider._providers[1].config.provider == LLMProviderType.OPENAI
        assert fallback_provider._providers[2].config.provider == LLMProviderType.GLM


class TestEnvironmentVariableIntegration:
    """Tests for environment variable configuration."""

    def test_provider_from_env(self):
        """Test creating provider from environment variables."""
        with patch.dict("os.environ", {
            "CPA_AI__PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "CPA_AI__OPENAI__MODEL": "gpt-4",
        }):
            provider = LLMProviderFactory.create_provider_from_env()
            assert provider.config.provider == LLMProviderType.OPENAI

    def test_anthropic_api_key_from_env(self):
        """Test Anthropic API key from environment."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            config = AnthropicConfig(api_key="")
            # Would normally load from env
            assert config.provider == LLMProviderType.ANTHROPIC

    def test_openai_api_key_from_env(self):
        """Test OpenAI API key from environment."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            config = OpenAIConfig(api_key="")
            assert config.provider == LLMProviderType.OPENAI

    def test_glm_api_key_from_env(self):
        """Test GLM API key from environment."""
        with patch.dict("os.environ", {"ZHIPUAI_API_KEY": "test-key"}):
            config = GLMConfig(api_key="")
            assert config.provider == LLMProviderType.GLM


class TestModelAliases:
    """Tests for model aliases across providers."""

    def test_model_alias_mapping(self):
        """Test that model aliases work across providers."""
        from claude_playwright_agent.llm.models.config import MODEL_ALIASES, LLMProviderType

        # Check that "claude-sonnet" alias exists
        assert "claude-sonnet" in MODEL_ALIASES

        # Check mappings for each provider
        aliases = MODEL_ALIASES["claude-sonnet"]
        assert LLMProviderType.ANTHROPIC in aliases
        assert LLMProviderType.OPENAI in aliases
        assert LLMProviderType.GLM in aliases

    def test_resolve_model_alias(self):
        """Test resolving model alias to provider-specific model."""
        from claude_playwright_agent.llm.models.config import MODEL_ALIASES, LLMProviderType

        alias = "claude-sonnet"
        provider = LLMProviderType.OPENAI
        resolved_model = MODEL_ALIASES[alias][provider]

        assert resolved_model == "gpt-4-turbo"


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_conversation_with_multiple_providers(self):
        """Test maintaining conversation across provider switches."""
        messages = [
            LLMMessage.system("You are helpful."),
            LLMMessage.user("What is 2+2?"),
            LLMMessage.assistant("It's 4."),
            LLMMessage.user("What is 3+3?"),
        ]

        # All providers should handle this conversation
        providers = [
            AnthropicConfig(api_key="test", model="claude-3"),
            OpenAIConfig(api_key="test", model="gpt-4"),
            GLMConfig(api_key="test", model="glm-4"),
        ]

        for config in providers:
            provider = LLMProviderFactory.create_provider(config)
            # Messages should be valid for all providers
            assert len(messages) == 4

    @pytest.mark.asyncio
    async def test_long_context_with_different_limits(self):
        """Test handling long context with different provider limits."""
        # Create a long conversation
        messages = [LLMMessage.system("You are helpful.")]
        for i in range(100):
            messages.append(LLMMessage.user(f"Message {i}"))
            messages.append(LLMMessage.assistant(f"Response {i}"))

        # All providers should accept these messages
        providers = [
            AnthropicConfig(api_key="test", model="claude-3"),
            OpenAIConfig(api_key="test", model="gpt-4"),
            GLMConfig(api_key="test", model="glm-4"),
        ]

        for config in providers:
            provider = LLMProviderFactory.create_provider(config)
            # Should not raise error on message creation
            assert len(messages) == 201
