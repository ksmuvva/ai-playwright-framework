"""
Ingestion Agent for processing Playwright recordings.

This agent handles:
- Reading Playwright recording files
- Extracting actions and selectors
- Identifying navigation patterns and user flows
- Preparing data for further processing
- AI-powered semantic analysis
"""

from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.agents.playwright_parser import (
    parse_recording,
    ParsedRecording,
)


class ActionCategory(str, Enum):
    """Categories of actions for semantic analysis."""

    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    ASSERTION = "assertion"
    WAITING = "waiting"
    DATA_INPUT = "data_input"
    FORM_SUBMISSION = "form_submission"


@dataclass
class IngestionResult:
    """Result of ingesting a recording."""

    success: bool
    recording_path: str
    test_name: str
    total_actions: int
    actions_by_category: dict[str, int]
    forms_detected: list[dict]
    pages_visited: list[str]
    data_fields: list[dict]
    selectors_used: list[dict]
    semantic_analysis: dict
    error: Optional[str] = None


class IngestionAgent(BaseAgent):
    """
    Agent for ingesting Playwright recordings.

    Processes recorded test sessions and extracts structured data
    for conversion to BDD scenarios. Provides semantic analysis
    of the recorded user flow.
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        """
        Initialize the ingestion agent.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        system_prompt = """You are the Ingestion Agent for Claude Playwright Agent.

Your role is to:
1. Read Playwright recording files (.js files from codegen)
2. Extract test actions, selectors, and page interactions
3. Identify navigation patterns and user flows
4. Categorize actions semantically
5. Detect forms and data input patterns
6. Structure the data for BDD conversion

Provide detailed extraction results including:
- Action sequences with semantic categorization
- Element selectors with fallbacks and quality metrics
- Page structure information
- Test data parameters and field types
- User flow analysis
- Form detection and field mapping

Be thorough in identifying:
- Login flows
- Form submissions
- Search operations
- Navigation sequences
- Assertion points
- Wait conditions
"""
        super().__init__(system_prompt=system_prompt)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a Playwright recording file.

        Args:
            input_data: Input with 'recording_path' key

        Returns:
            Extracted actions and metadata
        """
        recording_path = input_data.get("recording_path", "")
        path = Path(recording_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Recording file not found: {recording_path}",
            }

        try:
            # Parse the recording
            parsed = parse_recording(path)

            # Categorize actions
            actions_by_category = self._categorize_actions(parsed.actions)

            # Detect forms
            forms_detected = self._detect_forms(parsed.actions)

            # Extract data fields
            data_fields = self._extract_data_fields(parsed.actions)

            # Perform semantic analysis
            semantic_analysis = await self._analyze_semantics(parsed)

            result = IngestionResult(
                success=True,
                recording_path=recording_path,
                test_name=parsed.test_name,
                total_actions=len(parsed.actions),
                actions_by_category=actions_by_category,
                forms_detected=forms_detected,
                pages_visited=parsed.urls_visited,
                data_fields=data_fields,
                selectors_used=[
                    {
                        "selector": str(s),
                        "type": getattr(s, "selector_type", "unknown"),
                        "fragility": getattr(s, "fragility", "unknown"),
                    }
                    for s in parsed.selectors_used
                ],
                semantic_analysis=semantic_analysis,
            )

            # Store in memory for learning
            await self.remember(
                key=f"recording_{path.stem}",
                value={
                    "test_name": parsed.test_name,
                    "actions_count": len(parsed.actions),
                    "categories": actions_by_category,
                    "forms": forms_detected,
                },
                memory_type="episodic",
                priority="medium",
                tags=["recording", path.stem, "ingestion"],
            )

            return result.__dict__

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse recording: {e}",
            }

    def _categorize_actions(self, actions: list) -> dict[str, int]:
        """Categorize actions by type."""
        categories = {
            "navigation": 0,
            "interaction": 0,
            "assertion": 0,
            "waiting": 0,
            "data_input": 0,
            "form_submission": 0,
        }

        for action in actions:
            action_type = getattr(action, "type", "").lower()

            if action_type in ["goto", "click", "dblclick"]:
                if action_type == "goto":
                    categories["navigation"] += 1
                else:
                    categories["interaction"] += 1
            elif action_type in ["fill", "check", "uncheck", "select_option"]:
                categories["data_input"] += 1
            elif action_type in ["expect", "assert"]:
                categories["assertion"] += 1
            elif action_type in ["wait_for", "wait_for_selector", "wait_for_timeout"]:
                categories["waiting"] += 1
            elif action_type == "press":
                categories["interaction"] += 1

        # Detect form submissions
        for i, action in enumerate(actions):
            action_type = getattr(action, "type", "").lower()
            if action_type == "click":
                selector = getattr(action, "selector", "") or ""
                if any(
                    keyword in selector.lower() for keyword in ["submit", "save", "send", "update"]
                ):
                    categories["form_submission"] += 1
                    categories["interaction"] -= 1  # Adjust from interaction

        return categories

    def _detect_forms(self, actions: list) -> list[dict]:
        """Detect forms in the recording."""
        forms = []
        current_form: Optional[dict] = None
        form_keywords = ["form", "login", "register", "contact", "search"]

        for action in actions:
            action_type = getattr(action, "type", "").lower()
            selector = getattr(action, "selector", "") or ""

            if action_type in ["fill", "check", "select_option"]:
                # Check if this is a new form
                is_new_form = True
                for keyword in form_keywords:
                    if keyword in selector.lower():
                        is_new_form = False
                        break

                if is_new_form and current_form is None:
                    current_form = {
                        "name": f"form_{len(forms) + 1}",
                        "fields": [],
                        "submit_button": None,
                    }

                if current_form:
                    field_type = "text"
                    field_name = selector.split(".")[-1].split("#")[-1]

                    if "email" in selector.lower():
                        field_type = "email"
                    elif "password" in selector.lower():
                        field_type = "password"
                    elif "phone" in selector.lower():
                        field_type = "phone"
                    elif action_type == "check":
                        field_type = "checkbox"

                    current_form["fields"].append(
                        {
                            "name": field_name,
                            "type": field_type,
                            "selector": selector,
                        }
                    )

            elif action_type == "click":
                selector = getattr(action, "selector", "") or ""
                if current_form and any(
                    kw in selector.lower() for kw in ["submit", "save", "send"]
                ):
                    current_form["submit_button"] = selector
                    forms.append(current_form)
                    current_form = None

        # Don't forget the last form if it has fields but no submit
        if current_form and len(current_form["fields"]) > 0:
            forms.append(current_form)

        return forms

    def _extract_data_fields(self, actions: list) -> list[dict]:
        """Extract data input fields from actions."""
        fields = []

        for action in actions:
            action_type = getattr(action, "type", "").lower()
            if action_type in ["fill", "check"]:
                selector = getattr(action, "selector", "") or ""
                value = getattr(action, "value", "") or ""

                field_type = "text"
                if "email" in selector.lower() or "@" in value:
                    field_type = "email"
                elif "password" in selector.lower():
                    field_type = "password"
                elif "phone" in selector.lower():
                    field_type = "phone"
                elif value.isdigit():
                    field_type = "number"
                elif value.lower() in ["true", "false"]:
                    field_type = "boolean"

                field_name = selector.split(".")[-1].split("#")[-1]
                if "[" in field_name:
                    field_name = field_name.split("[")[0]

                fields.append(
                    {
                        "name": field_name,
                        "type": field_type,
                        "value": value if field_type in ["text", "email"] else None,
                        "selector": selector,
                    }
                )

        return fields

    async def _analyze_semantics(self, parsed: ParsedRecording) -> dict:
        """Perform semantic analysis on the recording."""
        analysis = {
            "user_flow_type": "unknown",
            "steps": [],
            "page_transitions": [],
            "key_interactions": [],
        }

        # Determine user flow type
        actions = parsed.actions
        if any("login" in str(getattr(a, "selector", "")).lower() for a in actions[:5]):
            analysis["user_flow_type"] = "authentication"
        elif any(
            "search" in str(getattr(a, "selector", "")).lower() or getattr(a, "value", "")
            for a in actions
            if getattr(a, "type", "") == "fill"
        ):
            analysis["user_flow_type"] = "search"
        elif any(
            "checkout" in str(getattr(a, "selector", "")).lower()
            or "cart" in str(getattr(a, "selector", "")).lower()
            for a in actions
        ):
            analysis["user_flow_type"] = "e-commerce"
        elif len(forms := self._detect_forms(actions)) > 0:
            analysis["user_flow_type"] = "form_submission"
        else:
            analysis["user_flow_type"] = "general_navigation"

        # Identify key interactions
        for action in actions:
            action_type = getattr(action, "type", "").lower()
            if action_type == "click":
                selector = getattr(action, "selector", "") or ""
                if any(kw in selector.lower() for kw in ["button", "link", "nav", "menu", "tab"]):
                    analysis["key_interactions"].append(
                        {
                            "type": "navigation",
                            "selector": selector,
                        }
                    )
            elif action_type == "fill":
                selector = getattr(action, "selector", "") or ""
                analysis["key_interactions"].append(
                    {
                        "type": "data_entry",
                        "selector": selector,
                        "value_preview": str(getattr(action, "value", ""))[:20],
                    }
                )

        # Track page transitions
        for url in parsed.urls_visited:
            analysis["page_transitions"].append(url)

        return analysis

    async def quick_parse(self, recording_path: str) -> dict[str, Any]:
        """
        Quick parsing without full semantic analysis.

        Args:
            recording_path: Path to recording file

        Returns:
            Basic parsing results
        """
        path = Path(recording_path)
        if not path.exists():
            return {"error": "Recording file not found"}

        parsed = parse_recording(path)

        return {
            "success": True,
            "test_name": parsed.test_name,
            "total_actions": len(parsed.actions),
            "unique_selectors": len(parsed.selectors_used),
            "urls_visited": parsed.urls_visited,
            "file_size": path.stat().st_size,
        }
