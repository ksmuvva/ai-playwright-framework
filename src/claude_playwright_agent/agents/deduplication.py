"""
Deduplication Module for Claude Playwright Agent.

This module analyzes multiple recordings to:
- Find repeated selectors and patterns
- Create reusable page object models
- Merge similar scenarios
- Identify common test flows
"""

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Deduplication Models
# =============================================================================


class SimilarityMetric(str, Enum):
    """Types of similarity metrics."""

    SELECTOR_EXACT = "selector_exact"
    SELECTOR_FUZZY = "selector_fuzzy"
    ACTION_SEQUENCE = "action_sequence"
    URL_PATTERN = "url_pattern"


@dataclass
class SelectorPattern:
    """A repeated selector pattern."""

    raw: str
    type: str
    value: str
    attributes: dict[str, Any]
    count: int = 0
    recordings: list[str] = field(default_factory=list)
    suggested_name: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "raw": self.raw,
            "type": self.type,
            "value": self.value,
            "attributes": self.attributes,
            "count": self.count,
            "recordings": self.recordings,
            "suggested_name": self.suggested_name,
            "confidence": self.confidence,
        }


@dataclass
class PageElement:
    """A reusable page element."""

    name: str
    selector: str
    selector_type: str
    description: str = ""
    actions: list[str] = field(default_factory=list)
    usage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "description": self.description,
            "actions": self.actions,
            "usage_count": self.usage_count,
        }


@dataclass
class PageObject:
    """A page object model."""

    name: str
    url_pattern: str = ""
    elements: dict[str, PageElement] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url_pattern": self.url_pattern,
            "elements": {k: v.to_dict() for k, v in self.elements.items()},
            "description": self.description,
        }

    def to_python_code(self) -> str:
        """Generate Python Page Object code."""
        elements_code = []

        for elem_name, elem in self.elements.items():
            elements_code.append(f'''
    @property
    def {elem_name}(self) -> Locator:
        """{elem.description}"""
        return self.page.{elem.selector_type}("{elem.selector}")
'''.strip())

        elements_str = "\n\n".join(elements_code)

        return f'''"""
Page Object: {self.name}

Auto-generated from Playwright recordings.
"""

from typing import Any
from playwright.sync_api import Page, Locator


class {self.name}:
    """Page object for {self.name}."""

    def __init__(self, page: Page) -> None:
        """Initialize the page object."""
        self.page = page
{elements_str if elements_str else '    # No elements defined yet'}
'''


@dataclass
class DeduplicationResult:
    """Result of deduplication analysis."""

    selector_patterns: list[SelectorPattern] = field(default_factory=list)
    page_objects: list[PageObject] = field(default_factory=list)
    merged_scenarios: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector_patterns": [p.to_dict() for p in self.selector_patterns],
            "page_objects": [p.to_dict() for p in self.page_objects],
            "merged_scenarios": self.merged_scenarios,
            "statistics": self.statistics,
        }


# =============================================================================
# Deduplication Engine
# =============================================================================


class DeduplicationEngine:
    """
    Analyzes recordings for patterns and creates page objects.

    Features:
    - Selector frequency analysis
    - Action sequence clustering
    - Page object generation
    - Scenario deduplication
    """

    # Minimum threshold for considering a pattern as "repeated"
    MIN_SELECTOR_COUNT = 2
    MIN_CONFIDENCE = 0.5

    def __init__(self) -> None:
        """Initialize the deduplication engine."""
        self._selector_counts: Counter = Counter()
        self._selector_sources: dict[str, set[str]] = defaultdict(set)
        self._action_sequences: dict[str, list[str]] = {}
        self._url_patterns: Counter = Counter()

    def analyze_recordings(
        self,
        recordings: list[dict[str, Any]],
    ) -> DeduplicationResult:
        """
        Analyze multiple recordings for patterns.

        Args:
            recordings: List of parsed recording dictionaries

        Returns:
            DeduplicationResult with patterns and page objects
        """
        # Reset state
        self._selector_counts = Counter()
        self._selector_sources = defaultdict(set)
        self._action_sequences = {}
        self._url_patterns = Counter()

        # Analyze each recording
        for recording in recordings:
            self._analyze_recording(recording)

        # Generate results
        result = DeduplicationResult()

        # Find repeated selectors
        result.selector_patterns = self._find_selector_patterns()

        # Generate page objects
        result.page_objects = self._generate_page_objects()

        # Calculate statistics
        result.statistics = {
            "total_recordings": len(recordings),
            "unique_selectors": len(self._selector_counts),
            "repeated_selectors": len([s for s in result.selector_patterns
                                      if s.count >= self.MIN_SELECTOR_COUNT]),
            "total_actions": sum(len(r.get("actions", [])) for r in recordings),
            "page_objects_generated": len(result.page_objects),
        }

        return result

    def _analyze_recording(self, recording: dict[str, Any]) -> None:
        """Analyze a single recording."""
        test_name = recording.get("test_name", "")
        actions = recording.get("actions", [])
        urls = recording.get("urls_visited", [])

        # Track URL patterns
        for url in urls:
            self._url_patterns[url] += 1

        # Extract action sequence
        action_types = [a.get("action_type") for a in actions]
        self._action_sequences[test_name] = action_types

        # Count selectors
        for action in actions:
            selector = action.get("selector")
            if selector:
                raw = selector.get("raw", "")
                self._selector_counts[raw] += 1
                self._selector_sources[raw].add(test_name)

    def _find_selector_patterns(self) -> list[SelectorPattern]:
        """Find repeated selector patterns."""
        patterns = []

        for raw, count in self._selector_counts.items():
            if count >= self.MIN_SELECTOR_COUNT:
                # Parse the selector to extract metadata
                selector_info = self._parse_selector(raw)

                # Calculate confidence (higher count = higher confidence)
                max_count = max(self._selector_counts.values()) if self._selector_counts else 1
                confidence = min(count / max_count, 1.0)

                # Generate suggested name
                suggested_name = self._suggest_element_name(selector_info)

                pattern = SelectorPattern(
                    raw=raw,
                    type=selector_info.get("type", ""),
                    value=selector_info.get("value", ""),
                    attributes=selector_info.get("attributes", {}),
                    count=count,
                    recordings=list(self._selector_sources[raw]),
                    suggested_name=suggested_name,
                    confidence=confidence,
                )
                patterns.append(pattern)

        # Sort by confidence and count
        patterns.sort(key=lambda p: (p.confidence, p.count), reverse=True)
        return patterns

    def _parse_selector(self, raw: str) -> dict[str, Any]:
        """Parse a raw selector string."""
        import re

        # Try getBy* patterns
        get_by_match = re.search(r'get(ByRole|ByLabel|ByText|ByPlaceholder|ByTestId|ByTitle)(?:\(["\']([^"\']+)["\'](?:\s*,\s*\{([^)]*)\})?\))?', raw)
        if get_by_match:
            method = get_by_match.group(1)  # ByRole, ByLabel, etc.
            name = get_by_match.group(2) if get_by_match.group(2) else ""
            attrs_str = get_by_match.group(3) if get_by_match.group(3) else ""

            # Parse attributes
            attributes = {}
            if attrs_str:
                attr_matches = re.findall(r'(\w+):\s*["\']?([^"\']+)["\']?', attrs_str)
                for attr_name, attr_value in attr_matches:
                    attributes[attr_name] = attr_value

            return {
                "type": f"get{method}",
                "value": name,
                "attributes": attributes,
            }

        # Try locator pattern
        locator_match = re.search(r'locator\(["\']([^"\']+)["\']\)', raw)
        if locator_match:
            return {
                "type": "locator",
                "value": locator_match.group(1),
                "attributes": {},
            }

        # Default
        return {
            "type": "unknown",
            "value": raw,
            "attributes": {},
        }

    def _suggest_element_name(self, selector_info: dict[str, Any]) -> str:
        """Suggest a name for a page element."""
        selector_type = selector_info.get("type", "")
        value = selector_info.get("value", "")
        attrs = selector_info.get("attributes", {})

        # getByRole - use role name or explicit name attribute
        if selector_type == "getByRole":
            role = value
            name = attrs.get("name", "")
            if name:
                return self._to_snake_case(f"{role}_{name}")
            return self._to_snake_case(role) if role else "element"

        # getByLabel - use label text
        if selector_type == "getByLabel":
            return self._to_snake_case(value) if value else "field"

        # getByPlaceholder - use placeholder text
        if selector_type == "getByPlaceholder":
            return self._to_snake_case(f"{value}_field") if value else "field"

        # getByTestId - use test ID
        if selector_type == "getByTestId":
            return self._to_snake_case(value) if value else "element"

        # getByText - use text content
        if selector_type == "getByText":
            return self._to_snake_case(f"{value}_element") if value else "element"

        # locator - use hash of selector
        if selector_type == "locator":
            # Generate a hash-based name for CSS selectors
            return f"element_{hashlib.md5(value.encode()).hexdigest()[:8]}"

        # Default
        return "element"

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        import re
        # Remove special chars, convert spaces to underscores
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', '_', text.strip())
        return text.lower()

    def _generate_page_objects(self) -> list[PageObject]:
        """Generate page objects from repeated patterns."""
        page_objects = []

        # Get repeated selectors
        repeated_selectors = [
            s for s in self._find_selector_patterns()
            if s.count >= self.MIN_SELECTOR_COUNT and s.confidence >= self.MIN_CONFIDENCE
        ]

        if not repeated_selectors:
            return page_objects

        # Group selectors by URL/recordings to create page objects
        # For now, create one page object per recording that has repeated selectors
        recording_groups: dict[str, list[SelectorPattern]] = defaultdict(list)

        for pattern in repeated_selectors:
            # Group by first recording
            if pattern.recordings:
                primary_recording = pattern.recordings[0]
                recording_groups[primary_recording].append(pattern)

        # Create page object for each group
        for recording, patterns in recording_groups.items():
            # Generate page object name from recording name
            page_name = self._to_page_object_name(recording)

            # Create elements
            elements = {}
            for pattern in patterns:
                elem_name = pattern.suggested_name
                # Ensure unique names
                base_name = elem_name
                counter = 1
                while elem_name in elements:
                    elem_name = f"{base_name}_{counter}"
                    counter += 1

                elements[elem_name] = PageElement(
                    name=elem_name,
                    selector=pattern.value,
                    selector_type=pattern.type,
                    description=f"Element found in {pattern.count} recording(s)",
                    usage_count=pattern.count,
                )

            page_obj = PageObject(
                name=page_name,
                description=f"Page object auto-generated from {recording}",
                elements=elements,
            )
            page_objects.append(page_obj)

        return page_objects

    def _to_page_object_name(self, recording_name: str) -> str:
        """Convert recording name to page object name."""
        import re

        # Convert test name to page object name
        # e.g., "user login" -> "UserLoginPage"
        name = recording_name.replace("_", " ").replace("-", " ").strip()
        name = re.sub(r'\s+', ' ', name)
        return "".join(word.capitalize() for word in name.split()) + "Page"


# =============================================================================
# Page Object Generator
# =============================================================================


class PageObjectGenerator:
    """Generates page object files."""

    def __init__(self) -> None:
        """Initialize the generator."""
        self._engine = DeduplicationEngine()

    def generate_from_recordings(
        self,
        recordings: list[dict[str, Any]],
        output_dir: str | Path,
    ) -> dict[str, Any]:
        """
        Generate page object files from recordings.

        Args:
            recordings: List of parsed recording dictionaries
            output_dir: Directory to save page object files

        Returns:
            Generation results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Analyze recordings
        result = self._engine.analyze_recordings(recordings)

        # Generate page object files
        files_created = []

        for page_obj in result.page_objects:
            file_name = f"{page_obj.name.lower()}.py"
            file_path = output_path / file_name

            code = page_obj.to_python_code()
            file_path.write_text(code, encoding="utf-8")

            files_created.append(str(file_path))

        return {
            "success": True,
            "files_created": files_created,
            "page_objects_count": len(result.page_objects),
            "selector_patterns_count": len(result.selector_patterns),
            "statistics": result.statistics,
        }

    def generate_code_string(self, recordings: list[dict[str, Any]]) -> str:
        """
        Generate page object code as string (without writing files).

        Args:
            recordings: List of parsed recording dictionaries

        Returns:
            Combined page object code
        """
        result = self._engine.analyze_recordings(recordings)

        if not result.page_objects:
            return "# No page objects generated - no repeated patterns found."

        code_blocks = []

        for page_obj in result.page_objects:
            code_blocks.append(page_obj.to_python_code())

        return "\n\n# ================================\n\n".join(code_blocks)


# =============================================================================
# Convenience Functions
# =============================================================================


def analyze_patterns(recordings: list[dict[str, Any]]) -> DeduplicationResult:
    """
    Analyze recordings for repeated patterns.

    Args:
        recordings: List of parsed recording dictionaries

    Returns:
        DeduplicationResult with patterns and statistics
    """
    engine = DeduplicationEngine()
    return engine.analyze_recordings(recordings)


def generate_page_objects(
    recordings: list[dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Generate page object files from recordings.

    Args:
        recordings: List of parsed recording dictionaries
        output_dir: Directory to save page object files

    Returns:
        Generation results
    """
    generator = PageObjectGenerator()
    return generator.generate_from_recordings(recordings, output_dir)
