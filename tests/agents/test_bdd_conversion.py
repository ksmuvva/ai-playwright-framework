"""
Tests for the BDD Conversion module.

Tests cover:
- Converting actions to Gherkin steps
- Generating feature files
- Step definition generation
- Element description generation
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.bdd_conversion import (
    BDDConverter,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    StepDefinitionGenerator,
    StepKeyword,
    convert_to_gherkin,
    save_feature_file,
)


# =============================================================================
# Test Fixtures
# =============================================================================


SAMPLE_PARSED_RECORDING = {
    "file_path": "test.js",
    "test_name": "user login",
    "actions": [
        {
            "action_type": "goto",
            "value": "https://example.com/login",
            "selector": None,
            "line_number": 1,
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
            "line_number": 2,
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
            "line_number": 3,
        },
        {
            "action_type": "click",
            "selector": {
                "raw": "getByRole('button', { name: 'Sign in' })",
                "type": "getByRole",
                "value": "button",
                "attributes": {"name": "Sign in"},
            },
            "line_number": 4,
        },
    ],
    "urls_visited": ["https://example.com/login"],
    "selectors_used": [],
    "metadata": {},
}


# =============================================================================
# GherkinStep Tests
# =============================================================================


class TestGherkinStep:
    """Tests for GherkinStep class."""

    def test_create_step(self) -> None:
        """Test creating a step."""
        step = GherkinStep(
            keyword=StepKeyword.GIVEN,
            text='the user navigates to "https://example.com"',
        )

        assert step.keyword == StepKeyword.GIVEN
        assert step.text == 'the user navigates to "https://example.com"'
        assert step.docstring is None
        assert step.table is None

    def test_step_to_gherkin(self) -> None:
        """Test converting step to Gherkin format."""
        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text='the user clicks on the button',
        )

        gherkin = step.to_gherkin()

        assert '  When the user clicks on the button' == gherkin

    def test_step_with_docstring(self) -> None:
        """Test step with docstring."""
        step = GherkinStep(
            keyword=StepKeyword.GIVEN,
            text="the user has the following data",
            docstring='{"name": "test", "value": "123"}',
        )

        gherkin = step.to_gherkin()

        assert '  Given the user has the following data' in gherkin
        assert '  """' in gherkin
        assert '{"name": "test", "value": "123"}' in gherkin

    def test_step_with_table(self) -> None:
        """Test step with data table."""
        step = GherkinStep(
            keyword=StepKeyword.GIVEN,
            text="the following users exist",
            table=[
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ],
        )

        gherkin = step.to_gherkin()

        assert "  | name | email |" in gherkin
        assert "  | Alice | alice@example.com |" in gherkin
        assert "  | Bob | bob@example.com |" in gherkin


# =============================================================================
# GherkinScenario Tests
# =============================================================================


class TestGherkinScenario:
    """Tests for GherkinScenario class."""

    def test_create_scenario(self) -> None:
        """Test creating a scenario."""
        steps = [
            GherkinStep(StepKeyword.GIVEN, "the user is on the login page"),
            GherkinStep(StepKeyword.WHEN, "the user enters credentials"),
            GherkinStep(StepKeyword.THEN, "the user is logged in"),
        ]

        scenario = GherkinScenario(
            name="Successful Login",
            steps=steps,
        )

        assert scenario.name == "Successful Login"
        assert len(scenario.steps) == 3
        assert len(scenario.tags) == 0

    def test_scenario_with_tags(self) -> None:
        """Test scenario with tags."""
        steps = [GherkinStep(StepKeyword.GIVEN, "step")]

        scenario = GherkinScenario(
            name="Tagged Scenario",
            steps=steps,
            tags=["@smoke", "@auth"],
        )

        assert scenario.tags == ["@smoke", "@auth"]

    def test_scenario_to_gherkin(self) -> None:
        """Test converting scenario to Gherkin format."""
        steps = [
            GherkinStep(StepKeyword.GIVEN, "the user is on the login page"),
            GherkinStep(StepKeyword.WHEN, "the user enters username"),
            GherkinStep(StepKeyword.AND, "the user enters password"),
            GherkinStep(StepKeyword.THEN, "the user is logged in"),
        ]

        scenario = GherkinScenario(name="Login", steps=steps)
        gherkin = scenario.to_gherkin()

        assert "  Scenario: Login" in gherkin
        assert "  Given the user is on the login page" in gherkin
        assert "  When the user enters username" in gherkin
        assert "  And the user enters password" in gherkin
        assert "  Then the user is logged in" in gherkin


# =============================================================================
# GherkinFeature Tests
# =============================================================================


class TestGherkinFeature:
    """Tests for GherkinFeature class."""

    def test_create_feature(self) -> None:
        """Test creating a feature."""
        feature = GherkinFeature(
            name="User Authentication",
            description="Tests for user login and registration",
        )

        assert feature.name == "User Authentication"
        assert "Tests for user login" in feature.description
        assert len(feature.scenarios) == 0

    def test_feature_to_gherkin(self) -> None:
        """Test converting feature to Gherkin format."""
        steps = [
            GherkinStep(StepKeyword.GIVEN, "the user is on the home page"),
            GherkinStep(StepKeyword.WHEN, "the user clicks login"),
            GherkinStep(StepKeyword.THEN, "the login form is shown"),
        ]

        scenario = GherkinScenario(name="Navigate to Login", steps=steps)
        feature = GherkinFeature(
            name="Navigation",
            description="  Test navigation features",
            scenarios=[scenario],
        )

        gherkin = feature.to_gherkin()

        assert "Feature: Navigation" in gherkin
        assert "  Test navigation features" in gherkin
        assert "  Scenario: Navigate to Login" in gherkin


# =============================================================================
# BDDConverter Tests
# =============================================================================


class TestBDDConverter:
    """Tests for BDDConverter class."""

    def test_initialization(self) -> None:
        """Test converter initialization."""
        converter = BDDConverter()

        assert isinstance(converter, BDDConverter)

    def test_convert_simple_recording(self) -> None:
        """Test converting a simple recording."""
        converter = BDDConverter()

        parsed = {
            "test_name": "simple test",
            "actions": [
                {
                    "action_type": "goto",
                    "value": "https://example.com",
                    "selector": None,
                },
                {
                    "action_type": "click",
                    "selector": None,
                },
            ],
            "urls_visited": ["https://example.com"],
        }

        feature = converter.convert_recording(parsed)

        assert feature.name == "Simple Test"
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "simple test"

    def test_convert_generates_proper_keywords(self) -> None:
        """Test that conversion generates proper Given/When/Then keywords."""
        converter = BDDConverter()

        parsed = {
            "test_name": "keyword test",
            "actions": [
                {
                    "action_type": "goto",
                    "value": "https://example.com",
                    "selector": None,
                },
                {
                    "action_type": "click",
                    "selector": None,
                },
                {
                    "action_type": "expect",
                    "selector": None,
                },
            ],
            "urls_visited": ["https://example.com"],
        }

        feature = converter.convert_recording(parsed)
        steps = feature.scenarios[0].steps

        assert steps[0].keyword == StepKeyword.GIVEN  # goto
        assert steps[1].keyword == StepKeyword.WHEN  # click
        assert steps[2].keyword == StepKeyword.THEN  # expect

    def test_convert_uses_and_for_repeated_keywords(self) -> None:
        """Test that repeated keywords use 'And'."""
        converter = BDDConverter()

        parsed = {
            "test_name": "and test",
            "actions": [
                {
                    "action_type": "goto",
                    "value": "https://example.com",
                    "selector": None,
                },
                {
                    "action_type": "fill",
                    "value": "test",
                    "selector": {"type": "getByLabel", "value": "Email"},
                },
                {
                    "action_type": "fill",
                    "value": "pass",
                    "selector": {"type": "getByLabel", "value": "Password"},
                },
            ],
            "urls_visited": ["https://example.com"],
        }

        feature = converter.convert_recording(parsed)
        steps = feature.scenarios[0].steps

        assert steps[1].keyword == StepKeyword.WHEN  # first fill
        assert steps[2].keyword == StepKeyword.AND  # second fill (same as first)

    def test_describe_element_get_by_role(self) -> None:
        """Test describing getByRole selector."""
        converter = BDDConverter()

        selector = {
            "type": "getByRole",
            "value": "button",
            "attributes": {"name": "Submit"},
        }

        desc = converter._describe_element(selector)

        assert 'the button named "Submit"' == desc

    def test_describe_element_get_by_label(self) -> None:
        """Test describing getByLabel selector."""
        converter = BDDConverter()

        selector = {
            "type": "getByLabel",
            "value": "Email",
            "attributes": {},
        }

        desc = converter._describe_element(selector)

        assert 'the field labeled "Email"' == desc

    def test_describe_element_locator(self) -> None:
        """Test describing locator selector."""
        converter = BDDConverter()

        selector = {
            "type": "locator",
            "value": "#submit-btn",
            "attributes": {},
        }

        desc = converter._describe_element(selector)

        assert 'the element with selector "#submit-btn"' == desc

    def test_convert_full_recording(self) -> None:
        """Test converting a full recording."""
        converter = BDDConverter()

        feature = converter.convert_recording(SAMPLE_PARSED_RECORDING)
        gherkin = feature.to_gherkin()

        assert "Feature: User Login" in gherkin
        assert "Scenario: user login" in gherkin
        assert 'Given the user navigates to "https://example.com/login"' in gherkin
        assert 'the field labeled "Email"' in gherkin
        assert 'the field labeled "Password"' in gherkin
        assert 'the button named "Sign in"' in gherkin


# =============================================================================
# StepDefinitionGenerator Tests
# =============================================================================


class TestStepDefinitionGenerator:
    """Tests for StepDefinitionGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        gen = StepDefinitionGenerator()

        assert isinstance(gen, StepDefinitionGenerator)

    def test_generate_for_feature(self) -> None:
        """Test generating step definitions for a feature."""
        gen = StepDefinitionGenerator()

        steps = [
            GherkinStep(StepKeyword.GIVEN, 'the user navigates to "https://example.com"'),
            GherkinStep(StepKeyword.WHEN, 'the user clicks on the button'),
        ]

        scenario = GherkinScenario(name="Test", steps=steps)
        feature = GherkinFeature(name="Test Feature", scenarios=[scenario])

        step_defs = gen.generate_for_feature(feature)

        assert "from behave import given, when, then" in step_defs
        assert '@given(\'the user navigates to "https://example.com"\')' in step_defs
        assert "@when('the user clicks on the button')" in step_defs

    def test_step_definition_has_function_name(self) -> None:
        """Test that step definitions have function names."""
        gen = StepDefinitionGenerator()

        steps = [
            GherkinStep(StepKeyword.GIVEN, "the user is on the login page"),
        ]

        scenario = GherkinScenario(name="Test", steps=steps)
        feature = GherkinFeature(name="Test Feature", scenarios=[scenario])

        step_defs = gen.generate_for_feature(feature)

        assert "def step_the_user_is_on_the_login_page" in step_defs


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_convert_to_gherkin(self) -> None:
        """Test convert_to_gherkin function."""
        gherkin = convert_to_gherkin(SAMPLE_PARSED_RECORDING)

        assert "Feature: User Login" in gherkin
        assert "Scenario: user login" in gherkin
        assert "Given" in gherkin
        assert "When" in gherkin

    def test_convert_to_gherkin_with_custom_name(self) -> None:
        """Test convert_to_gherkin with custom feature name."""
        gherkin = convert_to_gherkin(
            SAMPLE_PARSED_RECORDING,
            feature_name="Custom Feature Name",
        )

        assert "Feature: Custom Feature Name" in gherkin

    def test_save_feature_file(self, tmp_path: Path) -> None:
        """Test save_feature_file function."""
        output_file = tmp_path / "test.feature"

        save_feature_file(SAMPLE_PARSED_RECORDING, output_file)

        assert output_file.exists()

        content = output_file.read_text()
        assert "Feature: User Login" in content
