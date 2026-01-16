"""
Failure Analysis Module for Claude Playwright Agent.

This module handles:
- Categorizing test failures
- Suggesting fixes
- Detecting flaky tests
- Analyzing failure patterns
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Failure Models
# =============================================================================


class FailureCategory(str, Enum):
    """Categories of test failures."""

    SELECTOR_NOT_FOUND = "selector_not_found"
    TIMEOUT = "timeout"
    ASSERTION_FAILED = "assertion_failed"
    NAVIGATION_ERROR = "navigation_error"
    NETWORK_ERROR = "network_error"
    JAVASCRIPT_ERROR = "javascript_error"
    ELEMENT_NOT_VISIBLE = "element_not_visible"
    ELEMENT_NOT_INTERACTABLE = "element_not_interactable"
    STALE_ELEMENT = "stale_element"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity levels for failures."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FixSuggestion:
    """Suggested fix for a failure."""

    description: str
    code_snippet: str = ""
    confidence: float = 0.0
    priority: int = 5  # 1-10, 1 = highest
    requires_manual_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "code_snippet": self.code_snippet,
            "confidence": self.confidence,
            "priority": self.priority,
            "requires_manual_review": self.requires_manual_review,
        }


@dataclass
class Failure:
    """A single test failure."""

    test_name: str
    category: FailureCategory
    error_message: str
    stack_trace: str
    severity: Severity
    selector: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    suggestions: list[FixSuggestion] = field(default_factory=list)
    is_flaky: bool = False
    flaky_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "category": self.category.value,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "severity": self.severity.value,
            "selector": self.selector,
            "timestamp": self.timestamp,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "is_flaky": self.is_flaky,
            "flaky_confidence": self.flaky_confidence,
        }


@dataclass
class FailureCluster:
    """Cluster of similar failures."""

    category: FailureCategory
    count: int
    tests_affected: list[str]
    common_selectors: list[str]
    common_patterns: list[str]
    suggested_fixes: list[FixSuggestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "count": self.count,
            "tests_affected": self.tests_affected,
            "common_selectors": self.common_selectors,
            "common_patterns": self.common_patterns,
            "suggested_fixes": [s.to_dict() for s in self.suggested_fixes],
        }


@dataclass
class FlakyTest:
    """Information about a flaky test."""

    test_name: str
    total_runs: int
    failed_runs: int
    pass_rate: float
    last_failure: str
    failure_categories: list[FailureCategory]
    likely_cause: str = ""
    flaky_confidence: float = 0.0  # 0.0 to 1.0, higher = more confident it's flaky
    passes_on_retry_rate: float = 0.0  # Percentage of failures that pass on retry
    inconsistency_score: float = 0.0  # How inconsistent the results are

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "total_runs": self.total_runs,
            "failed_runs": self.failed_runs,
            "pass_rate": self.pass_rate,
            "last_failure": self.last_failure,
            "failure_categories": [c.value for c in self.failure_categories],
            "likely_cause": self.likely_cause,
            "flaky_confidence": self.flaky_confidence,
            "passes_on_retry_rate": self.passes_on_retry_rate,
            "inconsistency_score": self.inconsistency_score,
        }


@dataclass
class AnalysisResult:
    """Result of failure analysis."""

    total_failures: int = 0
    failures: list[Failure] = field(default_factory=list)
    clusters: list[FailureCluster] = field(default_factory=list)
    flaky_tests: list[FlakyTest] = field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_failures": self.total_failures,
            "failures": [f.to_dict() for f in self.failures],
            "clusters": [c.to_dict() for c in self.clusters],
            "flaky_tests": [t.to_dict() for t in self.flaky_tests],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Failure Analyzer
# =============================================================================


class FailureAnalyzer:
    """
    Analyze test failures and provide actionable insights.

    Features:
    - Categorize failures by type
    - Suggest fixes based on patterns
    - Detect flaky tests
    - Cluster similar failures
    """

    # Error patterns for categorization
    ERROR_PATTERNS = {
        FailureCategory.SELECTOR_NOT_FOUND: [
            r"selector.*not found",
            r"element.*not found",
            r"no element matching",
            r"failed to find element",
            r"Target closed",
            r"NoSuchElementError",
        ],
        FailureCategory.TIMEOUT: [
            r"timeout",
            r"timed out",
            r"exceeded.*timeout",
            r"waiting.*failed",
        ],
        FailureCategory.ASSERTION_FAILED: [
            r"assertion",
            r"expected.*actual",
            r"AssertionError",
        ],
        FailureCategory.NAVIGATION_ERROR: [
            r"navigation",
            r"failed to load",
            r"cannot navigate",
            r"net::ERR_",
        ],
        FailureCategory.NETWORK_ERROR: [
            r"network error",
            r"connection",
            r"refused to connect",
            r"CORS",
        ],
        FailureCategory.JAVASCRIPT_ERROR: [
            r"javascript error",
            r"uncaught exception",
            r"ReferenceError",
            r"TypeError",
            r"SyntaxError",
        ],
        FailureCategory.ELEMENT_NOT_VISIBLE: [
            r"not visible",
            r"hidden",
            r"opacity.*0",
            r"display.*none",
        ],
        FailureCategory.ELEMENT_NOT_INTERACTABLE: [
            r"not interactable",
            r"point.*not clickable",
            r"obstructs element",
            r"element.*center",
        ],
        FailureCategory.STALE_ELEMENT: [
            r"stale",
            r"detached from DOM",
            r"element.*no longer attached",
        ],
    }

    def __init__(self) -> None:
        """Initialize the failure analyzer."""
        self._history: dict[str, list[dict[str, Any]]] = {}

    def analyze_execution_result(
        self,
        execution_result: dict[str, Any],
    ) -> AnalysisResult:
        """
        Analyze execution results for failures.

        Args:
            execution_result: Result from TestExecutionEngine

        Returns:
            AnalysisResult with categorized failures and suggestions
        """
        result = AnalysisResult()

        # Extract failed tests
        test_results = execution_result.get("test_results", [])

        for test_result in test_results:
            if test_result.get("status") in ["failed", "error"]:
                failure = self._analyze_single_failure(test_result)
                result.failures.append(failure)

        result.total_failures = len(result.failures)

        # Cluster failures
        result.clusters = self._cluster_failures(result.failures)

        # Generate summary
        result.summary = self._generate_summary(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _analyze_single_failure(self, test_result: dict[str, Any]) -> Failure:
        """Analyze a single test failure."""
        error_message = test_result.get("error_message", "")
        stack_trace = test_result.get("stack_trace", "")

        # Categorize failure
        category = self._categorize_failure(error_message, stack_trace)

        # Determine severity
        severity = self._determine_severity(category, error_message)

        # Extract selector if present
        selector = self._extract_selector(error_message, stack_trace)

        # Generate suggestions
        suggestions = self._generate_suggestions(category, selector, error_message)

        # Check for flakiness
        is_flaky, flaky_confidence = self._check_flakiness(
            test_result.get("name", ""),
            category,
        )

        return Failure(
            test_name=test_result.get("name", "Unknown"),
            category=category,
            error_message=error_message,
            stack_trace=stack_trace,
            severity=severity,
            selector=selector,
            suggestions=suggestions,
            is_flaky=is_flaky,
            flaky_confidence=flaky_confidence,
        )

    def _categorize_failure(
        self,
        error_message: str,
        stack_trace: str,
    ) -> FailureCategory:
        """Categorize a failure based on error patterns."""
        text = f"{error_message} {stack_trace}".lower()

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category

        return FailureCategory.UNKNOWN

    def _determine_severity(
        self,
        category: FailureCategory,
        error_message: str,
    ) -> Severity:
        """Determine severity of a failure."""
        # Critical categories
        if category in [
            FailureCategory.SELECTOR_NOT_FOUND,
            FailureCategory.NAVIGATION_ERROR,
            FailureCategory.NETWORK_ERROR,
        ]:
            return Severity.CRITICAL

        # High severity
        if category in [
            FailureCategory.ASSERTION_FAILED,
            FailureCategory.JAVASCRIPT_ERROR,
        ]:
            return Severity.HIGH

        # Medium severity
        if category in [
            FailureCategory.TIMEOUT,
            FailureCategory.ELEMENT_NOT_INTERACTABLE,
            FailureCategory.STALE_ELEMENT,
        ]:
            return Severity.MEDIUM

        return Severity.LOW

    def _extract_selector(
        self,
        error_message: str,
        stack_trace: str,
    ) -> str:
        """Extract selector from error message."""
        # Look for common selector patterns in error messages
        patterns = [
            r'selector["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'locator["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'[:\s]([#\.\[][a-zA-Z][^\s"\')\]]{3,50})\s',
            r'([#\.\[][a-zA-Z][^\s"\')\]]{3,50})\s+not found',
        ]

        text = f"{error_message} {stack_trace}"

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def _generate_suggestions(
        self,
        category: FailureCategory,
        selector: str,
        error_message: str,
    ) -> list[FixSuggestion]:
        """Generate fix suggestions based on failure category."""
        suggestions = []

        if category == FailureCategory.SELECTOR_NOT_FOUND:
            suggestions.append(
                FixSuggestion(
                    description="Use a more robust selector strategy",
                    code_snippet=f"# Instead of: {selector}\n"
                    f"# Try: page.get_by_role('button', name='Submit')\n"
                    f"# Or: page.locator('[data-testid=\"submit-btn\"]')",
                    confidence=0.8,
                    priority=1,
                )
            )
            suggestions.append(
                FixSuggestion(
                    description="Add explicit wait for element",
                    code_snippet=f"page.wait_for_selector('{selector}', timeout=10000)",
                    confidence=0.7,
                    priority=2,
                )
            )

        elif category == FailureCategory.TIMEOUT:
            suggestions.append(
                FixSuggestion(
                    description="Increase timeout for this operation",
                    code_snippet="page.wait_for_load_state('networkidle', timeout=30000)",
                    confidence=0.6,
                    priority=3,
                )
            )
            suggestions.append(
                FixSuggestion(
                    description="Check for slow network conditions or server delays",
                    code_snippet="# Consider using wait_for_response() for API calls",
                    confidence=0.5,
                    priority=4,
                )
            )

        elif category == FailureCategory.ELEMENT_NOT_INTERACTABLE:
            suggestions.append(
                FixSuggestion(
                    description="Scroll element into view before interaction",
                    code_snippet=f"element.scroll_into_view_if_needed()\n"
                    f"element.click()",
                    confidence=0.9,
                    priority=1,
                )
            )
            suggestions.append(
                FixSuggestion(
                    description="Use force option if element is covered by another",
                    code_snippet="element.click(force=True)",
                    confidence=0.7,
                    priority=3,
                    requires_manual_review=True,
                )
            )

        elif category == FailureCategory.STALE_ELEMENT:
            suggestions.append(
                FixSuggestion(
                    description="Re-locate element before interaction",
                    code_snippet="# Always re-locate element before action\n"
                    f"element = page.locator('{selector}')\n"
                    "element.click()",
                    confidence=0.95,
                    priority=1,
                )
            )

        elif category == FailureCategory.NAVIGATION_ERROR:
            suggestions.append(
                FixSuggestion(
                    description="Verify URL is correct and accessible",
                    code_snippet="# Check URL format and server availability",
                    confidence=0.8,
                    priority=1,
                )
            )

        return suggestions

    def _check_flakiness(
        self,
        test_name: str,
        category: FailureCategory,
    ) -> tuple[bool, float]:
        """
        Check if a test failure is likely due to flakiness.

        Returns:
            Tuple of (is_flaky, confidence)
        """
        # Flaky indicators
        flaky_categories = {
            FailureCategory.TIMEOUT,
            FailureCategory.STALE_ELEMENT,
            FailureCategory.ELEMENT_NOT_INTERACTABLE,
        }

        if category in flaky_categories:
            return True, 0.7

        # Check test history if available
        if test_name in self._history:
            history = self._history[test_name]
            if len(history) >= 3:
                passed = sum(1 for r in history if r.get("status") == "passed")
                pass_rate = passed / len(history)

                # If pass rate is between 30-70%, likely flaky
                if 0.3 < pass_rate < 0.7:
                    return True, 0.9

        return False, 0.0

    def _cluster_failures(self, failures: list[Failure]) -> list[FailureCluster]:
        """Cluster similar failures together."""
        if not failures:
            return []

        clusters_dict: dict[FailureCategory, list[Failure]] = {}

        for failure in failures:
            if failure.category not in clusters_dict:
                clusters_dict[failure.category] = []
            clusters_dict[failure.category].append(failure)

        clusters = []

        for category, category_failures in clusters_dict.items():
            tests_affected = [f.test_name for f in category_failures]

            # Find common selectors
            selectors = [f.selector for f in category_failures if f.selector]
            selector_counter = Counter(selectors)
            common_selectors = [s for s, _ in selector_counter.most_common(5)]

            # Find common patterns
            common_patterns = []
            if category == FailureCategory.SELECTOR_NOT_FOUND:
                if any(":nth-child" in s for s in common_selectors):
                    common_patterns.append("Uses fragile nth-child selectors")
                if any(">" in s and s.count(">") > 2 for s in common_selectors):
                    common_patterns.append("Uses deeply nested selectors")

            # Aggregate suggestions
            all_suggestions = []
            for f in category_failures:
                all_suggestions.extend(f.suggestions)

            # Get top suggestions by confidence
            suggestion_scores = {}
            for suggestion in all_suggestions:
                key = suggestion.description
                if key not in suggestion_scores:
                    suggestion_scores[key] = {
                        "suggestion": suggestion,
                        "count": 0,
                    }
                suggestion_scores[key]["count"] += 1

            top_suggestions = sorted(
                suggestion_scores.values(),
                key=lambda x: (x["count"], x["suggestion"].confidence),
                reverse=True,
            )[:3]

            suggested_fixes = [item["suggestion"] for item in top_suggestions]

            clusters.append(
                FailureCluster(
                    category=category,
                    count=len(category_failures),
                    tests_affected=tests_affected,
                    common_selectors=common_selectors,
                    common_patterns=common_patterns,
                    suggested_fixes=suggested_fixes,
                )
            )

        # Sort by count (most common failures first)
        clusters.sort(key=lambda c: c.count, reverse=True)

        return clusters

    def _generate_summary(self, result: AnalysisResult) -> str:
        """Generate a human-readable summary."""
        if result.total_failures == 0:
            return "All tests passed successfully!"

        lines = [
            f"Found {result.total_failures} test failure(s):",
            "",
        ]

        for cluster in result.clusters[:5]:  # Top 5 clusters
            lines.append(
                f"• {cluster.count}x {cluster.category.value.replace('_', ' ').title()}: "
                f"{', '.join(cluster.tests_affected[:3])}"
                + (f" and {len(cluster.tests_affected) - 3} more" if len(cluster.tests_affected) > 3 else "")
            )

        if result.flaky_tests:
            lines.append("")
            lines.append(f"⚠️  {len(result.flaky_tests)} potentially flaky test(s) detected")

        return "\n".join(lines)

    def _generate_recommendations(self, result: AnalysisResult) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Check for high-priority issues
        for cluster in result.clusters:
            if cluster.category == FailureCategory.SELECTOR_NOT_FOUND and cluster.count >= 3:
                recommendations.append(
                    f"CRITICAL: {cluster.count} selector failures detected. "
                    f"Review selectors: {', '.join(cluster.common_selectors[:3])}"
                )

            if cluster.category == FailureCategory.TIMEOUT and cluster.count >= 2:
                recommendations.append(
                    f"HIGH: {cluster.count} timeout failures. "
                    "Consider increasing timeouts or checking for performance issues."
                )

        # Check for flaky tests
        if result.flaky_tests:
            flaky_names = [t.test_name for t in result.flaky_tests[:3]]
            recommendations.append(
                f"FLAKY: Review tests with inconsistent results: {', '.join(flaky_names)}"
            )

        # General recommendations
        if result.total_failures > 10:
            recommendations.append(
                "Large number of failures detected. Consider running tests in smaller batches."
            )

        return recommendations

    def update_history(self, test_results: list[dict[str, Any]]) -> None:
        """
        Update test history for flakiness detection.

        Args:
            test_results: List of test result dictionaries
        """
        # Keep last 20 runs per test
        for result in test_results:
            test_name = result.get("name", "")
            if not test_name:
                continue

            if test_name not in self._history:
                self._history[test_name] = []

            # Extract retry information for flaky test detection
            retry_count = result.get("retry_count", 0)
            passed_on_retry = (
                result.get("status") == "passed" and
                retry_count > 0 and
                len(result.get("previous_attempts", [])) > 0
            )

            self._history[test_name].append({
                "status": result.get("status", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "retry_count": retry_count,
                "passed_on_retry": passed_on_retry,
                "duration": result.get("duration", 0.0),
            })

            # Trim history
            if len(self._history[test_name]) > 20:
                self._history[test_name] = self._history[test_name][-20:]

    def detect_flaky_tests(
        self,
        min_runs: int = 3,
        flaky_threshold: float = 0.5,
    ) -> list[FlakyTest]:
        """
        Detect flaky tests from history.

        Args:
            min_runs: Minimum number of runs to consider
            flaky_threshold: Pass rate below this is considered flaky

        Returns:
            List of FlakyTest objects
        """
        flaky_tests = []

        for test_name, history in self._history.items():
            if len(history) < min_runs:
                continue

            total = len(history)
            failed = sum(1 for h in history if h.get("status") in ["failed", "error"])
            pass_rate = (total - failed) / total

            # Check if flaky (inconsistent but not completely broken)
            if flaky_threshold < pass_rate < (1.0 - flaky_threshold):
                # Find failure categories and last failure
                categories = set()
                last_failure = ""
                total_retries = 0
                passed_on_retry_count = 0

                # Track result pattern for inconsistency calculation
                results = []

                for h in history:
                    status = h.get("status", "unknown")
                    results.append(1 if status in ["passed", "skipped"] else 0)

                    if status in ["failed", "error"]:
                        last_failure = h.get("timestamp", "")

                    # Track retry behavior
                    retry_count = h.get("retry_count", 0)
                    if retry_count > 0:
                        total_retries += retry_count
                        if h.get("passed_on_retry", False):
                            passed_on_retry_count += 1

                # Calculate flaky_confidence (0.0 to 1.0)
                # Higher confidence with more runs and when pass_rate is near 0.5
                runs_factor = min(total / 10.0, 1.0)  # Max at 10 runs
                flakiness_factor = 1.0 - abs(pass_rate - 0.5) * 2  # 1.0 at 50% pass rate
                flaky_confidence = runs_factor * flakiness_factor

                # Calculate passes_on_retry_rate
                if total_retries > 0:
                    # Percentage of retry attempts that resulted in pass
                    passes_on_retry_rate = passed_on_retry_count / total_retries
                else:
                    passes_on_retry_rate = 0.0

                # Calculate inconsistency_score using variance
                if len(results) > 1:
                    mean = sum(results) / len(results)
                    variance = sum((x - mean) ** 2 for x in results) / len(results)
                    # Normalize to 0-1 range (max variance is 0.25 for binary results)
                    inconsistency_score = min(variance * 4, 1.0)
                else:
                    inconsistency_score = 0.0

                # Determine likely cause based on metrics
                if pass_rate < 0.7:
                    likely_cause = "Frequent failures - check test stability and environment"
                elif passes_on_retry_rate > 0.5:
                    likely_cause = "High retry pass rate - likely timing or race condition"
                elif inconsistency_score > 0.7:
                    likely_cause = "Highly inconsistent results - environment dependency suspected"
                else:
                    likely_cause = "Occasional failures - may be timing-dependent"

                flaky_tests.append(
                    FlakyTest(
                        test_name=test_name,
                        total_runs=total,
                        failed_runs=failed,
                        pass_rate=pass_rate,
                        last_failure=last_failure,
                        failure_categories=list(categories),
                        likely_cause=likely_cause,
                        flaky_confidence=flaky_confidence,
                        passes_on_retry_rate=passes_on_retry_rate,
                        inconsistency_score=inconsistency_score,
                    )
                )

        # Sort by flaky confidence (most confidently flaky first)
        flaky_tests.sort(key=lambda t: t.flaky_confidence, reverse=True)

        return flaky_tests


# =============================================================================
# Convenience Functions
# =============================================================================


def analyze_failures(
    execution_result: dict[str, Any],
) -> AnalysisResult:
    """
    Analyze test execution results for failures.

    Args:
        execution_result: Result from TestExecutionEngine

    Returns:
        AnalysisResult with categorized failures
    """
    analyzer = FailureAnalyzer()
    return analyzer.analyze_execution_result(execution_result)
