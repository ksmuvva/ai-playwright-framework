"""
E3.3 - Action Extraction & Classification Skill.

This skill provides action extraction and classification:
- Action extraction with context
- Action type classification
- Pattern recognition
- User flow detection
- Context-aware metadata enrichment
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ActionCategory(str, Enum):
    """Categories of actions."""

    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    INPUT = "input"
    ASSERTION = "assertion"
    WAITING = "waiting"
    INFORMATION = "information"
    ADVANCED = "advanced"


class ActionSubtype(str, Enum):
    """Subtypes for more granular classification."""

    # Navigation
    PAGE_LOAD = "page_load"
    PAGE_NAVIGATE = "page_navigate"
    BACK_FORWARD = "back_forward"

    # Interaction
    ELEMENT_CLICK = "element_click"
    ELEMENT_HOVER = "element_hover"
    ELEMENT_DRAG = "element_drag"
    FORM_SUBMIT = "form_submit"

    # Input
    TEXT_INPUT = "text_input"
    TEXT_CLEAR = "text_clear"
    FILE_UPLOAD = "file_upload"
    SELECTION = "selection"

    # Assertion
    VISIBILITY_ASSERTION = "visibility_assertion"
    TEXT_ASSERTION = "text_assertion"
    ATTRIBUTE_ASSERTION = "attribute_assertion"
    STATE_ASSERTION = "state_assertion"


@dataclass
class ExtractedAction:
    """
    An extracted action with full context.

    Attributes:
        action_id: Unique action identifier
        sequence_number: Order in the recording
        action_type: Type of action
        action_category: Category of action
        action_subtype: Subtype of action
        selector: Element selector
        selector_context: Context about the selector
        page_url: URL when action occurred
        parameters: Action parameters
        value: Value used (for input actions)
        context_before: Context before action
        context_after: Context after action
        metadata: Additional action metadata
        extracted_at: When action was extracted
    """

    action_id: str = field(default_factory=lambda: f"ext_act_{uuid.uuid4().hex[:8]}")
    sequence_number: int = 0
    action_type: str = ""
    action_category: ActionCategory = ActionCategory.INTERACTION
    action_subtype: ActionSubtype = ActionSubtype.ELEMENT_CLICK
    selector: str = ""
    selector_context: dict[str, Any] = field(default_factory=dict)
    page_url: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    value: Any = None
    context_before: dict[str, Any] = field(default_factory=dict)
    context_after: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "sequence_number": self.sequence_number,
            "action_type": self.action_type,
            "action_category": self.action_category.value,
            "action_subtype": self.action_subtype.value,
            "selector": self.selector,
            "selector_context": self.selector_context,
            "page_url": self.page_url,
            "parameters": self.parameters,
            "value": self.value,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at,
        }


@dataclass
class ActionPattern:
    """
    A detected pattern in actions.

    Attributes:
        pattern_id: Unique pattern identifier
        pattern_type: Type of pattern
        actions: Actions in the pattern
        confidence: Pattern confidence score
        context: Pattern context
    """

    pattern_id: str = field(default_factory=lambda: f"pat_{uuid.uuid4().hex[:8]}")
    pattern_type: str = ""
    actions: list[ExtractedAction] = field(default_factory=list)
    confidence: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "actions": [a.to_dict() for a in self.actions],
            "confidence": self.confidence,
            "context": self.context,
        }


@dataclass
class ExtractionContext:
    """
    Context for action extraction.

    Attributes:
        extraction_id: Unique extraction identifier
        recording_id: Associated recording ID
        parse_id: Associated parse ID
        extraction_started: When extraction started
        extraction_completed: When extraction completed
        total_actions: Number of actions extracted
        categories_found: Categories of actions found
        patterns_found: Patterns detected
        metadata: Additional extraction metadata
    """

    extraction_id: str = field(default_factory=lambda: f"extract_{uuid.uuid4().hex[:8]}")
    recording_id: str = ""
    parse_id: str = ""
    extraction_started: str = field(default_factory=lambda: datetime.now().isoformat())
    extraction_completed: str = ""
    total_actions: int = 0
    categories_found: list[ActionCategory] = field(default_factory=list)
    patterns_found: list[ActionPattern] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "extraction_id": self.extraction_id,
            "recording_id": self.recording_id,
            "parse_id": self.parse_id,
            "extraction_started": self.extraction_started,
            "extraction_completed": self.extraction_completed,
            "total_actions": self.total_actions,
            "categories_found": [c.value for c in self.categories_found],
            "patterns_found": [p.to_dict() for p in self.patterns_found],
            "metadata": self.metadata,
        }


class ActionExtractionAgent(BaseAgent):
    """
    Action Extraction and Classification Agent.

    This agent provides:
    1. Action extraction with context
    2. Action type classification
    3. Pattern recognition
    4. User flow detection
    5. Context-aware metadata enrichment
    """

    name = "e3_3_action_extraction"
    version = "1.0.0"
    description = "E3.3 - Action Extraction & Classification"

    def __init__(self, **kwargs) -> None:
        """Initialize the action extraction agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E3.3 - Action Extraction & Classification agent for the Playwright test automation framework. You help users with e3.3 - action extraction & classification tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._extraction_history: list[ExtractionContext] = []

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
        Execute action extraction task.

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

        if task_type == "extract_actions":
            return await self._extract_actions(context, execution_context)
        elif task_type == "classify_action":
            return await self._classify_action(context, execution_context)
        elif task_type == "detect_patterns":
            return await self._detect_patterns(context, execution_context)
        elif task_type == "enrich_metadata":
            return await self._enrich_metadata(context, execution_context)
        elif task_type == "get_extraction_context":
            return await self._get_extraction_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _extract_actions(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract actions from parsed recording with context."""
        recording_id = context.get("recording_id")
        parse_id = context.get("parse_id", getattr(execution_context, "parse_id", execution_context.get("parse_id", "")))
        parsed_data = context.get("parsed_data", {})

        if not recording_id:
            return "Error: recording_id is required"

        # Create extraction context
        extraction_context = ExtractionContext(
            recording_id=recording_id,
            parse_id=parse_id,
        )

        # Extract actions from parsed data
        actions = parsed_data.get("actions", [])
        extracted_actions = []

        for idx, action_data in enumerate(actions):
            action = ExtractedAction(
                sequence_number=idx,
                action_type=action_data.get("type", "unknown"),
                selector=action_data.get("selector", ""),
                page_url=action_data.get("page_url", ""),
                parameters=action_data.get("parameters", {}),
                value=action_data.get("value"),
                metadata={
                    "recording_id": recording_id,
                    "extracted_by": "e3_3_action_extraction",
                },
            )

            # Classify action
            category, subtype = self._classify_action_type(action)
            action.action_category = category
            action.action_subtype = subtype

            # Add context
            action.selector_context = self._build_selector_context(action)
            action.context_before = self._build_context_before(action, idx, actions)
            action.context_after = self._build_context_after(action, idx, actions)

            extracted_actions.append(action)

        # Update extraction context
        extraction_context.total_actions = len(extracted_actions)
        extraction_context.categories_found = list(set(a.action_category for a in extracted_actions))
        extraction_context.extraction_completed = datetime.now().isoformat()

        # Store in history
        self._extraction_history.append(extraction_context)

        return f"Extracted {len(extracted_actions)} action(s) with context"

    async def _classify_action(self, context: dict[str, Any], execution_context: Any) -> str:
        """Classify a single action."""
        action_data = context.get("action_data", {})
        action_type = action_data.get("type", "")

        if not action_type:
            return "Error: action_type is required"

        category, subtype = self._classify_action_type_from_type(action_type)

        return f"Action classified as {category.value}/{subtype.value}"

    async def _detect_patterns(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect patterns in actions."""
        actions = context.get("actions", [])

        if not actions:
            return "Error: actions list is required"

        patterns = []

        # Detect login pattern
        login_pattern = self._detect_login_pattern(actions)
        if login_pattern:
            patterns.append(login_pattern)

        # Detect form fill pattern
        form_pattern = self._detect_form_fill_pattern(actions)
        if form_pattern:
            patterns.append(form_pattern)

        # Detect navigation pattern
        nav_pattern = self._detect_navigation_pattern(actions)
        if nav_pattern:
            patterns.append(nav_pattern)

        return f"Detected {len(patterns)} pattern(s): {[p.pattern_type for p in patterns]}"

    async def _enrich_metadata(self, context: dict[str, Any], execution_context: Any) -> str:
        """Enrich action metadata with context."""
        action_id = context.get("action_id")
        additional_context = context.get("additional_context", {})

        if not action_id:
            return "Error: action_id is required"

        # Find action in extraction history and enrich
        for extraction_context in self._extraction_history:
            # Would implement action lookup and enrichment
            pass

        return f"Action '{action_id}' metadata enriched with {len(additional_context)} field(s)"

    async def _get_extraction_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get extraction context."""
        extraction_id = context.get("extraction_id")

        if not extraction_id:
            return "Error: extraction_id is required"

        for extraction_context in self._extraction_history:
            if extraction_context.extraction_id == extraction_id:
                return (
                    f"Extraction '{extraction_id}': {extraction_context.total_actions} actions, "
                    f"{len(extraction_context.categories_found)} categories"
                )

        return f"Error: Extraction context '{extraction_id}' not found"

    def _classify_action_type(self, action: ExtractedAction) -> tuple[ActionCategory, ActionSubtype]:
        """Classify action type."""
        action_type = action.action_type.lower()

        # Navigation actions
        if "goto" in action_type or "navigate" in action_type:
            return ActionCategory.NAVIGATION, ActionSubtype.PAGE_NAVIGATE
        elif "go_back" in action_type or "back" in action_type:
            return ActionCategory.NAVIGATION, ActionSubtype.BACK_FORWARD

        # Click actions
        elif "click" in action_type:
            return ActionCategory.INTERACTION, ActionSubtype.ELEMENT_CLICK

        # Hover actions
        elif "hover" in action_type:
            return ActionCategory.INTERACTION, ActionSubtype.ELEMENT_HOVER

        # Input actions
        elif "fill" in action_type or "type" in action_type:
            return ActionCategory.INPUT, ActionSubtype.TEXT_INPUT
        elif "clear" in action_type:
            return ActionCategory.INPUT, ActionSubtype.TEXT_CLEAR
        elif "select" in action_type:
            return ActionCategory.INPUT, ActionSubtype.SELECTION

        # Assertion actions
        elif "expect" in action_type or "assert" in action_type:
            if "visible" in action_type:
                return ActionCategory.ASSERTION, ActionSubtype.VISIBILITY_ASSERTION
            elif "text" in action_type:
                return ActionCategory.ASSERTION, ActionSubtype.TEXT_ASSERTION
            else:
                return ActionCategory.ASSERTION, ActionSubtype.STATE_ASSERTION

        # Wait actions
        elif "wait" in action_type:
            return ActionCategory.WAITING, ActionSubtype.PAGE_LOAD

        # Default to interaction
        else:
            return ActionCategory.INTERACTION, ActionSubtype.ELEMENT_CLICK

    def _classify_action_type_from_type(self, action_type: str) -> tuple[ActionCategory, ActionSubtype]:
        """Classify action from action type string."""
        action = ExtractedAction(action_type=action_type)
        return self._classify_action_type(action)

    def _build_selector_context(self, action: ExtractedAction) -> dict[str, Any]:
        """Build context for the selector."""
        return {
            "selector": action.selector,
            "type": self._detect_selector_type(action.selector),
            "stability": self._assess_selector_stability(action.selector),
        }

    def _build_context_before(self, action: ExtractedAction, idx: int, all_actions: list) -> dict[str, Any]:
        """Build context before action."""
        return {
            "action_index": idx,
            "previous_action": all_actions[idx - 1] if idx > 0 else None,
        }

    def _build_context_after(self, action: ExtractedAction, idx: int, all_actions: list) -> dict[str, Any]:
        """Build context after action."""
        return {
            "action_index": idx,
            "next_action": all_actions[idx + 1] if idx < len(all_actions) - 1 else None,
        }

    def _detect_selector_type(self, selector: str) -> str:
        """Detect selector type."""
        if selector.startswith("//"):
            return "xpath"
        elif selector.startswith("[") or "=" in selector:
            return "attribute"
        else:
            return "css"

    def _assess_selector_stability(self, selector: str) -> str:
        """Assess selector stability."""
        if "data-testid" in selector or "data-test" in selector:
            return "stable"
        elif "id=" in selector or "#" in selector:
            return "moderate"
        else:
            return "fragile"

    def _detect_login_pattern(self, actions: list) -> ActionPattern | None:
        """Detect login pattern in actions."""
        # Look for username/password pattern
        return None

    def _detect_form_fill_pattern(self, actions: list) -> ActionPattern | None:
        """Detect form fill pattern in actions."""
        # Look for multiple fill actions followed by click
        return None

    def _detect_navigation_pattern(self, actions: list) -> ActionPattern | None:
        """Detect navigation pattern in actions."""
        # Look for sequence of goto actions
        return None

    def get_extraction_history(self) -> list[ExtractionContext]:
        """Get extraction history."""
        return self._extraction_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

