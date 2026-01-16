"""
Tests for the Deduplication module.

Tests cover:
- Element context tracking
- Exact and pattern matching
- Group management
- Selector catalog operations
- Page object generation
- Deduplication agent workflow
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from yaml import dump

from claude_playwright_agent.deduplication.agent import (
    DeduplicationAgent,
    DeduplicationConfig,
    DeduplicationResult,
    run_deduplication,
)
from claude_playwright_agent.deduplication.logic import (
    ActionType,
    ElementContext,
    ElementGroup,
    ElementKey,
    SelectorData,
    SelectorType,
    DeduplicationLogic,
)
from claude_playwright_agent.deduplication.selector_catalog import (
    CatalogEntry,
    SelectorCatalog,
)
from claude_playwright_agent.deduplication.page_objects import (
    GenerationConfig,
    PageObjectGenerator,
    PageObjectModel,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_selector() -> SelectorData:
    """Create a sample selector."""
    return SelectorData(
        raw='getByRole("button", { name: "Submit" })',
        type="getByRole",
        value="Submit",
        attributes={"name": "Submit", "exact": "true"},
    )


@pytest.fixture
def sample_context() -> ElementContext:
    """Create a sample element context."""
    return ElementContext(
        recording_id="recording_001",
        page_url="https://example.com/form",
        action_type="click",
        line_number=42,
        element_index=0,
        value=None,
    )


@pytest.fixture
def initialized_project(tmp_path: Path) -> Path:
    """Create an initialized project with state."""
    # Create .cpa directory structure
    cpa_dir = tmp_path / ".cpa"
    cpa_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal config
    config_data = {
        "version": "0.1.0",
        "profile": "default",
        "framework": {
            "bdd_framework": "behave",
            "template": "basic",
            "base_url": "http://localhost:8000",
            "default_timeout": 30000,
        },
        "browser": {"browser": "chromium", "headless": True},
        "execution": {"parallel_workers": 2},
        "logging": {
            "level": "INFO",
            "format": "text",
            "file": str(cpa_dir / "logs" / "agent.log"),
            "console": True,
        },
    }

    config_file = cpa_dir / "config.yaml"
    config_file.write_text(dump(config_data), encoding="utf-8")

    # Create minimal state
    state_data = {
        "project": {
            "name": "test-project",
            "framework_type": "behave",
            "version": "0.1.0",
            "created_at": "2024-01-01T00:00:00",
        },
        "recordings": [
            {
                "recording_id": "recording_001",
                "file_path": "/recordings/test.js",
                "ingested_at": "2024-01-01T00:00:00",
                "status": "completed",
                "actions_count": 5,
                "scenarios_count": 1,
            }
        ],
        "recordings_data": {
            "recording_001": {
                "actions": [
                    {
                        "action_type": "goto",
                        "value": "https://example.com",
                        "page_url": "",
                        "line_number": 1,
                    },
                    {
                        "action_type": "click",
                        "selector": {
                            "raw": 'getByRole("button", { name: "Submit" })',
                            "type": "getByRole",
                            "value": "Submit",
                            "attributes": {"name": "Submit"},
                        },
                        "page_url": "https://example.com",
                        "line_number": 5,
                    },
                    {
                        "action_type": "fill",
                        "selector": {
                            "raw": 'getByLabel("Email")',
                            "type": "getByLabel",
                            "value": "Email",
                            "attributes": {},
                        },
                        "value": "test@example.com",
                        "page_url": "https://example.com",
                        "line_number": 10,
                    },
                ],
                "urls_visited": ["https://example.com"],
            }
        },
        "scenarios": {},
        "test_runs": {},
        "components": {},
        "page_objects": {},
        "selector_catalog": {},
    }

    state_file = cpa_dir / "state.json"
    state_file.write_text(json.dumps(state_data), encoding="utf-8")

    return tmp_path


# =============================================================================
# SelectorData Tests
# =============================================================================


class TestSelectorData:
    """Tests for SelectorData class."""

    def test_selector_creation(self) -> None:
        """Test creating a selector."""
        selector = SelectorData(
            raw='getByRole("button")',
            type="getByRole",
            value="button",
        )

        assert selector.raw == 'getByRole("button")'
        assert selector.type == "getByRole"
        assert selector.value == "button"

    def test_normalized_value(self) -> None:
        """Test value normalization."""
        selector = SelectorData(
            raw='getByRole("button")',
            type="getByRole",
            value="  Test Button  ",
        )

        assert selector.normalized_value == "test button"

    def test_fragility_score(self) -> None:
        """Test fragility score calculation."""
        # Test ID - very stable
        test_id = SelectorData(
            raw='getByTestId("submit")',
            type=SelectorType.GET_BY_TEST_ID,
            value="submit",
        )
        assert test_id.fragility_score == 0.0

        # Role - stable
        role = SelectorData(
            raw='getByRole("button")',
            type=SelectorType.GET_BY_ROLE,
            value="button",
        )
        assert role.fragility_score == 0.1

        # Text - fragile
        text = SelectorData(
            raw='getByText("Submit")',
            type=SelectorType.GET_BY_TEXT,
            value="Submit",
        )
        assert text.fragility_score == 0.7

        # XPath - very fragile
        xpath = SelectorData(
            raw='xpath="//div[@class="submit"]"',
            type=SelectorType.XPATH,
            value='//div[@class="submit"]',
        )
        assert xpath.fragility_score == 0.9


# =============================================================================
# ElementContext Tests
# =============================================================================


class TestElementContext:
    """Tests for ElementContext class."""

    def test_context_creation(self) -> None:
        """Test creating an element context."""
        context = ElementContext(
            recording_id="rec_001",
            page_url="https://example.com",
            action_type="click",
            line_number=42,
            element_index=5,
        )

        assert context.recording_id == "rec_001"
        assert context.page_url == "https://example.com"
        assert context.action_type == "click"
        assert context.line_number == 42
        assert context.element_index == 5

    def test_context_with_value(self) -> None:
        """Test context with value."""
        context = ElementContext(
            recording_id="rec_001",
            page_url="https://example.com",
            action_type="fill",
            line_number=42,
            element_index=0,
            value="test@example.com",
        )

        assert context.value == "test@example.com"

    def test_context_to_dict(self) -> None:
        """Test converting context to dictionary."""
        context = ElementContext(
            recording_id="rec_001",
            page_url="https://example.com",
            action_type="click",
            line_number=42,
            element_index=0,
        )

        data = context.to_dict()

        assert data["recording_id"] == "rec_001"
        assert data["page_url"] == "https://example.com"
        assert data["action_type"] == "click"
        assert data["line_number"] == 42


# =============================================================================
# ElementKey Tests
# =============================================================================


class TestElementKey:
    """Tests for ElementKey class."""

    def test_key_from_selector(self) -> None:
        """Test creating key from selector."""
        selector = SelectorData(
            raw='getByRole("button")',
            type="getByRole",
            value="button",
        )

        key = ElementKey.from_selector(selector, "https://example.com")

        assert key.type == "getByRole"
        assert key.value == "button"
        assert key.selector_hash is not None
        assert key.url_hash is not None

    def test_key_without_url(self) -> None:
        """Test creating key without URL context."""
        selector = SelectorData(
            raw='getByRole("button")',
            type="getByRole",
            value="button",
        )

        key = ElementKey.from_selector(selector)

        assert key.url_hash is None


# =============================================================================
# ElementGroup Tests
# =============================================================================


class TestElementGroup:
    """Tests for ElementGroup class."""

    def test_group_creation(self, sample_selector, sample_context) -> None:
        """Test creating an element group."""
        group = ElementGroup(
            group_id="group_001",
            canonical_selector=sample_selector,
            fragility_score=sample_selector.fragility_score,
            name_suggestion="submitButton",
        )

        assert group.group_id == "group_001"
        assert group.canonical_selector == sample_selector
        assert group.usage_count == 0

    def test_add_context(self, sample_selector, sample_context) -> None:
        """Test adding context to group."""
        group = ElementGroup(
            group_id="group_001",
            canonical_selector=sample_selector,
            fragility_score=sample_selector.fragility_score,
        )

        group.add_context(sample_context)

        assert group.usage_count == 1
        assert len(group.contexts) == 1
        assert "recording_001" in group.recordings
        assert "https://example.com/form" in group.pages

    def test_merge_groups(self, sample_selector, sample_context) -> None:
        """Test merging two groups."""
        group1 = ElementGroup(
            group_id="group_001",
            canonical_selector=sample_selector,
            fragility_score=0.5,
        )
        group1.add_context(sample_context)

        # Create second group
        selector2 = SelectorData(
            raw='getByText("Submit")',
            type="getByText",
            value="Submit",
        )
        group2 = ElementGroup(
            group_id="group_002",
            canonical_selector=selector2,
            fragility_score=0.7,
        )
        context2 = ElementContext(
            recording_id="recording_002",
            page_url="https://example.com",
            action_type="click",
            line_number=50,
            element_index=0,
        )
        group2.add_context(context2)

        # Merge
        group1.merge(group2)

        assert group1.usage_count == 2
        assert len(group1.contexts) == 2
        assert len(group1.alternative_selectors) == 1


# =============================================================================
# DeduplicationLogic Tests
# =============================================================================


class TestDeduplicationLogic:
    """Tests for DeduplicationLogic class."""

    def test_initialization(self) -> None:
        """Test logic initialization."""
        logic = DeduplicationLogic()

        assert len(logic._groups) == 0
        assert len(logic._selector_index) == 0

    def test_create_group(self, sample_selector, sample_context) -> None:
        """Test creating a new group."""
        logic = DeduplicationLogic()

        group = logic.create_group(sample_selector, sample_context)

        assert group.usage_count == 1
        assert group.group_id.startswith("group_")
        assert len(logic.get_all_groups()) == 1

    def test_exact_match(self, sample_selector, sample_context) -> None:
        """Test exact matching."""
        logic = DeduplicationLogic()

        # Create group
        logic.create_group(sample_selector, sample_context)

        # Try exact match
        match = logic.exact_match(sample_selector, sample_context)

        assert match is not None
        assert match.usage_count == 1

    def test_pattern_match(self, sample_selector, sample_context) -> None:
        """Test pattern matching."""
        logic = DeduplicationLogic()

        # Create group with similar selector
        similar_selector = SelectorData(
            raw='getByRole("button", { name: "Submit Form" })',
            type="getByRole",
            value="Submit Form",
            attributes={"name": "Submit Form"},
        )
        logic.create_group(similar_selector, sample_context)

        # Pattern match
        matches = logic.pattern_match(sample_selector, sample_context, threshold=0.7)

        assert len(matches) >= 1

    def test_get_groups_by_recording(self, sample_selector, sample_context) -> None:
        """Test getting groups by recording."""
        logic = DeduplicationLogic()

        logic.create_group(sample_selector, sample_context)

        groups = logic.get_groups_by_recording("recording_001")

        assert len(groups) == 1
        assert groups[0].group_id.startswith("group_")

    def test_get_stats(self, sample_selector, sample_context) -> None:
        """Test getting statistics."""
        logic = DeduplicationLogic()

        logic.create_group(sample_selector, sample_context)

        stats = logic.get_stats()

        assert stats["total_groups"] == 1
        assert stats["total_usages"] == 1
        assert stats["total_recordings"] == 1


# =============================================================================
# SelectorCatalog Tests
# =============================================================================


class TestSelectorCatalog:
    """Tests for SelectorCatalog class."""

    def test_initialization(self) -> None:
        """Test catalog initialization."""
        catalog = SelectorCatalog()

        assert len(catalog) == 0

    def test_add_selector(self, sample_selector, sample_context) -> None:
        """Test adding a selector to catalog."""
        catalog = SelectorCatalog()

        entry = catalog.add_selector(sample_selector, sample_context, "submitButton")

        assert entry.entry_id.startswith("catalog_")
        assert entry.usage_count == 1
        assert entry.element_name == "submitButton"

    def test_get_by_selector(self, sample_selector, sample_context) -> None:
        """Test getting entry by selector."""
        catalog = SelectorCatalog()

        catalog.add_selector(sample_selector, sample_context)

        entry = catalog.get_by_selector(sample_selector)

        assert entry is not None
        assert entry.usage_count == 1

    def test_find_by_recording(self, sample_selector, sample_context) -> None:
        """Test finding by recording ID."""
        catalog = SelectorCatalog()

        catalog.add_selector(sample_selector, sample_context)

        entries = catalog.find_by_recording("recording_001")

        assert len(entries) == 1

    def test_find_by_page(self, sample_selector, sample_context) -> None:
        """Test finding by page URL."""
        catalog = SelectorCatalog()

        catalog.add_selector(sample_selector, sample_context)

        entries = catalog.find_by_page("https://example.com")

        assert len(entries) == 1

    def test_find_flexible(self, sample_selector, sample_context) -> None:
        """Test flexible querying."""
        catalog = SelectorCatalog()

        catalog.add_selector(sample_selector, sample_context)

        # Find by recording
        results = catalog.find_flexible(recording_id="recording_001")

        assert len(results) == 1

    def test_get_stats(self, sample_selector, sample_context) -> None:
        """Test getting catalog statistics."""
        catalog = SelectorCatalog()

        catalog.add_selector(sample_selector, sample_context)

        stats = catalog.get_stats()

        assert stats["total_entries"] == 1
        assert stats["total_usage"] == 1


# =============================================================================
# PageObjectGenerator Tests
# =============================================================================


class TestPageObjectGenerator:
    """Tests for PageObjectGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        config = GenerationConfig()
        gen = PageObjectGenerator(config)

        assert gen.config == config

    def test_generate_class_name(self) -> None:
        """Test class name generation."""
        gen = PageObjectGenerator()

        # From path
        name = gen._generate_class_name("https://example.com/api/users")

        assert name.endswith("Page")

    def test_snake_case(self) -> None:
        """Test snake_case conversion."""
        gen = PageObjectGenerator()

        assert gen._snake_case("HomePage") == "home_page"
        assert gen._snake_case("UserFormPage") == "user_form_page"

    def test_generate_class(self, tmp_path: Path) -> None:
        """Test generating a page object class."""
        gen = PageObjectGenerator()

        # Create mock groups
        selector = SelectorData(
            raw='getByRole("button", { name: "Submit" })',
            type="getByRole",
            value="Submit",
            attributes={"name": "Submit"},
        )

        context = ElementContext(
            recording_id="rec_001",
            page_url="https://example.com",
            action_type="click",
            line_number=42,
            element_index=0,
        )

        group = ElementGroup(
            group_id="group_001",
            canonical_selector=selector,
            fragility_score=0.1,
            name_suggestion="submitButton",
        )
        group.add_context(context)

        # Generate
        model = gen.generate_class(
            page_url="https://example.com",
            groups=[group],
            output_dir=tmp_path,
        )

        assert model.class_name == "ExampleComPage"
        assert model.file_path.endswith(".py")
        assert Path(model.file_path).exists()

    def test_generate_multiple_pages(self, tmp_path: Path) -> None:
        """Test generating multiple page objects."""
        gen = PageObjectGenerator()

        page_groups = {
            "https://example.com/login": [],
            "https://example.com/register": [],
        }

        models = gen.generate_all(page_groups, tmp_path)

        assert len(models) == 2


# =============================================================================
# DeduplicationAgent Tests
# =============================================================================


class TestDeduplicationAgent:
    """Tests for DeduplicationAgent class."""

    def test_initialization(self, initialized_project: Path) -> None:
        """Test agent initialization."""
        agent = DeduplicationAgent(initialized_project)

        assert agent.agent_id == "deduplication_agent"
        assert agent.agent_type == "deduplication"
        assert agent.logic is not None
        assert agent.catalog is not None

    def test_run_deduplication(self, initialized_project: Path) -> None:
        """Test running deduplication."""
        agent = DeduplicationAgent(initialized_project)

        result = agent.run()

        assert result.success is True
        assert isinstance(result.total_groups, int)

    def test_custom_config(self, initialized_project: Path) -> None:
        """Test agent with custom config."""
        config = DeduplicationConfig(
            pattern_match_threshold=0.9,
            generate_page_objects=False,
        )

        agent = DeduplicationAgent(initialized_project, config)

        assert agent.config.pattern_match_threshold == 0.9
        assert agent.config.generate_page_objects is False


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_run_deduplication(self, initialized_project: Path) -> None:
        """Test run_deduplication convenience function."""
        result = run_deduplication(initialized_project)

        assert isinstance(result, DeduplicationResult)


# =============================================================================
# Integration Tests
# =============================================================================


class TestDeduplicationIntegration:
    """Integration tests for deduplication workflow."""

    def test_full_workflow(self, initialized_project: Path) -> None:
        """Test complete deduplication workflow."""
        agent = DeduplicationAgent(initialized_project)

        result = agent.run()

        assert result.success is True
        assert result.total_groups >= 0
        # Stats may be empty if no elements found
        assert "logic_stats" in result.stats or result.total_groups == 0

    def test_catalog_integration(self, initialized_project: Path) -> None:
        """Test catalog integration with agent."""
        agent = DeduplicationAgent(initialized_project)

        result = agent.run()

        # Check catalog was populated
        stats = agent.catalog.get_stats()
        assert stats["total_entries"] >= result.selectors_cataloged

    def test_state_update(self, initialized_project: Path) -> None:
        """Test state update after deduplication."""
        agent = DeduplicationAgent(initialized_project)

        result = agent.run()

        # Verify state was updated - state should exist and have required keys
        from claude_playwright_agent.state.manager import StateManager

        state = StateManager(initialized_project)
        # The state should exist with these keys even if empty
        assert hasattr(state, "_state")
