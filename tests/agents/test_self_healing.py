"""
Tests for the Self-Healing Selectors module.

Tests cover:
- HealingStatus and HealingStrategy enums
- SelectorHealing and HealingAttempt models
- SelfHealingEngine initialization
- Selector analysis and healing generation
- Strategy application
- History tracking
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.self_healing import (
    analyze_selector_for_healing,
    heal_selector,
    HealingAttempt,
    HealingConfig,
    HealingStatus,
    HealingStrategy,
    SelectorHealing,
    SelfHealingEngine,
)


# =============================================================================
# Model Tests
# =============================================================================


class TestHealingStatus:
    """Tests for HealingStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum has correct values."""
        assert HealingStatus.PENDING.value == "pending"
        assert HealingStatus.ATTEMPTED.value == "attempted"
        assert HealingStatus.SUCCESS.value == "success"
        assert HealingStatus.FAILED.value == "failed"
        assert HealingStatus.APPROVED.value == "approved"
        assert HealingStatus.REJECTED.value == "rejected"
        assert HealingStatus.AUTO_APPLIED.value == "auto_applied"


class TestHealingStrategy:
    """Tests for HealingStrategy enum."""

    def test_strategy_values(self) -> None:
        """Test strategy enum has correct values."""
        assert HealingStrategy.FALLBACK_SELECTOR.value == "fallback_selector"
        assert HealingStrategy.ARIA_ATTRIBUTES.value == "aria_attributes"
        assert HealingStrategy.DATA_TESTID.value == "data_testid"
        assert HealingStrategy.TEXT_CONTENT.value == "text_content"
        assert HealingStrategy.ROLE_BASED.value == "role_based"
        assert HealingStrategy.PARENT_RELATIVE.value == "parent_relative"
        assert HealingStrategy.SIBLING_RELATIVE.value == "sibling_relative"


class TestSelectorHealing:
    """Tests for SelectorHealing model."""

    def test_create_healing(self) -> None:
        """Test creating a selector healing."""
        healing = SelectorHealing(
            original_selector="#submit-btn",
            healed_selector='[data-testid="submit-btn"]',
            strategy=HealingStrategy.DATA_TESTID,
            status=HealingStatus.PENDING,
            confidence=0.9,
        )

        assert healing.original_selector == "#submit-btn"
        assert healing.healed_selector == '[data-testid="submit-btn"]'
        assert healing.strategy == HealingStrategy.DATA_TESTID
        assert healing.status == HealingStatus.PENDING
        assert healing.confidence == 0.9

    def test_healing_to_dict(self) -> None:
        """Test converting healing to dictionary."""
        healing = SelectorHealing(
            original_selector=".button",
            healed_selector='role="button"',
            strategy=HealingStrategy.ROLE_BASED,
            status=HealingStatus.SUCCESS,
            confidence=0.8,
        )

        data = healing.to_dict()

        assert data["original_selector"] == ".button"
        assert data["healed_selector"] == 'role="button"'
        assert data["strategy"] == "role_based"
        assert data["status"] == "success"
        assert "timestamp" in data


class TestHealingAttempt:
    """Tests for HealingAttempt model."""

    def test_create_attempt(self) -> None:
        """Test creating a healing attempt."""
        healing = SelectorHealing(
            original_selector="#btn",
            healed_selector="#btn2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.ATTEMPTED,
            confidence=0.7,
        )

        attempt = HealingAttempt(
            healing=healing,
            success=True,
            execution_time=1.5,
        )

        assert attempt.healing == healing
        assert attempt.success is True
        assert attempt.execution_time == 1.5

    def test_attempt_to_dict(self) -> None:
        """Test converting attempt to dictionary."""
        healing = SelectorHealing(
            original_selector="button",
            healed_selector='role="button"',
            strategy=HealingStrategy.ROLE_BASED,
            status=HealingStatus.SUCCESS,
            confidence=0.8,
        )

        attempt = HealingAttempt(
            healing=healing,
            success=False,
            error_message="Element not found",
        )

        data = attempt.to_dict()

        assert data["success"] is False
        assert data["error_message"] == "Element not found"
        assert "healing" in data


class TestHealingConfig:
    """Tests for HealingConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = HealingConfig()

        assert config.enabled is True
        assert config.max_attempts == 3
        assert config.auto_apply_threshold == 0.8
        assert config.require_approval is True
        assert config.track_history is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = HealingConfig(
            enabled=False,
            max_attempts=5,
            auto_apply_threshold=0.9,
        )

        assert config.enabled is False
        assert config.max_attempts == 5
        assert config.auto_apply_threshold == 0.9

    def test_config_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = HealingConfig(
            allowed_strategies=[
                HealingStrategy.DATA_TESTID,
                HealingStrategy.ROLE_BASED,
            ],
        )

        data = config.to_dict()

        assert data["enabled"] is True
        assert data["max_attempts"] == 3
        assert len(data["allowed_strategies"]) == 2


# =============================================================================
# SelfHealingEngine Tests
# =============================================================================


class TestSelfHealingEngine:
    """Tests for SelfHealingEngine class."""

    def test_initialization(self) -> None:
        """Test engine initialization."""
        engine = SelfHealingEngine()

        assert engine._config.enabled is True
        assert engine._history == []

    def test_initialization_with_config(self) -> None:
        """Test engine initialization with custom config."""
        config = HealingConfig(
            enabled=False,
            max_attempts=5,
        )
        engine = SelfHealingEngine(config)

        assert engine._config.enabled is False
        assert engine._config.max_attempts == 5

    def test_analyze_empty_selector(self) -> None:
        """Test analyzing an empty selector."""
        engine = SelfHealingEngine()

        healings = engine.analyze_selector("")

        assert healings == []

    def test_analyze_selector_with_nth_child(self) -> None:
        """Test analyzing selector with nth-child."""
        engine = SelfHealingEngine()

        healings = engine.analyze_selector("div > ul > li:nth-child(2) > a")

        assert len(healings) > 0

        # Check that nth-child was removed
        fallback_healings = [
            h for h in healings
            if h.strategy == HealingStrategy.FALLBACK_SELECTOR
        ]
        assert any(":nth-child" not in h.healed_selector for h in fallback_healings)

    def test_analyze_selector_for_button(self) -> None:
        """Test analyzing button selector."""
        engine = SelfHealingEngine()

        healings = engine.analyze_selector("button.submit")

        assert len(healings) > 0

        # Should have ARIA-based alternative
        aria_healings = [
            h for h in healings
            if h.strategy == HealingStrategy.ARIA_ATTRIBUTES
        ]
        assert len(aria_healings) > 0

    def test_analyze_selector_for_id(self) -> None:
        """Test analyzing ID selector."""
        engine = SelfHealingEngine()

        healings = engine.analyze_selector("#submit-btn")

        assert len(healings) > 0

        # Should have data-testid alternative
        data_healings = [
            h for h in healings
            if h.strategy == HealingStrategy.DATA_TESTID
        ]
        assert len(data_healings) > 0

    def test_heal_selector_success(self) -> None:
        """Test successful selector healing."""
        engine = SelfHealingEngine()

        attempt = engine.heal_selector("#submit-btn", "test_login")

        assert attempt.healing.original_selector == "#submit-btn"
        assert attempt.healing.test_name == "test_login"
        assert len(attempt.healing.healed_selector) > 0

    def test_heal_selector_no_options(self) -> None:
        """Test healing with no available options."""
        engine = SelfHealingEngine()

        # Use a selector that's unlikely to have alternatives
        attempt = engine.heal_selector("")

        assert attempt.success is False
        assert "No healing options" in attempt.error_message

    def test_approve_healing(self) -> None:
        """Test approving a healing."""
        engine = SelfHealingEngine()

        healing = SelectorHealing(
            original_selector="#btn",
            healed_selector="#btn2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.PENDING,
            confidence=0.7,
        )

        approved = engine.approve_healing(healing, "user")

        assert approved.status == HealingStatus.APPROVED
        assert approved.approved_by == "user"

    def test_reject_healing(self) -> None:
        """Test rejecting a healing."""
        engine = SelfHealingEngine()

        healing = SelectorHealing(
            original_selector="#btn",
            healed_selector="#btn2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.PENDING,
            confidence=0.7,
        )

        rejected = engine.reject_healing(healing, "Too generic")

        assert rejected.status == HealingStatus.REJECTED
        assert rejected.rejection_reason == "Too generic"

    def test_get_history_empty(self) -> None:
        """Test getting history when empty."""
        engine = SelfHealingEngine()

        history = engine.get_history()

        assert history == []

    def test_get_history_with_selector_filter(self) -> None:
        """Test getting history filtered by selector."""
        engine = SelfHealingEngine()

        # Add some history
        engine._add_to_history(SelectorHealing(
            original_selector="#btn1",
            healed_selector="#btn2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.SUCCESS,
            confidence=0.8,
        ))

        engine._add_to_history(SelectorHealing(
            original_selector="#other",
            healed_selector="#other2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.SUCCESS,
            confidence=0.7,
        ))

        # Filter by selector
        history = engine.get_history(selector="#btn1")

        assert len(history) == 1
        assert history[0].original_selector == "#btn1"

    def test_get_statistics_empty(self) -> None:
        """Test getting statistics when empty."""
        engine = SelfHealingEngine()

        stats = engine.get_statistics()

        assert stats["total_healings"] == 0
        assert stats["successful"] == 0
        assert stats["success_rate"] == 0.0

    def test_get_statistics_with_history(self) -> None:
        """Test getting statistics with history."""
        engine = SelfHealingEngine()

        # Add some history
        engine._add_to_history(SelectorHealing(
            original_selector="#btn1",
            healed_selector="#btn2",
            strategy=HealingStrategy.FALLBACK_SELECTOR,
            status=HealingStatus.SUCCESS,
            confidence=0.8,
        ))

        engine._add_to_history(SelectorHealing(
            original_selector="#other",
            healed_selector="#other2",
            strategy=HealingStrategy.DATA_TESTID,
            status=HealingStatus.SUCCESS,
            confidence=0.9,
        ))

        stats = engine.get_statistics()

        assert stats["total_healings"] == 2
        assert stats["successful"] == 2
        assert stats["success_rate"] == 1.0

    def test_history_trimming(self) -> None:
        """Test that history is trimmed to max size."""
        config = HealingConfig(history_size=5)
        engine = SelfHealingEngine(config)

        # Add more than history_size items
        for i in range(10):
            engine._add_to_history(SelectorHealing(
                original_selector=f"#btn{i}",
                healed_selector=f"#btn{i+1}",
                strategy=HealingStrategy.FALLBACK_SELECTOR,
                status=HealingStatus.SUCCESS,
                confidence=0.8,
            ))

        history = engine.get_history()

        assert len(history) == 5


class TestStrategyGeneration:
    """Tests for individual strategy generation methods."""

    def test_generate_fallback_selectors(self) -> None:
        """Test fallback selector generation."""
        engine = SelfHealingEngine()

        healings = engine._generate_fallback_selectors("li:nth-child(2)")

        assert len(healings) > 0
        assert any(":nth-child" not in h.healed_selector for h in healings)

    def test_generate_aria_alternatives(self) -> None:
        """Test ARIA alternative generation."""
        engine = SelfHealingEngine()

        healings = engine._generate_aria_alternatives("button.submit")

        assert len(healings) > 0
        assert any('role="button"' in h.healed_selector for h in healings)

    def test_generate_data_testid_alternatives(self) -> None:
        """Test data-testid alternative generation."""
        engine = SelfHealingEngine()

        healings = engine._generate_data_testid_alternatives("#submit-button")

        assert len(healings) > 0
        assert any('[data-testid="submit-button"]' in h.healed_selector for h in healings)

    def test_generate_role_based_alternatives(self) -> None:
        """Test role-based alternative generation."""
        engine = SelfHealingEngine()

        healings = engine._generate_role_based_alternatives("input.username")

        assert len(healings) > 0
        assert any("get_by_role" in h.healed_selector for h in healings)

    def test_generate_text_based_alternatives(self) -> None:
        """Test text-based alternative generation."""
        engine = SelfHealingEngine()

        page_context = {"text_content": "Submit"}

        healings = engine._generate_text_based_alternatives(
            "#submit-btn",
            page_context,
        )

        assert len(healings) > 0
        assert any("text" in h.strategy.value for h in healings)

    def test_generate_parent_relative_alternatives(self) -> None:
        """Test parent-relative alternative generation."""
        engine = SelfHealingEngine()

        healings = engine._generate_parent_relative_alternatives("form > div > button")

        assert len(healings) > 0
        assert any("*" in h.healed_selector for h in healings)

    def test_generate_sibling_relative_alternatives(self) -> None:
        """Test sibling-relative alternative generation."""
        engine = SelfHealingEngine()

        # Pattern requires both selectors to start with . or [
        healings = engine._generate_sibling_relative_alternatives(".field .input")

        assert len(healings) > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_analyze_selector_for_healing(self) -> None:
        """Test analyze_selector_for_healing convenience function."""
        healings = analyze_selector_for_healing("#submit-btn")

        assert isinstance(healings, list)

    def test_heal_selector_convenience(self) -> None:
        """Test heal_selector convenience function."""
        attempt = heal_selector("#submit-btn", "test_login")

        assert isinstance(attempt, HealingAttempt)
        assert attempt.healing.original_selector == "#submit-btn"
