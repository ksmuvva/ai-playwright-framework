"""Unit tests for E6.2 - Network Recording skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e6_2_network_recording import (
    MockRule,
    NetworkRecordingAgent,
    NetworkRequest,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestNetworkRequest:
    """Test suite for NetworkRequest dataclass."""

    @pytest.mark.unit
    def test_network_request_creation(self):
        """Test creating a network request."""
        request = NetworkRequest(
            request_id="req_001",
            method="POST",
            url="https://api.example.com/login",
            status_code=200,
        )

        assert request.request_id == "req_001"
        assert request.method == "POST"
        assert request.status_code == 200


class TestMockRule:
    """Test suite for MockRule dataclass."""

    @pytest.mark.unit
    def test_mock_rule_creation(self):
        """Test creating a mock rule."""
        rule = MockRule(
            rule_id="rule_001",
            url_pattern="/api/*",
            response_status=200,
            response_body={"success": True},
        )

        assert rule.rule_id == "rule_001"
        assert rule.response_status == 200


class TestNetworkRecordingAgent:
    """Test suite for NetworkRecordingAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return NetworkRecordingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e6_2_network_recording"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_record_har(self, agent):
        """Test recording HAR file."""
        context = {
            "task_type": "record_har",
        }

        result = await agent.run("record_har", context)

        assert "har" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_mock_request(self, agent):
        """Test mocking a request."""
        context = {
            "task_type": "mock_request",
            "url_pattern": "/api/login",
            "response": {"token": "abc123"},
        }

        result = await agent.run("mock_request", context)

        assert "mock" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_intercept_request(self, agent):
        """Test intercepting a request."""
        context = {
            "task_type": "intercept",
            "url_pattern": "/api/*",
        }

        result = await agent.run("intercept", context)

        assert "intercept" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
