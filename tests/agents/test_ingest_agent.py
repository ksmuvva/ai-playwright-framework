"""
Tests for the Ingestion Agent.

Tests cover:
- IngestionAgent initialization
- Processing Playwright recording files
- Error handling for missing files
- Integration with PlaywrightParser
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.ingest_agent import IngestionAgent


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_RECORDING = """// @ts-check
const { test, expect } = require('@playwright/test');

test('login test', async ({ page }) => {
  await page.goto('https://example.com/login');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Submit' }).click();
});
"""


# =============================================================================
# IngestionAgent Tests
# =============================================================================


class TestIngestionAgent:
    """Tests for IngestionAgent class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test agent initialization."""
        agent = IngestionAgent(tmp_path)

        assert agent._project_path == tmp_path
        assert agent.system_prompt is not None

    def test_initialization_without_path(self) -> None:
        """Test agent initialization without path."""
        agent = IngestionAgent()

        assert agent._project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_process_recording_file(self, tmp_path: Path) -> None:
        """Test processing a recording file."""
        # Create test recording file
        recording_file = tmp_path / "test.js"
        recording_file.write_text(SAMPLE_RECORDING)

        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(recording_file),
        })

        assert result["success"] is True
        assert result["recording_path"] == str(recording_file)
        assert "parsed_recording" in result
        assert "summary" in result

        # Check summary
        summary = result["summary"]
        assert summary["test_name"] == "login test"
        assert summary["total_actions"] == 5
        assert summary["urls_visited"] == 1

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self, tmp_path: Path) -> None:
        """Test processing a non-existent file."""
        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(tmp_path / "nonexistent.js"),
        })

        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_empty_recording(self, tmp_path: Path) -> None:
        """Test processing an empty recording file."""
        recording_file = tmp_path / "empty.js"
        recording_file.write_text("")

        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(recording_file),
        })

        assert result["success"] is True
        assert result["summary"]["total_actions"] == 0

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_without_recording_path(self, tmp_path: Path) -> None:
        """Test processing without providing recording path."""
        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({})

        assert result["success"] is False
        assert "error" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_returns_parsed_actions(self, tmp_path: Path) -> None:
        """Test that process returns parsed actions."""
        recording_file = tmp_path / "actions.js"
        recording_file.write_text(SAMPLE_RECORDING)

        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(recording_file),
        })

        assert result["success"] is True
        parsed = result["parsed_recording"]
        assert "actions" in parsed

        actions = parsed["actions"]
        assert len(actions) == 5
        assert actions[0]["action_type"] == "goto"
        assert actions[1]["action_type"] == "click"

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_returns_selectors(self, tmp_path: Path) -> None:
        """Test that process returns extracted selectors."""
        recording_file = tmp_path / "selectors.js"
        recording_file.write_text(SAMPLE_RECORDING)

        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(recording_file),
        })

        assert result["success"] is True
        parsed = result["parsed_recording"]
        assert "selectors_used" in parsed

        selectors = parsed["selectors_used"]
        assert len(selectors) >= 3  # At least 3 selectors in sample

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_returns_metadata(self, tmp_path: Path) -> None:
        """Test that process returns metadata."""
        recording_file = tmp_path / "metadata.js"
        recording_file.write_text(SAMPLE_RECORDING)

        agent = IngestionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recording_path": str(recording_file),
        })

        assert result["success"] is True
        parsed = result["parsed_recording"]
        assert "metadata" in parsed

        metadata = parsed["metadata"]
        assert "ts_check" in metadata
        assert "imports" in metadata
        assert "action_counts" in metadata

        await agent.cleanup()
