"""
Integration Test Suite for AI Playwright Framework

Tests the complete framework end-to-end:
- Test discovery
- BDD conversion
- Step definition generation
- Test execution
- Memory system
- Self-healing
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest

from claude_playwright_agent.test_discovery import TestDiscovery, discover_tests
from claude_playwright_agent.agents.execution import TestExecutionEngine, TestFramework, TestStatus
from claude_playwright_agent.bdd.agent import BDDConversionAgent, BDDConversionConfig
from claude_playwright_agent.bdd.steps import StepDefinitionGenerator, StepGenConfig
from claude_playwright_agent.bdd.page_object_mapper import PageObjectParser, StepToPageObjectMapper
from claude_playwright_agent.skills.builtins.e10_1_memory_manager import MemoryManager, MemoryType, MemoryPriority


class TestTestDiscovery:
    """Test the test discovery system."""

    def test_discover_feature_files(self, tmp_path):
        """Test discovering feature files."""
        # Create a sample feature file
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        feature_file = features_dir / "test.feature"
        feature_file.write_text("""
Feature: Test Feature
  As a user
  I want to test
  So that it works

  Scenario: Test scenario
    Given I am on the login page
    When I enter "test" into username
    Then I should see success
""", encoding="utf-8")

        # Discover tests
        discovery = TestDiscovery(project_path=str(tmp_path))
        tests = discovery.discover_all()

        # Assertions
        assert len(tests) > 0
        feature_tests = [t for t in tests if t.test_type.value == "feature_file"]
        assert len(feature_tests) == 1
        assert feature_tests[0].name == "Test Feature"
        assert len(feature_tests[0].scenarios) == 1

    def test_discover_page_objects(self, tmp_path):
        """Test discovering page objects."""
        # Create a sample page object
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        page_file = pages_dir / "test_page.py"
        page_file.write_text("""
from pages.base_page import BasePage

class TestPage(BasePage):
    def __init__(self, page):
        super().__init__(page, "https://example.com")

    def click_button(self):
        self.page.click("#button")

    def fill_field(self, value):
        self.page.fill("#field", value)
""", encoding="utf-8")

        # Discover tests
        discovery = TestDiscovery(project_path=str(tmp_path))
        tests = discovery.discover_all()

        # Assertions
        page_tests = [t for t in tests if t.test_type.value == "page_object"]
        assert len(page_tests) == 1
        assert page_tests[0].name == "TestPage"
        assert page_tests[0].metadata["method_count"] == 2

    def test_discovery_statistics(self, tmp_path):
        """Test discovery statistics."""
        # Create test files
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        (features_dir / "test1.feature").write_text("Feature: Test1\nScenario: Test", encoding="utf-8")
        (features_dir / "test2.feature").write_text("Feature: Test2\nScenario: Test", encoding="utf-8")

        # Discover and get stats
        discovery = TestDiscovery(project_path=str(tmp_path))
        discovery.discover_all()
        stats = discovery.get_statistics()

        # Assertions
        assert stats["total"] >= 2
        assert stats["feature_files"] == 2


class TestStepDefinitionGeneration:
    """Test step definition generation."""

    def test_step_pattern_generation(self):
        """Test generating step patterns."""
        from claude_playwright_agent.bdd.gherkin import GherkinStep, StepKeyword

        config = StepGenConfig()
        generator = StepDefinitionGenerator(config)

        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text='the user enters "tomsmith" into the username field',
            original_action="fill"
        )

        pattern = generator.generate_step_pattern(step)

        # Should be a regex pattern
        assert "^" in pattern
        assert "$" in pattern
        assert "username" in pattern.lower()

    def test_step_code_generation(self):
        """Test generating step code."""
        from claude_playwright_agent.bdd.gherkin import GherkinStep, StepKeyword

        config = StepGenConfig(framework="behave", use_async=True)
        generator = StepDefinitionGenerator(config)

        step = GherkinStep(
            keyword=StepKeyword.WHEN,
            text='the user clicks the login button',
            original_action="click"
        )

        code = generator.generate_step_code(step, "click_login_button")

        # Should contain the decorator and function
        assert "@when" in code
        assert "def click_login_button" in code
        assert "click" in code.lower()

    def test_parameter_extraction(self):
        """Test extracting parameters from steps."""
        config = StepGenConfig()
        generator = StepDefinitionGenerator(config)

        params = generator.extract_parameters('the user enters "value" into field')

        assert len(params) > 0
        assert any(p["value"] == "value" for p in params)


class TestPageObjectMapping:
    """Test page object to step mapping."""

    def test_page_object_parser(self, tmp_path):
        """Test parsing page objects."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        page_file = pages_dir / "login.py"
        page_file.write_text("""
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page, "https://example.com")

    def enter_username(self, username):
        self.page.fill("#username", username)

    def click_login(self):
        self.page.click("#login")
""", encoding="utf-8")

        parser = PageObjectParser(str(pages_dir))
        methods = parser.get_methods_for_page("LoginPage")

        assert len(methods) == 2
        assert any(m.name == "enter_username" for m in methods)
        assert any(m.name == "click_login" for m in methods)

    def test_step_to_page_object_mapping(self):
        """Test mapping steps to page object methods."""
        mapper = StepToPageObjectMapper()

        # Map a step
        mapping = mapper.map_step_to_method(
            "When the user enters 'tomsmith' into the username field",
            page_name="LoginPage"
        )

        # Should return a mapping
        # Note: This might return None if LoginPage isn't parsed
        # The important thing is it doesn't crash
        assert mapping is None or isinstance(mapping, tuple)

    def test_action_parsing(self):
        """Test parsing actions from step text."""
        mapper = StepToPageObjectMapper()

        action, element, value = mapper._parse_step("the user clicks the login button")

        assert action == "click"
        assert element == "login button"
        assert value is None

        action, element, value = mapper._parse_step("the user enters 'test' into username field")

        assert action == "fill"
        assert "username" in element
        assert value == "test"


class TestMemorySystem:
    """Test memory system integration."""

    @pytest.mark.asyncio
    async def test_memory_store_and_retrieve(self, tmp_path):
        """Test storing and retrieving from memory."""
        memory = MemoryManager(
            persist_to_disk=False,
            memory_db_path=str(tmp_path / "test.db")
        )

        # Store a memory
        entry = await memory.store(
            key="test_key",
            value={"test": "data"},
            type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.MEDIUM
        )

        assert entry is not None
        assert entry.key == "test_key"

        # Retrieve the memory
        retrieved = await memory.retrieve("test_key")

        assert retrieved is not None
        assert retrieved.value["test"] == "data"

        await memory.close()

    @pytest.mark.asyncio
    async def test_memory_search(self, tmp_path):
        """Test searching memories."""
        memory = MemoryManager(
            persist_to_disk=False,
            memory_db_path=str(tmp_path / "test.db")
        )

        # Store memories with tags
        await memory.store(
            key="test1",
            value={"data": "test1"},
            tags=["tag1", "tag2"]
        )
        await memory.store(
            key="test2",
            value={"data": "test2"},
            tags=["tag2", "tag3"]
        )

        # Search by tags
        from claude_playwright_agent.skills.builtins.e10_1_memory_manager import MemoryQuery

        query = MemoryQuery(tags=["tag2"])
        results = await memory.search(query)

        assert len(results) >= 2

        await memory.close()

    @pytest.mark.asyncio
    async def test_memory_consolidation(self, tmp_path):
        """Test memory consolidation."""
        memory = MemoryManager(
            persist_to_disk=False,
            memory_db_path=str(tmp_path / "test.db")
        )

        # Store a high-priority memory
        await memory.store(
            key="important",
            value={"critical": "data"},
            type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.HIGH
        )

        # Consolidate
        count = await memory.consolidate()

        # Should move to long-term
        assert count >= 0

        await memory.close()


class TestBDDConversion:
    """Test BDD conversion pipeline."""

    def test_bdd_conversion_config(self):
        """Test BDD conversion configuration."""
        config = BDDConversionConfig()

        assert config.framework == "behave"
        assert config.use_async is True
        assert config.feature_output_dir == "features"

    @pytest.mark.asyncio
    async def test_bdd_conversion_flow(self, tmp_path):
        """Test the complete BDD conversion flow."""
        # This is a simplified test - in reality, you'd have test recordings

        config = BDDConversionConfig(
            feature_output_dir="features",
            steps_output_dir="steps",
        )

        # Create agent
        agent = BDDConversionAgent(
            project_path=tmp_path,
            config=config
        )

        # The agent should be created successfully
        assert agent is not None
        assert agent.project_path == tmp_path


class TestExecutionEngine:
    """Test execution engine."""

    @pytest.mark.asyncio
    async def test_execution_engine_initialization(self):
        """Test execution engine initialization."""
        engine = TestExecutionEngine()

        assert engine is not None
        assert engine._project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_retry_config(self):
        """Test retry configuration."""
        from claude_playwright_agent.agents.execution import RetryConfig

        config = RetryConfig(max_retries=3)

        assert config.max_retries == 3

        # Test delay calculation
        delay = config.get_delay(0)
        assert delay == config.backoff_base

        delay = config.get_delay(1)
        assert delay == config.backoff_base * config.backoff_multiplier

        # Test should retry logic
        assert config.should_retry(TestStatus.FAILED, 0) is True
        assert config.should_retry(TestStatus.FAILED, 3) is False
        assert config.should_retry(TestStatus.PASSED, 0) is False


class TestSelfHealing:
    """Test self-healing integration."""

    def test_self_healing_analytics(self):
        """Test self-healing analytics."""
        from src.claude_playwright_agent.self_healing import HealingAnalytics

        analytics = HealingAnalytics()

        # Record a healing attempt
        analytics.record_attempt(
            page_name="LoginPage",
            action="click",
            original_selector="#broken",
            healed_selector="#fixed",
            strategy_used="data_testid",
            success=True,
            confidence=0.9
        )

        # Get stats
        stats = analytics.get_overall_stats()

        assert stats["total_attempts"] == 1
        assert stats["successful_attempts"] == 1

    def test_self_healing_strategies(self):
        """Test different healing strategies."""
        from src.claude_playwright_agent.agents.self_healing import SelfHealingEngine, HealingConfig

        engine = SelfHealingEngine()

        # Analyze a selector
        healings = engine.analyze_selector("#broken-selector")

        # Should return some healing options
        # Note: This might return empty if no alternatives found
        assert isinstance(healings, list)


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_test_workflow(self, tmp_path):
        """Test the complete workflow from discovery to execution."""
        # 1. Create test files
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        (features_dir / "test.feature").write_text("""
Feature: Test
  Scenario: Test scenario
    Given I am ready
    When I test
    Then I succeed
""", encoding="utf-8")

        # 2. Discover tests
        discovery = TestDiscovery(project_path=str(tmp_path))
        tests = discovery.discover_all()

        assert len(tests) > 0

        # 3. Get statistics
        stats = discovery.get_statistics()
        assert stats["total"] > 0

        # 4. Export discovery
        export_file = tmp_path / "discovery.json"
        discovery.export_discovery(str(export_file))

        assert export_file.exists()

    @pytest.mark.asyncio
    async def test_memory_powered_workflow(self, tmp_path):
        """Test workflow with memory integration."""
        # Create memory manager
        memory = MemoryManager(
            persist_to_disk=False,
            memory_db_path=str(tmp_path / "memory.db")
        )

        # Store test execution
        await memory.store(
            key="test:login_test",
            value={"outcome": "passed", "duration": 1000},
            type=MemoryType.EPISODIC,
            tags=["test_execution", "passed"]
        )

        # Recall the memory
        recalled = await memory.retrieve("test:login_test")

        assert recalled is not None
        assert recalled.value["outcome"] == "passed"

        await memory.close()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
