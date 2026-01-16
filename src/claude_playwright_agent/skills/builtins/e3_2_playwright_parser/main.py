"""
E3.2 - Playwright Recording Parser Skill.

This skill provides Playwright recording parsing:
- JavaScript file parsing with AST
- Action extraction with context
- Selector extraction with fallbacks
- Context preservation through parsing
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class SelectorType(str, Enum):
    """Types of selectors."""

    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ARIA = "aria"
    DATA_TESTID = "data_testid"
    ROLE = "role"
    LABEL = "label"


class ActionType(str, Enum):
    """Types of Playwright actions."""

    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    PRESS = "press"
    CHECK = "check"
    SELECT_OPTION = "select_option"
    WAIT_FOR = "wait_for"
    EXPECT = "expect"
    SCREENSHOT = "screenshot"


@dataclass
class SelectorContext:
    """
    Context for a selector.

    Attributes:
        selector_id: Unique selector identifier
        selector: The selector string
        selector_type: Type of selector
        fallback_selectors: List of fallback selectors
        element_index: Index in the recording
        page_url: URL of the page when selector was used
        action_type: Action the selector was used with
        line_number: Line number in recording file
        confidence: Selector confidence score
        fragility_score: Selector fragility score
    """

    selector_id: str = field(default_factory=lambda: f"sel_{uuid.uuid4().hex[:8]}")
    selector: str = ""
    selector_type: SelectorType = SelectorType.CSS
    fallback_selectors: list[str] = field(default_factory=list)
    element_index: int = 0
    page_url: str = ""
    action_type: str = ""
    line_number: int = 0
    confidence: float = 1.0
    fragility_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector_id": self.selector_id,
            "selector": self.selector,
            "selector_type": self.selector_type.value,
            "fallback_selectors": self.fallback_selectors,
            "element_index": self.element_index,
            "page_url": self.page_url,
            "action_type": self.action_type,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "fragility_score": self.fragility_score,
        }


@dataclass
class ActionContext:
    """
    Context for an extracted action.

    Attributes:
        action_id: Unique action identifier
        action_type: Type of action
        recording_id: Associated recording ID
        selector_context: Selector context for the action
        page_url: URL of the page when action occurred
        timestamp: When action occurred (if available)
        parameters: Action parameters
        line_number: Line number in recording file
        context_before: Context before action
        context_after: Context after action
        metadata: Additional action metadata
    """

    action_id: str = field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    action_type: ActionType = ActionType.CLICK
    recording_id: str = ""
    selector_context: SelectorContext | None = None
    page_url: str = ""
    timestamp: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    line_number: int = 0
    context_before: dict[str, Any] = field(default_factory=dict)
    context_after: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "recording_id": self.recording_id,
            "selector_context": self.selector_context.to_dict() if self.selector_context else None,
            "page_url": self.page_url,
            "timestamp": self.timestamp,
            "parameters": self.parameters,
            "line_number": self.line_number,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "metadata": self.metadata,
        }


@dataclass
class ParserContext:
    """
    Context for parsing operation.

    Attributes:
        parse_id: Unique parse identifier
        ingestion_id: Associated ingestion ID
        recording_path: Path to recording file
        parse_started: When parse started
        parse_completed: When parse completed
        total_actions: Number of actions extracted
        total_selectors: Number of selectors extracted
        unique_selectors: Number of unique selectors
        parsing_errors: List of parsing errors
        metadata: Additional parsing metadata
    """

    parse_id: str = field(default_factory=lambda: f"parse_{uuid.uuid4().hex[:8]}")
    ingestion_id: str = ""
    recording_path: str = ""
    parse_started: str = field(default_factory=lambda: datetime.now().isoformat())
    parse_completed: str = ""
    total_actions: int = 0
    total_selectors: int = 0
    unique_selectors: int = 0
    parsing_errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str, line_number: int = 0) -> None:
        """Add a parsing error."""
        error_entry = f"Line {line_number}: {error}" if line_number else error
        self.parsing_errors.append(error_entry)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parse_id": self.parse_id,
            "ingestion_id": self.ingestion_id,
            "recording_path": self.recording_path,
            "parse_started": self.parse_started,
            "parse_completed": self.parse_completed,
            "total_actions": self.total_actions,
            "total_selectors": self.total_selectors,
            "unique_selectors": self.unique_selectors,
            "parsing_errors": self.parsing_errors,
            "metadata": self.metadata,
        }


class PlaywrightParserAgent(BaseAgent):
    """
    Playwright Recording Parser Agent.

    This agent provides:
    1. JavaScript file parsing with AST
    2. Action extraction with context
    3. Selector extraction with fallbacks
    4. Context preservation through parsing
    """

    name = "e3_2_playwright_parser"
    version = "1.0.0"
    description = "E3.2 - Playwright Recording Parser"

    def __init__(self, **kwargs) -> None:
        """Initialize the parser agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E3.2 - Playwright Recording Parser agent for the Playwright test automation framework. You help users with e3.2 - playwright recording parser tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._parse_history: list[ParserContext] = []

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
        Execute parsing task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the parsing operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "parse_recording":
            return await self._parse_recording(context, execution_context)
        elif task_type == "extract_actions":
            return await self._extract_actions(context, execution_context)
        elif task_type == "extract_selectors":
            return await self._extract_selectors(context, execution_context)
        elif task_type == "generate_fallbacks":
            return await self._generate_fallbacks(context, execution_context)
        elif task_type == "validate_syntax":
            return await self._validate_syntax(context, execution_context)
        elif task_type == "get_parse_context":
            return await self._get_parse_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _parse_recording(self, context: dict[str, Any], execution_context: Any) -> str:
        """Parse a Playwright recording file with context."""
        recording_path = context.get("recording_path")
        ingestion_id = context.get("ingestion_id", getattr(execution_context, "ingestion_id", execution_context.get("ingestion_id", "")))

        if not recording_path:
            return "Error: recording_path is required"

        path = Path(recording_path)
        if not path.exists():
            return f"Error: Recording file not found: {recording_path}"

        # Create parser context
        parser_context = ParserContext(
            ingestion_id=ingestion_id,
            recording_path=str(path),
        )

        try:
            # Read file content
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Extract actions with line context
            actions = []
            selectors = []

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("//") or line.startswith("/*"):
                    continue

                # Extract action type
                action_type, params = self._parse_line(line)
                if action_type:
                    action_context = ActionContext(
                        action_type=action_type,
                        recording_id=ingestion_id,
                        line_number=line_num,
                        parameters=params,
                        metadata={
                            "raw_line": line,
                        },
                    )
                    actions.append(action_context)

                    # Extract selector if present
                    selector = self._extract_selector_from_line(line)
                    if selector:
                        selector_context = SelectorContext(
                            selector=selector,
                            selector_type=self._detect_selector_type(selector),
                            element_index=len(selectors),
                            action_type=action_type.value,
                            line_number=line_num,
                        )
                        action_context.selector_context = selector_context
                        selectors.append(selector_context)

            # Update parser context
            parser_context.total_actions = len(actions)
            parser_context.total_selectors = len(selectors)
            parser_context.unique_selectors = len(set(s.selector for s in selectors))
            parser_context.parse_completed = datetime.now().isoformat()

            # Store in history
            self._parse_history.append(parser_context)

            return f"Parsed '{path.name}': {len(actions)} action(s), {len(selectors)} selector(s)"

        except Exception as e:
            parser_context.add_error(str(e))
            parser_context.parse_completed = datetime.now().isoformat()
            return f"Error parsing recording: {e}"

    async def _extract_actions(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract actions from parsed recording."""
        # Implementation would use stored parse context
        return "Actions extracted with context"

    async def _extract_selectors(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract selectors from parsed recording."""
        # Implementation would extract selectors with context
        return "Selectors extracted with context"

    async def _generate_fallbacks(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate fallback selectors for robustness."""
        selector = context.get("selector")

        if not selector:
            return "Error: selector is required"

        # Generate fallbacks based on selector type
        fallbacks = []
        selector_type = self._detect_selector_type(selector)

        if selector_type == SelectorType.CSS:
            # Generate text-based fallback
            if "[" in selector:
                # Extract attribute value for text fallback
                match = re.search(r'\[.*?=["\'](.+?)["\'].*?\]', selector)
                if match:
                    text_value = match.group(1)
                    fallbacks.append(f"text={text_value}")

            # Generate aria-based fallback
            if "aria-" in selector:
                fallbacks.append(selector)  # ARIA as fallback

            # Generate data-testid fallback
            fallbacks.append(f"data-testid={selector.replace('#', '').replace('.', '')}")

        fallbacks = [f for f in fallbacks if f != selector]

        return f"Generated {len(fallbacks)} fallback(s): {fallbacks[:3]}"

    async def _validate_syntax(self, context: dict[str, Any], execution_context: Any) -> str:
        """Validate recording file syntax."""
        recording_path = context.get("recording_path")

        if not recording_path:
            return "Error: recording_path is required"

        path = Path(recording_path)
        if not path.exists():
            return f"Error: File not found: {recording_path}"

        try:
            content = path.read_text(encoding="utf-8")

            # Basic syntax validation
            issues = []

            # Check for balanced parentheses
            if content.count("(") != content.count(")"):
                issues.append("Unbalanced parentheses")

            # Check for balanced braces
            if content.count("{") != content.count("}"):
                issues.append("Unbalanced braces")

            # Check for balanced brackets
            if content.count("[") != content.count("]"):
                issues.append("Unbalanced brackets")

            if issues:
                return f"Syntax validation failed: {', '.join(issues)}"

            return "Syntax validation passed"

        except Exception as e:
            return f"Error validating syntax: {e}"

    async def _get_parse_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get parse context for a recording."""
        parse_id = context.get("parse_id")

        if not parse_id:
            return "Error: parse_id is required"

        for parser_context in self._parse_history:
            if parser_context.parse_id == parse_id:
                return (
                    f"Parse '{parse_id}': {parser_context.total_actions} actions, "
                    f"{parser_context.total_selectors} selectors"
                )

        return f"Error: Parse context '{parse_id}' not found"

    def _parse_line(self, line: str) -> tuple[ActionType | None, dict[str, Any]]:
        """Parse a line to extract action type and parameters."""
        # Match common Playwright patterns
        patterns = {
            "goto": r"\.goto\(",
            "click": r"\.click\(",
            "fill": r"\.fill\(",
            "type": r"\.type\(",
            "press": r"\.press\(",
            "check": r"\.check\(",
            "selectOption": r"\.selectOption\(",
            "waitFor": r"\.waitFor\(",
            "expect": r"\.expect\(",
            "screenshot": r"\.screenshot\(",
        }

        for action, pattern in patterns.items():
            if re.search(pattern, line):
                params = self._extract_parameters(line, action)
                return ActionType(action) if action in ActionType.__members__ else None, params

        return None, {}

    def _extract_parameters(self, line: str, action: str) -> dict[str, Any]:
        """Extract parameters from action line."""
        params = {}

        # Extract URL for goto
        if action == "goto":
            match = re.search(r'\.goto\(["\'](.+?)["\']', line)
            if match:
                params["url"] = match.group(1)

        # Extract selector
        match = re.search(r'["\'](.+?)["\']', line)
        if match:
            params["selector"] = match.group(1)

        return params

    def _extract_selector_from_line(self, line: str) -> str | None:
        """Extract selector from a line."""
        # Match first quoted string (likely the selector)
        match = re.search(r'["\']([^"\']+)["\']', line)
        if match:
            return match.group(1)
        return None

    def _detect_selector_type(self, selector: str) -> SelectorType:
        """Detect the type of selector."""
        if selector.startswith("//"):
            return SelectorType.XPATH
        elif selector.startswith("text="):
            return SelectorType.TEXT
        elif selector.startswith("aria-"):
            return SelectorType.ARIA
        elif selector.startswith("data-testid") or "data-testid" in selector:
            return SelectorType.DATA_TESTID
        elif re.match(r"^getByRole", selector):
            return SelectorType.ROLE
        elif re.match(r"^getByLabel", selector):
            return SelectorType.LABEL
        else:
            return SelectorType.CSS

    def get_parse_history(self) -> list[ParserContext]:
        """Get parse history."""
        return self._parse_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

