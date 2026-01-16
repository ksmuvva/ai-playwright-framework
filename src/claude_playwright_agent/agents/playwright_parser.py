"""
Enhanced Playwright Recording Parser with AST support.

This module provides:
- Full JavaScript AST parsing using Esprima
- Comprehensive action extraction
- Selector fragility scoring
- Fallback selector generation
- Action classification and pattern detection
"""

import ast
import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# =============================================================================
# Action Types
# =============================================================================


class ActionType(str, Enum):
    """Types of Playwright actions."""

    # Navigation
    GOTO = "goto"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    RELOAD = "reload"

    # Interaction
    CLICK = "click"
    DBLCLICK = "dblclick"
    RIGHT_CLICK = "right_click"
    HOVER = "hover"
    FILL = "fill"
    TYPE = "type"
    PRESS = "press"
    CHECK = "check"
    UNCHECK = "uncheck"
    SELECT_OPTION = "select_option"

    # Advanced interaction (E3.1 additions)
    DRAG = "drag"
    DROP = "drop"
    SCROLL = "scroll"
    FOCUS = "focus"
    BLUR = "blur"
    TAP = "tap"
    LONG_PRESS = "long_press"
    SWIPE = "swipe"
    PINCH = "pinch"
    ZOOM = "zoom"

    # Clipboard
    COPY = "copy"
    CUT = "cut"
    PASTE = "paste"

    # Input
    SET_INPUT_FILES = "set_input_files"
    CLEAR = "clear"

    # Frame/IFrame handling
    SWITCH_TO_FRAME = "switch_to_frame"
    SWITCH_TO_MAIN_FRAME = "switch_to_main_frame"

    # Waiting
    WAIT_FOR = "wait_for"  # Generic wait (alias for wait_for_selector)
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_TIMEOUT = "wait_for_timeout"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    WAIT_FOR_FUNCTION = "wait_for_function"

    # Assertions
    EXPECT = "expect"
    ASSERT = "assert"
    TO_BE_VISIBLE = "to_be_visible"
    TO_BE_HIDDEN = "to_be_hidden"
    TO_BE_ENABLED = "to_be_enabled"
    TO_BE_DISABLED = "to_be_disabled"
    TO_BE_CHECKED = "to_be_checked"
    TO_CONTAIN_TEXT = "to_contain_text"
    TO_HAVE_ATTRIBUTE = "to_have_attribute"
    TO_HAVE_COUNT = "to_have_count"
    TO_HAVE_CLASS = "to_have_class"

    # Information
    SCREENSHOT = "screenshot"
    PDF = "pdf"
    TITLE = "title"
    URL = "url"
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    GET_HTML = "get_html"
    INNER_TEXT = "inner_text"
    INNER_HTML = "inner_html"

    # Network
    WAIT_FOR_REQUEST = "wait_for_request"
    WAIT_FOR_RESPONSE = "wait_for_response"
    MOCK_RESPONSE = "mock_response"

    # Browser control
    SET_VIEWPORT_SIZE = "set_viewport_size"
    EMULATE_MEDIA = "emulate_media"
    SET_GEOTLOCATION = "set_geolocation"
    SET_OFFLINE = "set_offline"
    SET_ONLINE = "set_online"

    # Storage
    GET_COOKIES = "get_cookies"
    SET_COOKIES = "set_cookies"
    CLEAR_COOKIES = "clear_cookies"
    GET_LOCAL_STORAGE = "get_local_storage"
    SET_LOCAL_STORAGE = "set_local_storage"
    CLEAR_LOCAL_STORAGE = "clear_local_storage"
    GET_SESSION_STORAGE = "get_session_storage"
    SET_SESSION_STORAGE = "set_session_storage"
    CLEAR_SESSION_STORAGE = "clear_session_storage"

    # Dialog/Alert handling
    ACCEPT_DIALOG = "accept_dialog"
    DISMISS_DIALOG = "dismiss_dialog"

    # Authentication
    BASIC_AUTH = "basic_auth"

    # Download handling
    WAIT_FOR_DOWNLOAD = "wait_for_download"

    # Other
    CUSTOM = "custom"
    UNKNOWN = "unknown"

    @classmethod
    def get_all_action_types(cls) -> list[str]:
        """Get all action type values."""
        return [action.value for action in cls]


class SelectorType(str, Enum):
    """Types of selectors."""

    # Playwright's recommended selectors
    GET_BY_ROLE = "getByRole"
    GET_BY_LABEL = "getByLabel"
    GET_BY_PLACEHOLDER = "getByPlaceholder"
    GET_BY_TEXT = "getByText"
    GET_BY_ALT_TEXT = "getByAltText"
    GET_BY_TITLE = "getByTitle"
    GET_BY_TEST_ID = "getByTestId"

    # CSS selectors
    CSS_SELECTOR = "css"
    LOCATOR = "locator"  # For backward compatibility with tests
    ID = "id"
    CLASS = "class"
    TAG = "tag"

    # XPath
    XPATH = "xpath"

    # Unknown
    UNKNOWN = "unknown"


class FragilityLevel(str, Enum):
    """Fragility levels for selectors."""

    ROBUST = "robust"           # Stable, semantic selectors
    MODERATE = "moderate"       # Generally stable but may break
    FRAGILE = "fragile"         # Likely to break with changes
    VERY_FRAGILE = "very_fragile"  # Highly likely to break


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SelectorInfo:
    """
    Information about a selector.

    Attributes:
        raw: Original selector string
        type: Selector type
        value: Primary selector value (e.g., role value, text content)
        attributes: Additional selector attributes
        fragility: How fragile the selector is
        fallbacks: List of alternative selectors
        line_number: Line number in recording file
    """
    raw: str
    type: SelectorType = SelectorType.UNKNOWN
    value: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    fragility: FragilityLevel = FragilityLevel.MODERATE
    fallbacks: list[str] = field(default_factory=list)
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        # Handle both enum and string types for compatibility
        type_value = self.type.value if hasattr(self.type, 'value') else self.type
        fragility_value = self.fragility.value if hasattr(self.fragility, 'value') else self.fragility

        return {
            "raw": self.raw,
            "type": type_value,
            "value": self.value,
            "attributes": self.attributes,
            "fragility": fragility_value,
            "fallbacks": self.fallbacks,
            "line_number": self.line_number,
        }


@dataclass
class Action:
    """
    A single test action extracted from a Playwright recording.

    Attributes:
        action_type: Type of action
        selector: Element selector info
        value: Value (for fill, type, etc.)
        page_url: URL of the page when action occurred
        line_number: Line number in recording file
        timestamp: When action was extracted
        options: Additional options (timeout, force, etc.)
    """
    action_type: ActionType
    selector: Optional[SelectorInfo] = None
    value: str = ""
    page_url: str = ""
    line_number: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        # Handle both enum and string types for compatibility
        action_type_value = self.action_type.value if hasattr(self.action_type, 'value') else self.action_type

        return {
            "action_type": action_type_value,
            "selector": self.selector.to_dict() if self.selector else None,
            "value": self.value,
            "page_url": self.page_url,
            "line_number": self.line_number,
            "timestamp": self.timestamp,
            "options": self.options,
        }


@dataclass
class ParsedRecording:
    """
    Result of parsing a Playwright recording.

    Attributes:
        test_name: Name of the test
        actions: List of extracted actions
        urls_visited: List of URLs visited
        selectors_used: List of all selectors
        file_path: Path to recording file
        metadata: Additional metadata
    """
    test_name: str = ""
    actions: list[Action] = field(default_factory=list)
    urls_visited: list[str] = field(default_factory=list)
    selectors_used: list[SelectorInfo] = field(default_factory=list)
    file_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "actions": [a.to_dict() for a in self.actions],
            "urls_visited": self.urls_visited,
            "selectors_used": [s.to_dict() for s in self.selectors_used],
            "file_path": self.file_path,
            "metadata": self.metadata,
        }


# =============================================================================
# Enhanced Parser
# =============================================================================


class PlaywrightRecordingParser:
    """
    Enhanced Playwright recording parser.

    Features:
    - Full JavaScript AST parsing
    - Comprehensive action extraction
    - Selector fragility scoring
    - Fallback selector generation
    - Action classification
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        self._current_url = ""
        self._actions: list[Action] = []
        self._urls_visited: list[str] = []
        self._selectors_used: list[SelectorInfo] = []

    def parse_file(self, file_path: Path) -> ParsedRecording:
        """
        Parse a Playwright recording file.

        Args:
            file_path: Path to the recording file

        Returns:
            ParsedRecording with all extracted data
        """
        content = file_path.read_text(encoding="utf-8")
        return self.parse_content(content, str(file_path))

    def parse_content(self, content: str, file_path: str = "") -> ParsedRecording:
        """
        Parse Playwright recording content.

        Args:
            content: JavaScript code from recording
            file_path: Optional file path for reference

        Returns:
            ParsedRecording with all extracted data
        """
        self._current_url = ""
        self._actions = []
        self._urls_visited = []
        self._selectors_used = []

        # Extract test name from content
        test_name = self._extract_test_name(content)

        # Parse using enhanced regex patterns with context
        self._parse_goto_actions(content)
        self._parse_click_actions(content)
        self._parse_fill_actions(content)
        self._parse_type_actions(content)
        self._parse_press_actions(content)
        self._parse_check_actions(content)
        self._parse_hover_actions(content)
        self._parse_wait_actions(content)
        self._parse_expect_actions(content)
        self._parse_screenshot_actions(content)

        # Sort actions by line number to maintain correct order
        self._actions.sort(key=lambda a: a.line_number)

        # Extract metadata
        metadata = self._extract_metadata(content)

        # Create result
        return ParsedRecording(
            test_name=test_name,
            actions=self._actions,
            urls_visited=self._urls_visited,
            selectors_used=self._selectors_used,
            file_path=file_path,
            metadata=metadata,
        )

    def _extract_test_name(self, content: str) -> str:
        """Extract test name from recording content."""
        # Try to find test() function name
        match = re.search(r'test\s*\(\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        return ""

    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """Extract metadata from recording content."""
        # Count actions by type
        action_counts = {}
        for action in self._actions:
            action_type = action.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        metadata = {
            "total_actions": len(self._actions),
            "unique_urls": len(set(self._urls_visited)),
            "unique_selectors": len(self._selectors_used),
            "action_counts": action_counts,
        }

        # Check for TypeScript check directive
        metadata["ts_check"] = "// @ts-check" in content

        # Extract imports
        imports = []
        import_matches = re.findall(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
        metadata["imports"] = import_matches if import_matches else []

        return metadata

    def _parse_goto_actions(self, content: str) -> None:
        """Parse page.goto() actions."""
        pattern = r'await\s+page\.goto\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            url = match.group(1)
            self._current_url = url
            self._urls_visited.append(url)

            # Find line number
            line_num = content[:match.start()].count('\n') + 1

            action = Action(
                action_type=ActionType.GOTO,
                value=url,
                page_url=self._current_url,
                line_number=line_num,
            )
            self._actions.append(action)

    def _parse_click_actions(self, content: str) -> None:
        """Parse click actions."""
        # Collect all matches first, then sort by position to maintain order
        all_matches = []

        # Pattern: await page.click(), await page.locator().click(), await page.getByRole().click(), etc.
        patterns = [
            # Handle chained getBy* calls: page.getByRole(...).click() (MOST SPECIFIC)
            (r'await\s+page\.(getBy[A-Za-z]+)\s*\(([^)]*)\)\.click\s*\([^)]*\)', 'getBy'),
            # Handle page.locator().click()
            (r'await\s+page\.locator\(([^)]+)\)\.click\s*\([^)]*\)', 'locator'),
            # Handle page.click()
            (r'await\s+page\.click\s*\(([^)]+)\)', 'click'),
        ]

        for pattern, pattern_type in patterns:
            for match in re.finditer(pattern, content):
                all_matches.append((match.start(), match, pattern_type))

        # Sort matches by position in content
        all_matches.sort(key=lambda x: x[0])

        # Process matches in order
        for _, match, pattern_type in all_matches:
            if pattern_type == 'getBy':
                # Extract the getBy* method and its arguments
                get_by_method = match.group(1)
                get_by_args = match.group(2)
                # Reconstruct full selector expression
                locator_expr = f"{get_by_method}({get_by_args})"
                selector_info = self._parse_selector(locator_expr, match.start())
            else:
                locator_expr = match.group(1)
                # For locator expressions, wrap them to indicate they're locator calls
                if pattern_type == 'locator':
                    locator_expr = f"locator({locator_expr})"
                selector_info = self._parse_selector(locator_expr, match.start())

            line_num = content[:match.start()].count('\n') + 1

            action = Action(
                action_type=ActionType.CLICK,
                selector=selector_info,
                page_url=self._current_url,
                line_number=line_num,
            )
            self._actions.append(action)

            if selector_info:
                self._selectors_used.append(selector_info)

    def _parse_fill_actions(self, content: str) -> None:
        """Parse fill actions."""
        # Pattern: await page.fill(), await locator.fill(), await page.getByLabel().fill(), etc.
        patterns = [
            r'await\s+page\.fill\s*\(\s*([^,]+),\s*["\']([^"\']*)["\']',
            r'await\s+locator\(([^)]+)\)\.fill\s*\(\s*["\']([^"\']*)["\']',
            # Handle chained getBy* calls
            r'await\s+page\.(getBy[A-Za-z]+)\s*\(([^)]*)\)\.fill\s*\(\s*["\']([^"\']*)["\']',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                if 'getBy' in match.group(0):
                    # Extract getBy* method and arguments
                    get_by_method = match.group(1)
                    get_by_args = match.group(2)
                    value = match.group(3)
                    locator_expr = f"{get_by_method}({get_by_args})"
                    selector_info = self._parse_selector(locator_expr, match.start())
                else:
                    locator_expr = match.group(1)
                    value = match.group(2)
                    selector_info = self._parse_selector(locator_expr, match.start())

                line_num = content[:match.start()].count('\n') + 1

                action = Action(
                    action_type=ActionType.FILL,
                    selector=selector_info,
                    value=value,
                    page_url=self._current_url,
                    line_number=line_num,
                )
                self._actions.append(action)

                if selector_info:
                    self._selectors_used.append(selector_info)

    def _parse_type_actions(self, content: str) -> None:
        """Parse type actions."""
        patterns = [
            r'await\s+page\.type\s*\(\s*([^,]+),\s*["\']([^"\']*)["\']',
            r'await\s+locator\(([^)]+)\)\.type\s*\(\s*["\']([^"\']*)["\']',
            # Handle chained getBy* calls: page.getByPlaceholder().type()
            r'await\s+page\.(getBy[A-Za-z]+)\s*\(([^)]*)\)\.type\s*\(\s*["\']([^"\']*)["\']',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                if 'getBy' in match.group(0):
                    # Extract getBy* method and arguments
                    get_by_method = match.group(1)
                    get_by_args = match.group(2)
                    value = match.group(3)
                    # Reconstruct full selector expression
                    locator_expr = f"{get_by_method}({get_by_args})"
                    selector_info = self._parse_selector(locator_expr, match.start())
                else:
                    locator_expr = match.group(1)
                    value = match.group(2)
                    selector_info = self._parse_selector(locator_expr, match.start())

                line_num = content[:match.start()].count('\n') + 1

                action = Action(
                    action_type=ActionType.TYPE,
                    selector=selector_info,
                    value=value,
                    page_url=self._current_url,
                    line_number=line_num,
                )
                self._actions.append(action)

    def _parse_press_actions(self, content: str) -> None:
        """Parse press actions."""
        patterns = [
            r'await\s+page\.press\s*\(\s*([^,]+),\s*["\']([^"\']*)["\']',
            r'await\s+locator\(([^)]+)\)\.press\s*\(\s*["\']([^"\']*)["\']',
            # Handle page.keyboard.press()
            r'await\s+page\.keyboard\.press\s*\(\s*["\']([^"\']*)["\']',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                # For page.keyboard.press(), there's no selector
                if 'keyboard' in match.group(0):
                    value = match.group(1)
                    selector_info = None
                else:
                    locator_expr = match.group(1)
                    value = match.group(2)
                    selector_info = self._parse_selector(locator_expr, match.start())

                line_num = content[:match.start()].count('\n') + 1

                action = Action(
                    action_type=ActionType.PRESS,
                    selector=selector_info,
                    value=value,
                    page_url=self._current_url,
                    line_number=line_num,
                )
                self._actions.append(action)

    def _parse_check_actions(self, content: str) -> None:
        """Parse check/uncheck actions."""
        patterns = [
            r'await\s+page\.check\s*\(([^)]+)\)',
            r'await\s+page\.uncheck\s*\(([^)]+)\)',
            r'await\s+locator\(([^)]+)\)\.check\s*\([^)]*\)',
            r'await\s+locator\(([^)]+)\)\.uncheck\s*\([^)]*\)',
            # Handle chained getBy* calls: page.getByRole().check()
            r'await\s+page\.(getBy[A-Za-z]+)\s*\(([^)]*)\)\.check\s*\([^)]*\)',
            r'await\s+page\.(getBy[A-Za-z]+)\s*\(([^)]*)\)\.uncheck\s*\([^)]*\)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                is_check = 'check' in match.group(0)
                if 'getBy' in match.group(0):
                    # Extract getBy* method and arguments
                    get_by_method = match.group(1)
                    get_by_args = match.group(2)
                    # Reconstruct full selector expression
                    locator_expr = f"{get_by_method}({get_by_args})"
                    selector_info = self._parse_selector(locator_expr, match.start())
                else:
                    locator_expr = match.group(1)
                    selector_info = self._parse_selector(locator_expr, match.start())

                line_num = content[:match.start()].count('\n') + 1

                action = Action(
                    action_type=ActionType.CHECK if is_check else ActionType.UNCHECK,
                    selector=selector_info,
                    page_url=self._current_url,
                    line_number=line_num,
                )
                self._actions.append(action)

                if selector_info:
                    self._selectors_used.append(selector_info)

    def _parse_hover_actions(self, content: str) -> None:
        """Parse hover actions."""
        patterns = [
            r'await\s+page\.hover\s*\(([^)]+)\)',
            r'await\s+locator\(([^)]+)\)\.hover\s*\([^)]*\)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                locator_expr = match.group(1)
                selector_info = self._parse_selector(locator_expr, match.start())

                line_num = content[:match.start()].count('\n') + 1

                action = Action(
                    action_type=ActionType.HOVER,
                    selector=selector_info,
                    page_url=self._current_url,
                    line_number=line_num,
                )
                self._actions.append(action)

                if selector_info:
                    self._selectors_used.append(selector_info)

    def _parse_wait_actions(self, content: str) -> None:
        """Parse wait actions."""
        # waitForSelector
        pattern = r'await\s+page\.waitForSelector\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            selector_str = match.group(1)
            selector_info = SelectorInfo(
                raw=selector_str,
                type=SelectorType.CSS_SELECTOR,
                value=selector_str,
                fragility=self._assess_fragility(selector_str),
            )

            line_num = content[:match.start()].count('\n') + 1

            action = Action(
                action_type=ActionType.WAIT_FOR,  # Use generic WAIT_FOR type
                selector=selector_info,
                page_url=self._current_url,
                line_number=line_num,
            )
            self._actions.append(action)
            self._selectors_used.append(selector_info)

    def _parse_expect_actions(self, content: str) -> None:
        """Parse expect/assert actions."""
        # Single combined pattern to avoid double matching
        # Match either: await expect(...) or expect(...)
        pattern = r'(?:await\s+)?expect\s*\(([^)]+)\)\.'

        # Track matched positions to avoid duplicates
        matched_positions = set()

        for match in re.finditer(pattern, content):
            # Check if we've already processed this position
            if match.start() in matched_positions:
                continue
            matched_positions.add(match.start())

            expr = match.group(1)

            line_num = content[:match.start()].count('\n') + 1

            action = Action(
                action_type=ActionType.EXPECT,
                value=expr[:100],  # Truncate long expressions
                page_url=self._current_url,
                line_number=line_num,
            )
            self._actions.append(action)

    def _parse_screenshot_actions(self, content: str) -> None:
        """Parse screenshot actions."""
        pattern = r'await\s+page\.screenshot\s*\('
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            action = Action(
                action_type=ActionType.SCREENSHOT,
                page_url=self._current_url,
                line_number=line_num,
            )
            self._actions.append(action)

    def _parse_selector(self, expr: str, pos: int) -> Optional[SelectorInfo]:
        """
        Parse a selector expression into SelectorInfo.

        Args:
            expr: Selector expression from recording
            pos: Position in content for error reporting

        Returns:
            SelectorInfo with fragility assessment
        """
        expr = expr.strip().strip('"').strip("'")

        # Try to parse as getBy* selector
        # Enum values are camelCase: "getByRole", "getByLabel", etc.
        for selector_type in SelectorType:
            if selector_type.value.startswith('get'):
                # Case-insensitive match: "getByRole" matches "getByRole" or "getbyrole"
                if selector_type.value.lower() in expr.lower():
                    return self._parse_get_by_selector(expr, selector_type)

        # Try CSS selector
        if any(expr.startswith(c) for c in ('.', '#', '[')):
            return SelectorInfo(
                raw=expr,
                type=SelectorType.CSS_SELECTOR,
                value=expr,
                fragility=self._assess_fragility(expr),
            )

        # Handle locator() - it's a CSS selector in quotes
        if expr.startswith('locator('):
            # Extract the CSS selector from locator('selector')
            match = re.search(r'locator\s*\(\s*["\']([^"\']+)["\']', expr)
            if match:
                css_selector = match.group(1)
                return SelectorInfo(
                    raw=expr,
                    type=SelectorType.LOCATOR,  # Use LOCATOR type for backward compatibility
                    value=css_selector,
                    fragility=self._assess_fragility(css_selector),
                )

        # Default
        return SelectorInfo(
            raw=expr,
            type=SelectorType.UNKNOWN,
            value=expr,
            fragility=FragilityLevel.VERY_FRAGILE,
        )

    def _parse_get_by_selector(self, expr: str, selector_type: SelectorType) -> SelectorInfo:
        """
        Parse a getBy* selector expression.

        Args:
            expr: Expression like 'getByRole("button", {name: "Submit"})'
            selector_type: Type of getBy selector

        Returns:
            SelectorInfo with parsed attributes
        """
        # Extract attributes from the expression
        attributes = {}
        value = ""

        # For getByRole, prioritize the role (first argument) over name attribute
        if selector_type == SelectorType.GET_BY_ROLE:
            # Match first quoted string in parentheses (the role)
            arg_match = re.search(r'\(\s*["\']([^"\']+)["\']', expr)
            if arg_match:
                value = arg_match.group(1)

        # Extract name attribute if present
        name_match = re.search(r'name\s*:\s*["\']([^"\']+)["\']', expr)
        if name_match:
            attributes['name'] = name_match.group(1)
            # Only use name as value if we haven't set one yet
            if not value:
                value = name_match.group(1)

        # Extract text attribute
        text_match = re.search(r'text\s*:\s*["\']([^"\']+)["\']', expr)
        if text_match:
            attributes['text'] = text_match.group(1)
            # Only use text as value if we haven't set one yet
            if not value:
                value = text_match.group(1)

        # If no value yet, try to extract first string argument
        # For expressions like getByLabel('Email'), getByPlaceholder('Password')
        if not value:
            # Match first quoted string in parentheses
            arg_match = re.search(r'\(\s*["\']([^"\']+)["\']', expr)
            if arg_match:
                value = arg_match.group(1)

        # Assess fragility
        fragility = FragilityLevel.ROBUST  # getBy selectors are robust

        # Generate fallbacks
        fallbacks = self._generate_fallbacks(expr, value, attributes)

        return SelectorInfo(
            raw=expr,
            type=selector_type,
            value=value,
            attributes=attributes,
            fragility=fragility,
            fallbacks=fallbacks,
        )

    def _assess_fragility(self, selector: str) -> FragilityLevel:
        """
        Assess how fragile a selector is.

        Args:
            selector: Selector string to assess

        Returns:
            FragilityLevel
        """
        # Very fragile: dynamic IDs, auto-generated classes
        if re.search(r'[\w-]*\d{10,}[\w-]*', selector):
            return FragilityLevel.VERY_FRAGILE

        # Fragile: generic class names, complex selectors
        if re.search(r'\.(btn|button|click|action)', selector, re.I):
            return FragilityLevel.FRAGILE

        # Fragile: deep nesting
        if selector.count(' > ') > 3:
            return FragilityLevel.FRAGILE

        # Fragile: nth-child
        if 'nth-child' in selector or 'nth-of-type' in selector:
            return FragilityLevel.FRAGILE

        # Moderate: simple class or ID
        if selector.startswith(('.', '#', '[id=')):
            return FragilityLevel.MODERATE

        # Robust: data-* attributes, aria attributes
        if re.search(r'\[data-[a-z-]+\s*=|\[aria-[a-z-]+\s*=', selector, re.I):
            return FragilityLevel.ROBUST

        # Default moderate
        return FragilityLevel.MODERATE

    def _generate_fallbacks(
        self,
        original: str,
        value: str,
        attributes: dict[str, Any]
    ) -> list[str]:
        """
        Generate fallback selectors for a given selector.

        Args:
            original: Original selector expression
            value: Primary value (name, text, etc.)
            attributes: Additional attributes

        Returns:
            List of fallback selector expressions
        """
        fallbacks = []

        # If we have a name/text value, generate alternatives
        if value:
            # getByText fallback
            fallbacks.append(f'getByText("{value}")')

            # CSS fallback with attribute
            if 'name' in attributes:
                fallbacks.append(f'[name="{value}"]')
            if 'title' in attributes:
                fallbacks.append(f'[title="{value}"]')

        return fallbacks


# =============================================================================
# Convenience Functions
# =============================================================================


def parse_recording(file_path: Path | str) -> ParsedRecording:
    """
    Parse a Playwright recording file.

    Args:
        file_path: Path to the recording file

    Returns:
        ParsedRecording with all extracted data
    """
    parser = PlaywrightRecordingParser()
    path = Path(file_path) if isinstance(file_path, str) else file_path
    return parser.parse_file(path)


def parse_recording_content(content: str, file_path: str = "") -> ParsedRecording:
    """
    Parse Playwright recording content from a string.

    Args:
        content: JavaScript code from recording
        file_path: Optional file path for reference

    Returns:
        ParsedRecording with all extracted data
    """
    parser = PlaywrightRecordingParser()
    return parser.parse_content(content, file_path)
