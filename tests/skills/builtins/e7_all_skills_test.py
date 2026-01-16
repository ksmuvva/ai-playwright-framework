"""Unit tests for E7-E9 skills - Batch 1 (E7)."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# E7.1
from claude_playwright_agent.skills.builtins.e7_1_skill_registry import SkillRegistryAgent
# E7.2
from claude_playwright_agent.skills.builtins.e7_2_manifest_parser import ManifestParserAgent
# E7.3
from claude_playwright_agent.skills.builtins.e7_3_custom_skill_support import CustomSkillAgent
# E7.4
from claude_playwright_agent.skills.builtins.e7_4_lifecycle_management import SkillLifecycleAgent
# E7.5
from claude_playwright_agent.skills.builtins.e7_5_discovery_documentation import DiscoveryAgent

from claude_playwright_agent.agents.base import BaseAgent


class TestSkillRegistryAgent:
    """Test suite for SkillRegistryAgent."""

    @pytest.fixture
    def agent(self):
        return SkillRegistryAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e7_1_skill_registry"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_register_skill(self, agent):
        context = {"skill_name": "test_skill", "version": "1.0.0"}
        result = await agent.run("register", context)
        assert "registered" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()


class TestManifestParserAgent:
    """Test suite for ManifestParserAgent."""

    @pytest.fixture
    def agent(self):
        return ManifestParserAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e7_2_manifest_parser"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_parse_manifest(self, agent, temp_project_path):
        manifest_file = temp_project_path / "skill.yaml"
        manifest_file.write_text("name: test\nversion: 1.0.0")

        context = {"manifest_path": str(manifest_file)}
        result = await agent.run("parse", context)
        assert "parsed" in result.lower()


class TestCustomSkillAgent:
    """Test suite for CustomSkillAgent."""

    @pytest.fixture
    def agent(self):
        return CustomSkillAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e7_3_custom_skill_support"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_skill(self, agent, temp_project_path):
        context = {
            "skill_name": "custom_skill",
            "output_path": str(temp_project_path),
        }
        result = await agent.run("create", context)
        assert "created" in result.lower()


class TestSkillLifecycleAgent:
    """Test suite for SkillLifecycleAgent."""

    @pytest.fixture
    def agent(self):
        return SkillLifecycleAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e7_4_lifecycle_management"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_load_skill(self, agent):
        context = {"skill_name": "test_skill"}
        result = await agent.run("load", context)
        assert "loaded" in result.lower() or "skill" in result.lower()


class TestDiscoveryAgent:
    """Test suite for DiscoveryAgent."""

    @pytest.fixture
    def agent(self):
        return DiscoveryAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e7_5_discovery_documentation"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_discover_skills(self, agent):
        context = {}
        result = await agent.run("discover", context)
        assert "discover" in result.lower() or "skill" in result.lower()
