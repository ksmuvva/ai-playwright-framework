"""
Page Object Mapper for Step Definition Generation

Maps Gherkin steps to page object methods for more realistic step definitions.
"""

import ast
import re
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict


class PageObjectMethod:
    """Represents a method in a page object."""

    def __init__(
        self,
        name: str,
        class_name: str,
        params: list[str],
        docstring: Optional[str] = None,
        code: str = "",
    ):
        self.name = name
        self.class_name = class_name
        self.params = params
        self.docstring = docstring
        self.code = code

    @property
    def full_signature(self) -> str:
        """Get the full method signature."""
        params_str = ", ".join(self.params)
        return f"{self.class_name}.{self.name}({params_str})"


class PageObjectParser:
    """
    Parse page object files to extract available methods.

    Analyzes page object classes to understand what methods are available
    for generating step definitions.
    """

    def __init__(self, pages_dir: str = "pages"):
        """
        Initialize the parser.

        Args:
            pages_dir: Directory containing page object files
        """
        self.pages_dir = Path(pages_dir)
        self.methods: dict[str, list[PageObjectMethod]] = {}
        self._parse_all_pages()

    def _parse_all_pages(self) -> None:
        """Parse all Python files in the pages directory."""
        if not self.pages_dir.exists():
            return

        for py_file in self.pages_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            self._parse_page_file(py_file)

    def _parse_page_file(self, filepath: Path) -> None:
        """
        Parse a single page object file.

        Args:
            filepath: Path to the Python file
        """
        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                    # Skip BasePage
                    if class_name == "BasePage":
                        continue

                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Skip private methods
                            if item.name.startswith("_"):
                                continue

                            # Extract parameters
                            params = [arg.arg for arg in item.args.args[1:]]  # Skip 'self'

                            # Extract docstring
                            docstring = ast.get_docstring(item)

                            methods.append(PageObjectMethod(
                                name=item.name,
                                class_name=class_name,
                                params=params,
                                docstring=docstring,
                            ))

                    if methods:
                        self.methods[class_name] = methods

        except Exception as e:
            print(f"Warning: Failed to parse {filepath}: {e}")

    def get_methods_for_page(self, page_name: str) -> list[PageObjectMethod]:
        """
        Get all methods for a specific page.

        Args:
            page_name: Name of the page class (e.g., "LoginPage")

        Returns:
            List of methods
        """
        return self.methods.get(page_name, [])

    def find_method_by_action(
        self,
        action: str,
        element: str,
        page_name: Optional[str] = None,
    ) -> Optional[PageObjectMethod]:
        """
        Find a method that performs the given action on an element.

        Args:
            action: Action type (click, fill, enter, etc.)
            element: Element name (username, password, button, etc.)
            page_name: Optional page class name

        Returns:
            Matching method or None
        """
        # Search all pages or specific page
        pages_to_search = [page_name] if page_name else self.methods.keys()

        for page in pages_to_search:
            if page not in self.methods:
                continue

            for method in self.methods[page]:
                # Check if method name contains the action and element
                method_lower = method.name.lower()
                action_lower = action.lower()
                element_lower = element.lower().replace("_", "").replace(" ", "")

                # Match patterns:
                # - enter_username, fill_username, type_username
                # - click_login_button, click_submit
                # - navigate, goto
                if (
                    action_lower in method_lower
                    and element_lower in method_lower.replace("_", "")
                ):
                    return method

                # Check for specific action patterns
                if action_lower == "click" and "click" in method_lower:
                    if element_lower in method_lower:
                        return method

                if action_lower in ["fill", "enter", "type"] and "fill" in method_lower:
                    if element_lower in method_lower:
                        return method

        return None

    def get_all_methods(self) -> dict[str, list[PageObjectMethod]]:
        """Get all parsed methods."""
        return self.methods


class StepToPageObjectMapper:
    """
    Map Gherkin steps to page object methods.

    Analyzes step text and maps it to appropriate page object methods.
    """

    # Step patterns to action mappings
    ACTION_PATTERNS = {
        r"user clicks?\s+(?:the\s+)?(.+?)(?:\s+button|$)": "click",
        r"user presses?\s+(.+?)$": "click",
        r"user enters?\s+\"?([^\"]+)\"?\s+into\s+(.+?)(?:\s+field|$)": "fill",
        r"user types?\s+\"?([^\"]+)\"?\s+into\s+(.+?)(?:\s+field|$)": "fill",
        r"user navigates?\s+to\s+(.+?)$": "goto",
        r"user goes?\s+to\s+(.+?)$": "goto",
        r"user should see\s+(.+?)$": "expect",
        r"user waits?\s+for\s+(.+?)$": "wait",
        r"user checks?\s+(.+?)$": "check",
        r"user unchecks?\s+(.+?)$": "uncheck",
    }

    def __init__(self, pages_dir: str = "pages"):
        """
        Initialize the mapper.

        Args:
            pages_dir: Directory containing page objects
        """
        self.parser = PageObjectParser(pages_dir)
        self.pages_dir = Path(pages_dir)

    def map_step_to_method(
        self,
        step_text: str,
        page_name: Optional[str] = None,
    ) -> Optional[tuple[str, str, list[str]]]:
        """
        Map a step text to a page object method.

        Args:
            step_text: The Gherkin step text
            page_name: Optional page class name

        Returns:
            Tuple of (page_class, method_name, parameters) or None
        """
        # Try to match step pattern
        action, element, value = self._parse_step(step_text)

        if not action:
            return None

        # Try to find matching method
        method = self.parser.find_method_by_action(action, element, page_name)

        if method:
            # Extract parameters from step
            params = self._extract_params(step_text, method.params)
            return (method.class_name, method.name, params)

        # Try to infer method name
        inferred_method = self._infer_method_name(action, element)
        if page_name and page_name in self.parser.methods:
            return (page_name, inferred_method, [])

        return None

    def _parse_step(self, step_text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse step text to extract action, element, and value.

        Args:
            step_text: Step text

        Returns:
            Tuple of (action, element, value)
        """
        step_lower = step_text.lower()

        for pattern, action in self.ACTION_PATTERNS.items():
            match = re.search(pattern, step_lower)
            if match:
                if action == "fill":
                    value = match.group(1)
                    element = match.group(2)
                    return action, element, value
                else:
                    element = match.group(1)
                    return action, element, None

        return None, None, None

    def _extract_params(self, step_text: str, method_params: list[str]) -> list[str]:
        """
        Extract parameter values from step text.

        Args:
            step_text: Step text
            method_params: Method parameter names

        Returns:
            List of parameter values
        """
        params = []

        # Extract quoted strings
        for match in re.finditer(r'"([^"]*)"', step_text):
            params.append(match.group(1))

        return params[:len(method_params)] if method_params else params

    def _infer_method_name(self, action: str, element: str) -> str:
        """
        Infer a method name from action and element.

        Args:
            action: Action type
            element: Element name

        Returns:
            Inferred method name
        """
        element_clean = element.lower().replace(" ", "_").replace("-", "_")

        action_map = {
            "click": "click",
            "fill": "fill",
            "enter": "enter",
            "type": "type",
            "goto": "goto",
            "navigate": "goto",
            "expect": "expect",
            "wait": "wait_for",
            "check": "check",
            "uncheck": "uncheck",
        }

        action_prefix = action_map.get(action, action)

        return f"{action_prefix}_{element_clean}"

    def generate_step_code(
        self,
        step_text: str,
        page_name: Optional[str] = None,
        use_async: bool = True,
    ) -> Optional[str]:
        """
        Generate Python code for a step definition using page objects.

        Args:
            step_text: Gherkin step text
            page_name: Optional page class name
            use_async: Whether to use async/await

        Returns:
            Generated Python code or None
        """
        mapping = self.map_step_to_method(step_text, page_name)

        if not mapping:
            return None

        page_class, method_name, params = mapping

        # Generate code
        indent = "    "
        lines = []

        # Add docstring
        lines.append(f'{indent}"""Step: {step_text}"""')

        # Get or create page object
        if page_class:
            var_name = page_class[0].lower() + page_class[1:]
            lines.append(f"{indent}if not hasattr(context, '{var_name}'):")
            lines.append(f"{indent}    from pages.{page_class.lower()}s import {page_class}")
            lines.append(f"{indent}    context.{var_name} = {page_class}(context.page)")
            lines.append(f"{indent}")

        # Build method call
        params_str = ", ".join(f'"{p}"' if isinstance(p, str) else str(p) for p in params)
        method_call = f"await {var_name}.{method_name}({params_str})" if use_async else f"{var_name}.{method_name}({params_str})"

        lines.append(f"{indent}{method_call}")

        return "\n".join(lines)
