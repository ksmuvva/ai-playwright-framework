"""Unit tests for E8.2 - Interactive Prompts skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e8_2_interactive_prompts import (
    InteractivePromptsAgent,
    PromptConfig,
    PromptResponse,
    PromptType,
    WizardContext,
    WizardStatus,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestPromptType:
    @pytest.mark.unit
    def test_prompt_type_values(self):
        assert PromptType.TEXT.value == "text"
        assert PromptType.CONFIRMATION.value == "confirmation"


class TestPromptResponse:
    @pytest.mark.unit
    def test_prompt_response_creation(self):
        response = PromptResponse(
            response_id="resp_001",
            prompt_type=PromptType.TEXT,
            value="test",
        )
        assert response.response_id == "resp_001"


class TestPromptConfig:
    @pytest.mark.unit
    def test_prompt_config_creation(self):
        config = PromptConfig(
            prompt_type=PromptType.TEXT,
            message="Enter value:",
        )
        assert config.message == "Enter value:"


class TestWizardStatus:
    @pytest.mark.unit
    def test_wizard_status_values(self):
        assert WizardStatus.IN_PROGRESS.value == "in_progress"


class TestWizardContext:
    @pytest.mark.unit
    def test_wizard_context_creation(self):
        context = WizardContext(
            context_id="wiz_001",
            workflow_id="wf_001",
        )
        assert context.context_id == "wiz_001"


class TestInteractivePromptsAgent:
    @pytest.fixture
    def agent(self):
        return InteractivePromptsAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e8_2_interactive_prompts"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_prompt(self, agent):
        context = {"message": "Enter value:"}
        result = await agent.run("prompt", context)
        assert "prompt" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_confirm(self, agent):
        context = {"message": "Continue?"}
        result = await agent.run("confirm", context)
        assert "confirm" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_start_wizard(self, agent):
        context = {"wizard_name": "setup"}
        result = await agent.run("start_wizard", context)
        assert "wizard" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
