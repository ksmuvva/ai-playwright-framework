"""
Tests for the Failure Analysis module.

Tests cover:
- FailureCategory and Severity enums
- FixSuggestion and Failure models
- FailureAnalyzer initialization
- Failure categorization
- Suggestion generation
- Flaky test detection
- Failure clustering
"""

from pathlib import Path

import pytest

from claude_playwright_agent.agents.failure_analysis import (
    analyze_failures,
    Failure,
    FailureAnalyzer,
    FailureCategory,
    FailureCluster,
    FlakyTest,
    FixSuggestion,
    Severity,
)


# =============================================================================
# Model Tests
# =============================================================================


class TestFixSuggestion:
    """Tests for FixSuggestion model."""

    def test_create_suggestion(self) -> None:
        """Test creating a fix suggestion."""
        suggestion = FixSuggestion(
            description="Use a better selector",
            code_snippet='page.get_by_role("button")',
            confidence=0.9,
            priority=1,
        )

        assert suggestion.description == "Use a better selector"
        assert suggestion.code_snippet == 'page.get_by_role("button")'
        assert suggestion.confidence == 0.9
        assert suggestion.priority == 1
        assert suggestion.requires_manual_review is True

    def test_suggestion_to_dict(self) -> None:
        """Test converting suggestion to dictionary."""
        suggestion = FixSuggestion(
            description="Add explicit wait",
            code_snippet="page.wait_for_selector('.btn')",
        )

        data = suggestion.to_dict()

        assert data["description"] == "Add explicit wait"
        assert data["code_snippet"] == "page.wait_for_selector('.btn')"
        assert data["confidence"] == 0.0
        assert data["priority"] == 5


class TestFailure:
    """Tests for Failure model."""

    def test_create_failure(self) -> None:
        """Test creating a failure."""
        failure = Failure(
            test_name="login test",
            category=FailureCategory.SELECTOR_NOT_FOUND,
            error_message="Element not found",
            stack_trace="at test_login.py:42",
            severity=Severity.CRITICAL,
            selector="#submit-btn",
        )

        assert failure.test_name == "login test"
        assert failure.category == FailureCategory.SELECTOR_NOT_FOUND
        assert failure.severity == Severity.CRITICAL
        assert failure.selector == "#submit-btn"

    def test_failure_to_dict(self) -> None:
        """Test converting failure to dictionary."""
        failure = Failure(
            test_name="checkout test",
            category=FailureCategory.TIMEOUT,
            error_message="Timeout exceeded",
            stack_trace="at test_checkout.py:10",
            severity=Severity.HIGH,
        )

        data = failure.to_dict()

        assert data["test_name"] == "checkout test"
        assert data["category"] == "timeout"
        assert data["severity"] == "high"
        assert "timestamp" in data


class TestFailureCluster:
    """Tests for FailureCluster model."""

    def test_create_cluster(self) -> None:
        """Test creating a failure cluster."""
        cluster = FailureCluster(
            category=FailureCategory.SELECTOR_NOT_FOUND,
            count=3,
            tests_affected=["test1", "test2", "test3"],
            common_selectors=["#btn", ".submit"],
            common_patterns=["nth-child used"],
        )

        assert cluster.category == FailureCategory.SELECTOR_NOT_FOUND
        assert cluster.count == 3
        assert len(cluster.tests_affected) == 3
        assert "#btn" in cluster.common_selectors

    def test_cluster_to_dict(self) -> None:
        """Test converting cluster to dictionary."""
        cluster = FailureCluster(
            category=FailureCategory.TIMEOUT,
            count=2,
            tests_affected=["test_a", "test_b"],
            common_selectors=[".loader"],
            common_patterns=[],
        )

        data = cluster.to_dict()

        assert data["category"] == "timeout"
        assert data["count"] == 2
        assert len(data["tests_affected"]) == 2


class TestFlakyTest:
    """Tests for FlakyTest model."""

    def test_create_flaky_test(self) -> None:
        """Test creating a flaky test."""
        flaky = FlakyTest(
            test_name="unstable test",
            total_runs=10,
            failed_runs=4,
            pass_rate=0.6,
            last_failure="2025-01-11T10:00:00",
            failure_categories=[FailureCategory.TIMEOUT],
            likely_cause="Race condition",
        )

        assert flaky.test_name == "unstable test"
        assert flaky.pass_rate == 0.6
        assert flaky.likely_cause == "Race condition"

    def test_flaky_test_to_dict(self) -> None:
        """Test converting flaky test to dictionary."""
        flaky = FlakyTest(
            test_name="timing test",
            total_runs=5,
            failed_runs=2,
            pass_rate=0.6,
            last_failure="2025-01-11T10:00:00",
            failure_categories=[],
        )

        data = flaky.to_dict()

        assert data["test_name"] == "timing test"
        assert data["pass_rate"] == 0.6
        assert "failure_categories" in data


# =============================================================================
# FailureAnalyzer Tests
# =============================================================================


class TestFailureAnalyzer:
    """Tests for FailureAnalyzer class."""

    def test_initialization(self) -> None:
        """Test analyzer initialization."""
        analyzer = FailureAnalyzer()

        assert analyzer._history == {}

    def test_categorize_selector_not_found(self) -> None:
        """Test categorizing selector not found error."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Element not found: #submit",
            "at test_login.py:10",
        )

        assert category == FailureCategory.SELECTOR_NOT_FOUND

    def test_categorize_timeout(self) -> None:
        """Test categorizing timeout error."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Timeout exceeded: 30000ms",
            "at test_checkout.py:25",
        )

        assert category == FailureCategory.TIMEOUT

    def test_categorize_assertion_failed(self) -> None:
        """Test categorizing assertion error."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "AssertionError: Expected 'success' but got 'error'",
            "at test_api.py:15",
        )

        assert category == FailureCategory.ASSERTION_FAILED

    def test_categorize_unknown(self) -> None:
        """Test categorizing unknown error."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Something unexpected happened",
            "at test_unknown.py:1",
        )

        assert category == FailureCategory.UNKNOWN

    def test_determine_severity_for_selector_not_found(self) -> None:
        """Test severity for selector not found."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.SELECTOR_NOT_FOUND,
            "Element not found",
        )

        assert severity == Severity.CRITICAL

    def test_determine_severity_for_timeout(self) -> None:
        """Test severity for timeout."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.TIMEOUT,
            "Timeout exceeded",
        )

        assert severity == Severity.MEDIUM

    def test_determine_severity_for_assertion(self) -> None:
        """Test severity for assertion failure."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.ASSERTION_FAILED,
            "AssertionError",
        )

        assert severity == Severity.HIGH

    def test_extract_selector_from_error(self) -> None:
        """Test extracting selector from error message."""
        analyzer = FailureAnalyzer()

        selector = analyzer._extract_selector(
            "Element #submit-btn not found",
            "at test.py:10",
        )

        assert selector == "#submit-btn"

    def test_generate_suggestions_for_selector_not_found(self) -> None:
        """Test generating suggestions for selector not found."""
        analyzer = FailureAnalyzer()

        suggestions = analyzer._generate_suggestions(
            FailureCategory.SELECTOR_NOT_FOUND,
            "#submit",
            "Element not found",
        )

        assert len(suggestions) > 0
        assert any("robust selector" in s.description.lower() for s in suggestions)

    def test_generate_suggestions_for_timeout(self) -> None:
        """Test generating suggestions for timeout."""
        analyzer = FailureAnalyzer()

        suggestions = analyzer._generate_suggestions(
            FailureCategory.TIMEOUT,
            ".loader",
            "Timeout exceeded",
        )

        assert len(suggestions) > 0
        assert any("timeout" in s.description.lower() for s in suggestions)

    def test_generate_suggestions_for_stale_element(self) -> None:
        """Test generating suggestions for stale element."""
        analyzer = FailureAnalyzer()

        suggestions = analyzer._generate_suggestions(
            FailureCategory.STALE_ELEMENT,
            "#button",
            "Element is no longer attached to DOM",
        )

        assert len(suggestions) > 0
        assert any("re-locate" in s.description.lower() for s in suggestions)

    def test_analyze_execution_result_no_failures(self) -> None:
        """Test analyzing execution with no failures."""
        analyzer = FailureAnalyzer()

        result = analyzer.analyze_execution_result({
            "test_results": [
                {"name": "test1", "status": "passed", "duration": 1.0},
                {"name": "test2", "status": "passed", "duration": 1.5},
            ],
        })

        assert result.total_failures == 0
        assert len(result.failures) == 0

    def test_analyze_execution_result_with_failures(self) -> None:
        """Test analyzing execution with failures."""
        analyzer = FailureAnalyzer()

        result = analyzer.analyze_execution_result({
            "test_results": [
                {"name": "test1", "status": "passed", "duration": 1.0},
                {
                    "name": "test2",
                    "status": "failed",
                    "error_message": "Element #submit not found",
                    "stack_trace": "at test.py:10",
                },
            ],
        })

        assert result.total_failures == 1
        assert len(result.failures) == 1
        assert result.failures[0].test_name == "test2"
        assert result.failures[0].category == FailureCategory.SELECTOR_NOT_FOUND

    def test_cluster_failures(self) -> None:
        """Test failure clustering."""
        analyzer = FailureAnalyzer()

        failures = [
            Failure(
                test_name="test1",
                category=FailureCategory.SELECTOR_NOT_FOUND,
                error_message="Element not found",
                stack_trace="",
                severity=Severity.CRITICAL,
                selector="#btn1",
            ),
            Failure(
                test_name="test2",
                category=FailureCategory.SELECTOR_NOT_FOUND,
                error_message="Element not found",
                stack_trace="",
                severity=Severity.CRITICAL,
                selector="#btn2",
            ),
            Failure(
                test_name="test3",
                category=FailureCategory.TIMEOUT,
                error_message="Timeout",
                stack_trace="",
                severity=Severity.MEDIUM,
            ),
        ]

        clusters = analyzer._cluster_failures(failures)

        assert len(clusters) == 2
        assert any(c.category == FailureCategory.SELECTOR_NOT_FOUND for c in clusters)
        assert any(c.category == FailureCategory.TIMEOUT for c in clusters)

        selector_cluster = next(c for c in clusters if c.category == FailureCategory.SELECTOR_NOT_FOUND)
        assert selector_cluster.count == 2

    def test_generate_summary(self) -> None:
        """Test summary generation."""
        analyzer = FailureAnalyzer()

        result = analyzer.analyze_execution_result({
            "test_results": [
                {
                    "name": "login_test",
                    "status": "failed",
                    "error_message": "Element #submit not found",
                    "stack_trace": "",
                },
                {
                    "name": "checkout_test",
                    "status": "failed",
                    "error_message": "Timeout exceeded",
                    "stack_trace": "",
                },
            ],
        })

        summary = result.summary

        assert "2 test failure" in summary
        assert "selector not found" in summary.lower()
        assert "timeout" in summary.lower()

    def test_update_history(self) -> None:
        """Test updating test history."""
        analyzer = FailureAnalyzer()

        test_results = [
            {"name": "test1", "status": "passed", "duration": 1.0},
            {"name": "test2", "status": "failed", "duration": 2.0},
        ]

        analyzer.update_history(test_results)

        assert "test1" in analyzer._history
        assert "test2" in analyzer._history
        assert len(analyzer._history["test1"]) == 1
        assert analyzer._history["test1"][0]["status"] == "passed"

    def test_detect_flaky_tests(self) -> None:
        """Test flaky test detection."""
        analyzer = FailureAnalyzer()

        # Create inconsistent history - 60% pass rate (6 passed, 4 failed)
        # With threshold=0.3, this is flaky since: 0.3 < 0.6 < 0.7
        statuses = ["passed", "passed", "failed", "passed", "failed", "passed", "passed", "failed", "passed", "failed"]
        analyzer._history["flaky_test"] = [
            {"status": statuses[i], "timestamp": f"2025-01-11T10:0{i}:00"}
            for i in range(10)
        ]

        flaky = analyzer.detect_flaky_tests(flaky_threshold=0.3)

        assert len(flaky) > 0
        assert any(t.test_name == "flaky_test" for t in flaky)

    def test_detect_flaky_insufficient_runs(self) -> None:
        """Test flaky detection with insufficient runs."""
        analyzer = FailureAnalyzer()

        analyzer._history["new_test"] = [
            {"status": "passed", "timestamp": "2025-01-11T10:00:00"},
            {"status": "failed", "timestamp": "2025-01-11T10:01:00"},
        ]

        flaky = analyzer.detect_flaky_tests(min_runs=3)

        assert not any(t.test_name == "new_test" for t in flaky)

    def test_detect_flaky_stable_passing(self) -> None:
        """Test flaky detection with stable passing test."""
        analyzer = FailureAnalyzer()

        analyzer._history["stable_test"] = [
            {"status": "passed", "timestamp": f"2025-01-11T10:0{i}:00"}
            for i in range(10)
        ]

        flaky = analyzer.detect_flaky_tests()

        assert not any(t.test_name == "stable_test" for t in flaky)

    def test_detect_flaky_stable_failing(self) -> None:
        """Test flaky detection with stable failing test."""
        analyzer = FailureAnalyzer()

        analyzer._history["broken_test"] = [
            {"status": "failed", "timestamp": f"2025-01-11T10:0{i}:00"}
            for i in range(10)
        ]

        flaky = analyzer.detect_flaky_tests()

        assert not any(t.test_name == "broken_test" for t in flaky)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_analyze_failures(self) -> None:
        """Test analyze_failures convenience function."""
        result = analyze_failures({
            "test_results": [
                {
                    "name": "test1",
                    "status": "failed",
                    "error_message": "Element not found",
                    "stack_trace": "",
                },
            ],
        })

        assert result.total_failures == 1
        assert len(result.failures) == 1


class TestCategoryPatterns:
    """Tests for category-specific patterns."""

    def test_navigation_error_detection(self) -> None:
        """Test navigation error categorization."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Navigation failed to load",
            "net::ERR_CONNECTION_REFUSED",
        )

        assert category == FailureCategory.NAVIGATION_ERROR

    def test_javascript_error_detection(self) -> None:
        """Test JavaScript error categorization."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "JavaScript error: Uncaught ReferenceError",
            "",
        )

        assert category == FailureCategory.JAVASCRIPT_ERROR

    def test_element_not_visible_detection(self) -> None:
        """Test element not visible categorization."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Element is not visible",
            "opacity: 0",
        )

        assert category == FailureCategory.ELEMENT_NOT_VISIBLE

    def test_element_not_interactable_detection(self) -> None:
        """Test element not interactable categorization."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "Element is not interactable",
            "point is not clickable",
        )

        assert category == FailureCategory.ELEMENT_NOT_INTERACTABLE

    def test_stale_element_detection(self) -> None:
        """Test stale element categorization."""
        analyzer = FailureAnalyzer()

        category = analyzer._categorize_failure(
            "StaleElementError",
            "detached from DOM",
        )

        assert category == FailureCategory.STALE_ELEMENT


class TestSeverityMapping:
    """Tests for severity mapping."""

    def test_network_error_is_critical(self) -> None:
        """Test network error gets critical severity."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.NETWORK_ERROR,
            "Connection refused",
        )

        assert severity == Severity.CRITICAL

    def test_assertion_is_high(self) -> None:
        """Test assertion gets high severity."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.ASSERTION_FAILED,
            "Expected 1, got 2",
        )

        assert severity == Severity.HIGH

    def test_unknown_is_low(self) -> None:
        """Test unknown gets low severity."""
        analyzer = FailureAnalyzer()

        severity = analyzer._determine_severity(
            FailureCategory.UNKNOWN,
            "Unknown error",
        )

        assert severity == Severity.LOW
