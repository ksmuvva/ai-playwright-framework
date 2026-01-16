"""
E4.3 - Component Extraction Skill.

This skill provides component extraction functionality:
- Component detection from patterns
- Reusable component extraction
- Component context tracking
- Action sequence analysis
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ComponentType(str, Enum):
    """Types of reusable components."""

    # Generic types (original)
    FORM = "form"
    NAVIGATION = "navigation"
    BUTTON_GROUP = "button_group"
    LIST = "list"
    TABLE = "table"
    MODAL = "modal"
    CARD = "card"
    INPUT_GROUP = "input_group"
    GENERIC = "generic"

    # Specific component types (enhanced)
    LOGIN_FORM = "login_form"
    SEARCH_BOX = "search_box"
    DROPDOWN = "dropdown"
    DATE_PICKER = "date_picker"
    FILE_UPLOAD = "file_upload"
    PAGINATION = "pagination"
    BREADCRUMB = "breadcrumb"
    DATA_TABLE = "data_table"
    ACCORDION = "accordion"
    TABS = "tabs"
    CAROUSEL = "carousel"
    PROGRESS_BAR = "progress_bar"


@dataclass
class ComponentElement:
    """
    An element within a component.

    Attributes:
        element_id: Unique element identifier
        selector: Element selector
        element_type: Type of element
        role: Role within component
        context: Element context
        actions: Common actions on this element
    """

    element_id: str = field(default_factory=lambda: f"comp_elem_{uuid.uuid4().hex[:8]}")
    selector: str = ""
    element_type: str = ""
    role: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "element_id": self.element_id,
            "selector": self.selector,
            "element_type": self.element_type,
            "role": self.role,
            "context": self.context,
            "actions": self.actions,
        }


@dataclass
class ReusableComponent:
    """
    A reusable component extracted from patterns.

    Attributes:
        component_id: Unique component identifier
        component_name: Suggested component name
        component_type: Type of component
        elements: List of elements in component
        selectors: List of selectors
        action_sequences: Common action sequences
        usage_contexts: List of contexts where used
        confidence: Confidence that this is a valid component
        extraction_context: Context at time of extraction
        extracted_at: When component was extracted
    """

    component_id: str = field(default_factory=lambda: f"comp_{uuid.uuid4().hex[:8]}")
    component_name: str = ""
    component_type: ComponentType = ComponentType.GENERIC
    elements: list[ComponentElement] = field(default_factory=list)
    selectors: list[str] = field(default_factory=list)
    action_sequences: list[list[str]] = field(default_factory=list)
    usage_contexts: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    extraction_context: dict[str, Any] = field(default_factory=dict)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "component_type": self.component_type.value,
            "elements": [e.to_dict() for e in self.elements],
            "selectors": self.selectors,
            "action_sequences": self.action_sequences,
            "usage_contexts": self.usage_contexts,
            "confidence": self.confidence,
            "extraction_context": self.extraction_context,
            "extracted_at": self.extracted_at,
        }


@dataclass
class ExtractionContext:
    """
    Context for component extraction.

    Attributes:
        extraction_id: Unique extraction identifier
        workflow_id: Associated workflow ID
        recording_ids: Recording IDs analyzed
        elements_analyzed: Number of elements analyzed
        components_found: Number of components found
        component_types: Breakdown by component type
        extraction_started: When extraction started
        extraction_completed: When extraction completed
        context_preserved: Whether context was preserved
    """

    extraction_id: str = field(default_factory=lambda: f"extract_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_ids: list[str] = field(default_factory=list)
    elements_analyzed: int = 0
    components_found: int = 0
    component_types: dict[str, int] = field(default_factory=dict)
    extraction_started: str = field(default_factory=lambda: datetime.now().isoformat())
    extraction_completed: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "extraction_id": self.extraction_id,
            "workflow_id": self.workflow_id,
            "recording_ids": self.recording_ids,
            "elements_analyzed": self.elements_analyzed,
            "components_found": self.components_found,
            "component_types": self.component_types,
            "extraction_started": self.extraction_started,
            "extraction_completed": self.extraction_completed,
            "context_preserved": self.context_preserved,
        }


class ComponentExtractionAgent(BaseAgent):
    """
    Component Extraction Agent.

    This agent provides:
    1. Component detection from patterns
    2. Reusable component extraction
    3. Component context tracking
    4. Action sequence analysis
    """

    name = "e4_3_component_extraction"
    version = "1.0.0"
    description = "E4.3 - Component Extraction"

    MIN_ELEMENT_COUNT = 2

    def __init__(self, **kwargs) -> None:
        """Initialize the component extraction agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E4.3 - Component Extraction agent for the Playwright test automation framework. You help users with e4.3 - component extraction tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._extraction_history: list[ExtractionContext] = []
        self._component_registry: dict[str, ReusableComponent] = {}

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute component extraction task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the extraction operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "extract_components":
            return await self._extract_components(context, execution_context)
        elif task_type == "detect_component_type":
            return await self._detect_component_type(context, execution_context)
        elif task_type == "analyze_action_sequences":
            return await self._analyze_action_sequences(context, execution_context)
        elif task_type == "create_component":
            return await self._create_component(context, execution_context)
        elif task_type == "get_extraction_context":
            return await self._get_extraction_context(context, execution_context)
        elif task_type == "get_component":
            return await self._get_component(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _extract_components(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract reusable components with full context."""
        element_groups = context.get("element_groups", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not element_groups:
            return "Error: element_groups list is required"

        # Create extraction context
        extraction_context = ExtractionContext(
            workflow_id=workflow_id,
        )

        components = []

        for group in element_groups:
            # Skip small groups
            element_ids = group.get("element_ids", [])
            if len(element_ids) < self.MIN_ELEMENT_COUNT:
                continue

            # Detect component type
            component_type = self._detect_component_from_group(group)

            # Create component
            component = ReusableComponent(
                component_name=group.get("group_name", f"component_{len(components)}"),
                component_type=component_type,
                selectors=group.get("selectors", []),
                usage_contexts=[group.get("grouping_context", {})],
                confidence=group.get("similarity", 0.8),
                extraction_context={
                    "workflow_id": workflow_id,
                    "extraction_id": extraction_context.extraction_id,
                    "element_count": len(element_ids),
                },
            )

            # Add elements
            for elem_data in group.get("elements", []):
                element = ComponentElement(
                    selector=elem_data.get("selector", ""),
                    element_type=elem_data.get("type", ""),
                    role=elem_data.get("role", ""),
                    context=elem_data.get("context", {}),
                )
                component.elements.append(element)

            components.append(component)
            self._component_registry[component.component_id] = component

        extraction_context.elements_analyzed = sum(len(g.get("element_ids", [])) for g in element_groups)
        extraction_context.components_found = len(components)

        # Type breakdown
        for comp in components:
            comp_type = comp.component_type.value
            extraction_context.component_types[comp_type] = extraction_context.component_types.get(comp_type, 0) + 1

        extraction_context.extraction_completed = datetime.now().isoformat()
        self._extraction_history.append(extraction_context)

        return f"Extracted {len(components)} component(s) from {len(element_groups)} group(s)"

    async def _detect_component_type(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect component type from element group."""
        elements = context.get("elements", [])

        if not elements:
            return "Error: elements list is required"

        component_type = self._infer_component_type(elements)

        return f"Detected component type: {component_type.value}"

    async def _analyze_action_sequences(self, context: dict[str, Any], execution_context: Any) -> str:
        """Analyze action sequences for component patterns."""
        actions = context.get("actions", [])

        if not actions:
            return "Error: actions list is required"

        # Group consecutive actions
        sequences = self._group_action_sequences(actions)

        return f"Found {len(sequences)} action sequence(s)"

    async def _create_component(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a component from elements."""
        elements = context.get("elements", [])
        component_name = context.get("component_name", "custom_component")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not elements:
            return "Error: elements list is required"

        component_type = self._infer_component_type(elements)

        component = ReusableComponent(
            component_name=component_name,
            component_type=component_type,
            selectors=[e.get("selector", {}).get("raw", "") for e in elements],
            extraction_context={
                "workflow_id": workflow_id,
                "manual_creation": True,
            },
        )

        for elem in elements:
            comp_elem = ComponentElement(
                selector=elem.get("selector", {}).get("raw", ""),
                element_type=elem.get("action_type", ""),
                context=elem,
            )
            component.elements.append(comp_elem)

        self._component_registry[component.component_id] = component

        return f"Created component: {component.component_id}"

    async def _get_extraction_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get extraction context."""
        extraction_id = context.get("extraction_id")

        if not extraction_id:
            return "Error: extraction_id is required"

        for extraction_context in self._extraction_history:
            if extraction_context.extraction_id == extraction_id:
                return (
                    f"Extraction '{extraction_id}': "
                    f"{extraction_context.elements_analyzed} elements, "
                    f"{extraction_context.components_found} components"
                )

        return f"Error: Extraction context '{extraction_id}' not found"

    async def _get_component(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get component by ID."""
        component_id = context.get("component_id")

        if not component_id:
            return "Error: component_id is required"

        component = self._component_registry.get(component_id)
        if component:
            return f"Component '{component.component_name}': {len(component.elements)} elements, type={component.component_type.value}"

        return f"Error: Component '{component_id}' not found"

    def _detect_component_from_group(self, group: dict[str, Any]) -> ComponentType:
        """Detect component type from element group."""
        elements = group.get("elements", [])
        return self._infer_component_type(elements)

    def _infer_component_type(self, elements: list[dict[str, Any]]) -> ComponentType:
        """Infer component type from elements."""
        if not elements:
            return ComponentType.GENERIC

        # Count element types
        action_types = [e.get("action_type", "") for e in elements]
        selectors = [e.get("selector", {}).get("raw", "") for e in elements]

        # Count various patterns
        input_count = sum(1 for t in action_types if "fill" in t.lower() or "input" in t.lower())
        click_count = sum(1 for t in action_types if "click" in t.lower())
        select_count = sum(1 for s in selectors for tag in ["select", "dropdown"] if tag in s.lower())

        # Check for specific component patterns

        # LOGIN_FORM: username + password fields
        if self._has_login_pattern(selectors):
            return ComponentType.LOGIN_FORM

        # SEARCH_BOX: search input + search button
        if self._has_search_pattern(selectors):
            return ComponentType.SEARCH_BOX

        # DROPDOWN: select elements or dropdown components
        if select_count > 0 and "select" in " ".join(selectors).lower():
            return ComponentType.DROPDOWN

        # DATE_PICKER: date input or calendar widget
        if self._has_date_pattern(selectors):
            return ComponentType.DATE_PICKER

        # FILE_UPLOAD: file input
        if self._has_file_upload_pattern(selectors):
            return ComponentType.FILE_UPLOAD

        # PAGINATION: next/prev buttons or page numbers
        if self._has_pagination_pattern(selectors):
            return ComponentType.PAGINATION

        # BREADCRUMB: breadcrumb navigation
        if self._has_breadcrumb_pattern(selectors):
            return ComponentType.BREADCRUMB

        # DATA_TABLE: table with multiple rows and data
        if self._has_data_table_pattern(selectors):
            return ComponentType.DATA_TABLE

        # ACCORDION: collapsible sections
        if self._has_accordion_pattern(selectors):
            return ComponentType.ACCORDION

        # TABS: tab navigation
        if self._has_tabs_pattern(selectors):
            return ComponentType.TABS

        # CAROUSEL: sliding content
        if self._has_carousel_pattern(selectors):
            return ComponentType.CAROUSEL

        # PROGRESS_BAR: progress indicator
        if self._has_progress_bar_pattern(selectors):
            return ComponentType.PROGRESS_BAR

        # Form detection (multiple inputs)
        if input_count >= 2 and click_count >= 1:
            return ComponentType.FORM

        # Navigation detection
        if any("link" in t.lower() or "nav" in t.lower() for t in action_types):
            return ComponentType.NAVIGATION

        # Button group detection
        if click_count >= 2 and input_count == 0:
            return ComponentType.BUTTON_GROUP

        # Input group detection
        if input_count >= 2:
            return ComponentType.INPUT_GROUP

        return ComponentType.GENERIC

    def _has_login_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match login form pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            ("username" in selector_text or "user" in selector_text or "email" in selector_text) and
            ("password" in selector_text or "pass" in selector_text) and
            ("login" in selector_text or "signin" in selector_text or "sign-in" in selector_text)
        )

    def _has_search_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match search box pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            "search" in selector_text and
            ("input" in selector_text or "textfield" in selector_text) and
            any(word in selector_text for word in ["button", "icon", "submit"])
        )

    def _has_date_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match date picker pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            "date" in selector_text or "calendar" in selector_text or
            "datepicker" in selector_text or "date-picker" in selector_text
        )

    def _has_file_upload_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match file upload pattern."""
        selector_text = " ".join(selectors).lower()
        return "file" in selector_text and "upload" in selector_text

    def _has_pagination_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match pagination pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            any(word in selector_text for word in ["pagination", "paging", "pager"]) or
            ("next" in selector_text and "prev" in selector_text) or
            ("page" in selector_text and any(str(i) in selector_text for i in range(1, 10)))
        )

    def _has_breadcrumb_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match breadcrumb pattern."""
        selector_text = " ".join(selectors).lower()
        return "breadcrumb" in selector_text or "breadcrumb" in selector_text

    def _has_data_table_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match data table pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            "table" in selector_text and
            any(word in selector_text for word in ["thead", "tbody", "row", "column", "cell"])
        )

    def _has_accordion_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match accordion pattern."""
        selector_text = " ".join(selectors).lower()
        return "accordion" in selector_text or "collapse" in selector_text

    def _has_tabs_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match tabs pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            any(word in selector_text for word in ["tab", "tabs", "tabpanel"]) and
            "active" in selector_text
        )

    def _has_carousel_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match carousel pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            any(word in selector_text for word in ["carousel", "slider", "slideshow"]) and
            any(word in selector_text for word in ["next", "prev", "arrow", "dot"])
        )

    def _has_progress_bar_pattern(self, selectors: list[str]) -> bool:
        """Check if selectors match progress bar pattern."""
        selector_text = " ".join(selectors).lower()
        return (
            any(word in selector_text for word in ["progress", "progressbar", "progress-bar"]) and
            any(word in selector_text for word in ["bar", "fill", "value", "percent"])
        )

    def _group_action_sequences(self, actions: list[dict[str, Any]]) -> list[list[str]]:
        """Group consecutive action sequences."""
        sequences = []
        current_sequence = []
        last_recording = None

        for action in actions:
            recording_id = action.get("recording_id", "")

            if last_recording and recording_id != last_recording:
                if current_sequence:
                    sequences.append(current_sequence)
                current_sequence = []

            current_sequence.append(action.get("action_type", ""))
            last_recording = recording_id

        if current_sequence:
            sequences.append(current_sequence)

        return sequences

    def get_extraction_history(self) -> list[ExtractionContext]:
        """Get extraction history."""
        return self._extraction_history.copy()

    def get_component_registry(self) -> dict[str, ReusableComponent]:
        """Get component registry."""
        return self._component_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

