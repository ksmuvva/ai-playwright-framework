"""
Backward compatibility tests for multi-LLM provider system.

Tests for:
- Existing configs work unchanged
- Default Anthropic path still uses ClaudeSDKClient
- New features are opt-in
- Migration path is smooth
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.agents.base import BaseAgent, get_settings
from claude_playwright_agent.llm import (
    LLMProviderFactory,
    LLMProviderType,
    LLMMessage,
    LLMResponse,
)
from claude_playwright_agent.llm.models.config import AnthropicConfig, ProviderConfig


class ConcreteTestAgent(BaseAgent):
    """Concrete test implementation of BaseAgent for testing."""

    async def process(self, user_input: str, context: dict | None = None) -> str:
        """Process a user input."""
        return f"Processed: {user_input}"


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing configurations."""

    def test_default_config_uses_anthropic(self):
        """Test that default configuration uses Anthropic provider."""
        with patch.dict("os.environ", {}, clear=True):
            config_manager = ConfigManager()
            assert config_manager.ai.provider == "anthropic"

    def test_default_config_no_fallback(self):
        """Test that default configuration has no fallback providers."""
        with patch.dict("os.environ", {}, clear=True):
            config_manager = ConfigManager()
            assert config_manager.ai.fallback_providers == []

    def test_default_config_has_model(self):
        """Test that default configuration has a model set."""
        with patch.dict("os.environ", {}, clear=True):
            config_manager = ConfigManager()
            assert config_manager.ai.model == "claude-3-5-sonnet-20241022"

    def test_existing_config_file_loads(self, tmp_path):
        """Test that existing config files load without errors."""
        # Create an old-style config file
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
  max_tokens: 8192
  temperature: 0.3
  enable_caching: true
  timeout: 120
framework:
  bdd_framework: behave
  language: python
  template: basic
  base_url: http://localhost:8000
  default_timeout: 30000
browser:
  browser: chromium
  headless: true
  viewport_width: 1280
  viewport_height: 720
execution:
  parallel_workers: 1
  retry_failed: 0
  fail_fast: false
  randomize: false
  self_healing: true
  video: false
  screenshots: on-failure
  trace: retain-on-failure
""")

        # Should load without errors
        config_manager = ConfigManager(tmp_path)
        assert config_manager.ai.model == "claude-3-5-sonnet-20241022"

    def test_config_without_provider_field(self, tmp_path):
        """Test that config without provider field defaults to Anthropic."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
  max_tokens: 8192
  temperature: 0.3
""")

        config_manager = ConfigManager(tmp_path)
        # Should default to anthropic
        assert config_manager.ai.provider == "anthropic"


class ConcreteTestAgentBackwardCompatibility:
    """Tests for BaseAgent backward compatibility."""

    @pytest.mark.asyncio
    async def test_agent_without_provider_uses_legacy(self):
        """Test that agent without explicit provider uses legacy path."""
        # Mock settings to simulate default config
        with patch("claude_playwright_agent.agents.base.get_settings") as mock_settings:
            mock_settings.return_value = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8192,
                "temperature": 0.3,
                "enable_caching": True,
                "timeout": 120,
                "provider": "anthropic",
                "fallback_providers": [],
                "provider_settings": {},
            }

            agent = ConcreteTestAgent(system_prompt="You are helpful.")

            # Should use legacy path
            assert agent._use_legacy is True

    @pytest.mark.asyncio
    async def test_agent_with_explicit_provider_uses_new_path(self):
        """Test that agent with explicit provider uses new path."""
        config = ProviderConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test",
            model="claude-3",
        )
        provider = LLMProviderFactory.create_provider(config)

        agent = ConcreteTestAgent(
            system_prompt="You are helpful.",
            llm_provider=provider,
        )

        # Should NOT use legacy path
        assert agent._use_legacy is False
        assert agent._explicit_provider is provider

    @pytest.mark.asyncio
    async def test_agent_with_fallback_uses_new_path(self):
        """Test that agent with fallback configured uses new path."""
        with patch("claude_playwright_agent.agents.base.get_settings") as mock_settings:
            mock_settings.return_value = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8192,
                "temperature": 0.3,
                "enable_caching": True,
                "timeout": 120,
                "provider": "anthropic",
                "fallback_providers": ["openai"],  # Has fallback
                "provider_settings": {},
            }

            agent = ConcreteTestAgent(system_prompt="You are helpful.")

            # Should NOT use legacy path (has fallback)
            assert agent._use_legacy is False

    @pytest.mark.asyncio
    async def test_agent_with_non_anthropic_provider(self):
        """Test that agent with non-Anthropic provider uses new path."""
        with patch("claude_playwright_agent.agents.base.get_settings") as mock_settings:
            mock_settings.return_value = {
                "model": "gpt-4",
                "max_tokens": 4096,
                "temperature": 0.7,
                "enable_caching": False,
                "timeout": 60,
                "provider": "openai",  # Not Anthropic
                "fallback_providers": [],
                "provider_settings": {},
            }

            agent = ConcreteTestAgent(system_prompt="You are helpful.")

            # Should NOT use legacy path
            assert agent._use_legacy is False


class TestLegacyClaudeSDKClient:
    """Tests for legacy ClaudeSDKClient path."""

    @pytest.mark.asyncio
    async def test_legacy_path_creates_claude_client(self):
        """Test that legacy path creates ClaudeSDKClient."""
        with patch("claude_playwright_agent.agents.base.get_settings") as mock_settings:
            mock_settings.return_value = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8192,
                "temperature": 0.3,
                "enable_caching": True,
                "timeout": 120,
                "provider": "anthropic",
                "fallback_providers": [],
                "provider_settings": {},
            }

            agent = ConcreteTestAgent(system_prompt="You are helpful.")

            with patch("claude_playwright_agent.agents.base.ClaudeSDKClient") as mock_client:
                await agent.initialize()

                # Should have created ClaudeSDKClient
                assert agent.client is not None

    @pytest.mark.asyncio
    async def test_legacy_path_cleanup(self):
        """Test that legacy path cleanup works."""
        with patch("claude_playwright_agent.agents.base.get_settings") as mock_settings:
            mock_settings.return_value = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8192,
                "temperature": 0.3,
                "enable_caching": True,
                "timeout": 120,
                "provider": "anthropic",
                "fallback_providers": [],
                "provider_settings": {},
            }

            agent = ConcreteTestAgent(system_prompt="You are helpful.")

            with patch("claude_playwright_agent.agents.base.ClaudeSDKClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.__aexit__ = AsyncMock()
                mock_client.return_value = mock_instance

                await agent.initialize()
                await agent.cleanup()

                # Cleanup should have been called
                mock_instance.__aexit__.assert_called_once()


class TestSettingsFunction:
    """Tests for get_settings function backward compatibility."""

    def test_settings_function_returns_existing_fields(self):
        """Test that get_settings returns all existing fields."""
        settings = get_settings()

        # Existing fields should be present
        assert "model" in settings
        assert "max_tokens" in settings
        assert "temperature" in settings
        assert "enable_caching" in settings
        assert "timeout" in settings

    def test_settings_function_returns_new_fields(self):
        """Test that get_settings returns new provider fields."""
        settings = get_settings()

        # New fields should be present
        assert "provider" in settings
        assert "fallback_providers" in settings
        assert "provider_settings" in settings


class TestConfigMigration:
    """Tests for configuration migration path."""

    def test_old_config_values_preserved(self, tmp_path):
        """Test that old config values are preserved."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-opus-20240229
  max_tokens: 4096
  temperature: 0.5
  enable_caching: false
  timeout: 60
""")

        config_manager = ConfigManager(tmp_path)

        # Old values should be preserved
        assert config_manager.ai.model == "claude-3-opus-20240229"
        assert config_manager.ai.max_tokens == 4096
        assert config_manager.ai.temperature == 0.5
        assert config_manager.ai.enable_caching is False
        assert config_manager.ai.timeout == 60

    def test_new_config_fields_have_defaults(self, tmp_path):
        """Test that new config fields have sensible defaults."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
""")

        config_manager = ConfigManager(tmp_path)

        # New fields should have defaults
        assert config_manager.ai.provider == "anthropic"
        assert config_manager.ai.fallback_providers == []
        assert config_manager.ai.provider_settings == {}

    def test_can_add_new_fields_to_old_config(self, tmp_path):
        """Test that new fields can be added to old config."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create old config
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
  max_tokens: 8192
""")

        # Load and add new fields
        config_manager = ConfigManager(tmp_path)
        config_manager.update(
            ai_provider="openai",
            ai_fallback_providers=["anthropic"],
        )
        config_manager.save()

        # Reload and verify
        config_manager2 = ConfigManager(tmp_path)
        assert config_manager2.ai.provider == "openai"
        assert config_manager2.ai.fallback_providers == ["anthropic"]
        # Old fields should still be there
        assert config_manager2.ai.model == "claude-3-5-sonnet-20241022"


class TestOptInNewFeatures:
    """Tests that new features are opt-in."""

    def test_multi_provider_is_opt_in(self, tmp_path):
        """Test that multi-provider is opt-in."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Old config without provider field
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
""")

        config_manager = ConfigManager(tmp_path)

        # Should default to single provider (anthropic)
        assert config_manager.ai.provider == "anthropic"
        assert len(config_manager.ai.fallback_providers) == 0

    def test_fallback_is_opt_in(self, tmp_path):
        """Test that fallback is opt-in."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
""")

        config_manager = ConfigManager(tmp_path)

        # Should have no fallback by default
        assert len(config_manager.ai.fallback_providers) == 0

    def test_new_provider_settings_are_opt_in(self, tmp_path):
        """Test that provider settings are opt-in."""
        config_dir = tmp_path / ".cpa"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("""
ai:
  model: claude-3-5-sonnet-20241022
""")

        config_manager = ConfigManager(tmp_path)

        # Should have empty provider settings by default
        assert config_manager.ai.provider_settings == {}


class TestAgentTypeCompatibility:
    """Tests for agent client type compatibility."""

    @pytest.mark.asyncio
    async def test_agent_accepts_both_client_types(self):
        """Test that agent accepts both ClaudeSDKClient and BaseLLMProvider."""
        # Legacy client type
        with patch("claude_playwright_agent.agents.base.ClaudeSDKClient"):
            agent1 = ConcreteTestAgent(system_prompt="You are helpful.")
            agent1.client = None  # Would be ClaudeSDKClient
            assert agent1.client is None

        # New provider type
        config = ProviderConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test",
            model="claude-3",
        )
        provider = LLMProviderFactory.create_provider(config)
        agent2 = ConcreteTestAgent(
            system_prompt="You are helpful.",
            llm_provider=provider,
        )
        assert agent2._explicit_provider is provider


class TestMessageCompatibility:
    """Tests for message format compatibility."""

    def test_legacy_message_format_works(self):
        """Test that legacy message format still works."""
        # Old-style message creation
        message = LLMMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_message_to_dict_compatibility(self):
        """Test that message to_dict is compatible with old code."""
        message = LLMMessage(role="user", content="Hello")
        message_dict = message.to_dict()

        # Should have the expected keys
        assert "role" in message_dict
        assert "content" in message_dict
        assert message_dict["role"] == "user"
        assert message_dict["content"] == "Hello"


class TestResponseCompatibility:
    """Tests for response format compatibility."""

    def test_legacy_response_format_works(self):
        """Test that legacy response format still works."""
        from claude_playwright_agent.llm.base import LLMResponse

        response = LLMResponse(content="Hello")
        assert response.content == "Hello"
        assert response.finish_reason is None
        assert response.usage == {}

    def test_response_total_tokens_compatibility(self):
        """Test that total_tokens calculation is backward compatible."""
        response = LLMResponse(
            content="Hello",
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert response.total_tokens == 15
