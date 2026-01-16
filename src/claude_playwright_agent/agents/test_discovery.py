"""
Test Discovery System for Claude Playwright Agent.

Discovers and catalogs all test files, scenarios, and test definitions.
"""

import ast
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TestType(str, Enum):
    """Types of tests."""
    BDD_FEATURE = "bdd_feature"
    PLAYWRIGHT_TEST = "playwright_test"
    STEP_DEFINITION = "step_definition"
    PAGE_OBJECT = "page_object"


@dataclass
class TestScenario:
    """A single test scenario."""
    name: str
    feature_file: str
    line_number: int
    tags: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class TestFile:
    """A discovered test file."""
    path: Path
    test_type: TestType
    name: str
    scenarios: list[TestScenario] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepDefinition:
    """A discovered step definition."""
    pattern: str
    function_name: str
    file_path: Path
    line_number: int
    docstring: Optional[str] = None


class TestDiscovery:
    """
    Discover and catalog all tests in a project.

    Features:
    - Scan directories for test files
    - Parse feature files for scenarios
    - Parse step definition files
    - Catalog page objects
    - Support filtering by tags, patterns
    """

    def __init__(self, project_path: str = "."):
        """
        Initialize the test discovery system.

        Args:
            project_path: Root directory of the project
        """
        self.project_path = Path(project_path).resolve()
        self.test_files: list[TestFile] = []
        self.step_definitions: list[StepDefinition] = []
        self.page_objects: dict[str, Path] = {}

    def discover_all(
        self,
        features_dir: str = "features",
        tests_dir: str = "tests",
        pages_dir: str = "pages",
    ) -> dict[str, Any]:
        """
        Discover all test artifacts.

        Args:
            features_dir: Directory containing feature files
            tests_dir: Directory containing test files
            pages_dir: Directory containing page objects

        Returns:
            Dictionary with discovery results
        """
        results = {
            "features": [],
            "scenarios": [],
            "step_definitions": [],
            "page_objects": [],
            "total_tests": 0,
        }

        # Discover feature files
        features_path = self.project_path / features_dir
        if features_path.exists():
            feature_files = self._discover_feature_files(features_path)
            results["features"] = [str(f.path) for f in feature_files]
            results["scenarios"] = sum(len(f.scenarios) for f in feature_files)
            self.test_files.extend(feature_files)

        # Discover step definitions
        steps_path = features_path / "steps"
        if steps_path.exists():
            step_defs = self._discover_step_definitions(steps_path)
            results["step_definitions"] = [s.function_name for s in step_defs]
            self.step_definitions.extend(step_defs)

        # Discover page objects
        pages_path = self.project_path / pages_dir
        if pages_path.exists():
            page_objects = self._discover_page_objects(pages_path)
            results["page_objects"] = list(page_objects.keys())
            self.page_objects = page_objects

        # Discover Playwright tests
        tests_path = self.project_path / tests_dir
        if tests_path.exists():
            playwright_tests = self._discover_playwright_tests(tests_path)
            results["playwright_tests"] = [str(t.path) for t in playwright_tests]
            self.test_files.extend(playwright_tests)

        results["total_tests"] = len(self.test_files)

        return results

    def _discover_feature_files(self, features_path: Path) -> list[TestFile]:
        """
        Discover all feature files.

        Args:
            features_path: Path to features directory

        Returns:
            List of TestFile objects
        """
        feature_files = []

        for feature_file in features_path.rglob("*.feature"):
            test_file = TestFile(
                path=feature_file,
                test_type=TestType.BDD_FEATURE,
                name=feature_file.stem,
            )

            # Parse feature file
            scenarios = self._parse_feature_file(feature_file)
            test_file.scenarios = scenarios

            # Extract tags from scenarios
            all_tags = set()
            for scenario in scenarios:
                all_tags.update(scenario.tags)
            test_file.tags = list(all_tags)

            feature_files.append(test_file)

        return feature_files

    def _parse_feature_file(self, feature_file: Path) -> list[TestScenario]:
        """
        Parse a feature file to extract scenarios.

        Args:
            feature_file: Path to feature file

        Returns:
            List of TestScenario objects
        """
        scenarios = []
        content = feature_file.read_text(encoding="utf-8")

        # Simple regex-based parsing (for basic Gherkin)
        scenario_pattern = re.compile(
            r'^(?:@\w+\s+\n)*Scenario:?\s+(.+?)$',
            re.MULTILINE
        )

        for match in scenario_pattern.finditer(content):
            scenario_name = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1

            # Extract tags before scenario
            lines_before = content[:match.start()].split('\n')
            tags = []
            for line in reversed(lines_before[-5:]):  # Check last 5 lines
                if line.strip().startswith('@'):
                    tags.extend(line.strip().split()[1:])
                elif line.strip() and not line.strip().startswith('@'):
                    break

            scenario = TestScenario(
                name=scenario_name,
                feature_file=str(feature_file),
                line_number=line_number,
                tags=tags,
            )

            scenarios.append(scenario)

        return scenarios

    def _discover_step_definitions(self, steps_path: Path) -> list[StepDefinition]:
        """
        Discover all step definitions.

        Args:
            steps_path: Path to steps directory

        Returns:
            List of StepDefinition objects
        """
        step_defs = []

        for step_file in steps_path.rglob("*.py"):
            if step_file.name.startswith("_"):
                continue

            # Parse Python file for decorators
            try:
                content = step_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for step decorators
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Call):
                                # Handle @when('pattern'), @given('pattern'), etc.
                                if hasattr(decorator.func, 'id'):
                                    func_name = decorator.func.id
                                elif isinstance(decorator.func, ast.Attribute):
                                    func_name = decorator.func.attr
                                else:
                                    continue

                                if func_name in ['when', 'given', 'then', 'step']:
                                    # Extract pattern
                                    if decorator.args:
                                        pattern = self._extract_string(decorator.args[0])
                                    else:
                                        pattern = ""

                                    if pattern:
                                        step_def = StepDefinition(
                                            pattern=pattern,
                                            function_name=node.name,
                                            file_path=step_file,
                                            line_number=node.lineno,
                                            docstring=ast.get_docstring(node),
                                        )
                                        step_defs.append(step_def)

            except Exception as e:
                print(f"Warning: Failed to parse {step_file}: {e}")

        return step_defs

    def _extract_string(self, node) -> str:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        return ""

    def _discover_page_objects(self, pages_path: Path) -> dict[str, Path]:
        """
        Discover all page objects.

        Args:
            pages_path: Path to pages directory

        Returns:
            Dictionary mapping page class names to file paths
        """
        page_objects = {}

        for page_file in pages_path.rglob("*.py"):
            if page_file.name.startswith("_"):
                continue

            try:
                content = page_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Skip BasePage
                        if node.name == "BasePage":
                            continue

                        page_objects[node.name] = page_file

            except Exception as e:
                print(f"Warning: Failed to parse {page_file}: {e}")

        return page_objects

    def _discover_playwright_tests(self, tests_path: Path) -> list[TestFile]:
        """
        Discover Playwright test files.

        Args:
            tests_path: Path to tests directory

        Returns:
            List of TestFile objects
        """
        test_files = []

        # Look for .spec.js files (JavaScript)
        for test_file in tests_path.rglob("*.spec.js"):
            test_files.append(TestFile(
                path=test_file,
                test_type=TestType.PLAYWRIGHT_TEST,
                name=test_file.stem,
            ))

        # Look for test_*.py files (Python)
        for test_file in tests_path.rglob("test_*.py"):
            test_files.append(TestFile(
                path=test_file,
                test_type=TestType.PLAYWRIGHT_TEST,
                name=test_file.stem,
            ))

        return test_files

    def filter_by_tags(self, tags: list[str]) -> list[TestFile]:
        """
        Filter test files by tags.

        Args:
            tags: List of tags to filter by

        Returns:
            List of matching TestFile objects
        """
        tags_set = set(tags)

        return [
            test_file for test_file in self.test_files
            if tags_set.intersection(set(test_file.tags))
        ]

    def filter_by_name(self, pattern: str) -> list[TestFile]:
        """
        Filter test files by name pattern.

        Args:
            pattern: Regex pattern to match

        Returns:
            List of matching TestFile objects
        """
        regex = re.compile(pattern)

        return [
            test_file for test_file in self.test_files
            if regex.search(test_file.name)
        ]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get discovery statistics.

        Returns:
            Dictionary with statistics
        """
        by_type = {}
        for test_file in self.test_files:
            test_type = test_file.test_type.value
            by_type[test_type] = by_type.get(test_type, 0) + 1

        total_scenarios = sum(len(f.scenarios) for f in self.test_files)

        return {
            "total_test_files": len(self.test_files),
            "total_scenarios": total_scenarios,
            "total_step_definitions": len(self.step_definitions),
            "total_page_objects": len(self.page_objects),
            "by_type": by_type,
        }

    def generate_test_report(self) -> str:
        """
        Generate a text report of discovered tests.

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Test Discovery Report")
        lines.append("=" * 60)
        lines.append("")

        stats = self.get_statistics()

        lines.append(f"Total Test Files: {stats['total_test_files']}")
        lines.append(f"Total Scenarios: {stats['total_scenarios']}")
        lines.append(f"Total Step Definitions: {stats['total_step_definitions']}")
        lines.append(f"Total Page Objects: {stats['total_page_objects']}")
        lines.append("")

        lines.append("By Type:")
        for test_type, count in stats['by_type'].items():
            lines.append(f"  {test_type}: {count}")
        lines.append("")

        lines.append("Feature Files:")
        for test_file in [f for f in self.test_files if f.test_type == TestType.BDD_FEATURE]:
            lines.append(f"  {test_file.path}")
            lines.append(f"    Scenarios: {len(test_file.scenarios)}")
            if test_file.tags:
                lines.append(f"    Tags: {', '.join(test_file.tags)}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
