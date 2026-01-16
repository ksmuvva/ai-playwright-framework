"""Unit tests for E6.1 - Advanced Recording skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e6_1_advanced_recording import (
    AdvancedRecordingAgent,
    RecordingArtifact,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestRecordingArtifact:
    """Test suite for RecordingArtifact dataclass."""

    @pytest.mark.unit
    def test_recording_artifact_creation(self):
        """Test creating a recording artifact."""
        artifact = RecordingArtifact(
            artifact_id="art_001",
            artifact_type="video",
            file_path="/tmp/recording.mp4",
            size_bytes=1024000,
        )

        assert artifact.artifact_id == "art_001"
        assert artifact.artifact_type == "video"
        assert artifact.size_bytes == 1024000


class TestAdvancedRecordingAgent:
    """Test suite for AdvancedRecordingAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return AdvancedRecordingAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert agent.name == "e6_1_advanced_recording"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_start_video_recording(self, agent):
        """Test starting video recording."""
        context = {
            "task_type": "start_video",
            "page_url": "https://example.com",
        }

        result = await agent.run("start_video", context)

        assert "started" in result.lower() or "video" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_capture_screenshot(self, agent):
        """Test capturing screenshot."""
        context = {
            "task_type": "capture_screenshot",
            "selector": "#main-content",
        }

        result = await agent.run("capture_screenshot", context)

        assert "screenshot" in result.lower() or "captured" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_record_trace(self, agent):
        """Test recording trace."""
        context = {
            "task_type": "record_trace",
        }

        result = await agent.run("record_trace", context)

        assert "trace" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()
