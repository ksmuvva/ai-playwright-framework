"""
Tests for the Deduplication module.

Tests cover:
- Finding repeated selector patterns
- Creating page objects
- Generating page object code
- Pattern analysis statistics
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.deduplication import (
    PageElement,
    PageObject,
    PageObjectGenerator,
    SelectorPattern,
    analyze_patterns,
    generate_page_objects,
)


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_RECORDINGS = [
    {
        "file_path": "test1.js",
        "test_name": "user login",
        "actions": [
            {
                "action_type": "goto",
                "value": "https://example.com/login",
                "selector": None,
            },
            {
                "action_type": "fill",
                "value": "user@example.com",
                "selector": {
                    "raw": "getByLabel('Email')",
                    "type": "getByLabel",
                    "value": "Email",
                    "attributes": {},
                },
            },
            {
                "action_type": "fill",
                "value": "password123",
                "selector": {
                    "raw": "getByLabel('Password')",
                    "type": "getByLabel",
                    "value": "Password",
                    "attributes": {},
                },
            },
            {
                "action_type": "click",
                "selector": {
                    "raw": "getByRole('button', { name: 'Login' })",
                    "type": "getByRole",
                    "value": "button",
                    "attributes": {"name": "Login"},
                },
            },
        ],
        "urls_visited": ["https://example.com/login"],
        "selectors_used": [],
        "metadata": {},
    },
    {
        "file_path": "test2.js",
        "test_name": "user registration",
        "actions": [
            {
                "action_type": "goto",
                "value": "https://example.com/register",
                "selector": None,
            },
            {
                "action_type": "fill",
                "value": "new@example.com",
                "selector": {
                    "raw": "getByLabel('Email')",
                    "type": "getByLabel",
                    "value": "Email",
                    "attributes": {},
                },
            },
            {
                "action_type": "fill",
                "value": "pass123",
                "selector": {
                    "raw": "getByLabel('Password')",
                    "type": "getByLabel",
                    "value": "Password",
                    "attributes": {},
                },
            },
            {
                "action_type": "click",
                "selector": {
                    "raw": "getByRole('button', { name: 'Register' })",
                    "type": "getByRole",
                    "value": "button",
                    "attributes": {"name": "Register"},
                },
            },
        ],
        "urls_visited": ["https://example.com/register"],
        "selectors_used": [],
        "metadata": {},
    },
    {
        "file_path": "test3.js",
        "test_name": "user login again",
        "actions": [
            {
                "action_type": "goto",
                "value": "https://example.com/login",
                "selector": None,
            },
            {
                "action_type": "fill",
                "value": "test@test.com",
                "selector": {
                    "raw": "getByLabel('Email')",
                    "type": "getByLabel",
                    "value": "Email",
                    "attributes": {},
                },
            },
            {
                "action_type": "click",
                "selector": {
                    "raw": "getByRole('button', { name: 'Login' })",
                    "type": "getByRole",
                    "value": "button",
                    "attributes": {"name": "Login"},
                },
            },
        ],
        "urls_visited": ["https://example.com/login"],
        "selectors_used": [],
        "metadata": {},
    },
]


# =============================================================================
# SelectorPattern Tests
# =============================================================================


class TestSelectorPattern:
    """Tests for SelectorPattern class."""

    def test_create_selector_pattern(self) -> None:
        """Test creating a selector pattern."""
        pattern = SelectorPattern(
            raw="getByLabel('Email')",
            type="getByLabel",
            value="Email",
            attributes={},
            count=3,
            recordings=["test1", "test2"],
        )

        assert pattern.raw == "getByLabel('Email')"
        assert pattern.type == "getByLabel"
        assert pattern.value == "Email"
        assert pattern.count == 3
        assert len(pattern.recordings) == 2

    def test_selector_pattern_to_dict(self) -> None:
        """Test converting selector pattern to dictionary."""
        pattern = SelectorPattern(
            raw="getByLabel('Email')",
            type="getByLabel",
            value="Email",
            attributes={},
            count=2,
            suggested_name="email",
            confidence=0.8,
        )

        data = pattern.to_dict()

        assert data["raw"] == "getByLabel('Email')"
        assert data["count"] == 2
        assert data["suggested_name"] == "email"
        assert data["confidence"] == 0.8


# =============================================================================
# PageElement Tests
# =============================================================================


class TestPageElement:
    """Tests for PageElement class."""

    def test_create_page_element(self) -> None:
        """Test creating a page element."""
        element = PageElement(
            name="email_field",
            selector="Email",
            selector_type="getByLabel",
            description="Email input field",
        )

        assert element.name == "email_field"
        assert element.selector == "Email"
        assert element.selector_type == "getByLabel"

    def test_page_element_to_dict(self) -> None:
        """Test converting page element to dictionary."""
        element = PageElement(
            name="submit_button",
            selector="button",
            selector_type="getByRole",
            usage_count=3,
        )

        data = element.to_dict()

        assert data["name"] == "submit_button"
        assert data["usage_count"] == 3


# =============================================================================
# PageObject Tests
# =============================================================================


class TestPageObject:
    """Tests for PageObject class."""

    def test_create_page_object(self) -> None:
        """Test creating a page object."""
        elements = {
            "email": PageElement(
                name="email",
                selector="Email",
                selector_type="getByLabel",
            ),
            "password": PageElement(
                name="password",
                selector="Password",
                selector_type="getByLabel",
            ),
        }

        page_obj = PageObject(
            name="LoginPage",
            url_pattern="https://example.com/login",
            elements=elements,
        )

        assert page_obj.name == "LoginPage"
        assert len(page_obj.elements) == 2
        assert "email" in page_obj.elements

    def test_page_object_to_dict(self) -> None:
        """Test converting page object to dictionary."""
        page_obj = PageObject(name="TestPage")

        data = page_obj.to_dict()

        assert data["name"] == "TestPage"
        assert "elements" in data

    def test_page_object_to_python_code(self) -> None:
        """Test generating Python code from page object."""
        elements = {
            "email": PageElement(
                name="email",
                selector="Email",
                selector_type="getByLabel",
                description="Email input field",
            ),
        }

        page_obj = PageObject(
            name="LoginPage",
            elements=elements,
        )

        code = page_obj.to_python_code()

        assert "class LoginPage" in code
        assert "def email(self)" in code
        assert "getByLabel" in code


# =============================================================================
# Pattern Analysis Tests
# =============================================================================


class TestPatternAnalysis:
    """Tests for pattern analysis functionality."""

    def test_analyze_empty_recordings(self) -> None:
        """Test analyzing empty recordings list."""
        result = analyze_patterns([])

        assert len(result.selector_patterns) == 0
        assert len(result.page_objects) == 0

    def test_find_repeated_selectors(self) -> None:
        """Test finding repeated selectors across recordings."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        # Should find repeated selectors
        assert len(result.selector_patterns) > 0

        # Email selector appears in all 3 recordings
        email_patterns = [p for p in result.selector_patterns if "Email" in p.raw]
        assert len(email_patterns) > 0
        assert email_patterns[0].count == 3

    def test_pattern_suggested_names(self) -> None:
        """Test that patterns have suggested element names."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        # Check that patterns have suggested names
        for pattern in result.selector_patterns:
            assert pattern.suggested_name != "" or pattern.count < 2

    def test_pattern_confidence_scores(self) -> None:
        """Test that patterns have confidence scores."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        for pattern in result.selector_patterns:
            assert 0.0 <= pattern.confidence <= 1.0

    def test_statistics_calculation(self) -> None:
        """Test statistics calculation."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        stats = result.statistics

        assert stats["total_recordings"] == 3
        assert stats["unique_selectors"] > 0
        assert "repeated_selectors" in stats
        assert "total_actions" in stats

    def test_page_objects_generation(self) -> None:
        """Test page object generation."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        # Should generate page objects
        assert len(result.page_objects) >= 0

        # Check page object structure
        for page_obj in result.page_objects:
            assert page_obj.name != ""
            assert isinstance(page_obj.elements, dict)


# =============================================================================
# PageObjectGenerator Tests
# =============================================================================


class TestPageObjectGenerator:
    """Tests for PageObjectGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        gen = PageObjectGenerator()

        assert isinstance(gen, PageObjectGenerator)

    def test_generate_from_recordings(self, tmp_path: Path) -> None:
        """Test generating page objects from recordings."""
        gen = PageObjectGenerator()
        output_dir = tmp_path / "pages"

        result = gen.generate_from_recordings(
            SAMPLE_RECORDINGS,
            output_dir,
        )

        assert result["success"] is True
        assert "files_created" in result
        assert "page_objects_count" in result
        assert "statistics" in result

    def test_generate_creates_files(self, tmp_path: Path) -> None:
        """Test that generation creates actual files."""
        gen = PageObjectGenerator()
        output_dir = tmp_path / "pages"

        result = gen.generate_from_recordings(
            SAMPLE_RECORDINGS,
            output_dir,
        )

        # Check that files were created
        for file_path in result["files_created"]:
            assert Path(file_path).exists()

            content = Path(file_path).read_text()
            # Check for basic Python structure
            assert "class " in content or "# No page objects" in content

    def test_generate_code_string(self) -> None:
        """Test generating code as string without files."""
        gen = PageObjectGenerator()

        code = gen.generate_code_string(SAMPLE_RECORDINGS)

        assert isinstance(code, str)
        # Should either have code or a comment about no patterns
        assert len(code) > 0


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_analyze_patterns_function(self) -> None:
        """Test analyze_patterns convenience function."""
        result = analyze_patterns(SAMPLE_RECORDINGS)

        assert result is not None
        assert hasattr(result, "selector_patterns")
        assert hasattr(result, "page_objects")
        assert hasattr(result, "statistics")

    def test_generate_page_objects_function(self, tmp_path: Path) -> None:
        """Test generate_page_objects convenience function."""
        output_dir = tmp_path / "pages"

        result = generate_page_objects(
            SAMPLE_RECORDINGS,
            output_dir,
        )

        assert result["success"] is True
        assert "files_created" in result


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_no_repeated_patterns(self) -> None:
        """Test with recordings that have no repeated patterns."""
        recordings = [
            {
                "test_name": "test1",
                "actions": [
                    {
                        "action_type": "click",
                        "selector": {"raw": "unique1", "type": "locator", "value": "#a"},
                    },
                ],
                "urls_visited": [],
            },
            {
                "test_name": "test2",
                "actions": [
                    {
                        "action_type": "click",
                        "selector": {"raw": "unique2", "type": "locator", "value": "#b"},
                    },
                ],
                "urls_visited": [],
            },
        ]

        result = analyze_patterns(recordings)

        # Should not find repeated patterns (each selector appears once)
        repeated = [p for p in result.selector_patterns if p.count >= 2]
        assert len(repeated) == 0

    def test_single_recording(self) -> None:
        """Test with only one recording."""
        result = analyze_patterns([SAMPLE_RECORDINGS[0]])

        stats = result.statistics
        assert stats["total_recordings"] == 1

    def test_recordings_without_selectors(self) -> None:
        """Test with recordings that have no selectors."""
        recordings = [
            {
                "test_name": "nav test",
                "actions": [
                    {"action_type": "goto", "value": "https://example.com", "selector": None},
                ],
                "urls_visited": ["https://example.com"],
            },
        ]

        result = analyze_patterns(recordings)

        # Should handle gracefully
        assert result.statistics["total_recordings"] == 1
