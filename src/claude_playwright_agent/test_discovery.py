"""
Test Discovery System for AI Playwright Framework

Discovers and catalogs all tests in the project, including:
- Feature files (Gherkin scenarios)
- Playwright test recordings
- Page object methods
- Step definitions
- Test metadata
"""

import ast
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TestType(str, Enum):
    """Types of tests in the framework."""

    FEATURE_FILE = "feature_file"
    PLAYWRIGHT_RECORDING = "playwright_recording"
    STEP_DEFINITION = "step_definition"
    PAGE_OBJECT = "page_object"


class TestDiscoveryStatus(str, Enum):
    """Status of discovered tests."""

    READY = "ready"
    NEEDS_STEPS = "needs_steps"
    NEEDS_PAGE_OBJECTS = "needs_page_objects"
    INCOMPLETE = "incomplete"
    ERROR = "error"


@dataclass
class DiscoveredTest:
    """A discovered test or test artifact."""

    test_type: TestType
    name: str
    path: str
    status: TestDiscoveryStatus
    metadata: dict[str, Any] = field(default_factory=dict)
    scenarios: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_type": self.test_type.value,
            "name": self.name,
            "path": str(self.path),
            "status": self.status.value,
            "metadata": self.metadata,
            "scenarios": self.scenarios,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "discovered_at": self.discovered_at,
        }


class TestDiscovery:
    """
    Discover and catalog all tests in the project.

    Scans the project for:
    - Feature files (.feature)
    - Playwright recordings (.spec.js, .spec.ts)
    - Step definition files (steps/*.py)
    - Page object files (pages/*.py)
    """

    def __init__(
        self,
        project_path: str = ".",
        features_dir: str = "features",
        recordings_dir: str = "recordings",
        steps_dir: str = "steps",
        pages_dir: str = "pages",
    ):
        """
        Initialize the test discovery system.

        Args:
            project_path: Root project directory
            features_dir: Features directory (default: features)
            recordings_dir: Recordings directory (default: recordings)
            steps_dir: Steps directory (default: steps)
            pages_dir: Pages directory (default: pages)
        """
        self.project_path = Path(project_path)
        self.features_dir = self.project_path / features_dir
        self.recordings_dir = self.project_path / recordings_dir
        self.steps_dir = self.project_path / steps_dir
        self.pages_dir = self.project_path / pages_dir

        self.discovered_tests: list[DiscoveredTest] = []

    def discover_all(self) -> list[DiscoveredTest]:
        """
        Discover all tests in the project.

        Returns:
            List of discovered tests
        """
        self.discovered_tests = []

        # Discover feature files
        self.discovered_tests.extend(self._discover_feature_files())

        # Discover playwright recordings
        self.discovered_tests.extend(self._discover_playwright_recordings())

        # Discover step definitions
        self.discovered_tests.extend(self._discover_step_definitions())

        # Discover page objects
        self.discovered_tests.extend(self._discover_page_objects())

        # Analyze dependencies
        self._analyze_dependencies()

        return self.discovered_tests

    def _discover_feature_files(self) -> list[DiscoveredTest]:
        """Discover all feature files."""
        tests = []

        if not self.features_dir.exists():
            return tests

        for feature_file in self.features_dir.rglob("*.feature"):
            try:
                parsed = self._parse_feature_file(feature_file)

                # Determine status based on step definitions
                status = TestDiscoveryStatus.READY
                if parsed["needs_steps"]:
                    status = TestDiscoveryStatus.NEEDS_STEPS

                test = DiscoveredTest(
                    test_type=TestType.FEATURE_FILE,
                    name=parsed["name"],
                    path=str(feature_file.relative_to(self.project_path)),
                    status=status,
                    metadata={
                        "feature": parsed["name"],
                        "description": parsed["description"],
                        "background": parsed["background"],
                        "scenario_count": len(parsed["scenarios"]),
                    },
                    scenarios=parsed["scenarios"],
                    tags=parsed["tags"],
                )

                tests.append(test)

            except Exception as e:
                # Add error entry
                tests.append(DiscoveredTest(
                    test_type=TestType.FEATURE_FILE,
                    name=feature_file.stem,
                    path=str(feature_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.ERROR,
                    metadata={"error": str(e)},
                ))

        return tests

    def _parse_feature_file(self, filepath: Path) -> dict[str, Any]:
        """
        Parse a feature file to extract metadata.

        Args:
            filepath: Path to feature file

        Returns:
            Dictionary with feature metadata
        """
        content = filepath.read_text(encoding="utf-8")

        # Extract feature name
        feature_match = re.search(r'^Feature:\s*(.+)$', content, re.MULTILINE)
        feature_name = feature_match.group(1).strip() if feature_match else filepath.stem

        # Extract description (lines between Feature and first scenario)
        description_lines = []
        in_description = False
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("Feature:"):
                in_description = True
                continue
            if in_description:
                if line.startswith("Scenario:") or line.startswith("Background:") or line.startswith("@"):
                    break
                if line and not line.startswith("#"):
                    description_lines.append(line)

        # Extract scenarios
        scenarios = []
        scenario_match = re.finditer(r'^Scenario:?\s*(.+)$', content, re.MULTILINE)
        for match in scenario_match:
            scenarios.append(match.group(1).strip())

        # Extract tags
        tags = set()
        tag_matches = re.findall(r'@(\w+)', content)
        tags.update(tag_matches)

        # Check for background
        has_background = bool(re.search(r'^Background:', content, re.MULTILINE))

        # Extract step patterns
        step_patterns = re.findall(r'^(Given|When|Then|And)\s+(.+)$', content, re.MULTILINE)
        unique_steps = set(step[1].strip() for step in step_patterns)

        # Determine if steps are defined
        needs_steps = True  # Will check against step definitions later

        return {
            "name": feature_name,
            "description": "\n".join(description_lines),
            "background": has_background,
            "scenarios": scenarios,
            "tags": list(tags),
            "steps": list(unique_steps),
            "step_count": len(unique_steps),
            "needs_steps": needs_steps,
        }

    def _discover_playwright_recordings(self) -> list[DiscoveredTest]:
        """Discover all Playwright test recordings."""
        tests = []

        if not self.recordings_dir.exists():
            return tests

        for recording_file in self.recordings_dir.rglob("*.spec.js"):
            try:
                parsed = self._parse_playwright_recording(recording_file)

                test = DiscoveredTest(
                    test_type=TestType.PLAYWRIGHT_RECORDING,
                    name=parsed["name"],
                    path=str(recording_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.READY,
                    metadata={
                        "test_count": parsed["test_count"],
                        "actions": parsed["actions"],
                        "selectors": parsed["selectors"],
                    },
                    scenarios=parsed["test_names"],
                )

                tests.append(test)

            except Exception as e:
                tests.append(DiscoveredTest(
                    test_type=TestType.PLAYWRIGHT_RECORDING,
                    name=recording_file.stem,
                    path=str(recording_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.ERROR,
                    metadata={"error": str(e)},
                ))

        return tests

    def _parse_playwright_recording(self, filepath: Path) -> dict[str, Any]:
        """
        Parse a Playwright recording to extract metadata.

        Args:
            filepath: Path to recording file

        Returns:
            Dictionary with recording metadata
        """
        content = filepath.read_text(encoding="utf-8")

        # Extract test names
        test_names = []
        test_matches = re.finditer(r'test\([\'"](.+?)[\'"]', content)
        for match in test_matches:
            test_names.append(match.group(1))

        # Extract actions (click, fill, goto, etc.)
        actions = []
        action_patterns = [
            r'\.goto\(',
            r'\.click\(',
            r'\.fill\(',
            r'\.type\(',
            r'\.check\(',
            r'\.selectOption\(',
        ]
        for pattern in action_patterns:
            matches = re.findall(pattern, content)
            actions.extend([pattern.replace('\\', '')] * len(matches))

        # Extract selectors
        selectors = []
        selector_matches = re.findall(r'[\'"](.*?\.selector.*?)[\'"]', content)
        selectors.extend(selector_matches)

        # Extract locators
        locator_matches = re.finditer(r'page\.locator\([\'"](.+?)[\'"]\)', content)
        for match in locator_matches:
            selectors.append(match.group(1))

        return {
            "name": filepath.stem,
            "test_count": len(test_names),
            "test_names": test_names,
            "actions": actions,
            "selectors": selectors,
        }

    def _discover_step_definitions(self) -> list[DiscoveredTest]:
        """Discover all step definition files."""
        tests = []

        if not self.steps_dir.exists():
            return tests

        for steps_file in self.steps_dir.rglob("*.py"):
            try:
                parsed = self._parse_step_file(steps_file)

                test = DiscoveredTest(
                    test_type=TestType.STEP_DEFINITION,
                    name=steps_file.stem,
                    path=str(steps_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.READY,
                    metadata={
                        "step_count": parsed["step_count"],
                        "patterns": parsed["patterns"],
                    },
                    scenarios=parsed["patterns"],
                )

                tests.append(test)

            except Exception as e:
                tests.append(DiscoveredTest(
                    test_type=TestType.STEP_DEFINITION,
                    name=steps_file.stem,
                    path=str(steps_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.ERROR,
                    metadata={"error": str(e)},
                ))

        return tests

    def _parse_step_file(self, filepath: Path) -> dict[str, Any]:
        """
        Parse a step definition file to extract patterns.

        Args:
            filepath: Path to step file

        Returns:
            Dictionary with step metadata
        """
        content = filepath.read_text(encoding="utf-8")

        # Extract step patterns (behave decorators)
        patterns = []
        pattern_matches = re.finditer(r'@(?:given|when|then)\([\'"]\^?(.+?)\$?[\'"]\)', content, re.MULTILINE)
        for match in pattern_matches:
            patterns.append(match.group(1))

        # Count function definitions
        function_count = len(re.findall(r'^def\s+\w+\s*\(', content, re.MULTILINE))

        return {
            "step_count": function_count,
            "patterns": patterns,
        }

    def _discover_page_objects(self) -> list[DiscoveredTest]:
        """Discover all page object files."""
        tests = []

        if not self.pages_dir.exists():
            return tests

        for page_file in self.pages_dir.rglob("*.py"):
            if page_file.name.startswith("_"):
                continue

            try:
                parsed = self._parse_page_object(page_file)

                test = DiscoveredTest(
                    test_type=TestType.PAGE_OBJECT,
                    name=parsed["class_name"],
                    path=str(page_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.READY,
                    metadata={
                        "class_name": parsed["class_name"],
                        "method_count": parsed["method_count"],
                        "methods": parsed["methods"],
                        "selectors": parsed.get("selectors", []),
                    },
                )

                tests.append(test)

            except Exception as e:
                tests.append(DiscoveredTest(
                    test_type=TestType.PAGE_OBJECT,
                    name=page_file.stem,
                    path=str(page_file.relative_to(self.project_path)),
                    status=TestDiscoveryStatus.ERROR,
                    metadata={"error": str(e)},
                ))

        return tests

    def _parse_page_object(self, filepath: Path) -> dict[str, Any]:
        """
        Parse a page object file to extract class and method info.

        Args:
            filepath: Path to page object file

        Returns:
            Dictionary with page object metadata
        """
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)

        class_name = "Unknown"
        methods = []
        selectors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Skip BasePage
                if node.name == "BasePage":
                    continue

                class_name = node.name

                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        methods.append(item.name)

                        # Extract selector literals from method body
                        for subnode in ast.walk(item):
                            if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
                                # Look for selector patterns (CSS, XPath, etc.)
                                if any(char in subnode.value for char in ['#', '.', '[', '@']):
                                    selectors.append(subnode.value)

        return {
            "class_name": class_name,
            "method_count": len(methods),
            "methods": methods,
            "selectors": selectors,
        }

    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between discovered tests."""
        # Build a mapping of step patterns to step definition files
        step_patterns: dict[str, str] = {}

        for test in self.discovered_tests:
            if test.test_type == TestType.STEP_DEFINITION:
                for pattern in test.scenarios:
                    # Convert regex pattern to simple string for matching
                    simple_pattern = re.sub(r'[\\^$.|?*+()\[\]{}]', '', pattern)
                    step_patterns[simple_pattern] = test.path

        # Check feature files against step definitions
        for test in self.discovered_tests:
            if test.test_type == TestType.FEATURE_FILE:
                steps_defined = test.metadata.get("steps", [])

                # Check if all steps have definitions
                undefined_steps = []
                for step in steps_defined:
                    step_clean = re.sub(r'["\\^$.|?*+()\[\]{}]', '', step)
                    if not any(step_clean in pattern for pattern in step_patterns.keys()):
                        undefined_steps.append(step)

                if undefined_steps:
                    test.status = TestDiscoveryStatus.NEEDS_STEPS
                    test.metadata["undefined_steps"] = undefined_steps
                else:
                    test.status = TestDiscoveryStatus.READY

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about discovered tests.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total": len(self.discovered_tests),
            "by_type": {},
            "by_status": {},
            "feature_files": 0,
            "scenarios": 0,
            "step_definitions": 0,
            "page_objects": 0,
        }

        for test in self.discovered_tests:
            # Count by type
            test_type = test.test_type.value
            stats["by_type"][test_type] = stats["by_type"].get(test_type, 0) + 1

            # Count by status
            status = test.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Count specifics
            if test.test_type == TestType.FEATURE_FILE:
                stats["feature_files"] += 1
                stats["scenarios"] += test.metadata.get("scenario_count", 0)
            elif test.test_type == TestType.STEP_DEFINITION:
                stats["step_definitions"] += 1
            elif test.test_type == TestType.PAGE_OBJECT:
                stats["page_objects"] += 1

        return stats

    def get_tests_by_status(self, status: TestDiscoveryStatus) -> list[DiscoveredTest]:
        """
        Get all tests with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of tests with the status
        """
        return [t for t in self.discovered_tests if t.status == status]

    def export_discovery(self, output_path: str) -> None:
        """
        Export discovery results to JSON.

        Args:
            output_path: Path to output JSON file
        """
        data = {
            "discovered_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "tests": [test.to_dict() for test in self.discovered_tests],
        }

        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def discover_tests(
    project_path: str = ".",
    features_dir: str = "features",
    recordings_dir: str = "recordings",
    steps_dir: str = "steps",
    pages_dir: str = "pages",
) -> TestDiscovery:
    """
    Discover all tests in a project.

    Args:
        project_path: Root project directory
        features_dir: Features directory
        recordings_dir: Recordings directory
        steps_dir: Steps directory
        pages_dir: Pages directory

    Returns:
        TestDiscovery instance with results
    """
    discovery = TestDiscovery(
        project_path=project_path,
        features_dir=features_dir,
        recordings_dir=recordings_dir,
        steps_dir=steps_dir,
        pages_dir=pages_dir,
    )

    discovery.discover_all()
    return discovery
