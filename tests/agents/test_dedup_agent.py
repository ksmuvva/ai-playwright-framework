"""
Tests for the Deduplication Agent.

Tests cover:
- DeduplicationAgent initialization
- Analyzing patterns across recordings
- Generating page object files
- Error handling
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.dedup_agent import DeduplicationAgent


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_RECORDINGS = [
    {
        "file_path": "test1.js",
        "test_name": "login test",
        "actions": [
            {
                "action_type": "fill",
                "selector": {
                    "raw": "getByLabel('Email')",
                    "type": "getByLabel",
                    "value": "Email",
                    "attributes": {},
                },
            },
            {
                "action_type": "fill",
                "selector": {
                    "raw": "getByLabel('Password')",
                    "type": "getByLabel",
                    "value": "Password",
                    "attributes": {},
                },
            },
        ],
        "urls_visited": ["https://example.com/login"],
    },
    {
        "file_path": "test2.js",
        "test_name": "register test",
        "actions": [
            {
                "action_type": "fill",
                "selector": {
                    "raw": "getByLabel('Email')",
                    "type": "getByLabel",
                    "value": "Email",
                    "attributes": {},
                },
            },
            {
                "action_type": "fill",
                "selector": {
                    "raw": "getByLabel('Password')",
                    "type": "getByLabel",
                    "value": "Password",
                    "attributes": {},
                },
            },
        ],
        "urls_visited": ["https://example.com/register"],
    },
]


# =============================================================================
# DeduplicationAgent Tests
# =============================================================================


class TestDeduplicationAgent:
    """Tests for DeduplicationAgent class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test agent initialization."""
        agent = DeduplicationAgent(tmp_path)

        assert agent._project_path == tmp_path
        assert agent._generator is not None

    def test_initialization_without_path(self) -> None:
        """Test agent initialization without path."""
        agent = DeduplicationAgent()

        assert agent._project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_process_analyzes_patterns(self, tmp_path: Path) -> None:
        """Test processing recordings for pattern analysis."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recordings": SAMPLE_RECORDINGS,
        })

        assert result["success"] is True
        assert "selector_patterns" in result
        assert "page_objects" in result
        assert "statistics" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_with_empty_recordings(self, tmp_path: Path) -> None:
        """Test processing with empty recordings list."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({"recordings": []})

        assert result["success"] is False
        assert "error" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_without_recordings(self, tmp_path: Path) -> None:
        """Test processing without recordings key."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({})

        assert result["success"] is False
        assert "error" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_analyze_patterns_method(self, tmp_path: Path) -> None:
        """Test the analyze_patterns method."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.analyze_patterns(SAMPLE_RECORDINGS)

        assert result["success"] is True
        assert "selector_patterns" in result
        assert "statistics" in result

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_generate_page_objects_creates_files(self, tmp_path: Path) -> None:
        """Test generating page object files."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        output_dir = tmp_path / "pages"

        result = await agent.generate_page_objects(
            SAMPLE_RECORDINGS,
            output_dir,
        )

        assert result["success"] is True
        assert "files_created" in result
        assert output_dir.exists()

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_generate_page_objects_code(self, tmp_path: Path) -> None:
        """Test that page objects include generated code."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recordings": SAMPLE_RECORDINGS,
        })

        assert result["success"] is True

        # Check that page objects code is included
        page_objects_code = result.get("page_objects_code", [])
        assert isinstance(page_objects_code, list)

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_statistics_are_calculated(self, tmp_path: Path) -> None:
        """Test that statistics are calculated correctly."""
        agent = DeduplicationAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "recordings": SAMPLE_RECORDINGS,
        })

        assert result["success"] is True

        stats = result["statistics"]
        assert stats["total_recordings"] == 2
        assert "unique_selectors" in stats
        assert "repeated_selectors" in stats

        await agent.cleanup()
