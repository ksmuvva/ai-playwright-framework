"""Unit tests for E4.2 - Element Deduplication skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e4_2_element_deduplication import (
    ElementCluster,
    ElementDeduplicationAgent,
    SimilarityScore,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestSimilarityScore:
    """Test suite for SimilarityScore dataclass."""

    @pytest.mark.unit
    def test_similarity_score_creation(self):
        """Test creating a similarity score."""
        score = SimilarityScore(
            score_id="score_001",
            selector1="#btn1",
            selector2="#btn2",
            similarity=0.95,
        )

        assert score.score_id == "score_001"
        assert score.selector1 == "#btn1"
        assert score.selector2 == "#btn2"
        assert score.similarity == 0.95


class TestElementCluster:
    """Test suite for ElementCluster dataclass."""

    @pytest.mark.unit
    def test_element_cluster_creation(self):
        """Test creating an element cluster."""
        cluster = ElementCluster(
            cluster_id="cluster_001",
            cluster_type="button",
            selectors=["#btn1", "#btn2", "button[type='submit']"],
        )

        assert cluster.cluster_id == "cluster_001"
        assert cluster.cluster_type == "button"
        assert len(cluster.selectors) == 3


class TestElementDeduplicationAgent:
    """Test suite for ElementDeduplicationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ElementDeduplicationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e4_2_element_deduplication"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_compare_selectors(self, agent):
        """Test comparing two selectors."""
        context = {
            "task_type": "compare_selectors",
            "selector1": "#submit-btn",
            "selector2": "#submit-button",
        }

        result = await agent.run("compare_selectors", context)

        assert "similar" in result.lower() or "score" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_cluster_elements(self, agent):
        """Test clustering similar elements."""
        context = {
            "task_type": "cluster_elements",
            "selectors": ["#btn1", "#btn2", "#submit-btn"],
        }

        result = await agent.run("cluster_elements", context)

        assert "cluster" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_find_representative(self, agent):
        """Test finding representative selector for cluster."""
        context = {
            "task_type": "find_representative",
            "selectors": ["#btn1", "#btn2", "#btn3"],
        }

        result = await agent.run("find_representative", context)

        assert "representative" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
