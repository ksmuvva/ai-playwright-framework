"""
E4.4 - Page Object Generation Skill.

This skill provides page object generation functionality:
- Page object model generation
- Element property generation
- Method generation from actions
- Context-aware code generation
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class GenerationFormat(str, Enum):
    """Code generation formats."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"


@dataclass
class PageObjectElement:
    """
    An element in a page object.

    Attributes:
        element_id: Unique element identifier
        name: Element property name
        selector: Element selector
        selector_type: Selector type
        description: Element description
        actions: List of actions available
        source_context: Context from source element
    """

    element_id: str = field(default_factory=lambda: f"po_elem_{uuid.uuid4().hex[:8]}")
    name: str = ""
    selector: str = ""
    selector_type: str = ""
    description: str = ""
    actions: list[str] = field(default_factory=list)
    source_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "element_id": self.element_id,
            "name": self.name,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "description": self.description,
            "actions": self.actions,
            "source_context": self.source_context,
        }


@dataclass
class PageObjectMethod:
    """
    A method in a page object.

    Attributes:
        method_id: Unique method identifier
        name: Method name
        parameters: Method parameters
        description: Method description
        action_sequence: Sequence of actions
        return_type: Return type
        source_context: Context from source actions
    """

    method_id: str = field(default_factory=lambda: f"po_method_{uuid.uuid4().hex[:8]}")
    name: str = ""
    parameters: list[dict[str, str]] = field(default_factory=list)
    description: str = ""
    action_sequence: list[str] = field(default_factory=list)
    return_type: str = "None"
    source_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "method_id": self.method_id,
            "name": self.name,
            "parameters": self.parameters,
            "description": self.description,
            "action_sequence": self.action_sequence,
            "return_type": self.return_type,
            "source_context": self.source_context,
        }


@dataclass
class GeneratedPageObject:
    """
    A generated page object.

    Attributes:
        page_object_id: Unique page object identifier
        class_name: Page object class name
        file_name: Suggested file name
        elements: List of elements
        methods: List of methods
        url_pattern: URL pattern for page
        description: Page object description
        generation_context: Context at time of generation
        generated_at: When page object was generated
    """

    page_object_id: str = field(default_factory=lambda: f"po_{uuid.uuid4().hex[:8]}")
    class_name: str = ""
    file_name: str = ""
    elements: list[PageObjectElement] = field(default_factory=list)
    methods: list[PageObjectMethod] = field(default_factory=list)
    url_pattern: str = ""
    description: str = ""
    generation_context: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "page_object_id": self.page_object_id,
            "class_name": self.class_name,
            "file_name": self.file_name,
            "elements": [e.to_dict() for e in self.elements],
            "methods": [m.to_dict() for m in self.methods],
            "url_pattern": self.url_pattern,
            "description": self.description,
            "generation_context": self.generation_context,
            "generated_at": self.generated_at,
        }

    def to_python_code(self) -> str:
        """Generate Python Page Object code."""
        # Generate imports
        lines = [
            '"""',
            f'{self.description or f"Page Object: {self.class_name}"}',
            f'\nAuto-generated from Playwright recordings.',
            '"""',
            '',
            'from typing import Any',
            'from playwright.sync_api import Page, Locator',
            '',
            '',
            f'class {self.class_name}:',
            f'    """{self.description or f"Page object for {self.class_name}"}."""',
            '',
            '    def __init__(self, page: Page) -> None:',
            f'        """Initialize the {self.class_name} page object."""',
            '        self.page = page',
        ]

        # Generate element properties
        for elem in self.elements:
            if elem.description:
                lines.append('')
                lines.append(f'    @property')
                lines.append(f'    def {elem.name}(self) -> Locator:')
                lines.append(f'        """{elem.description}"""')
                lines.append(f'        return self.page.{elem.selector_type}("{elem.selector}")')
            else:
                lines.append('')
                lines.append(f'    @property')
                lines.append(f'    def {elem.name}(self) -> Locator:')
                lines.append(f'        return self.page.{elem.selector_type}("{elem.selector}")')

        # Generate methods
        for method in self.methods:
            params = ", ".join([f"{p['name']}: {p['type']}" for p in method.parameters])
            lines.append('')
            lines.append(f'    def {method.name}(self{", " + params if params else ""}) -> {method.return_type}:')
            if method.description:
                lines.append(f'        """{method.description}"""')

            # Simple implementation
            if method.action_sequence:
                for action in method.action_sequence[:3]:  # First few actions
                    lines.append(f'        # {action}')
            lines.append(f'        pass')

        return "\n".join(lines)


@dataclass
class GenerationContext:
    """
    Context for page object generation.

    Attributes:
        generation_id: Unique generation identifier
        workflow_id: Associated workflow ID
        components_used: Components used for generation
        page_objects_generated: Number of page objects generated
        total_elements: Total elements across all page objects
        total_methods: Total methods across all page objects
        output_dir: Output directory for generated files
        generation_started: When generation started
        generation_completed: When generation completed
        context_preserved: Whether context was preserved
    """

    generation_id: str = field(default_factory=lambda: f"gen_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    components_used: list[str] = field(default_factory=list)
    page_objects_generated: int = 0
    total_elements: int = 0
    total_methods: int = 0
    output_dir: str = ""
    generation_started: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_completed: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generation_id": self.generation_id,
            "workflow_id": self.workflow_id,
            "components_used": self.components_used,
            "page_objects_generated": self.page_objects_generated,
            "total_elements": self.total_elements,
            "total_methods": self.total_methods,
            "output_dir": self.output_dir,
            "generation_started": self.generation_started,
            "generation_completed": self.generation_completed,
            "context_preserved": self.context_preserved,
        }


class PageObjectGenerationAgent(BaseAgent):
    """
    Page Object Generation Agent.

    This agent provides:
    1. Page object model generation
    2. Element property generation
    3. Method generation from actions
    4. Context-aware code generation
    """

    name = "e4_4_page_object_generation"
    version = "1.0.0"
    description = "E4.4 - Page Object Generation"

    def __init__(self, **kwargs) -> None:
        """Initialize the page object generation agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E4.4 - Page Object Generation agent for the Playwright test automation framework. You help users with e4.4 - page object generation tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._generation_history: list[GenerationContext] = []
        self._page_object_registry: dict[str, GeneratedPageObject] = {}

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
        Execute page object generation task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the generation operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "generate_page_objects":
            return await self._generate_page_objects(context, execution_context)
        elif task_type == "generate_from_component":
            return await self._generate_from_component(context, execution_context)
        elif task_type == "generate_elements":
            return await self._generate_elements(context, execution_context)
        elif task_type == "generate_methods":
            return await self._generate_methods(context, execution_context)
        elif task_type == "save_page_objects":
            return await self._save_page_objects(context, execution_context)
        elif task_type == "get_generation_context":
            return await self._get_generation_context(context, execution_context)
        elif task_type == "get_page_object":
            return await self._get_page_object(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _generate_page_objects(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate page objects from components."""
        components = context.get("components", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        output_dir = context.get("output_dir", "")

        if not components:
            return "Error: components list is required"

        # Create generation context
        generation_context = GenerationContext(
            workflow_id=workflow_id,
            output_dir=output_dir,
        )

        page_objects = []

        for component in components:
            component_id = component.get("component_id", "")
            component_name = component.get("component_name", "Component")
            elements = component.get("elements", [])

            # Generate page object
            page_object = GeneratedPageObject(
                class_name=self._to_class_name(component_name),
                file_name=f"{self._to_snake_case(component_name)}.py",
                url_pattern=component.get("url_pattern", ""),
                description=f"Page object for {component_name}",
                generation_context={
                    "workflow_id": workflow_id,
                    "component_id": component_id,
                    "element_count": len(elements),
                },
            )

            # Generate elements
            for elem_data in elements:
                element = PageObjectElement(
                    name=self._to_snake_case(elem_data.get("role", elem_data.get("element_type", "element"))),
                    selector=elem_data.get("selector", ""),
                    selector_type=elem_data.get("selector_type", "locator"),
                    description=f"Element from {component_name}",
                    actions=elem_data.get("actions", []),
                    source_context={
                        "component_id": component_id,
                        "element_type": elem_data.get("element_type", ""),
                    },
                )
                page_object.elements.append(element)

            page_objects.append(page_object)
            self._page_object_registry[page_object.page_object_id] = page_object
            generation_context.components_used.append(component_id)

        generation_context.page_objects_generated = len(page_objects)
        generation_context.total_elements = sum(len(po.elements) for po in page_objects)
        generation_context.generation_completed = datetime.now().isoformat()
        self._generation_history.append(generation_context)

        return f"Generated {len(page_objects)} page object(s) with {generation_context.total_elements} element(s)"

    async def _generate_from_component(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate page object from single component."""
        component = context.get("component")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not component:
            return "Error: component is required"

        component_name = component.get("component_name", "Component")
        elements = component.get("elements", [])

        page_object = GeneratedPageObject(
            class_name=self._to_class_name(component_name),
            file_name=f"{self._to_snake_case(component_name)}.py",
            description=f"Page object for {component_name}",
            generation_context={
                "workflow_id": workflow_id,
                "component_id": component.get("component_id", ""),
            },
        )

        for elem_data in elements:
            element = PageObjectElement(
                name=self._to_snake_case(elem_data.get("role", "element")),
                selector=elem_data.get("selector", ""),
                selector_type="locator",
                source_context={"from_component": component.get("component_id", "")},
            )
            page_object.elements.append(element)

        self._page_object_registry[page_object.page_object_id] = page_object

        return f"Generated page object: {page_object.class_name}"

    async def _generate_elements(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate element properties."""
        elements_data = context.get("elements", [])

        if not elements_data:
            return "Error: elements list is required"

        page_object_id = context.get("page_object_id")
        if not page_object_id:
            return "Error: page_object_id is required"

        page_object = self._page_object_registry.get(page_object_id)
        if not page_object:
            return f"Error: Page object '{page_object_id}' not found"

        for elem_data in elements_data:
            element = PageObjectElement(
                name=self._to_snake_case(elem_data.get("name", "element")),
                selector=elem_data.get("selector", ""),
                selector_type=elem_data.get("selector_type", "locator"),
                description=elem_data.get("description", ""),
                actions=elem_data.get("actions", []),
                source_context=elem_data.get("context", {}),
            )
            page_object.elements.append(element)

        return f"Added {len(elements_data)} element(s) to {page_object.class_name}"

    async def _generate_methods(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate methods from action sequences."""
        action_sequences = context.get("action_sequences", [])

        if not action_sequences:
            return "Error: action_sequences list is required"

        page_object_id = context.get("page_object_id")
        if not page_object_id:
            return "Error: page_object_id is required"

        page_object = self._page_object_registry.get(page_object_id)
        if not page_object:
            return f"Error: Page object '{page_object_id}' not found"

        for seq_data in action_sequences:
            actions = seq_data.get("actions", [])
            method = PageObjectMethod(
                name=self._to_method_name(seq_data.get("name", "action")),
                description=seq_data.get("description", f"Performs {len(actions)} action(s)"),
                action_sequence=actions,
                source_context={"sequence_id": seq_data.get("sequence_id", "")},
            )
            page_object.methods.append(method)

        return f"Added {len(action_sequences)} method(s) to {page_object.class_name}"

    async def _save_page_objects(self, context: dict[str, Any], execution_context: Any) -> str:
        """Save page objects to files."""
        output_dir = context.get("output_dir")
        page_object_ids = context.get("page_object_ids", [])

        if not output_dir:
            return "Error: output_dir is required"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files_created = []

        # Save specific or all
        if page_object_ids:
            page_objects = [
                self._page_object_registry[pid]
                for pid in page_object_ids
                if pid in self._page_object_registry
            ]
        else:
            page_objects = list(self._page_object_registry.values())

        for page_object in page_objects:
            file_path = output_path / page_object.file_name
            code = page_object.to_python_code()
            file_path.write_text(code, encoding="utf-8")
            files_created.append(str(file_path))

        return f"Saved {len(files_created)} page object file(s)"

    async def _get_generation_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get generation context."""
        generation_id = context.get("generation_id")

        if not generation_id:
            return "Error: generation_id is required"

        for generation_context in self._generation_history:
            if generation_context.generation_id == generation_id:
                return (
                    f"Generation '{generation_id}': "
                    f"{generation_context.page_objects_generated} page objects, "
                    f"{generation_context.total_elements} elements"
                )

        return f"Error: Generation context '{generation_id}' not found"

    async def _get_page_object(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get page object by ID."""
        page_object_id = context.get("page_object_id")

        if not page_object_id:
            return "Error: page_object_id is required"

        page_object = self._page_object_registry.get(page_object_id)
        if page_object:
            return f"Page object '{page_object.class_name}': {len(page_object.elements)} elements, {len(page_object.methods)} methods"

        return f"Error: Page object '{page_object_id}' not found"

    def _to_class_name(self, name: str) -> str:
        """Convert name to class name."""
        return "".join(word.capitalize() for word in name.replace("-", "_").split("_")) + "Page"

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake case."""
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        name = name.replace("-", "_").replace(" ", "_")
        return re.sub(r'_+', '_', name).strip('_')

    def _to_method_name(self, name: str) -> str:
        """Convert name to method name."""
        return self._to_snake_case(name)

    def get_generation_history(self) -> list[GenerationContext]:
        """Get generation history."""
        return self._generation_history.copy()

    def get_page_object_registry(self) -> dict[str, GeneratedPageObject]:
        """Get page object registry."""
        return self._page_object_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

