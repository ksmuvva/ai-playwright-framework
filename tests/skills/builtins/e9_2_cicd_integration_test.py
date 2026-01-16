"""Unit tests for E9.2 - CI/CD Integration skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e9_2_cicd_integration import (
    CICDIntegrationAgent,
    PipelineConfig,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestPipelineConfig:
    @pytest.mark.unit
    def test_pipeline_config_creation(self):
        config = PipelineConfig(
            config_id="cfg_001",
            platform="github",
            pipeline_name="test-pipeline",
        )
        assert config.platform == "github"


class TestCICDIntegrationAgent:
    @pytest.fixture
    def agent(self):
        return CICDIntegrationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e9_2_cicd_integration"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_github_actions(self, agent):
        context = {"workflow_name": "test"}
        result = await agent.run("generate_github", context)
        assert "github" in result.lower() or "generated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_gitlab_ci(self, agent):
        context = {"workflow_name": "test"}
        result = await agent.run("generate_gitlab", context)
        assert "gitlab" in result.lower() or "generated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_generate_jenkins(self, agent):
        context = {"job_name": "test"}
        result = await agent.run("generate_jenkins", context)
        assert "jenkins" in result.lower() or "generated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
