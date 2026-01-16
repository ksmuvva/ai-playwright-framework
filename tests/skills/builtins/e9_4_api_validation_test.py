"""Unit tests for E9.4 - API Validation skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e9_4_api_validation import (
    APIResponse,
    APISchema,
    APIValidationAgent,
    ValidationError,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestAPISchema:
    @pytest.mark.unit
    def test_api_schema_creation(self):
        schema = APISchema(
            schema_id="sch_001",
            endpoint="/api/login",
            method="POST",
        )
        assert schema.endpoint == "/api/login"


class TestAPIResponse:
    @pytest.mark.unit
    def test_api_response_creation(self):
        response = APIResponse(
            response_id="resp_001",
            status_code=200,
            body={"success": True},
        )
        assert response.status_code == 200


class TestValidationError:
    @pytest.mark.unit
    def test_validation_error_creation(self):
        error = ValidationError(
            error_id="err_001",
            field="username",
            message="Required",
        )
        assert error.field == "username"


class TestAPIValidationAgent:
    @pytest.fixture
    def agent(self):
        return APIValidationAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e9_4_api_validation"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_schema(self, agent):
        context = {"schema": {"type": "object"}, "data": {}}
        result = await agent.run("validate", context)
        assert "valid" in result.lower() or "schema" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_response(self, agent):
        context = {"response": {"status": 200}, "schema": {}}
        result = await agent.run("validate_response", context)
        assert "response" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_check_contract(self, agent):
        context = {"endpoint": "/api/users", "response": {}}
        result = await agent.run("check_contract", context)
        assert "contract" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
