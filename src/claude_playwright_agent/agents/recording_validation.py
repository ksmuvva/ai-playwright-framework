"""
Recording validation for Claude Playwright Agent.

This module implements:
- Recording file validation
- Recording structure validation
- Action sequence validation
- Detect problematic patterns
"""

import ast
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """
    Issue found during recording validation.

    Attributes:
        severity: Severity level
        code: Issue code for categorization
        message: Human-readable message
        location: Location in file (line number, etc.)
        suggestion: Suggested fix
    """

    severity: ValidationSeverity
    code: str
    message: str
    location: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """
    Result of recording validation.

    Attributes:
        valid: Whether recording passed validation
        issues: List of issues found
        warnings: Count of warnings
        errors: Count of errors
        actions: Number of actions validated
        duration: Recording duration
    """

    valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    actions: int = 0
    duration: float = 0.0

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add an issue to the result."""
        self.issues.append(issue)
        if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.valid = False

    def get_summary(self) -> dict[str, Any]:
        """Get validation summary."""
        errors = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
        critical = sum(1 for i in self.issues if i.severity == ValidationSeverity.CRITICAL)

        return {
            "valid": self.valid,
            "errors": errors,
            "warnings": warnings,
            "critical": critical,
            "total_issues": len(self.issues),
            "actions": self.actions,
        }


class RecordingValidator:
    """
    Validates Playwright recording files.

    Checks:
    - File existence and format
    - Valid JavaScript syntax
    - Playwright API usage
    - Action sequence validity
    - Common anti-patterns
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self._common_issues = {
            # Hardcoded selectors
            "hardcoded_selector": {
                "patterns": [r'page\.locator\("\$\+"', r'page\.click\("\$\+"'],
                "severity": ValidationSeverity.WARNING,
                "code": "HARDCODED_SELECTOR",
                "message": "Hardcoded selector found",
                "suggestion": "Use data-testid or role-based selectors",
            },
            # Missing waits
            "missing_wait": {
                "patterns": [r'page\.goto\([^)]+\)\s*page\.click'],
                "severity": ValidationSeverity.WARNING,
                "code": "MISSING_WAIT",
                "message": "Navigation without wait",
                "suggestion": "Add wait_for_load_state or wait_for_selector",
            },
            # Fragile selectors
            "fragile_selector": {
                "patterns": [r':nth-of-type\(', r':nth-child\(', r'[0-9]+\]'],
                "severity": ValidationSeverity.WARNING,
                "code": "FRAGILE_SELECTOR",
                "message": "Fragile selector pattern detected",
                "suggestion": "Use stable selectors like text, role, or testid",
            },
        }

    def validate(
        self,
        recording_path: Path,
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate a Playwright recording file.

        Args:
            recording_path: Path to recording file
            strict: Whether to use strict validation

        Returns:
            ValidationResult with all findings
        """
        result = ValidationResult()

        # Check file existence
        if not recording_path.exists():
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                code="FILE_NOT_FOUND",
                message=f"Recording file not found: {recording_path}",
                suggestion="Check the file path",
            ))
            return result

        # Check file extension
        if recording_path.suffix != ".js":
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="WRONG_EXTENSION",
                message=f"Recording file should have .js extension: {recording_path}",
                suggestion="Rename file to .js",
            ))

        # Read and validate content
        try:
            content = recording_path.read_text(encoding="utf-8")
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                code="READ_ERROR",
                message=f"Failed to read recording file: {e}",
                suggestion="Check file permissions and encoding",
            ))
            return result

        # Validate JavaScript syntax
        if not self._validate_syntax(content, result):
            return result

        # Validate Playwright API usage
        self._validate_playwright_api(content, result)

        # Validate action sequence
        self._validate_action_sequence(content, result, strict)

        # Check for common issues
        self._check_common_issues(content, result)

        # Count actions
        result.actions = self._count_actions(content)

        return result

    def _validate_syntax(self, content: str, result: ValidationResult) -> bool:
        """Validate JavaScript syntax."""
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                code="SYNTAX_ERROR",
                message=f"JavaScript syntax error at line {e.lineno}: {e.msg}",
                suggestion="Fix the syntax error",
                location=f"line {e.lineno}",
            ))
            return False

    def _validate_playwright_api(self, content: str, result: ValidationResult) -> None:
        """Validate Playwright API usage."""
        # Check for required Playwright imports
        if "const { chromium" not in content and "from 'playwright'" not in content:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MISSING_IMPORT",
                message="Missing Playwright import",
                suggestion="Add: const { chromium } = require('playwright');",
            ))

        # Check for browser/page context
        if "page" not in content:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_PAGE_CONTEXT",
                message="No page context found",
                suggestion="Ensure recording includes browser.newPage() or page object",
            ))

    def _validate_action_sequence(
        self,
        content: str,
        result: ValidationResult,
        strict: bool,
    ) -> None:
        """Validate action sequence."""
        # Check for empty recording
        if not content.strip() or len(content.strip()) < 50:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EMPTY_RECORDING",
                message="Recording appears to be empty",
                suggestion="Record some actions first",
            ))

        # Check for missing goto
        if "goto" not in content:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="NO_GOTO",
                message="No page navigation (goto) found",
                suggestion="Recordings should usually start with page.goto()",
            ))

        # In strict mode, check for assertion
        if strict and "expect" not in content and "assert" not in content:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="NO_ASSERTIONS",
                message="No assertions found in recording",
                suggestion="Add assertions to verify expected behavior",
            ))

    def _check_common_issues(self, content: str, result: ValidationResult) -> None:
        """Check for common anti-patterns."""
        import re

        for issue_name, issue_config in self._common_issues.items():
            for pattern in issue_config["patterns"]:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1

                    result.add_issue(ValidationIssue(
                        severity=issue_config["severity"],
                        code=issue_config["code"],
                        message=issue_config["message"],
                        suggestion=issue_config["suggestion"],
                        location=f"line {line_num}",
                    ))

    def _count_actions(self, content: str) -> int:
        """Count number of actions in recording."""
        # Common Playwright action methods
        action_methods = [
            "goto", "click", "fill", "type", "press", "check", "uncheck",
            "selectOption", "hover", "dblclick", "screenshot", "waitFor",
            "waitForSelector", "waitForNavigation", "expect",
        ]

        count = 0
        for method in action_methods:
            count += content.count(f"page.{method}(")
            count += content.count(f"locator.{method}(")

        return count

    def validate_batch(
        self,
        recording_paths: list[Path],
        strict: bool = False,
    ) -> dict[str, ValidationResult]:
        """
        Validate multiple recording files.

        Args:
            recording_paths: List of recording file paths
            strict: Whether to use strict validation

        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        for path in recording_paths:
            results[str(path)] = self.validate(path, strict)
        return results
