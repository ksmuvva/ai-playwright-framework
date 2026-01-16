"""
Test Discovery System for AI Playwright Framework

Discovers and catalogs tests from multiple sources:
- BDD feature files (Behave, pytest-bdd)
- Playwright test recordings
- Python test files
- Custom test formats
"""

import ast
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class TestType(str, Enum):
    """Types of tests that can be discovered."""
    BDD_FEATURE = "bdd_feature"
    PLAYWRIGHT_RECORDING = "playwright_recording"
    PYTHON_TEST = "python_test"
    STEP_DEFINITION = "step_definition"


class TestFramework(str, Enum):
    """Test frameworks."""
    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"
    PYTEST = "pytest"
    PLAYWRIGHT = "playwright"


@dataclass
class DiscoveredTest:
    """A discovered test."""
    test_id: str
    name: str
    test_type: TestType
    framework: TestFramework
    file_path: str
    line_number: int = 0
    tags: list[str] = field(default_factory=list)
    description: str = ""
    scenarios: list[str] = field(default_factory=list)  # For BDD features
    steps_count: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "test_type": self.test_type.value,
            "framework": self.framework.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "tags": self.tags,
            "description": self.description,
            "scenarios": self.scenarios,
            "steps_count": self.steps_count,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
        }


class TestDiscovery:
    """
    Discover tests from multiple sources.

    Features:
    - Scan directories for test files
    - Parse BDD feature files
    - Parse Playwright recordings
    - Parse Python test files
    - Extract metadata (tags, descriptions, etc.)
    """

    def __init__(
        self,
        project_path: str = ".",
        features_dir: str = "features",
        recordings_dir: str = "recordings",
        tests_dir: str = "tests",
    ):
        """
        Initialize the test discovery system.

        Args:
            project_path: Root project directory
            features_dir: BDD features directory
            recordings_dir: Playwright recordings directory
            tests_dir: Python tests directory
        """
        self.project_path = Path(project_path)
        self.features_dir = self.project_path / features_dir
        self.recordings_dir = self.project_path / recordings_dir
        self.tests_dir = self.project_path / tests_dir

        self.discovered_tests: dict[str, DiscoveredTest] = {}
        self.tests_by_type: dict[TestType, list[DiscoveredTest]] = defaultdict(list)
        self.tests_by_tag: dict[str, list[DiscoveredTest]] = defaultdict(list)

    def discover_all(self) -> list[DiscoveredTest]:
        """
        Discover all tests in the project.

        Returns:
            List of all discovered tests
        """
        self.discovered_tests.clear()
        self.tests_by_type.clear()
        self.tests_by_tag.clear()

        # Discover different test types
        self._discover_bdd_features()
        self._discover_playwright_recordings()
        self._discover_python_tests()

        # Index tests
        for test in self.discovered_tests.values():
            self.tests_by_type[test.test_type].append(test)
            for tag in test.tags:
                self.tests_by_tag[tag].append(test)

        return list(self.discovered_tests.values())

    def _discover_bdd_features(self) -> None:
        """Discover BDD feature files."""
        if not self.features_dir.exists():
            return

        for feature_file in self.features_dir.rglob("*.feature"):
            tests = self._parse_feature_file(feature_file)
            for test in tests:
                self.discovered_tests[test.test_id] = test

    def _parse_feature_file(self, filepath: Path) -> list[DiscoveredTest]:
        """
        Parse a BDD feature file.

        Args:
            filepath: Path to the feature file

        Returns:
            List of discovered tests
        """
        tests = []
        content = filepath.read_text(encoding="utf-8")

        # Parse feature
        feature_name = ""
        feature_tags = []
        scenarios = []

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Feature name
            if line.startswith("Feature:"):
                feature_name = line.replace("Feature:", "").strip()
                feature_tags = self._extract_tags(line)

            # Scenario
            elif line.startswith("Scenario:"):
                scenario_name = line.replace("Scenario:", "").strip()
                scenario_tags = feature_tags.copy()

                # Look for tags on previous lines
                if i > 1:
                    prev_line = lines[i - 2].strip()
                    if prev_line.startswith("@"):
                        scenario_tags.extend(self._extract_tags(prev_line))

                scenarios.append({
                    "name": scenario_name,
                    "line": i,
                    "tags": scenario_tags,
                })

        # Create test for feature
        if feature_name:
            test_id = f"feature:{filepath.name}:{feature_name}"

            test = DiscoveredTest(
                test_id=test_id,
                name=feature_name,
                test_type=TestType.BDD_FEATURE,
                framework=TestFramework.BEHAVE,
                file_path=str(filepath.relative_to(self.project_path)),
                line_number=0,
                tags=feature_tags,
                description=f"BDD Feature: {feature_name}",
                scenarios=[s["name"] for s in scenarios],
                steps_count=len(scenarios),
            )

            tests.append(test)

            # Create individual tests for scenarios
            for scenario in scenarios:
                scenario_test_id = f"scenario:{filepath.name}:{scenario['name']}"

                scenario_test = DiscoveredTest(
                    test_id=scenario_test_id,
                    name=scenario["name"],
                    test_type=TestType.BDD_FEATURE,
                    framework=TestFramework.BEHAVE,
                    file_path=str(filepath.relative_to(self.project_path)),
                    line_number=scenario["line"],
                    tags=scenario["tags"],
                    description=f"Scenario from {feature_name}",
                    steps_count=0,  # Would need to parse steps
                )

                tests.append(scenario_test)

        return tests

    def _discover_playwright_recordings(self) -> None:
        """Discover Playwright test recordings."""
        if not self.recordings_dir.exists():
            return

        for recording_file in self.recordings_dir.rglob("*.spec.js"):
            tests = self._parse_playwright_recording(recording_file)
            for test in tests:
                self.discovered_tests[test.test_id] = test

    def _parse_playwright_recording(self, filepath: Path) -> list[DiscoveredTest]:
        """
        Parse a Playwright recording file.

        Args:
            filepath: Path to the recording file

        Returns:
            List of discovered tests
        """
        tests = []
        content = filepath.read_text(encoding="utf-8")

        # Extract test names using regex
        test_pattern = r'test\(["\']([^"\']+)["\']'
        matches = re.finditer(test_pattern, content)

        for match in matches:
            test_name = match.group(1)
            test_id = f"recording:{filepath.name}:{test_name}"

            test = DiscoveredTest(
                test_id=test_id,
                name=test_name,
                test_type=TestType.PLAYWRIGHT_RECORDING,
                framework=TestFramework.PLAYWRIGHT,
                file_path=str(filepath.relative_to(self.project_path)),
                description=f"Playwright recording: {test_name}",
            )

            tests.append(test)

        return tests

    def _discover_python_tests(self) -> None:
        """Discover Python test files."""
        if not self.tests_dir.exists():
            return

        # Also check project root for test_*.py files
        test_dirs = [self.tests_dir, self.project_path]

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            for test_file in test_dir.rglob("test_*.py"):
                tests = self._parse_python_test(test_file)
                for test in tests:
                    self.discovered_tests[test.test_id] = test

    def _parse_python_test(self, filepath: Path) -> list[DiscoveredTest]:
        """
        Parse a Python test file.

        Args:
            filepath: Path to the test file

        Returns:
            List of discovered tests
        """
        tests = []

        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_name = node.name
                    test_id = f"python:{filepath.name}:{test_name}"

                    # Extract docstring
                    docstring = ast.get_docstring(node) or ""

                    test = DiscoveredTest(
                        test_id=test_id,
                        name=test_name,
                        test_type=TestType.PYTHON_TEST,
                        framework=TestFramework.PYTEST,
                        file_path=str(filepath.relative_to(self.project_path)),
                        line_number=node.lineno,
                        description=docstring,
                    )

                    tests.append(test)

        except Exception as e:
            print(f"Warning: Failed to parse {filepath}: {e}")

        return tests

    def _extract_tags(self, line: str) -> list[str]:
        """
        Extract tags from a line.

        Args:
            line: Line to parse

        Returns:
            List of tags
        """
        tags = []
        for match in re.finditer(r'@(\w+)', line):
            tags.append(match.group(1))
        return tags

    def get_test_by_id(self, test_id: str) -> Optional[DiscoveredTest]:
        """
        Get a test by ID.

        Args:
            test_id: Test ID

        Returns:
            DiscoveredTest or None
        """
        return self.discovered_tests.get(test_id)

    def get_tests_by_type(self, test_type: TestType) -> list[DiscoveredTest]:
        """
        Get tests by type.

        Args:
            test_type: Test type

        Returns:
            List of tests
        """
        return self.tests_by_type.get(test_type, [])

    def get_tests_by_tag(self, tag: str) -> list[DiscoveredTest]:
        """
        Get tests by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tests
        """
        return self.tests_by_tag.get(tag, [])

    def get_test_statistics(self) -> dict[str, Any]:
        """
        Get statistics about discovered tests.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_tests": len(self.discovered_tests),
            "by_type": {
                test_type.value: len(tests)
                for test_type, tests in self.tests_by_type.items()
            },
            "by_framework": self._count_by_framework(),
            "total_tags": len(self.tests_by_tag),
            "top_tags": self._get_top_tags(10),
        }

    def _count_by_framework(self) -> dict[str, int]:
        """Count tests by framework."""
        counts: dict[str, int] = defaultdict(int)
        for test in self.discovered_tests.values():
            counts[test.framework.value] += 1
        return dict(counts)

    def _get_top_tags(self, limit: int) -> list[tuple[str, int]]:
        """Get most used tags."""
        tag_counts = [(tag, len(tests)) for tag, tests in self.tests_by_tag.items()]
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        return tag_counts[:limit]
