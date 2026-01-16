"""Unit tests for E3.1 - Ingestion Agent skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e3_1_ingestion_agent import (
    IngestionAgent,
    IngestionContext,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestIngestionContext:
    """Test suite for IngestionContext dataclass."""

    @pytest.mark.unit
    def test_ingestion_context_creation(self):
        """Test creating an ingestion context."""
        context = IngestionContext(
            workflow_id="wf_001",
            recording_path="/tmp/recording.js",
            recording_name="Test Recording",
        )

        assert context.workflow_id == "wf_001"
        assert context.recording_path == "/tmp/recording.js"
        assert context.pipeline_stage == "initialized"

    @pytest.mark.unit
    def test_ingestion_context_advance_stage(self):
        """Test advancing pipeline stage."""
        context = IngestionContext(
            workflow_id="wf_001",
        )

        context.advance_stage("parsing")

        assert context.pipeline_stage == "parsing"
        assert "initialized" in context.previous_context
        assert "entered_parsing_at" in context.metadata


class TestIngestionAgent:
    """Test suite for IngestionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return IngestionAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert hasattr(agent, "description")
        assert agent.name == "e3_1_ingestion_agent"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_ingest_recording(self, agent, temp_project_path):
        """Test ingesting a recording."""
        # Create a sample recording file
        recording_file = temp_project_path / "test_recording.js"
        recording_file.write_text("sample recording content")

        context = {
            "task_type": "ingest_recording",
            "recording_path": str(recording_file),
            "workflow_id": "wf_001",
        }

        result = await agent.run("ingest_recording", context)

        assert "ingested" in result.lower() or "recording" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_validate_recording(self, agent, temp_project_path):
        """Test validating a recording."""
        recording_file = temp_project_path / "test_recording.js"
        recording_file.write_text("sample recording content")

        context = {
            "task_type": "validate_recording",
            "recording_path": str(recording_file),
        }

        result = await agent.run("validate_recording", context)

        assert "valid" in result.lower() or "recording" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_extract_metadata(self, agent, temp_project_path):
        """Test extracting recording metadata."""
        recording_file = temp_project_path / "test_recording.js"
        recording_file.write_text("sample recording content")

        context = {
            "task_type": "extract_metadata",
            "recording_path": str(recording_file),
        }

        result = await agent.run("extract_metadata", context)

        assert "metadata" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent, temp_project_path):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_get_ingestion_history(self, agent):
        """Test getting ingestion history."""
        result = agent.get_ingestion_history()

        assert isinstance(result, list)
