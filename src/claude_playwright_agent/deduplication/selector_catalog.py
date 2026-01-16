"""
Selector catalog for centralized selector management.

This module provides:
- Global catalog of all selectors across recordings
- Query interface for finding selectors
- Metadata tracking for selectors
- Integration with state persistence
"""

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.deduplication.logic import (
    SelectorData,
    ElementContext,
    ElementGroup,
)


# =============================================================================
# Catalog Entry Models
# =============================================================================


class CatalogEntry(BaseModel):
    """
    A single entry in the selector catalog.

    Tracks a selector and all its metadata across the project.
    """

    entry_id: str = Field(..., description="Unique entry ID")
    selector: SelectorData = Field(..., description="The selector")
    element_name: str = Field(default="", description="Suggested element name")
    component_id: str = Field(default="", description="Component ID if part of component")

    # Usage tracking
    usage_count: int = Field(default=0, description="Total usage count")
    first_seen_recording: str = Field(default="", description="First recording ID")
    last_seen_recording: str = Field(default="", description="Most recent recording ID")

    # Context tracking
    recordings: list[str] = Field(
        default_factory=list,
        description="All recording IDs using this selector"
    )
    pages: list[str] = Field(
        default_factory=list,
        description="All page URLs where this appears"
    )
    actions: list[str] = Field(
        default_factory=list,
        description="Action types performed on this element"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Custom tags")
    notes: str = Field(default="", description="User notes")
    is_stable: bool = Field(default=False, description="Marked as stable by user")

    class Config:
        """Pydantic config."""
        use_enum_values = True

    def add_usage(self, context: ElementContext) -> None:
        """Add a usage context."""
        self.usage_count += 1

        if context.recording_id not in self.recordings:
            self.recordings.append(context.recording_id)

        if context.page_url and context.page_url not in self.pages:
            self.pages.append(context.page_url)

        if context.action_type and context.action_type not in self.actions:
            self.actions.append(context.action_type)

        # Update first/last seen
        if not self.first_seen_recording:
            self.first_seen_recording = context.recording_id
        self.last_seen_recording = context.recording_id


# =============================================================================
# Selector Catalog
# =============================================================================


class SelectorCatalog:
    """
    Central catalog for all project selectors.

    Provides:
    - Global storage of all selectors
    - Query and lookup capabilities
    - Integration with state persistence
    - Metadata management
    """

    def __init__(self) -> None:
        """Initialize the selector catalog."""
        self._entries: dict[str, CatalogEntry] = {}
        self._selector_index: dict[str, str] = {}  # selector_hash -> entry_id

    # =========================================================================
    # Entry Management
    # =========================================================================

    def add_selector(
        self,
        selector: SelectorData,
        context: ElementContext,
        element_name: str = "",
    ) -> CatalogEntry:
        """
        Add or update a selector in the catalog.

        Args:
            selector: Selector to add
            context: Usage context
            element_name: Optional element name

        Returns:
            The catalog entry (created or updated)
        """
        # Generate entry ID from selector hash
        selector_hash = self._hash_selector(selector)
        entry_id = f"catalog_{selector_hash}"

        # Check if exists
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            entry.add_usage(context)
            return entry

        # Create new entry
        entry = CatalogEntry(
            entry_id=entry_id,
            selector=selector,
            element_name=element_name or selector.value,
        )

        entry.add_usage(context)

        self._entries[entry_id] = entry
        self._selector_index[selector_hash] = entry_id

        return entry

    def get_entry(self, entry_id: str) -> CatalogEntry | None:
        """Get an entry by ID."""
        return self._entries.get(entry_id)

    def get_by_selector(self, selector: SelectorData) -> CatalogEntry | None:
        """Get an entry by selector."""
        selector_hash = self._hash_selector(selector)
        entry_id = self._selector_index.get(selector_hash)
        return self._entries.get(entry_id) if entry_id else None

    def update_entry(
        self,
        entry_id: str,
        element_name: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
        is_stable: bool | None = None,
    ) -> CatalogEntry | None:
        """
        Update catalog entry metadata.

        Args:
            entry_id: Entry to update
            element_name: New element name
            tags: New tags
            notes: New notes
            is_stable: Stable flag

        Returns:
            Updated entry or None if not found
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        if element_name is not None:
            entry.element_name = element_name

        if tags is not None:
            entry.tags = tags

        if notes is not None:
            entry.notes = notes

        if is_stable is not None:
            entry.is_stable = is_stable

        return entry

    # =========================================================================
    # Query Interface
    # =========================================================================

    def find_by_recording(self, recording_id: str) -> list[CatalogEntry]:
        """Find all selectors used in a recording."""
        return [
            entry for entry in self._entries.values()
            if recording_id in entry.recordings
        ]

    def find_by_page(self, page_url: str) -> list[CatalogEntry]:
        """Find all selectors used on a page."""
        return [
            entry for entry in self._entries.values()
            if any(page_url in p for p in entry.pages)
        ]

    def find_by_action(self, action_type: str) -> list[CatalogEntry]:
        """Find all selectors used with an action type."""
        return [
            entry for entry in self._entries.values()
            if action_type in entry.actions
        ]

    def find_by_tag(self, tag: str) -> list[CatalogEntry]:
        """Find all selectors with a tag."""
        return [
            entry for entry in self._entries.values()
            if tag in entry.tags
        ]

    def find_by_type(self, selector_type: str) -> list[CatalogEntry]:
        """Find all selectors of a type."""
        return [
            entry for entry in self._entries.values()
            if entry.selector.type == selector_type
        ]

    def find_flexible(
        self,
        recording_id: str | None = None,
        page_url: str | None = None,
        action_type: str | None = None,
        selector_type: str | None = None,
        tag: str | None = None,
        min_usage: int | None = None,
        is_stable: bool | None = None,
    ) -> list[CatalogEntry]:
        """
        Flexible query with multiple filters.

        Args:
            recording_id: Filter by recording
            page_url: Filter by page URL
            action_type: Filter by action type
            selector_type: Filter by selector type
            tag: Filter by tag
            min_usage: Minimum usage count
            is_stable: Filter by stable flag

        Returns:
            Matching entries
        """
        results = list(self._entries.values())

        if recording_id:
            results = [e for e in results if recording_id in e.recordings]

        if page_url:
            results = [e for e in results if any(page_url in p for p in e.pages)]

        if action_type:
            results = [e for e in results if action_type in e.actions]

        if selector_type:
            results = [e for e in results if e.selector.type == selector_type]

        if tag:
            results = [e for e in results if tag in e.tags]

        if min_usage:
            results = [e for e in results if e.usage_count >= min_usage]

        if is_stable is not None:
            results = [e for e in results if e.is_stable == is_stable]

        return results

    def find_alternatives(
        self,
        selector: SelectorData,
        threshold: float = 0.7,
    ) -> list[tuple[CatalogEntry, float]]:
        """
        Find similar selectors (alternatives).

        Args:
            selector: Selector to find alternatives for
            threshold: Similarity threshold

        Returns:
            List of (entry, similarity_score) tuples
        """
        from claude_playwright_agent.deduplication.logic import DeduplicationLogic

        logic = DeduplicationLogic()
        alternatives = []

        for entry in self._entries.values():
            # Skip exact match
            if entry.selector.raw == selector.raw:
                continue

            # Calculate similarity
            similarity = logic._calculate_similarity(
                selector,
                entry.selector,
                ElementContext(
                    recording_id="",
                    page_url="",
                    action_type="",
                    line_number=0,
                    element_index=0,
                ),
            )

            if similarity >= threshold:
                alternatives.append((entry, similarity))

        # Sort by similarity descending
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return alternatives

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get catalog statistics."""
        total_entries = len(self._entries)
        total_usage = sum(e.usage_count for e in self._entries.values())

        # Count by type
        type_counts: dict[str, int] = {}
        for entry in self._entries.values():
            st = entry.selector.type
            type_counts[st] = type_counts.get(st, 0) + 1

        # Count by action
        action_counts: dict[str, int] = {}
        for entry in self._entries.values():
            for action in entry.actions:
                action_counts[action] = action_counts.get(action, 0) + 1

        # Stable selectors
        stable_count = sum(1 for e in self._entries.values() if e.is_stable)

        # Average usage
        avg_usage = total_usage / total_entries if total_entries > 0 else 0

        return {
            "total_entries": total_entries,
            "total_usage": total_usage,
            "type_distribution": type_counts,
            "action_distribution": action_counts,
            "stable_selectors": stable_count,
            "avg_usage_per_selector": avg_usage,
        }

    # =========================================================================
    # State Integration
    # =========================================================================

    def from_state(self, state_data: dict[str, Any]) -> None:
        """
        Load catalog from state data.

        Args:
            state_data: State data from state.json
        """
        selector_catalog = state_data.get("selector_catalog", {})

        for entry_id, entry_data in selector_catalog.items():
            # Reconstruct SelectorData
            selector = SelectorData(
                raw=entry_data.get("selector", ""),
                type=entry_data.get("selector_type", ""),
                value=entry_data.get("value", ""),
                attributes=entry_data.get("metadata", {}).get("attributes", {}),
            )

            # Create entry
            entry = CatalogEntry(
                entry_id=entry_id,
                selector=selector,
                element_name=entry_data.get("name", ""),
                usage_count=entry_data.get("usage_count", 1),
                first_seen_recording=entry_data.get("recordings", [""])[0] if entry_data.get("recordings") else "",
                last_seen_recording=entry_data.get("recordings", [""])[-1] if entry_data.get("recordings") else "",
                recordings=entry_data.get("recordings", []),
                pages=entry_data.get("metadata", {}).get("pages", []),
                actions=[],
            )

            self._entries[entry_id] = entry
            self._selector_index[self._hash_selector(selector)] = entry_id

    def to_state(self) -> dict[str, Any]:
        """
        Export catalog to state format.

        Returns:
            Dictionary suitable for state.json
        """
        selector_catalog = {}

        for entry_id, entry in self._entries.items():
            selector_catalog[entry_id] = {
                "selector": entry.selector.raw,
                "selector_type": entry.selector.type,
                "value": entry.selector.value,
                "usage_count": entry.usage_count,
                "recordings": entry.recordings,
                "fragility_score": entry.selector.fragility_score,
                "alternatives": [],  # Built from groups
                "metadata": {
                    "name": entry.element_name,
                    "pages": entry.pages,
                    "actions": entry.actions,
                    "tags": entry.tags,
                    "notes": entry.notes,
                    "is_stable": entry.is_stable,
                },
            }

        return selector_catalog

    # =========================================================================
    # Import/Export
    # =========================================================================

    def import_from_groups(self, groups: list[ElementGroup]) -> None:
        """
        Import selectors from deduplication groups.

        Args:
            groups: Groups to import from
        """
        for group in groups:
            # Import canonical selector
            for context in group.contexts:
                self.add_selector(
                    group.canonical_selector,
                    context,
                    group.name_suggestion,
                )

            # Import alternatives
            for alt_selector in group.alternative_selectors:
                for context in group.contexts:
                    self.add_selector(
                        alt_selector,
                        context,
                        group.name_suggestion,
                    )

    # =========================================================================
    # Utilities
    # =========================================================================

    def _hash_selector(self, selector: SelectorData) -> str:
        """Generate hash for selector indexing."""
        return hashlib.sha256(selector.raw.encode()).hexdigest()[:16]

    def clear(self) -> None:
        """Clear all entries from the catalog."""
        self._entries.clear()
        self._selector_index.clear()

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self._entries)

    def __contains__(self, selector: SelectorData) -> bool:
        """Check if selector exists in catalog."""
        selector_hash = self._hash_selector(selector)
        return selector_hash in self._selector_index
