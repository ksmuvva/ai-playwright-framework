"""
Deduplication Agent for identifying common elements across recordings.

This agent:
- Loads parsed recording data from state
- Performs element deduplication
- Extracts UI components
- Generates page objects
- Manages the selector catalog
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.deduplication.logic import (
    DeduplicationLogic,
    ElementGroup,
    ElementContext,
    SelectorData,
)
from claude_playwright_agent.deduplication.selector_catalog import SelectorCatalog
from claude_playwright_agent.deduplication.page_objects import (
    PageObjectGenerator,
    GenerationConfig,
)
from claude_playwright_agent.state.manager import StateManager


# =============================================================================
# Agent Configuration
# =============================================================================


class DeduplicationConfig(BaseModel):
    """Configuration for deduplication agent."""

    exact_match_threshold: float = Field(
        default=1.0,
        description="Threshold for exact matching (0-1)"
    )
    pattern_match_threshold: float = Field(
        default=0.85,
        description="Threshold for pattern matching (0-1)"
    )
    min_usage_for_component: int = Field(
        default=2,
        description="Minimum usage count to be considered a component"
    )
    generate_page_objects: bool = Field(
        default=True,
        description="Whether to generate page object classes"
    )
    page_object_output_dir: str = Field(
        default="pages",
        description="Output directory for page objects"
    )


# =============================================================================
# Deduplication Result
# =============================================================================


class DeduplicationResult(BaseModel):
    """Result of deduplication process."""

    success: bool = Field(..., description="Whether deduplication succeeded")
    total_groups: int = Field(default=0, description="Total element groups found")
    total_elements: int = Field(default=0, description="Total elements processed")
    components_extracted: int = Field(default=0, description="UI components extracted")
    page_objects_generated: int = Field(default=0, description="Page objects generated")
    selectors_cataloged: int = Field(default=0, description="Selectors added to catalog")
    deduplication_ratio: float = Field(default=0.0, description="Ratio of unique to total elements")
    groups: list[ElementGroup] = Field(
        default_factory=list,
        description="All element groups"
    )
    stats: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed statistics"
    )


# =============================================================================
# Deduplication Agent
# =============================================================================


class DeduplicationAgent:
    """
    Agent for deduplicating elements across recordings.

    Process:
    1. Load parsed recordings from state
    2. Extract all selectors with context
    3. Perform exact and pattern matching
    4. Group similar elements
    5. Extract components
    6. Generate page objects
    7. Update state with results
    """

    def __init__(
        self,
        project_path: Path,
        config: DeduplicationConfig | None = None,
    ) -> None:
        """
        Initialize the deduplication agent.

        Args:
            project_path: Path to the project
            config: Optional deduplication configuration
        """
        self.agent_id = "deduplication_agent"
        self.agent_type = "deduplication"
        self.project_path = project_path

        self.config = config or DeduplicationConfig()
        self.logic = DeduplicationLogic()
        self.catalog = SelectorCatalog()
        self.page_gen = PageObjectGenerator()

    # =========================================================================
    # Main Processing
    # =========================================================================

    def run(self) -> DeduplicationResult:
        """
        Run the deduplication process.

        Returns:
            DeduplicationResult with outcomes
        """
        try:
            # Load state
            state = StateManager(self.project_path)

            # Load recordings and extract selectors
            selectors_with_context = self._extract_selectors_from_state(state)

            if not selectors_with_context:
                return DeduplicationResult(
                    success=True,
                    total_groups=0,
                    total_elements=0,
                )

            # Perform deduplication
            groups = self._deduplicate_selectors(selectors_with_context)

            # Update catalog
            for group in groups:
                for context in group.contexts:
                    self.catalog.add_selector(
                        group.canonical_selector,
                        context,
                        group.name_suggestion,
                    )

            # Extract components
            components = self._extract_components(groups)

            # Generate page objects
            page_objects = []
            if self.config.generate_page_objects:
                page_objects = self._generate_page_objects(groups)

            # Update state
            self._update_state(state, groups, components, page_objects)

            # Calculate statistics
            total_elements = len(selectors_with_context)
            dedup_ratio = len(groups) / total_elements if total_elements > 0 else 0

            stats = {
                "logic_stats": self.logic.get_stats(),
                "catalog_stats": self.catalog.get_stats(),
                "components_count": len(components),
                "page_objects_count": len(page_objects),
            }

            return DeduplicationResult(
                success=True,
                total_groups=len(groups),
                total_elements=total_elements,
                components_extracted=len(components),
                page_objects_generated=len(page_objects),
                selectors_cataloged=len(self.catalog),
                deduplication_ratio=dedup_ratio,
                groups=groups,
                stats=stats,
            )

        except Exception as e:
            return DeduplicationResult(
                success=False,
                stats={"error": str(e)},
            )

    # =========================================================================
    # Selector Extraction
    # =========================================================================

    def _extract_selectors_from_state(
        self,
        state: StateManager,
    ) -> list[tuple[SelectorData, ElementContext]]:
        """
        Extract all selectors with context from state.

        Args:
            state: State manager

        Returns:
            List of (selector, context) tuples
        """
        selectors = []

        # Get recordings from state
        recordings = state.get_recordings()

        for recording in recordings:
            # Get parsed actions for this recording
            # This would be stored in state after ingestion
            recording_data = state._state.get("recordings_data", {}).get(recording.recording_id, {})

            actions = recording_data.get("actions", [])
            urls = recording_data.get("urls_visited", [])

            current_url = urls[0] if urls else ""

            for i, action_data in enumerate(actions):
                selector_data = self._action_to_selector(action_data)
                if selector_data:
                    context = ElementContext(
                        recording_id=recording.recording_id,
                        page_url=current_url,
                        action_type=action_data.get("action_type", ""),
                        line_number=action_data.get("line_number", 0),
                        element_index=i,
                        value=action_data.get("value"),
                    )
                    selectors.append((selector_data, context))

        return selectors

    def _action_to_selector(self, action: dict[str, Any]) -> SelectorData | None:
        """
        Convert action data to SelectorData.

        Args:
            action: Action dictionary from state

        Returns:
            SelectorData or None if not applicable
        """
        selector_info = action.get("selector")
        if not selector_info:
            return None

        return SelectorData(
            raw=selector_info.get("raw", ""),
            type=selector_info.get("type", ""),
            value=selector_info.get("value", ""),
            attributes=selector_info.get("attributes", {}),
        )

    # =========================================================================
    # Deduplication Logic
    # =========================================================================

    def _deduplicate_selectors(
        self,
        selectors_with_context: list[tuple[SelectorData, ElementContext]],
    ) -> list[ElementGroup]:
        """
        Perform deduplication on selectors.

        Args:
            selectors_with_context: List of (selector, context) tuples

        Returns:
            List of element groups
        """
        for selector, context in selectors_with_context:
            # Try exact match first
            existing_group = self.logic.exact_match(selector, context)

            if existing_group:
                # Add to existing group
                self.logic.add_to_group(
                    existing_group.group_id,
                    selector,
                    context,
                )
            else:
                # Try pattern match
                pattern_matches = self.logic.pattern_match(
                    selector,
                    context,
                    threshold=self.config.pattern_match_threshold,
                )

                if pattern_matches:
                    # Add to best matching group
                    best_group, _ = pattern_matches[0]
                    self.logic.add_to_group(
                        best_group.group_id,
                        selector,
                        context,
                    )
                else:
                    # Create new group
                    self.logic.create_group(selector, context)

        # Get all groups
        groups = self.logic.get_all_groups()

        # Merge contextually similar groups
        groups = self._merge_contextual_groups(groups)

        return groups

    def _merge_contextual_groups(
        self,
        groups: list[ElementGroup],
    ) -> list[ElementGroup]:
        """
        Merge groups with similar contexts.

        Args:
            groups: All element groups

        Returns:
            Merged groups
        """
        # For now, return as-is
        # Advanced merging could happen here based on:
        # - Same page + same action type
        # - Proximity in line numbers
        # - Similar usage patterns

        return groups

    # =========================================================================
    # Component Extraction
    # =========================================================================

    def _extract_components(
        self,
        groups: list[ElementGroup],
    ) -> dict[str, list[ElementGroup]]:
        """
        Extract UI components from element groups.

        A component is a set of related elements that:
        - Appear together across recordings
        - Are on the same page
        - Have similar usage patterns

        Args:
            groups: All element groups

        Returns:
            Dictionary mapping component IDs to element groups
        """
        components: dict[str, list[ElementGroup]] = {}

        # Group by page
        page_groups: dict[str, list[ElementGroup]] = {}
        for group in groups:
            for page in group.pages:
                if page not in page_groups:
                    page_groups[page] = []
                page_groups[page].append(group)

        # Find components on each page
        for page, page_elements in page_groups.items():
            # Group elements that appear together
            # For now, treat all elements on a page as one component
            component_id = f"component_{hash(page)}"

            # Only create component if enough elements
            if len(page_elements) >= self.config.min_usage_for_component:
                # Determine component type based on elements
                component_type = self._determine_component_type(page_elements)

                # Update component type for each group
                for group in page_elements:
                    group.component_type = component_type

                components[component_id] = page_elements

        return components

    def _determine_component_type(self, groups: list[ElementGroup]) -> str:
        """
        Determine component type from element groups.

        Args:
            groups: Element groups to analyze

        Returns:
            Component type string
        """
        actions = set()
        for group in groups:
            actions.update(ctx.action_type for ctx in group.contexts)

        # Heuristics for component type
        if 'fill' in actions or 'type' in actions:
            if 'check' in actions or 'select' in actions:
                return 'form'
            return 'input_field'

        if 'click' in actions:
            return 'button_group'

        return 'generic'

    # =========================================================================
    # Page Object Generation
    # =========================================================================

    def _generate_page_objects(
        self,
        groups: list[ElementGroup],
    ) -> list[Any]:
        """
        Generate page object classes.

        Args:
            groups: All element groups

        Returns:
            List of generated page object models
        """
        # Group by page
        page_groups: dict[str, list[ElementGroup]] = {}
        for group in groups:
            for page in group.pages:
                if page not in page_groups:
                    page_groups[page] = []
                page_groups[page].append(group)

        # Generate for each page
        output_dir = self.project_path / self.config.page_object_output_dir

        return self.page_gen.generate_all(page_groups, output_dir)

    # =========================================================================
    # State Update
    # =========================================================================

    def _update_state(
        self,
        state: StateManager,
        groups: list[ElementGroup],
        components: dict[str, list[ElementGroup]],
        page_objects: list[Any],
    ) -> None:
        """
        Update state with deduplication results.

        Args:
            state: State manager
            groups: Element groups
            components: Extracted components
            page_objects: Generated page objects
        """
        # Update components in state
        for component_id, element_groups in components.items():
            from claude_playwright_agent.state.models import UIComponent, ComponentElement

            # Build component elements
            component_elements = {}
            for group in element_groups:
                component_elements[group.name_suggestion] = ComponentElement(
                    selector=group.canonical_selector.raw,
                    selector_type=group.canonical_selector.type,
                    fragility_score=group.fragility_score,
                    usage_count=group.usage_count,
                    recordings=list(group.recordings),
                    alternatives=[s.raw for s in group.alternative_selectors],
                    metadata={
                        "component_type": group.component_type,
                        "name_suggestion": group.name_suggestion,
                        "pages": list(group.pages),
                    },
                )

            # Create UI component
            ui_component = UIComponent(
                component_id=component_id,
                name=element_groups[0].component_type if element_groups else "unknown",
                component_type=element_groups[0].component_type if element_groups else "generic",
                elements=component_elements,
                pages=list(set(
                    page for group in element_groups for page in group.pages
                )),
            )

            state._state.setdefault("components", {})[component_id] = ui_component.model_dump()

        # Update page objects in state
        for po in page_objects:
            state._state.setdefault("page_objects", {})[po.page_object_id] = po.model_dump()

        # Update selector catalog in state
        catalog_data = self.catalog.to_state()
        if catalog_data:
            state._state["selector_catalog"] = catalog_data

        # Save state
        state.save()


# =============================================================================
# Convenience Functions
# =============================================================================

def run_deduplication(
    project_path: Path,
    config: DeduplicationConfig | None = None,
) -> DeduplicationResult:
    """
    Run deduplication on a project.

    Args:
        project_path: Path to the project
        config: Optional deduplication configuration

    Returns:
        DeduplicationResult with outcomes
    """
    agent = DeduplicationAgent(project_path, config)
    return agent.run()
