"""
Tests for the Playwright Recording Parser.

Tests cover:
- Parsing Playwright codegen JavaScript files
- Extracting actions (goto, click, fill, etc.)
- Extracting selectors (getByRole, getByLabel, etc.)
- Building metadata
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.playwright_parser import (
    Action,
    ActionType,
    parse_recording,
    parse_recording_content,
    PlaywrightRecordingParser,
    ParsedRecording,
    SelectorInfo,
    SelectorType,
    FragilityLevel,
)


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_RECORDING = """// @ts-check
const { test, expect } = require('@playwright/test');

test('example test', async ({ page }) => {
  await page.goto('https://example.com');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByPlaceholder('Password').type('secret123');
  await page.getByRole('checkbox', { name: 'Remember me' }).check();
  await page.locator('#submit').click();
});
"""

SIMPLE_RECORDING = """test('simple', async ({ page }) => {
  await page.goto('https://example.com');
  await page.click('button');
});
"""

# =============================================================================
# SelectorInfo Tests
# =============================================================================


class TestSelectorInfo:
    """Tests for SelectorInfo class."""

    def test_create_selector(self) -> None:
        """Test creating a selector."""
        selector = SelectorInfo(
            raw="getByRole('button')",
            type="getByRole",
            value="button",
        )

        assert selector.raw == "getByRole('button')"
        assert selector.type == "getByRole"
        assert selector.value == "button"

    def test_selector_to_dict(self) -> None:
        """Test converting selector to dictionary."""
        selector = SelectorInfo(
            raw="getByRole('button')",
            type="getByRole",
            value="button",
            attributes={"name": "Submit"},
        )

        data = selector.to_dict()

        assert data["raw"] == "getByRole('button')"
        assert data["type"] == "getByRole"
        assert data["value"] == "button"
        assert data["attributes"]["name"] == "Submit"


# =============================================================================
# Action Tests
# =============================================================================


class TestAction:
    """Tests for Action class."""

    def test_create_action(self) -> None:
        """Test creating an action."""
        selector = SelectorInfo(
            raw="getByRole('button')",
            type="getByRole",
            value="button",
        )
        action = Action(
            action_type=ActionType.CLICK,
            selector=selector,
            page_url="https://example.com",
            line_number=5,
        )

        assert action.action_type == ActionType.CLICK
        assert action.selector == selector
        assert action.page_url == "https://example.com"
        assert action.line_number == 5

    def test_action_to_dict(self) -> None:
        """Test converting action to dictionary."""
        selector = SelectorInfo(
            raw="getByRole('button')",
            type="getByRole",
            value="button",
        )
        action = Action(
            action_type=ActionType.CLICK,
            selector=selector,
        )

        data = action.to_dict()

        assert data["action_type"] == "click"
        assert data["selector"]["type"] == "getByRole"
        assert data["selector"]["value"] == "button"


# =============================================================================
# PlaywrightRecordingParser Tests
# =============================================================================


class TestPlaywrightRecordingParser:
    """Tests for PlaywrightRecordingParser class."""

    def test_parse_goto_action(self) -> None:
        """Test parsing goto action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.goto('https://example.com');")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.GOTO
        assert result.actions[0].value == "https://example.com"
        assert len(result.urls_visited) == 1
        assert result.urls_visited[0] == "https://example.com"

    def test_parse_click_action(self) -> None:
        """Test parsing click action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByRole('button', { name: 'Sign in' }).click();"
        )

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.CLICK
        assert result.actions[0].selector is not None
        assert result.actions[0].selector.type == "getByRole"

    def test_parse_fill_action(self) -> None:
        """Test parsing fill action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByLabel('Email').fill('test@example.com');"
        )

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.FILL
        assert result.actions[0].value == "test@example.com"
        assert result.actions[0].selector is not None
        assert result.actions[0].selector.type == "getByLabel"

    def test_parse_type_action(self) -> None:
        """Test parsing type action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByPlaceholder('Password').type('secret123');"
        )

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.TYPE
        assert result.actions[0].value == "secret123"

    def test_parse_check_action(self) -> None:
        """Test parsing check action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByRole('checkbox').check();"
        )

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.CHECK

    def test_parse_hover_action(self) -> None:
        """Test parsing hover action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.hover('button');")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.HOVER

    def test_parse_press_action(self) -> None:
        """Test parsing press action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.keyboard.press('Enter');")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.PRESS

    def test_parse_wait_for_action(self) -> None:
        """Test parsing waitFor action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.waitForSelector('.loaded');")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.WAIT_FOR

    def test_parse_expect_action(self) -> None:
        """Test parsing expect action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await expect(page).toHaveTitle('Example');")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.EXPECT

    def test_parse_screenshot_action(self) -> None:
        """Test parsing screenshot action."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.screenshot({ path: 'screenshot.png' });")

        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.SCREENSHOT

    def test_extract_get_by_role_selector(self) -> None:
        """Test extracting getByRole selector."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByRole('button', { name: 'Sign in' }).click();"
        )

        assert len(result.selectors_used) == 1
        selector = result.selectors_used[0]
        assert selector.type == "getByRole"
        assert selector.value == "button"
        assert selector.attributes.get("name") == "Sign in"

    def test_extract_get_by_label_selector(self) -> None:
        """Test extracting getByLabel selector."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(
            "await page.getByLabel('Email address').fill('test@example.com');"
        )

        assert len(result.selectors_used) == 1
        selector = result.selectors_used[0]
        assert selector.type == "getByLabel"
        assert selector.value == "Email address"

    def test_extract_locator_selector(self) -> None:
        """Test extracting locator selector."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("await page.locator('#submit').click();")

        assert len(result.selectors_used) == 1
        selector = result.selectors_used[0]
        assert selector.type == "locator"
        assert selector.value == "#submit"

    def test_extract_test_name(self) -> None:
        """Test extracting test name."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(SAMPLE_RECORDING)

        assert result.test_name == "example test"

    def test_build_metadata(self) -> None:
        """Test building metadata."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(SAMPLE_RECORDING)

        assert result.metadata["ts_check"] is True
        assert "@playwright/test" in result.metadata["imports"]
        assert "action_counts" in result.metadata

    def test_parse_full_recording(self) -> None:
        """Test parsing a full recording."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(SAMPLE_RECORDING)

        assert result.test_name == "example test"
        assert len(result.actions) == 6
        assert result.actions[0].action_type == ActionType.GOTO
        assert result.actions[1].action_type == ActionType.CLICK
        assert result.actions[2].action_type == ActionType.FILL
        assert result.actions[3].action_type == ActionType.TYPE
        assert result.actions[4].action_type == ActionType.CHECK
        assert result.actions[5].action_type == ActionType.CLICK

    def test_parsed_recording_to_dict(self) -> None:
        """Test converting parsed recording to dictionary."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(SIMPLE_RECORDING)

        data = result.to_dict()

        assert data["test_name"] == "simple"
        assert len(data["actions"]) == 2
        assert "urls_visited" in data
        assert "selectors_used" in data
        assert "metadata" in data


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_recording_content(self) -> None:
        """Test parse_recording_content function."""
        result = parse_recording_content(SAMPLE_RECORDING, "test.js")

        assert result.test_name == "example test"
        assert result.file_path == "test.js"
        assert len(result.actions) == 6

    def test_parse_recording_file(self, tmp_path: Path) -> None:
        """Test parse_recording function with file."""
        test_file = tmp_path / "test.js"
        test_file.write_text(SAMPLE_RECORDING)

        result = parse_recording(test_file)

        assert result.test_name == "example test"
        assert str(test_file) in result.file_path

    def test_parse_recording_file_not_found(self, tmp_path: Path) -> None:
        """Test parse_recording with non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_recording(tmp_path / "nonexistent.js")


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content."""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content("")

        assert len(result.actions) == 0
        assert len(result.urls_visited) == 0
        assert len(result.selectors_used) == 0

    def test_parse_comments_only(self) -> None:
        """Test parsing content with only comments."""
        content = """
// This is a comment
/* Multi-line
   comment */
"""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(content)

        assert len(result.actions) == 0

    def test_parse_multiple_urls(self) -> None:
        """Test parsing content with multiple goto actions."""
        content = """
await page.goto('https://example.com');
await page.goto('https://another.com');
"""
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(content)

        assert len(result.urls_visited) == 2
        assert result.urls_visited[0] == "https://example.com"
        assert result.urls_visited[1] == "https://another.com"

    def test_parse_without_test_name(self) -> None:
        """Test parsing content without test name."""
        content = "await page.goto('https://example.com');"
        parser = PlaywrightRecordingParser()
        result = parser.parse_content(content)

        assert result.test_name == ""
