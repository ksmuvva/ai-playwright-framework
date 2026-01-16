"""
E5.3 - Step Definition Creator Skill.

This skill provides step definition creation functionality:
- Step definition generation
- Code template creation
- Parameter extraction
- Implementation context tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from pathlib import Path

from claude_playwright_agent.agents.base import BaseAgent


class StepFramework(str, Enum):
    """BDD frameworks."""

    BEHAVE = "behave"
    PYTEST_BDD = "pytest-bdd"
    RADISH = "radish"


class ImplementationStatus(str, Enum):
    """Step definition implementation status."""

    PENDING = "pending"
    IMPLEMENTED = "implemented"
    TODO = "todo"
    SKIPPED = "skipped"


@dataclass
class StepParameter:
    """
    A parameter extracted from a step.

    Attributes:
        param_id: Unique parameter identifier
        name: Parameter name
        param_type: Parameter type
        default_value: Default value
        pattern: Regex pattern for extraction
        description: Parameter description
        source_context: Context from source step
    """

    param_id: str = field(default_factory=lambda: f"param_{uuid.uuid4().hex[:8]}")
    name: str = ""
    param_type: str = "str"
    default_value: str = ""
    pattern: str = ""
    description: str = ""
    source_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "param_id": self.param_id,
            "name": self.name,
            "param_type": self.param_type,
            "default_value": self.default_value,
            "pattern": self.pattern,
            "description": self.description,
            "source_context": self.source_context,
        }


@dataclass
class StepDefinition:
    """
    A step definition with implementation.

    Attributes:
        definition_id: Unique definition identifier
        step_text: Original step text
        decorator: Step decorator (@given, @when, @then)
        function_name: Generated function name
        parameters: List of parameters
        implementation_code: Generated implementation code
        status: Implementation status
        definition_context: Context at creation time
        source_step: Source Gherkin step
        created_at: When definition was created
    """

    definition_id: str = field(default_factory=lambda: f"def_{uuid.uuid4().hex[:8]}")
    step_text: str = ""
    decorator: str = ""
    function_name: str = ""
    parameters: list[StepParameter] = field(default_factory=list)
    implementation_code: str = ""
    status: ImplementationStatus = ImplementationStatus.PENDING
    definition_context: dict[str, Any] = field(default_factory=dict)
    source_step: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "definition_id": self.definition_id,
            "step_text": self.step_text,
            "decorator": self.decorator,
            "function_name": self.function_name,
            "parameters": [p.to_dict() for p in self.parameters],
            "implementation_code": self.implementation_code,
            "status": self.status.value,
            "definition_context": self.definition_context,
            "source_step": self.source_step,
            "created_at": self.created_at,
        }

    def to_python_code(self, framework: StepFramework = StepFramework.BEHAVE) -> str:
        """Generate Python step definition code."""
        lines = []

        if framework == StepFramework.BEHAVE:
            lines.append(f'@{self.decorator}(\'{self.step_text}\')')
        elif framework == StepFramework.PYTEST_BDD:
            lines.append(f'@{self.decorator}(\'{self.step_text}\')')

        # Function signature
        params = ["context"]
        params.extend([f"{p.name}: {p.param_type}" for p in self.parameters])
        params_str = ", ".join(params)
        lines.append(f'def {self.function_name}({params_str}) -> None:')

        # Docstring
        lines.append(f'    """{self.step_text}"""')

        # Implementation
        if self.implementation_code:
            lines.append(self.implementation_code)
        else:
            lines.append("    # TODO: Implement step logic")
            lines.append("    pass")

        return "\n".join(lines)


@dataclass
class DefinitionFile:
    """
    A file containing step definitions.

    Attributes:
        file_id: Unique file identifier
        file_name: Suggested file name
        file_path: Full file path
        definitions: List of step definitions
        imports: Required imports
        framework: BDD framework
        file_context: Context at file creation
        created_at: When file was created
    """

    file_id: str = field(default_factory=lambda: f"file_{uuid.uuid4().hex[:8]}")
    file_name: str = ""
    file_path: str = ""
    definitions: list[StepDefinition] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    framework: StepFramework = StepFramework.BEHAVE
    file_context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "definitions": [d.to_dict() for d in self.definitions],
            "imports": self.imports,
            "framework": self.framework.value,
            "file_context": self.file_context,
            "created_at": self.created_at,
        }

    def to_python_code(self) -> str:
        """Generate complete Python file content."""
        lines = [
            '"""',
            f'Step definitions for {self.file_name}',
            f'Auto-generated with {self.framework.value}',
            '"""',
            '',
        ]

        # Add imports
        if self.imports:
            lines.extend(self.imports)
        else:
            lines.extend([
                'from behave import given, when, then',
                'from playwright.sync_api import Page, expect',
            ])

        lines.append("")

        # Add definitions
        for definition in self.definitions:
            lines.append(definition.to_python_code(self.framework))
            lines.append("")

        return "\n".join(lines)


@dataclass
class CreationContext:
    """
    Context for step definition creation.

    Attributes:
        creation_id: Unique creation identifier
        workflow_id: Associated workflow ID
        feature_id: Source feature ID
        definitions_created: Number of definitions created
        files_created: Number of files created
        implementation_status: Breakdown by status
        creation_started: When creation started
        creation_completed: When creation completed
        context_preserved: Whether context was preserved
    """

    creation_id: str = field(default_factory=lambda: f"create_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    feature_id: str = ""
    definitions_created: int = 0
    files_created: int = 0
    implementation_status: dict[str, int] = field(default_factory=dict)
    creation_started: str = field(default_factory=lambda: datetime.now().isoformat())
    creation_completed: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "creation_id": self.creation_id,
            "workflow_id": self.workflow_id,
            "feature_id": self.feature_id,
            "definitions_created": self.definitions_created,
            "files_created": self.files_created,
            "implementation_status": self.implementation_status,
            "creation_started": self.creation_started,
            "creation_completed": self.creation_completed,
            "context_preserved": self.context_preserved,
        }


class StepDefinitionCreatorAgent(BaseAgent):
    """
    Step Definition Creator Agent.

    This agent provides:
    1. Step definition generation
    2. Code template creation
    3. Parameter extraction
    4. Implementation context tracking
    """

    name = "e5_3_step_definitions"
    version = "1.0.0"
    description = "E5.3 - Step Definition Creator"

    def __init__(self, **kwargs) -> None:
        """Initialize the step definition creator agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E5.3 - Step Definition Creator agent for the Playwright test automation framework. You help users with e5.3 - step definition creator tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._creation_history: list[CreationContext] = []
        self._definition_registry: dict[str, StepDefinition] = {}
        self._file_registry: dict[str, DefinitionFile] = {}

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
        Execute step definition creation task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the creation operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "create_definition":
            return await self._create_definition(context, execution_context)
        elif task_type == "create_definitions_from_steps":
            return await self._create_definitions_from_steps(context, execution_context)
        elif task_type == "extract_parameters":
            return await self._extract_parameters(context, execution_context)
        elif task_type == "generate_implementation":
            return await self._generate_implementation(context, execution_context)
        elif task_type == "create_file":
            return await self._create_file(context, execution_context)
        elif task_type == "save_file":
            return await self._save_file(context, execution_context)
        elif task_type == "get_creation_context":
            return await self._get_creation_context(context, execution_context)
        elif task_type == "get_definition":
            return await self._get_definition(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _create_definition(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a single step definition."""
        step = context.get("step")
        framework = context.get("framework", StepFramework.BEHAVE)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not step:
            return "Error: step is required"

        step_text = step.get("text", "")
        keyword = step.get("keyword", "when")

        # Extract parameters
        parameters = self._extract_params_from_step(step_text)

        # Generate function name
        function_name = self._generate_function_name(step_text)

        # Create definition
        definition = StepDefinition(
            step_text=step_text,
            decorator=keyword.lower(),
            function_name=function_name,
            parameters=parameters,
            definition_context={
                "workflow_id": workflow_id,
                "framework": framework if isinstance(framework, str) else framework.value,
            },
            source_step=step,
        )

        self._definition_registry[definition.definition_id] = definition

        return f"Created definition: {definition.function_name}({len(definition.parameters)} param(s))"

    async def _create_definitions_from_steps(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create definitions from multiple steps."""
        steps = context.get("steps", [])
        framework = context.get("framework", StepFramework.BEHAVE)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        feature_id = context.get("feature_id", "")

        if not steps:
            return "Error: steps list is required"

        # Create creation context
        creation_context = CreationContext(
            workflow_id=workflow_id,
            feature_id=feature_id,
        )

        for step in steps:
            step_text = step.get("text", "")
            keyword = step.get("keyword", "when")

            parameters = self._extract_params_from_step(step_text)
            function_name = self._generate_function_name(step_text)

            definition = StepDefinition(
                step_text=step_text,
                decorator=keyword.lower(),
                function_name=function_name,
                parameters=parameters,
                definition_context={
                    "workflow_id": workflow_id,
                    "creation_id": creation_context.creation_id,
                    "framework": framework if isinstance(framework, str) else framework.value,
                },
                source_step=step,
            )

            self._definition_registry[definition.definition_id] = definition
            creation_context.definitions_created += 1

            # Track status
            status = definition.status.value
            creation_context.implementation_status[status] = creation_context.implementation_status.get(status, 0) + 1

        creation_context.creation_completed = datetime.now().isoformat()
        self._creation_history.append(creation_context)

        return f"Created {creation_context.definitions_created} definition(s)"

    async def _extract_parameters(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract parameters from step text."""
        step_text = context.get("step_text", "")

        if not step_text:
            return "Error: step_text is required"

        parameters = self._extract_params_from_step(step_text)

        return f"Extracted {len(parameters)} parameter(s): {[p.name for p in parameters]}"

    async def _generate_implementation(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate implementation code for definition."""
        definition_id = context.get("definition_id")

        if not definition_id:
            return "Error: definition_id is required"

        definition = self._definition_registry.get(definition_id)
        if not definition:
            return f"Error: Definition '{definition_id}' not found"

        # Generate implementation
        implementation = self._generate_impl_code(definition)
        definition.implementation_code = implementation
        definition.status = ImplementationStatus.TODO

        return f"Generated implementation for: {definition.function_name}"

    async def _create_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a definition file."""
        definition_ids = context.get("definition_ids", [])
        file_name = context.get("file_name", "steps.py")
        framework = context.get("framework", StepFramework.BEHAVE)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        # Gather definitions
        definitions = []
        for def_id in definition_ids:
            definition = self._definition_registry.get(def_id)
            if definition:
                definitions.append(definition)

        # Create file
        definition_file = DefinitionFile(
            file_name=file_name,
            definitions=definitions,
            framework=framework if isinstance(framework, StepFramework) else StepFramework(framework),
            file_context={
                "workflow_id": workflow_id,
                "definition_count": len(definitions),
            },
        )

        self._file_registry[definition_file.file_id] = definition_file

        return f"Created file: {definition_file.file_name} ({len(definitions)} definition(s))"

    async def _save_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Save definition file to disk."""
        file_id = context.get("file_id")
        output_dir = context.get("output_dir", "")

        if not file_id:
            return "Error: file_id is required"

        definition_file = self._file_registry.get(file_id)
        if not definition_file:
            return f"Error: File '{file_id}' not found"

        output_path = Path(output_dir) / definition_file.file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        code = definition_file.to_python_code()
        output_path.write_text(code, encoding="utf-8")

        return f"Saved file to: {output_path}"

    async def _get_creation_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get creation context."""
        creation_id = context.get("creation_id")

        if not creation_id:
            return "Error: creation_id is required"

        for creation_context in self._creation_history:
            if creation_context.creation_id == creation_id:
                return (
                    f"Creation '{creation_id}': "
                    f"{creation_context.definitions_created} definition(s), "
                    f"{creation_context.files_created} file(s)"
                )

        return f"Error: Creation context '{creation_id}' not found"

    async def _get_definition(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get definition by ID."""
        definition_id = context.get("definition_id")

        if not definition_id:
            return "Error: definition_id is required"

        definition = self._definition_registry.get(definition_id)
        if definition:
            return f"Definition '{definition.function_name}': status={definition.status.value}, {len(definition.parameters)} param(s)"

        return f"Error: Definition '{definition_id}' not found"

    def _extract_params_from_step(self, step_text: str) -> list[StepParameter]:
        """Extract parameters from step text."""
        import re

        parameters = []

        # Find quoted strings
        for match in re.finditer(r'"([^"]+)"', step_text):
            param = StepParameter(
                name=f"param_{len(parameters) + 1}",
                param_type="str",
                pattern=f'"([^"]+)"',
                source_context={"matched_text": match.group(0)},
            )
            parameters.append(param)

        # Find numbers
        for match in re.finditer(r'\b(\d+)\b', step_text):
            param = StepParameter(
                name=f"num_{len(parameters) + 1}",
                param_type="int",
                pattern=r'\b(\d+)\b',
                source_context={"matched_text": match.group(0)},
            )
            parameters.append(param)

        return parameters

    def _generate_function_name(self, step_text: str) -> str:
        """Generate function name from step text."""
        import re

        # Remove quotes, special chars, convert to snake_case
        cleaned = step_text.lower()
        cleaned = re.sub(r'["\'.,]', ' ', cleaned)
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())

        # Truncate if too long
        if len(cleaned) > 50:
            cleaned = cleaned[:50]

        return f"step_{cleaned}"

    def _generate_impl_code(self, definition: StepDefinition) -> str:
        """Generate implementation code."""
        lines = ["    # Implementation"]

        if "navigates" in definition.step_text.lower():
            lines.append("    page.goto(context.page_url)")
        elif "clicks" in definition.step_text.lower():
            lines.append("    page.click('selector_here')")
        elif "enters" in definition.step_text.lower():
            lines.append("    page.fill('selector_here', context.text)")
        elif "visible" in definition.step_text.lower():
            lines.append("    expect(page.locator('selector_here')).to_be_visible()")

        return "\n".join(lines)

    def get_creation_history(self) -> list[CreationContext]:
        """Get creation history."""
        return self._creation_history.copy()

    def get_definition_registry(self) -> dict[str, StepDefinition]:
        """Get definition registry."""
        return self._definition_registry.copy()

    def get_file_registry(self) -> dict[str, DefinitionFile]:
        """Get file registry."""
        return self._file_registry.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

