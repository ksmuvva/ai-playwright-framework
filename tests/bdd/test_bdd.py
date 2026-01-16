"""
Tests for the BDD Conversion module.

Tests cover:
- Gherkin scenario generation with context
- Step definition generation
- Scenario optimization
- Feature file management
- BDD conversion agent workflow
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from yaml import dump

from claude_playwright_agent.bdd.agent import (
    BDDConversionAgent,
    BDDConversionConfig,
    BDDConversionResult,
    run_bdd_conversion,
)
from claude_playwright_agent.bdd.gherkin import (
    GherkinGenerator,
    GherkinScenario,
    GherkinStep,
    ScenarioOutline,
    ActionStepMapper,
    StepKeyword,
)
from claude_playwright_agent.bdd.steps import StepDefinitionGenerator, StepGenConfig
from claude_playwright_agent.bdd.optimization import (
    ScenarioOptimizer,
    BackgroundSteps,
    TagSuggestion,
)
from claude_playwright_agent.bdd.features import (
    FeatureFileManager,
    FeatureFile,
    FeatureMetadata,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_actions():
    """Create sample actions for testing."""
    return [
        {
            "action_type": "goto",
            "value": "https://example.com/login",
            "page_url": "",
            "line_number": 1,
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
            "page_url": "https://example.com/login",
            "line_number": 5,
        },
        {
            "action_type": "fill",
            "selector": {
                "raw": 'getByLabel("Password")',
                "type": "getByLabel",
                "value": "Password",
                "attributes": {},
            },
            "value": "password123",
            "page_url": "https://example.com/login",
            "line_number": 10,
        },
        {
            "action_type": "click",
            "selector": {
                "raw": 'getByRole("button", { name: "Login" })',
                "type": "getByRole",
                "value": "Login",
                "attributes": {"name": "Login"},
            },
            "page_url": "https://example.com/login",
            "line_number": 15,
        },
    ]


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

    # Create minimal state with deduplicated data
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
                "file_path": "/recordings/login.js",
                "ingested_at": "2024-01-01T00:00:00",
                "status": "completed",
                "actions_count": 4,
                "scenarios_count": 0,
            }
        ],
        "recordings_data": {
            "recording_001": {
                "actions": [
                    {
                        "action_type": "goto",
                        "value": "https://example.com/login",
                        "page_url": "",
                        "line_number": 1,
                    },
                    {
                        "action_type": "fill",
                        "selector": {
                            "raw": 'getByLabel("Email")',
                            "type": "getByLabel",
                            "value": "Email",
                        },
                        "value": "test@example.com",
                        "page_url": "https://example.com/login",
                        "line_number": 5,
                    },
                    {
                        "action_type": "click",
                        "selector": {
                            "raw": 'getByRole("button", { name: "Login" })',
                            "type": "getByRole",
                            "value": "Login",
                        },
                        "page_url": "https://example.com/login",
                        "line_number": 10,
                    },
                ],
                "urls_visited": ["https://example.com/login"],
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
# GherkinStep Tests
# =============================================================================


class TestGherkinStep:
    """Tests for GherkinStep class."""

    def test_step_creation(self) -> None:
        """Test creating a step."""
        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text="the user clicks the login button",
        )

        assert step.keyword == StepKeyword.WHEN
        assert step.text == "the user clicks the login button"
        assert step.line_number == 0

    def test_step_with_context(self) -> None:
        """Test step with full context."""
        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text="the user clicks submit",
            line_number=42,
            recording_id="rec_001",
            page_url="https://example.com",
            original_action="click",
            element_name="submitButton",
            element_selector='getByRole("button", { name: "Submit" })',
        )

        assert step.recording_id == "rec_001"
        assert step.page_url == "https://example.com"
        assert step.original_action == "click"

    def test_step_to_gherkin(self) -> None:
        """Test converting to Gherkin format."""
        step = GherkinStep(
            keyword=StepKeyword.GIVEN,
            text="the user is on the login page",
        )

        gherkin = step.to_gherkin()

        assert "Given" in gherkin
        assert "the user is on the login page" in gherkin

    def test_step_to_dict(self) -> None:
        """Test converting to dictionary."""
        step = GherkinStep(
            keyword=StepKeyword.THEN,
            text="the user should see the dashboard",
        )

        data = step.to_dict()

        assert data["keyword"] == "Then"
        assert data["text"] == "the user should see the dashboard"


# =============================================================================
# GherkinScenario Tests
# =============================================================================


class TestGherkinScenario:
    """Tests for GherkinScenario class."""

    def test_scenario_creation(self) -> None:
        """Test creating a scenario."""
        scenario = GherkinScenario(
            name="Login Scenario",
            scenario_id="scenario_001",
        )

        assert scenario.name == "Login Scenario"
        assert scenario.scenario_id == "scenario_001"
        assert len(scenario.steps) == 0
        assert len(scenario.tags) == 0

    def test_scenario_with_steps(self) -> None:
        """Test scenario with steps."""
        scenario = GherkinScenario(
            name="Test",
            scenario_id="test_001",
        )

        step1 = GherkinStep(StepKeyword.GIVEN, "the user is on the page")
        step2 = GherkinStep(StepKeyword.WHEN, "the user clicks login")
        step3 = GherkinStep(StepKeyword.THEN, "the user should be logged in")

        scenario.add_step(step1)
        scenario.add_step(step2)
        scenario.add_step(step3)

        assert len(scenario.steps) == 3

    def test_scenario_with_tags(self) -> None:
        """Test scenario with tags."""
        scenario = GherkinScenario(
            name="Test",
            scenario_id="test_001",
            tags=["@auth", "@smoke"],
        )

        assert "@auth" in scenario.tags
        assert "@smoke" in scenario.tags

    def test_scenario_to_gherkin(self) -> None:
        """Test converting to Gherkin format."""
        scenario = GherkinScenario(
            name="User Login",
            scenario_id="login_001",
            tags=["@auth"],
        )

        scenario.add_step(GherkinStep(StepKeyword.GIVEN, "the user is on the login page"))
        scenario.add_step(GherkinStep(StepKeyword.WHEN, "the user enters credentials"))
        scenario.add_step(GherkinStep(StepKeyword.THEN, "the user should be logged in"))

        gherkin = scenario.to_gherkin()

        assert "@auth" in gherkin
        assert "Scenario: User Login" in gherkin
        assert "Given the user is on the login page" in gherkin

    def test_scenario_with_background_steps(self) -> None:
        """Test scenario with background steps."""
        scenario = GherkinScenario(
            name="Test",
            scenario_id="test_001",
        )

        bg_step = GherkinStep(StepKeyword.GIVEN, "the user is on the homepage")
        scenario.background_steps.append(bg_step)

        assert len(scenario.background_steps) == 1
        assert scenario.background_steps[0].text == "the user is on the homepage"


# =============================================================================
# GherkinGenerator Tests
# =============================================================================


class TestGherkinGenerator:
    """Tests for GherkinGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        gen = GherkinGenerator()

        assert gen.mapper is not None
        assert len(gen.get_all_scenarios()) == 0

    def test_generate_scenario(self, sample_actions) -> None:
        """Test generating a scenario from actions."""
        gen = GherkinGenerator()

        scenario = gen.generate_scenario(
            name="User Login",
            actions=sample_actions,
            recording_id="rec_001",
            page_url="https://example.com/login",
        )

        assert scenario.name == "User Login"
        assert scenario.recording_id == "rec_001"
        assert len(scenario.steps) == len(sample_actions)

    def test_generate_with_element_names(self, sample_actions) -> None:
        """Test generating with element name mapping."""
        gen = GherkinGenerator()

        element_names = {
            "some_hash": "emailField",
        }

        scenario = gen.generate_scenario(
            name="Test",
            actions=sample_actions,
            element_names=element_names,
        )

        assert scenario is not None

    def test_clear_scenarios(self, sample_actions) -> None:
        """Test clearing generated scenarios."""
        gen = GherkinGenerator()

        gen.generate_scenario(name="Test", actions=sample_actions)
        assert len(gen.get_all_scenarios()) == 1

        gen.clear()
        assert len(gen.get_all_scenarios()) == 0


# =============================================================================
# ActionStepMapper Tests
# =============================================================================


class TestActionStepMapper:
    """Tests for ActionStepMapper class."""

    def test_initialization(self) -> None:
        """Test mapper initialization."""
        mapper = ActionStepMapper()

        assert mapper._element_name_cache == {}

    def test_map_goto_action(self) -> None:
        """Test mapping goto action."""
        mapper = ActionStepMapper()

        step = mapper.map_action_to_step(
            action_type="goto",
            selector=None,
            value="https://example.com",
            page_url="",
        )

        assert "navigate" in step.text.lower()
        assert "https://example.com" in step.text

    def test_map_click_action(self) -> None:
        """Test mapping click action."""
        mapper = ActionStepMapper()

        selector = {
            "raw": 'getByRole("button")',
            "type": "getByRole",
            "value": "button",
        }

        step = mapper.map_action_to_step(
            action_type="click",
            selector=selector,
        )

        assert "click" in step.text.lower()

    def test_map_fill_action(self) -> None:
        """Test mapping fill action."""
        mapper = ActionStepMapper()

        selector = {
            "raw": 'getByLabel("Email")',
            "type": "getByLabel",
            "value": "Email",
        }

        step = mapper.map_action_to_step(
            action_type="fill",
            selector=selector,
            value="test@example.com",
        )

        assert "enter" in step.text.lower() or "fill" in step.text.lower()
        assert "test@example.com" in step.text or "email" in step.text.lower()

    def test_describe_selector(self) -> None:
        """Test selector description generation."""
        mapper = ActionStepMapper()

        # getByRole
        selector = {"type": "getByRole", "value": "button"}
        desc = mapper._describe_selector(selector)
        assert "button" in desc.lower()

        # getByLabel
        selector = {"type": "getByLabel", "value": "Email"}
        desc = mapper._describe_selector(selector)
        assert "email" in desc.lower()

    def test_element_name_cache(self) -> None:
        """Test element name caching."""
        mapper = ActionStepMapper()

        mapper.set_element_name("hash123", "submitButton")
        assert mapper.get_element_name("hash123") == "submitButton"
        assert mapper.get_element_name("unknown") is None


# =============================================================================
# StepDefinitionGenerator Tests
# =============================================================================


class TestStepDefinitionGenerator:
    """Tests for StepDefinitionGenerator class."""

    def test_initialization(self) -> None:
        """Test generator initialization."""
        config = StepGenConfig()
        gen = StepDefinitionGenerator(config)

        assert gen.config == config

    def test_generate_step_pattern(self) -> None:
        """Test pattern generation."""
        gen = StepDefinitionGenerator()

        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text='the user clicks the "Login" button',
        )

        pattern = gen.generate_step_pattern(step)

        assert pattern.startswith("^")
        assert pattern.endswith("$")

    def test_extract_parameters(self) -> None:
        """Test parameter extraction."""
        gen = StepDefinitionGenerator()

        params = gen.extract_parameters('the user enters "test@example.com" into the email field')

        assert len(params) > 0
        assert params[0]["value"] == "test@example.com"

    def test_generate_step_code_behave(self) -> None:
        """Test Behave code generation."""
        config = StepGenConfig(framework="behave")
        gen = StepDefinitionGenerator(config)

        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text="the user clicks the submit button",
            original_action="click",
            element_selector='getByRole("button", { name: "Submit" })',
        )

        code = gen.generate_step_code(step, "step_click_submit")

        assert "@when" in code
        assert "def step_click_submit" in code

    def test_generate_step_code_pytest_bdd(self) -> None:
        """Test pytest-bdd code generation."""
        config = StepGenConfig(framework="pytest-bdd")
        gen = StepDefinitionGenerator(config)

        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text="the user navigates to https://example.com",
            original_action="goto",
        )

        code = gen.generate_step_code(step, "step_navigate")

        assert "@scenario" in code
        assert "def step_navigate" in code


# =============================================================================
# ScenarioOptimizer Tests
# =============================================================================


class TestScenarioOptimizer:
    """Tests for ScenarioOptimizer class."""

    def test_initialization(self) -> None:
        """Test optimizer initialization."""
        optimizer = ScenarioOptimizer()

        assert len(optimizer._backgrounds) == 0

    def test_extract_common_backgrounds(self) -> None:
        """Test background extraction."""
        optimizer = ScenarioOptimizer()

        # Create scenarios with common prefix
        scenarios = []
        for i in range(3):
            scenario = GherkinScenario(
                name=f"Scenario {i}",
                scenario_id=f"scen_{i}",
            )
            scenario.add_step(GherkinStep(StepKeyword.GIVEN, "the user is on the homepage"))
            scenario.add_step(GherkinStep(StepKeyword.WHEN, f"the user clicks button {i}"))
            scenarios.append(scenario)

        backgrounds = optimizer.extract_common_backgrounds(scenarios)

        assert len(backgrounds) > 0
        assert backgrounds[0]["usage_count"] == 3

    def test_generate_tags(self) -> None:
        """Test tag generation."""
        optimizer = ScenarioOptimizer()

        scenario = GherkinScenario(
            name="User Login",
            scenario_id="login_001",
        )
        scenario.add_step(GherkinStep(StepKeyword.GIVEN, "the user is on the login page"))
        scenario.add_step(GherkinStep(StepKeyword.WHEN, "the user enters credentials"))

        tags = optimizer.generate_tags(scenario)

        assert len(tags) > 0

    def test_find_duplicate_scenarios(self) -> None:
        """Test duplicate detection."""
        optimizer = ScenarioOptimizer()

        # Create duplicate scenarios
        scenario1 = GherkinScenario(name="Test", scenario_id="test_1")
        scenario1.add_step(GherkinStep(StepKeyword.GIVEN, "step one"))
        scenario1.add_step(GherkinStep(StepKeyword.WHEN, "step two"))

        scenario2 = GherkinScenario(name="Test", scenario_id="test_2")
        scenario2.add_step(GherkinStep(StepKeyword.GIVEN, "step one"))
        scenario2.add_step(GherkinStep(StepKeyword.WHEN, "step two"))

        duplicates = optimizer.find_duplicate_scenarios([scenario1, scenario2])

        assert len(duplicates) == 1

    def test_get_optimization_stats(self) -> None:
        """Test statistics calculation."""
        optimizer = ScenarioOptimizer()

        scenario = GherkinScenario(
            name="Test",
            scenario_id="test_001",
        )
        for i in range(5):
            scenario.add_step(GherkinStep(StepKeyword.WHEN, f"step {i}"))

        stats = optimizer.get_optimization_stats([scenario])

        assert stats["total_scenarios"] == 1
        assert stats["total_steps"] == 5
        assert stats["avg_steps_per_scenario"] == 5.0


# =============================================================================
# FeatureFileManager Tests
# =============================================================================


class TestFeatureFileManager:
    """Tests for FeatureFileManager class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test manager initialization."""
        mgr = FeatureFileManager(tmp_path / "features")

        assert mgr.output_dir == tmp_path / "features"

    def test_generate_file_name(self) -> None:
        """Test file name generation."""
        mgr = FeatureFileManager(Path("features"))

        name1 = mgr._generate_file_name("Feature: User Login")
        name2 = mgr._generate_file_name("Checkout Flow")
        name3 = mgr._generate_file_name("Feature: API Testing")

        assert "login" in name1.lower()
        assert "checkout" in name2.lower()
        assert "api" in name3.lower()

    def test_format_feature_content(self, tmp_path: Path) -> None:
        """Test feature content formatting."""
        mgr = FeatureFileManager(tmp_path / "features")

        feature = {
            "name": "User Authentication",
            "description": "Tests for user login and logout",
            "scenarios": [],
            "background": None,
            "tags": {"@auth", "@smoke"},
        }

        content = mgr._format_feature_content(feature)

        assert "Feature: User Authentication" in content
        assert "@auth" in content
        assert "@smoke" in content

    def test_write_feature_file(self, tmp_path: Path) -> None:
        """Test writing feature file."""
        mgr = FeatureFileManager(tmp_path / "features")

        scenario = GherkinScenario(name="Test", scenario_id="test_001")
        scenario.add_step(GherkinStep(StepKeyword.GIVEN, "the user is on the page"))

        feature = {
            "name": "Test Feature",
            "description": "",
            "scenarios": [scenario],
            "background": None,
            "tags": set(),
        }

        file_path = mgr.write_feature_file(feature)

        assert file_path is not None
        assert file_path.exists()

    def test_get_stats(self, tmp_path: Path) -> None:
        """Test statistics calculation."""
        mgr = FeatureFileManager(tmp_path / "features")

        scenario = GherkinScenario(name="Test", scenario_id="test_001")
        scenario.add_step(GherkinStep(StepKeyword.GIVEN, "step one"))

        feature = {
            "name": "Test",
            "description": "",
            "scenarios": [scenario],
            "background": None,
            "tags": {"@test"},
        }

        mgr.write_feature_file(feature)

        stats = mgr.get_stats()

        assert stats["total_features"] == 1
        assert stats["total_scenarios"] == 1


# =============================================================================
# BDDConversionAgent Tests
# =============================================================================


class TestBDDConversionAgent:
    """Tests for BDDConversionAgent class."""

    def test_initialization(self, initialized_project: Path) -> None:
        """Test agent initialization."""
        agent = BDDConversionAgent(initialized_project)

        assert agent.agent_id == "bdd_conversion_agent"
        assert agent.agent_type == "bdd_conversion"

    def test_custom_config(self, initialized_project: Path) -> None:
        """Test agent with custom config."""
        config = BDDConversionConfig(
            framework="pytest-bdd",
            use_async=False,
            extract_backgrounds=False,
        )

        agent = BDDConversionAgent(initialized_project, config)

        assert agent.config.framework == "pytest-bdd"
        assert agent.config.use_async is False

    def test_run_conversion(self, initialized_project: Path) -> None:
        """Test running conversion."""
        agent = BDDConversionAgent(initialized_project)

        result = agent.run()

        assert result.success is True
        assert isinstance(result.total_scenarios, int)

    def test_empty_project(self, tmp_path: Path) -> None:
        """Test conversion with empty project."""
        # Create empty state
        cpa_dir = tmp_path / ".cpa"
        cpa_dir.mkdir(parents=True, exist_ok=True)

        state_data = {
            "project": {"name": "empty", "framework_type": "behave"},
            "recordings": [],
            "recordings_data": {},
            "scenarios": {},
            "components": {},
            "page_objects": {},
            "selector_catalog": {},
        }

        (cpa_dir / "state.json").write_text(json.dumps(state_data))

        agent = BDDConversionAgent(tmp_path)
        result = agent.run()

        assert result.success is True
        assert result.total_scenarios == 0


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_run_bdd_conversion(self, initialized_project: Path) -> None:
        """Test run_bdd_conversion function."""
        result = run_bdd_conversion(initialized_project)

        assert isinstance(result, BDDConversionResult)

    def test_actions_to_gherkin(self, sample_actions) -> None:
        """Test actions_to_gherkin convenience function."""
        from claude_playwright_agent.bdd.gherkin import actions_to_gherkin

        gherkin = actions_to_gherkin(sample_actions, "Test Scenario")

        assert "Scenario: Test Scenario" in gherkin
        assert "Given" in gherkin or "When" in gherkin


# =============================================================================
# Integration Tests
# =============================================================================


class TestBDDIntegration:
    """Integration tests for BDD conversion workflow."""

    def test_full_conversion_workflow(self, initialized_project: Path) -> None:
        """Test complete conversion workflow."""
        agent = BDDConversionAgent(initialized_project)

        result = agent.run()

        assert result.success is True
        assert result.total_scenarios >= 0

    def test_feature_and_step_generation(self, tmp_path: Path) -> None:
        """Test feature and step file generation."""
        # Create project with recording
        cpa_dir = tmp_path / ".cpa"
        cpa_dir.mkdir(parents=True, exist_ok=True)

        state_data = {
            "project": {"name": "test", "framework_type": "behave"},
            "recordings": [
                {
                    "recording_id": "rec_001",
                    "file_path": "/test.js",
                    "status": "completed",
                    "actions_count": 3,
                }
            ],
            "recordings_data": {
                "rec_001": {
                    "actions": [
                        {"action_type": "goto", "value": "https://example.com", "line_number": 1},
                        {
                            "action_type": "click",
                            "selector": {"raw": 'getByRole("button")', "type": "getByRole", "value": "button"},
                            "line_number": 2,
                        },
                    ],
                    "urls_visited": ["https://example.com"],
                }
            },
            "scenarios": {},
            "components": {},
            "page_objects": {},
            "selector_catalog": {},
        }

        (cpa_dir / "state.json").write_text(json.dumps(state_data))

        agent = BDDConversionAgent(tmp_path)
        result = agent.run()

        assert result.success is True
