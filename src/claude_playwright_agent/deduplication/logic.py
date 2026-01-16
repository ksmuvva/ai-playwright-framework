"""
Element deduplication logic with context tracking.

This module provides:
- Exact selector matching
- Pattern-based selector matching
- Context-aware element grouping
- Fragility scoring for selectors
"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Context Models
# =============================================================================


class SelectorType(str, Enum):
    """Types of selectors."""

    GET_BY_ROLE = "getByRole"
    GET_BY_LABEL = "getByLabel"
    GET_BY_TEXT = "getByText"
    GET_BY_PLACEHOLDER = "getByPlaceholder"
    GET_BY_TEST_ID = "getByTestId"
    GET_BY_TITLE = "getByTitle"
    LOCATOR = "locator"
    CSS = "css"
    XPATH = "xpath"


class ActionType(str, Enum):
    """Types of actions that can be performed on elements."""

    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    CHECK = "check"
    UNCHECK = "uncheck"
    SELECT = "select_option"
    HOVER = "hover"
    PRESS = "press"
    UPLOAD = "set_input_files"


@dataclass
class ElementContext:
    """
    Full context for an element usage.

    Maintains complete traceability of where and how an element is used.
    """

    recording_id: str
    page_url: str
    action_type: str
    line_number: int
    element_index: int
    value: str | None = None  # Value filled/typed if applicable

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recording_id": self.recording_id,
            "page_url": self.page_url,
            "action_type": self.action_type,
            "line_number": self.line_number,
            "element_index": self.element_index,
            "value": self.value,
        }


@dataclass
class SelectorData:
    """Selector data with metadata."""

    raw: str
    type: str
    value: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "raw": self.raw,
            "type": self.type,
            "value": self.value,
            "attributes": self.attributes,
        }

    @property
    def normalized_value(self) -> str:
        """Get normalized value for comparison."""
        return self.value.lower().strip()

    @property
    def fragility_score(self) -> float:
        """
        Calculate fragility score (0-1, higher is more fragile).

        Scoring:
        - getByTestId: 0.0 (very stable)
        - getByRole: 0.1
        - getByLabel/Placeholder: 0.2
        - locator: 0.4
        - css: 0.6
        - getByText: 0.7
        - xpath: 0.9 (very fragile)
        """
        fragility_map = {
            SelectorType.GET_BY_TEST_ID: 0.0,
            SelectorType.GET_BY_ROLE: 0.1,
            SelectorType.GET_BY_LABEL: 0.2,
            SelectorType.GET_BY_PLACEHOLDER: 0.2,
            SelectorType.LOCATOR: 0.4,
            SelectorType.CSS: 0.6,
            SelectorType.GET_BY_TEXT: 0.7,
            SelectorType.GET_BY_TITLE: 0.5,
            SelectorType.XPATH: 0.9,
        }
        return fragility_map.get(SelectorType(self.type), 0.5)


@dataclass
class ElementKey:
    """
    Unique key for element identification.

    Combines selector with context for grouping.
    """

    selector_hash: str
    type: str
    value: str
    url_hash: str | None = None  # Optional URL context for page-specific elements

    @classmethod
    def from_selector(cls, selector: SelectorData, page_url: str = "") -> "ElementKey":
        """Create element key from selector data."""
        # Hash the selector value
        selector_hash = hashlib.sha256(selector.raw.encode()).hexdigest()[:16]

        # Optional: include URL in hash for page-specific elements
        url_hash = None
        if page_url:
            url_hash = hashlib.sha256(page_url.encode()).hexdigest()[:12]

        return cls(
            selector_hash=selector_hash,
            type=selector.type,
            value=selector.value,
            url_hash=url_hash,
        )


# =============================================================================
# Element Group Model
# =============================================================================


class ElementGroup(BaseModel):
    """
    A group of matching elements across recordings.

    Maintains full context of all usages while providing
    a canonical selector for the group.
    """

    group_id: str = Field(..., description="Unique group ID")
    canonical_selector: SelectorData = Field(..., description="Best selector to use")
    alternative_selectors: list[SelectorData] = Field(
        default_factory=list,
        description="Alternative selectors for this element"
    )
    contexts: list[ElementContext] = Field(
        default_factory=list,
        description="All contexts where this element is used"
    )
    usage_count: int = Field(default=0, description="Total times used")
    fragility_score: float = Field(..., description="Combined fragility score")
    component_type: str = Field(default="", description="Component type if identified")
    name_suggestion: str = Field(default="", description="Suggested element name")

    # Tracking which recordings/pages use this element
    recordings: set[str] = Field(
        default_factory=set,
        description="Recording IDs using this element"
    )
    pages: set[str] = Field(
        default_factory=set,
        description="Page URLs where this appears"
    )

    class Config:
        """Pydantic config."""
        use_enum_values = True

    def add_context(self, context: ElementContext) -> None:
        """Add a usage context."""
        self.contexts.append(context)
        self.usage_count += 1
        self.recordings.add(context.recording_id)
        if context.page_url:
            self.pages.add(context.page_url)

    def merge(self, other: "ElementGroup") -> None:
        """Merge another group into this one."""
        self.contexts.extend(other.contexts)
        self.usage_count += other.usage_count
        self.recordings.update(other.recordings)
        self.pages.update(other.pages)

        # Add other group's canonical selector as alternative if different
        if other.canonical_selector.raw != self.canonical_selector.raw:
            if other.canonical_selector.raw not in [s.raw for s in self.alternative_selectors]:
                self.alternative_selectors.append(other.canonical_selector)

        # Merge alternative selectors
        for alt in other.alternative_selectors:
            if alt.raw not in [s.raw for s in self.alternative_selectors]:
                self.alternative_selectors.append(alt)

        # Keep the most stable selector as canonical
        if other.canonical_selector.fragility_score < self.canonical_selector.fragility_score:
            # Move current canonical to alternatives if not already there
            if self.canonical_selector.raw not in [s.raw for s in self.alternative_selectors]:
                self.alternative_selectors.append(self.canonical_selector)
            self.canonical_selector = other.canonical_selector

    def to_state_model(self) -> dict[str, Any]:
        """Convert to state model format."""
        from claude_playwright_agent.state.models import ComponentElement

        return ComponentElement(
            selector=self.canonical_selector.raw,
            selector_type=self.canonical_selector.type,
            fragility_score=self.fragility_score,
            usage_count=self.usage_count,
            recordings=list(self.recordings),
            alternatives=[s.raw for s in self.alternative_selectors],
            metadata={
                "component_type": self.component_type,
                "name_suggestion": self.name_suggestion,
                "pages": list(self.pages),
            },
        ).model_dump()


# =============================================================================
# Deduplication Logic
# =============================================================================


class DeduplicationLogic:
    """
    Core deduplication algorithms with context tracking.

    Provides:
    - Exact selector matching
    - Pattern-based matching
    - Context-aware grouping
    - Fragility-aware canonical selection
    """

    def __init__(self) -> None:
        """Initialize deduplication logic."""
        self._groups: dict[str, ElementGroup] = {}
        self._selector_index: dict[str, list[str]] = {}  # hash -> group_ids

    # =============================================================================
    # Exact Matching
    # =============================================================================

    def exact_match(self, selector: SelectorData, context: ElementContext) -> ElementGroup | None:
        """
        Find exact match for a selector.

        Args:
            selector: Selector to match
            context: Usage context

        Returns:
            Matching group or None
        """
        # Search for existing group with same selector
        for group in self._groups.values():
            if group.canonical_selector.raw == selector.raw:
                return group

        return None

    # =============================================================================
    # Pattern Matching
    # =============================================================================

    def pattern_match(
        self,
        selector: SelectorData,
        context: ElementContext,
        threshold: float = 0.85,
    ) -> list[tuple[ElementGroup, float]]:
        """
        Find pattern-based matches for a selector.

        Args:
            selector: Selector to match
            context: Usage context
            threshold: Similarity threshold (0-1)

        Returns:
            List of (group, similarity_score) tuples
        """
        matches = []

        for group in self._groups.values():
            similarity = self._calculate_similarity(
                selector,
                group.canonical_selector,
                context,
            )

            if similarity >= threshold:
                matches.append((group, similarity))

        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _calculate_similarity(
        self,
        selector1: SelectorData,
        selector2: SelectorData,
        context: ElementContext,
    ) -> float:
        """
        Calculate similarity between two selectors.

        Considers:
        - Selector type match
        - Value similarity
        - Attribute overlap
        - URL context (optional)
        """
        score = 0.0

        # Type match (40% weight)
        if selector1.type == selector2.type:
            score += 0.4

        # Value similarity (40% weight)
        value_similarity = self._string_similarity(
            selector1.normalized_value,
            selector2.normalized_value,
        )
        score += value_similarity * 0.4

        # Attribute overlap (20% weight)
        if selector1.attributes and selector2.attributes:
            attr_overlap = self._attribute_similarity(
                selector1.attributes,
                selector2.attributes,
            )
            score += attr_overlap * 0.2

        # URL context bonus (up to 10% extra)
        if context.page_url and any(
            context.page_url in page for page in self._get_group_pages(selector2)
        ):
            score += 0.1

        return min(score, 1.0)

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using Jaro-Winkler distance."""
        if s1 == s2:
            return 1.0

        # Simple Levenshtein-based similarity
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Dynamic programming for edit distance
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )

        max_len = max(len1, len2)
        distance = dp[len1][len2]
        return 1.0 - (distance / max_len)

    def _attribute_similarity(
        self,
        attrs1: dict[str, Any],
        attrs2: dict[str, Any],
    ) -> float:
        """Calculate attribute similarity."""
        if not attrs1 or not attrs2:
            return 0.0

        keys1 = set(attrs1.keys())
        keys2 = set(attrs2.keys())

        if not keys1 or not keys2:
            return 0.0

        # Jaccard similarity for keys
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)

        if union == 0:
            return 0.0

        key_sim = intersection / union

        # Value similarity for matching keys
        value_sims = []
        for key in keys1 & keys2:
            val1 = str(attrs1[key]).lower()
            val2 = str(attrs2[key]).lower()
            if val1 == val2:
                value_sims.append(1.0)
            else:
                value_sims.append(self._string_similarity(val1, val2))

        if value_sims:
            value_sim = sum(value_sims) / len(value_sims)
            return (key_sim + value_sim) / 2

        return key_sim

    def _get_group_pages(self, selector: SelectorData) -> set[str]:
        """Get all pages associated with a selector (from indexed groups)."""
        pages = set()
        for group in self._groups.values():
            if any(s.raw == selector.raw for s in group.alternative_selectors):
                pages.update(group.pages)
        return pages

    # =============================================================================
    # Context-Based Grouping
    # =============================================================================

    def context_match(
        self,
        selector: SelectorData,
        context: ElementContext,
    ) -> list[ElementGroup]:
        """
        Find groups with matching context.

        Matches based on:
        - Same page URL
        - Same action type
        - Similar position in recording

        Args:
            selector: Selector to match
            context: Usage context

        Returns:
            List of matching groups
        """
        matches = []

        for group in self._groups.values():
            # Check for same page
            page_match = any(context.page_url in page for page in group.pages)

            # Check for same action type
            action_match = any(
                ctx.action_type == context.action_type
                for ctx in group.contexts
            )

            # Check for similar position
            position_match = any(
                abs(ctx.line_number - context.line_number) <= 5
                for ctx in group.contexts
            )

            # Require at least 2 criteria to match
            if sum([page_match, action_match, position_match]) >= 2:
                matches.append(group)

        return matches

    # =============================================================================
    # Group Management
    # =============================================================================

    def create_group(
        self,
        selector: SelectorData,
        context: ElementContext,
        name_suggestion: str = "",
    ) -> ElementGroup:
        """
        Create a new element group.

        Args:
            selector: Canonical selector for the group
            context: Initial usage context
            name_suggestion: Suggested element name

        Returns:
            New element group
        """
        key = ElementKey.from_selector(selector, context.page_url)
        group_id = f"group_{key.selector_hash}"

        # Generate name suggestion if not provided
        if not name_suggestion:
            name_suggestion = self._generate_name_suggestion(selector, context)

        group = ElementGroup(
            group_id=group_id,
            canonical_selector=selector,
            fragility_score=selector.fragility_score,
            name_suggestion=name_suggestion,
        )

        group.add_context(context)

        self._groups[group_id] = group
        self._index_group(group_id, selector)

        return group

    def add_to_group(
        self,
        group_id: str,
        selector: SelectorData,
        context: ElementContext,
    ) -> ElementGroup:
        """
        Add a selector usage to an existing group.

        Args:
            group_id: Group to add to
            selector: Selector being used
            context: Usage context

        Returns:
            Updated group
        """
        if group_id not in self._groups:
            raise ValueError(f"Group {group_id} not found")

        group = self._groups[group_id]

        # Add as alternative if different from canonical
        if selector.raw != group.canonical_selector.raw:
            if selector.raw not in [s.raw for s in group.alternative_selectors]:
                group.alternative_selectors.append(selector)

        group.add_context(context)

        # Update fragility score (weighted average)
        total_selectors = 1 + len(group.alternative_selectors)
        group.fragility_score = (
            group.canonical_selector.fragility_score +
            sum(s.fragility_score for s in group.alternative_selectors)
        ) / total_selectors

        self._index_group(group_id, selector)

        return group

    def merge_groups(self, group_ids: list[str]) -> ElementGroup:
        """
        Merge multiple groups into one.

        Args:
            group_ids: Groups to merge

        Returns:
            Merged group
        """
        if len(group_ids) < 2:
            if group_ids:
                return self._groups[group_ids[0]]
            raise ValueError("No groups to merge")

        # Sort by fragility (most stable first)
        sorted_groups = sorted(
            [self._groups[gid] for gid in group_ids],
            key=lambda g: g.fragility_score,
        )

        # Use most stable as base
        merged = sorted_groups[0]

        # Merge others
        for group in sorted_groups[1:]:
            merged.merge(group)
            del self._groups[group.group_id]

        return merged

    def _index_group(self, group_id: str, selector: SelectorData) -> None:
        """Index a group by its selector hash."""
        selector_hash = hashlib.sha256(selector.raw.encode()).hexdigest()[:16]

        if selector_hash not in self._selector_index:
            self._selector_index[selector_hash] = []

        if group_id not in self._selector_index[selector_hash]:
            self._selector_index[selector_hash].append(group_id)

    def _generate_name_suggestion(
        self,
        selector: SelectorData,
        context: ElementContext,
    ) -> str:
        """Generate a suggested name for an element."""
        # Start with selector type
        type_parts = selector.type.replace("get", "").replace("By", " ").split()
        base_name = "".join(p.capitalize() for p in type_parts)

        # Add value if meaningful
        if selector.value and len(selector.value) < 30:
            # Sanitize value
            value = re.sub(r'[^a-zA-Z0-9]', '', selector.value)
            if value:
                return f"{base_name}{value.capitalize()}"

        # Add action type
        if context.action_type:
            action = context.action_type.capitalize()
            return f"{base_name}To{action}"

        return base_name

    # =============================================================================
    # Query Methods
    # =============================================================================

    def get_group(self, group_id: str) -> ElementGroup | None:
        """Get a group by ID."""
        return self._groups.get(group_id)

    def get_all_groups(self) -> list[ElementGroup]:
        """Get all groups."""
        return list(self._groups.values())

    def get_groups_by_recording(self, recording_id: str) -> list[ElementGroup]:
        """Get all groups used in a recording."""
        return [
            group for group in self._groups.values()
            if recording_id in group.recordings
        ]

    def get_groups_by_page(self, page_url: str) -> list[ElementGroup]:
        """Get all groups used on a page."""
        return [
            group for group in self._groups.values()
            if any(page_url in p for p in group.pages)
        ]

    def get_canonical_selector(self, group_id: str) -> SelectorData | None:
        """Get the canonical selector for a group."""
        group = self.get_group(group_id)
        return group.canonical_selector if group else None

    def get_alternatives(self, group_id: str) -> list[SelectorData]:
        """Get alternative selectors for a group."""
        group = self.get_group(group_id)
        return group.alternative_selectors if group else []

    def get_contexts(self, group_id: str) -> list[ElementContext]:
        """Get all contexts for a group."""
        group = self.get_group(group_id)
        return group.contexts if group else []

    # =============================================================================
    # Statistics
    # =============================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get deduplication statistics."""
        total_groups = len(self._groups)
        total_usages = sum(g.usage_count for g in self._groups.values())
        total_recordings = len(set(
            rec for g in self._groups.values() for rec in g.recordings
        ))

        avg_fragility = (
            sum(g.fragility_score for g in self._groups.values()) / total_groups
            if total_groups > 0 else 0
        )

        # Count groups by selector type
        type_counts: dict[str, int] = {}
        for group in self._groups.values():
            st = group.canonical_selector.type
            type_counts[st] = type_counts.get(st, 0) + 1

        return {
            "total_groups": total_groups,
            "total_usages": total_usages,
            "total_recordings": total_recordings,
            "avg_fragility_score": avg_fragility,
            "selector_type_distribution": type_counts,
            "avg_alternatives_per_group": (
                sum(len(g.alternative_selectors) for g in self._groups.values()) / total_groups
                if total_groups > 0 else 0
            ),
        }
