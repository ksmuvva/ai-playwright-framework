"""
Tests for the BDD Conversion Agent.

Tests cover:
- BDDConversionAgent initialization
- Converting parsed recordings to Gherkin
- Generating step definitions
- Saving feature files
- Error handling
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.bdd_agent import BDDConversionAgent


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_PARSED_RECORDING = {
    "file_path": "test.js",
    "test_name": "login test",
    "actions": [
        {
            "action_type": "goto",
            "value": "https://example.com",
            "selector": None,
        },
        {
            "action_type": "fill",
            "value": "user@example.com",
            "selector": {
                "type": "getByLabel",
                "value": "Email",
                "attributes": {},
            },
        },
        {
            "action_type": "click",
            "selector": {
                "type": "getByRole",
                "value": "button",
                "attributes": {"name": "Submit"},
            },
        },
    ],
    "urls_visited": ["https://example.com"],
    "selectors_used": [],
    "metadata": {},
}


# =============================================================================
# BDDConversionAgent Tests
# =============================================================================


class TestBDDConversionAgent:
    """Tests for BDDConversionAgent class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test agent initialization."""
        agent = BDDConversionAgent(tmp_path)

        assert agent._project_path == tmp_path
        assert agent._converter is not None
        assert agent._step_gen is not None

    def test_initialization_without_path(self) -> None:
        """Test agent initialization without path."""
        agent = BDDConversionAgent()

        assert agent._project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_process_parsed_recording(self, tmp_path: Path) -> None:
        """Test processing a parsed recording."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "parsed_recording": SAMPLE_PARSED_RECORDING,
        })

        assert result["success"] is True
        assert "feature_file" in result
        assert "step_definitions" in result
        assert "summary" in result

        # Check feature file content
        feature_content = result["feature_file"]
        assert "Feature:" in feature_content
        assert "Scenario:" in feature_content

        # Check summary
        summary = result["summary"]
        assert summary["scenario_count"] == 1
        assert summary["test_name"] == "login test"

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_with_custom_feature_name(self, tmp_path: Path) -> None:
        """Test processing with custom feature name."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "parsed_recording": SAMPLE_PARSED_RECORDING,
            "feature_name": "Custom Login Feature",
        })

        assert result["success"] is True
        assert "Feature: Custom Login Feature" in result["feature_file"]

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_without_parsed_recording(self, tmp_path: Path) -> None:
        """Test processing without parsed recording."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({})

        assert result["success"] is False
        assert "error" in result
        assert "No parsed_recording" in result["error"]

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_convert_recording_to_file(self, tmp_path: Path) -> None:
        """Test converting and saving to file."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        output_file = tmp_path / "test.feature"

        result = await agent.convert_recording_to_file(
            SAMPLE_PARSED_RECORDING,
            output_file,
        )

        assert result["success"] is True
        assert output_file.exists()

        content = output_file.read_text()
        assert "Feature:" in content
        assert "Scenario:" in content

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_generates_step_definitions(self, tmp_path: Path) -> None:
        """Test that process generates step definitions."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "parsed_recording": SAMPLE_PARSED_RECORDING,
        })

        assert result["success"] is True

        step_defs = result["step_definitions"]
        assert "from behave import given, when, then" in step_defs
        assert "@given" in step_defs or "@when" in step_defs
        assert "def step_" in step_defs

        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_process_generates_proper_gherkin(self, tmp_path: Path) -> None:
        """Test that process generates proper Gherkin syntax."""
        agent = BDDConversionAgent(tmp_path)
        await agent.initialize()

        result = await agent.process({
            "parsed_recording": SAMPLE_PARSED_RECORDING,
        })

        assert result["success"] is True

        feature = result["feature_file"]
        # Check for proper Gherkin structure
        assert "Feature:" in feature
        assert "Scenario:" in feature
        assert "Given" in feature or "When" in feature or "Then" in feature

        await agent.cleanup()
