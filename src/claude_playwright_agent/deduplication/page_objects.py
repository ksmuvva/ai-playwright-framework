"""
Page Object Model generation from deduplicated elements.

This module provides:
- Automatic page object class generation
- Element method generation
- File output management
- Integration with state persistence
"""

import re
from pathlib import Path
from textwrap import dedent, indent
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.deduplication.logic import (
    ElementGroup,
    SelectorData,
)


# =============================================================================
# Generation Configuration
# =============================================================================


class GenerationConfig(BaseModel):
    """Configuration for page object generation."""

    base_class: str = Field(default="Page", description="Base page object class")
    use_async: bool = Field(default=True, description="Use async methods")
    include_type_hints: bool = Field(default=True, description="Include type hints")
    include_docstrings: bool = Field(default=True, description="Include docstrings")
    generate_actions: bool = Field(default=True, description="Generate action methods")
    indent_size: int = Field(default=4, description="Indentation size")
    locators_module: str = Field(default="playwright.async_api", description="Locators module")

    class Config:
        """Pydantic config."""
        use_enum_values = True


# =============================================================================
# Page Object Model
# =============================================================================


class PageObjectModel(BaseModel):
    """Model for a generated page object."""

    page_object_id: str = Field(..., description="Unique page object ID")
    class_name: str = Field(..., description="Generated class name")
    file_path: str = Field(..., description="Generated file path")
    url_pattern: str = Field(default="", description="URL pattern for this page")

    # Elements
    elements: dict[str, SelectorData] = Field(
        default_factory=dict,
        description="Page elements by name"
    )

    # Methods
    methods: list[str] = Field(
        default_factory=list,
        description="Generated method names"
    )

    # Metadata
    imports: list[str] = Field(
        default_factory=list,
        description="Required imports"
    )
    base_classes: list[str] = Field(
        default_factory=list,
        description="Base classes to inherit from"
    )


# =============================================================================
# Page Object Generator
# =============================================================================


class PageObjectGenerator:
    """
    Generate Page Object classes from deduplicated elements.

    Features:
    - Automatic class name generation
    - Element locator methods
    - Action methods (click, fill, etc.)
    - Proper Python formatting
    - File output
    """

    def __init__(self, config: GenerationConfig | None = None) -> None:
        """
        Initialize the generator.

        Args:
            config: Generation configuration
        """
        self.config = config or GenerationConfig()

    # =========================================================================
    # Class Generation
    # =========================================================================

    def generate_class(
        self,
        page_url: str,
        groups: list[ElementGroup],
        output_dir: Path,
    ) -> PageObjectModel:
        """
        Generate a page object class for a page.

        Args:
            page_url: URL of the page
            groups: Element groups for this page
            output_dir: Directory to write to

        Returns:
            PageObjectModel with generation info
        """
        # Generate class name
        class_name = self._generate_class_name(page_url)
        file_name = self._snake_case(class_name) + ".py"
        file_path = str(output_dir / file_name)

        # Build content
        content = self._generate_class_content(
            class_name,
            page_url,
            groups,
        )

        # Write file
        output_dir.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text(content, encoding="utf-8")

        # Extract metadata
        elements = {}
        methods = []

        for group in groups:
            if group.name_suggestion:
                elements[group.name_suggestion] = group.canonical_selector

            # Determine methods based on actions
            actions = set(ctx.action_type for ctx in group.contexts)
            for action in actions:
                if group.name_suggestion:
                    methods.append(f"{action}_{group.name_suggestion}")

        return PageObjectModel(
            page_object_id=f"po_{hash(page_url)}",
            class_name=class_name,
            file_path=file_path,
            url_pattern=page_url,
            elements=elements,
            methods=methods,
        )

    def _generate_class_content(
        self,
        class_name: str,
        page_url: str,
        groups: list[ElementGroup],
    ) -> str:
        """Generate the class content."""
        lines = []

        # Add docstring
        if self.config.include_docstrings:
            lines.append(f'"""')
            lines.append(f'Page object for {page_url}')
            lines.append(f'')
            lines.append(f'Auto-generated from deduplicated elements.')
            lines.append(f'"""')
            lines.append(f'')

        # Add imports
        imports = self._generate_imports(groups)
        if imports:
            lines.extend(imports)
            lines.append('')

        # Class definition
        base = self.config.base_class
        lines.append(f'class {class_name}({base}):')
        lines.append('')

        # Class docstring
        if self.config.include_docstrings:
            lines.append(f'    """')
            lines.append(f'    Page object for {page_url}.')
            lines.append(f'    ')
            lines.append(f'    Attributes:')
            for group in groups:
                if group.name_suggestion:
                    lines.append(f'        {group.name_suggestion}: {group.name_suggestion} element')
            lines.append(f'    """')
            lines.append('')

        # Init method
        lines.append(self._generate_init_method(groups))

        # Element locators
        for group in groups:
            if group.name_suggestion:
                locator_method = self._generate_locator_method(group)
                if locator_method:
                    lines.append('')
                    lines.append(locator_method)

        # Action methods
        if self.config.generate_actions:
            for group in groups:
                if group.name_suggestion:
                    for action_method in self._generate_action_methods(group):
                        lines.append('')
                        lines.append(action_method)

        return '\n'.join(lines)

    def _generate_class_name(self, page_url: str) -> str:
        """Generate class name from page URL."""
        # Extract path from URL
        from urllib.parse import urlparse

        parsed = urlparse(page_url)
        path = parsed.path.strip('/')

        if not path:
            # Use hostname
            hostname = parsed.hostname or "page"
            parts = hostname.split('.')
            parts = [p.capitalize() for p in parts if p]
            return ''.join(parts) + 'Page'

        # Convert path to class name
        parts = path.split('/')
        parts = [p.capitalize() for p in parts if p]

        # Remove common prefixes
        if parts and parts[0] in ['Api', 'V1', 'V2']:
            parts = parts[1:]

        class_name = ''.join(parts) + 'Page'

        # Ensure it starts with a letter
        if not class_name[0].isalpha():
            class_name = 'Page' + class_name

        return class_name

    def _snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    # =========================================================================
    # Method Generation
    # =========================================================================

    def _generate_init_method(self, groups: list[ElementGroup]) -> str:
        """Generate the __init__ method."""
        lines = []

        async_prefix = 'async ' if self.config.use_async else ''
        type_hint = ': Page' if self.config.include_type_hints else ''

        lines.append(f'    def __init__(self, page{type_hint}) -> None:')
        lines.append(f'        """')
        lines.append(f'        Initialize the page object.')

        if self.config.include_docstrings and groups:
            lines.append(f'')
            for group in groups:
                if group.name_suggestion:
                    lines.append(f'        Args:')
                    break

        lines.append(f'            page: Playwright page object')
        lines.append(f'        """')
        lines.append(f'        self._page = page')
        lines.append(f'        self._url = "{groups[0].pages.pop() if groups and groups[0].pages else ""}"')

        return '\n'.join(lines)

    def _generate_locator_method(self, group: ElementGroup) -> str:
        """Generate a locator method for an element."""
        name = group.name_suggestion or 'element'
        selector = group.canonical_selector

        lines = []

        # Docstring
        if self.config.include_docstrings:
            lines.append(f'    @property')
            lines.append(f'    def {name}(self) -> Locator:')
            lines.append(f'        """')
            lines.append(f'        Get the {name} element locator.')
            lines.append(f'')
            lines.append(f'        Selector: {selector.raw}')
            lines.append(f'        Type: {selector.type}')
            lines.append(f'        Fragility: {selector.fragility_score:.2f}')
            lines.append(f'        """')

            # Generate locator code
            lines.append(f'        return self._page.{self._get_locator_code(selector)}')

        else:
            lines.append(f'    @property')
            lines.append(f'    def {name}(self) -> Locator:')
            lines.append(f'        return self._page.{self._get_locator_code(selector)}')

        return '\n'.join(lines)

    def _generate_action_methods(self, group: ElementGroup) -> list[str]:
        """Generate action methods for an element group."""
        methods = []

        # Get unique actions
        actions = set(ctx.action_type for ctx in group.contexts)
        element_name = group.name_suggestion or 'element'

        for action in actions:
            method_lines = []

            if self.config.include_type_hints:
                return_type = ' -> None' if action != 'click' else ' -> None'
            else:
                return_type = ''

            # Method definition
            async_prefix = 'async ' if self.config.use_async else ''
            method_name = f'{action}_{element_name}'

            # Docstring
            if self.config.include_docstrings:
                method_lines.append(f'    {async_prefix}def {method_name}(self{return_type}):')
                method_lines.append(f'        """')
                method_lines.append(f'        Perform {action} action on {element_name}.')
                method_lines.append(f'        """')

            # Method body
            if action == 'click':
                method_lines.append(f'        await self.{element_name}.click()')
            elif action == 'fill':
                method_lines.append(f'        async def _inner(value: str) -> None:')
                method_lines.append(f'            await self.{element_name}.fill(value)')
                method_lines.append(f'        return _inner')
            elif action == 'type':
                method_lines.append(f'        async def _inner(value: str) -> None:')
                method_lines.append(f'            await self.{element_name}.type(value)')
                method_lines.append(f'        return _inner')
            elif action == 'check':
                method_lines.append(f'        await self.{element_name}.check()')
            elif action == 'uncheck':
                method_lines.append(f'        await self.{element_name}.uncheck()')
            elif action == 'select':
                method_lines.append(f'        async def _inner(value: str) -> None:')
                method_lines.append(f'            await self.{element_name}.select_option(value)')
                method_lines.append(f'        return _inner')
            elif action == 'hover':
                method_lines.append(f'        await self.{element_name}.hover()')
            elif action == 'press':
                method_lines.append(f'        async def _inner(key: str) -> None:')
                method_lines.append(f'            await self.{element_name}.press(key)')
                method_lines.append(f'        return _inner')

            if method_lines:
                methods.append('\n'.join(method_lines))

        return methods

    def _get_locator_code(self, selector: SelectorData) -> str:
        """Generate Playwright locator code from selector data."""
        selector_type = selector.type
        value = selector.value
        attrs = selector.attributes

        if selector_type == 'getByRole':
            role = attrs.get('name', value).lower()
            return f'get_by_role("{role}")'

        elif selector_type == 'getByLabel':
            return f'get_by_label("{value}")'

        elif selector_type == 'getByText':
            return f'get_by_text("{value}")'

        elif selector_type == 'getByPlaceholder':
            return f'get_by_placeholder("{value}")'

        elif selector_type == 'getByTestId':
            return f'get_by_test_id("{value}")'

        elif selector_type == 'getByTitle':
            return f'get_by_title("{value}")'

        elif selector_type == 'locator':
            return f'locator("{value}")'

        elif selector_type == 'css':
            return f'locator("{value}")'

        elif selector_type == 'xpath':
            return f'locator("xpath={value}")'

        else:
            return f'locator("{value}")'

    def _generate_imports(self, groups: list[ElementGroup]) -> list[str]:
        """Generate import statements."""
        imports = []

        # Base imports
        imports.append('from playwright.async_api import Page, Locator')

        # Check if we need specific imports
        for group in groups:
            for context in group.contexts:
                if context.action_type in ['select']:
                    # No special imports needed
                    pass

        return imports

    # =========================================================================
    # Batch Generation
    # =========================================================================

    def generate_all(
        self,
        page_groups: dict[str, list[ElementGroup]],
        output_dir: Path,
    ) -> list[PageObjectModel]:
        """
        Generate page objects for all pages.

        Args:
            page_groups: Dictionary mapping page URLs to element groups
            output_dir: Base output directory

        Returns:
            List of generated page object models
        """
        results = []

        for page_url, groups in page_groups.items():
            try:
                model = self.generate_class(page_url, groups, output_dir)
                results.append(model)
            except Exception as e:
                # Continue with other pages on error
                pass

        return results

    # =========================================================================
    # State Integration
    # =========================================================================

    def export_to_state(self, models: list[PageObjectModel]) -> dict[str, Any]:
        """
        Export generated models to state format.

        Args:
            models: Generated page object models

        Returns:
            Dictionary suitable for state.json
        """
        page_objects = {}

        for model in models:
            page_objects[model.page_object_id] = {
                "class_name": model.class_name,
                "file_path": model.file_path,
                "url_pattern": model.url_pattern,
                "elements": {
                    name: {
                        "selector": sel.raw,
                        "selector_type": sel.type,
                        "fragility_score": sel.fragility_score,
                    }
                    for name, sel in model.elements.items()
                },
                "methods": model.methods,
            }

        return page_objects

    def load_from_state(
        self,
        state_data: dict[str, Any],
    ) -> list[PageObjectModel]:
        """
        Load page object models from state.

        Args:
            state_data: State data from state.json

        Returns:
            List of page object models
        """
        models = []

        page_objects = state_data.get("page_objects", {})

        for po_id, po_data in page_objects.items():
            # Reconstruct elements
            elements = {}
            for name, sel_data in po_data.get("elements", {}).items():
                elements[name] = SelectorData(
                    raw=sel_data.get("selector", ""),
                    type=sel_data.get("selector_type", ""),
                    value="",
                    attributes={},
                )

            model = PageObjectModel(
                page_object_id=po_id,
                class_name=po_data.get("class_name", ""),
                file_path=po_data.get("file_path", ""),
                url_pattern=po_data.get("url_pattern", ""),
                elements=elements,
                methods=po_data.get("methods", []),
            )

            models.append(model)

        return models
