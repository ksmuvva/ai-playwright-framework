"""
Developer Documentation System for Claude Playwright Agent.

This module implements:
- Auto-generated API documentation
- Developer guides
- Architecture documentation
- Interactive help system
- Example/tutorial system
"""

import ast
import inspect
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_type_hints


# =============================================================================
# Documentation Models
# =============================================================================


class DocType(str, Enum):
    """Types of documentation."""

    API = "api"
    GUIDE = "guide"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    EXAMPLE = "example"


class DocFormat(str, Enum):
    """Documentation output formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


@dataclass
class APIDocument:
    """
    API documentation for a function or class.

    Attributes:
        name: Name of the function/class
        type: Type (function, class, method)
        signature: Function signature
        docstring: Docstring content
        parameters: List of parameters
        returns: Return type description
        examples: List of usage examples
        source_file: Source file path
        source_line: Line number in source
    """

    name: str
    type: str
    signature: str = ""
    docstring: str = ""
    parameters: list[dict[str, Any]] = field(default_factory=list)
    returns: str = ""
    examples: list[str] = field(default_factory=list)
    source_file: str = ""
    source_line: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "signature": self.signature,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "returns": self.returns,
            "examples": self.examples,
            "source_file": self.source_file,
            "source_line": self.source_line,
        }


@dataclass
class DocSection:
    """
    A section in documentation.

    Attributes:
        title: Section title
        content: Section content
        subsections: List of subsections
        level: Section level (1-6)
    """

    title: str
    content: str = ""
    subsections: list["DocSection"] = field(default_factory=list)
    level: int = 1

    def to_markdown(self) -> str:
        """Convert section to markdown."""
        prefix = "#" * self.level
        md = f"{prefix} {self.title}\n\n"

        if self.content:
            md += f"{self.content}\n\n"

        for subsection in self.subsections:
            md += subsection.to_markdown()

        return md


@dataclass
class DeveloperGuide:
    """
    A developer guide.

    Attributes:
        id: Unique identifier
        title: Guide title
        description: Guide description
        category: Guide category
        content: Guide content sections
        tags: List of tags
        difficulty: Difficulty level
        estimated_time: Estimated reading time (minutes)
    """

    id: str
    title: str
    description: str
    category: str
    content: list[DocSection]
    tags: list[str] = field(default_factory=list)
    difficulty: str = "beginner"
    estimated_time: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
        }


@dataclass
class CodeExample:
    """
    A code example with explanation.

    Attributes:
        title: Example title
        description: Example description
        code: Code snippet
        language: Programming language
        output: Expected output
        explanation: Step-by-step explanation
    """

    title: str
    description: str
    code: str
    language: str = "python"
    output: str = ""
    explanation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "code": self.code,
            "language": self.language,
            "output": self.output,
            "explanation": self.explanation,
        }


# =============================================================================
# API Documentation Generator
# =============================================================================


class APIDocGenerator:
    """
    Generate API documentation from Python code.

    Features:
    - Extract functions, classes, methods
    - Parse docstrings
    - Generate signatures
    - Create examples
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the API doc generator.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()

    def generate_module_docs(
        self,
        module_path: str | Path,
    ) -> list[APIDocument]:
        """
        Generate documentation for a Python module.

        Args:
            module_path: Path to Python module

        Returns:
            List of API documents
        """
        module_path = Path(module_path)

        if not module_path.exists():
            return []

        docs = []

        # Read source file
        source = module_path.read_text(encoding="utf-8")

        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        # Extract class and function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = self._generate_class_doc(node, module_path)
                docs.append(doc)

                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_doc = self._generate_method_doc(
                            item, node.name, module_path
                        )
                        docs.append(method_doc)

            elif isinstance(node, ast.FunctionDef):
                # Top-level function
                func_doc = self._generate_function_doc(node, module_path)
                docs.append(func_doc)

        return docs

    def _generate_class_doc(
        self,
        node: ast.ClassDef,
        file_path: Path,
    ) -> APIDocument:
        """Generate documentation for a class."""
        docstring = ast.get_docstring(node) or ""

        return APIDocument(
            name=node.name,
            type="class",
            docstring=docstring,
            source_file=str(file_path),
            source_line=node.lineno,
        )

    def _generate_function_doc(
        self,
        node: ast.FunctionDef,
        file_path: Path,
    ) -> APIDocument:
        """Generate documentation for a function."""
        docstring = ast.get_docstring(node) or ""

        # Generate signature
        signature = self._generate_signature(node)

        # Extract parameters
        parameters = self._extract_parameters(node)

        return APIDocument(
            name=node.name,
            type="function",
            signature=signature,
            docstring=docstring,
            parameters=parameters,
            source_file=str(file_path),
            source_line=node.lineno,
        )

    def _generate_method_doc(
        self,
        node: ast.FunctionDef,
        class_name: str,
        file_path: Path,
    ) -> APIDocument:
        """Generate documentation for a method."""
        docstring = ast.get_docstring(node) or ""

        # Generate signature
        signature = f"{class_name}.{self._generate_signature(node)}"

        # Extract parameters
        parameters = self._extract_parameters(node)

        return APIDocument(
            name=f"{class_name}.{node.name}",
            type="method",
            signature=signature,
            docstring=docstring,
            parameters=parameters,
            source_file=str(file_path),
            source_line=node.lineno,
        )

    def _generate_signature(self, node: ast.FunctionDef) -> str:
        """Generate function signature."""
        args = []

        # Positional args
        pos_only = getattr(node, "posonlyargs", [])
        for arg in pos_only:
            args.append(arg.arg)

        # Regular args
        for arg in node.args.args:
            if arg not in pos_only:
                args.append(arg.arg)

        # Var args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        # Keyword-only args
        kw_only = getattr(node, "kwonlyargs", [])
        for arg in kw_only:
            args.append(arg.arg)

        # Kw args
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        signature = f"{node.name}({', '.join(args)})"

        # Return annotation
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"

        return signature

    def _extract_parameters(
        self,
        node: ast.FunctionDef,
    ) -> list[dict[str, str]]:
        """Extract parameter information."""
        params = []

        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "type": "",
                "default": "",
            }

            # Get annotation
            if arg.annotation:
                param["type"] = ast.unparse(arg.annotation)

            params.append(param)

        return params


# =============================================================================
# Architecture Documentation Generator
# =============================================================================


class ArchitectureDocGenerator:
    """
    Generate architecture documentation.

    Features:
    - Module dependency graphs
    - Class hierarchy diagrams
    - Data flow diagrams
    - Component descriptions
    """

    def __init__(self, project_path: Path | None = None) -> None:
        """
        Initialize the architecture doc generator.

        Args:
            project_path: Path to project root
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()

    def generate_architecture_doc(self) -> DocSection:
        """
        Generate architecture documentation.

        Returns:
            DocSection with architecture information
        """
        section = DocSection(
            title="Architecture",
            level=1,
        )

        # Add subsections
        section.subsections = [
            DocSection(
                title="Overview",
                level=2,
                content="""
Claude Playwright Agent is an AI-powered test automation framework that converts
Playwright recordings into BDD tests and executes them with self-healing capabilities.
""",
            ),
            DocSection(
                title="Core Components",
                level=2,
                content=self._get_core_components_doc(),
            ),
            DocSection(
                title="Data Flow",
                level=2,
                content=self._get_data_flow_doc(),
            ),
            DocSection(
                title="Agent System",
                level=2,
                content=self._get_agent_system_doc(),
            ),
        ]

        return section

    def _get_core_components_doc(self) -> str:
        """Get core components documentation."""
        return """
The framework consists of several core components:

- **CLI**: Command-line interface for project management and test execution
- **Ingestion**: Converts Playwright recordings to BDD scenarios
- **Deduplication**: Groups similar elements across recordings
- **BDD Conversion**: Generates Gherkin scenarios from recordings
- **Execution**: Runs tests with Playwright or Behave
- **Self-Healing**: Automatically repairs broken selectors
- **Skills**: Extensible agent-based skill system
- **State Management**: Tracks project state and test results
"""

    def _get_data_flow_doc(self) -> str:
        """Get data flow documentation."""
        return """
```
Playwright Recording → Ingestion Agent → Deduplication Agent
                                              ↓
                                        BDD Conversion Agent
                                              ↓
                                        Scenario Storage
                                              ↓
                                        Execution Engine
                                              ↓
                                        Test Results + Reports
```
"""

    def _get_agent_system_doc(self) -> str:
        """Get agent system documentation."""
        return """
The agent system consists of:

- **OrchestratorAgent**: Coordinates multi-agent workflows
- **IngestionAgent**: Processes Playwright recordings
- **DeduplicationAgent**: Groups similar elements
- **BDDConversionAgent**: Generates BDD scenarios
- **ExecutionAgent**: Runs tests and captures results
- **Priority Messaging**: Task prioritization with aging
- **Event Broadcasting**: Pub/sub for inter-agent communication
- **Resource Limits**: CPU and memory tracking per agent
"""


# =============================================================================
# Interactive Help System
# =============================================================================


class InteractiveHelpSystem:
    """
    Interactive help system for developers.

    Features:
    - Contextual help
    - Command documentation
    - Examples generator
    - Search functionality
    """

    def __init__(self) -> None:
        """Initialize the help system."""
        self._command_docs: dict[str, str] = {}
        self._examples: dict[str, list[CodeExample]] = {}

    def get_help_for_command(self, command: str) -> str:
        """
        Get help text for a command.

        Args:
            command: Command name

        Returns:
            Help text
        """
        # Define command documentation
        docs = {
            "init": """
Initialize a new Claude Playwright Agent project.

Usage: cpa init [OPTIONS]

Options:
  --name, -n: Project name
  --framework, -F: BDD framework (behave, pytest-bdd)
  --template: Project template (basic, advanced, ecommerce)
  --profile: Configuration profile

Example:
  cpa init --name my-tests --framework behave
""",
            "ingest": """
Ingest a Playwright recording into BDD scenarios.

Usage: cpa ingest RECORDING [OPTIONS]

Options:
  --name: Name for the recording
  --tags: Tags to add to scenarios
  --dry-run: Show what would be done

Example:
  cpa ingest recordings/login.js --name login-scenario
""",
            "run": """
Run BDD tests.

Usage: cpa run [OPTIONS]

Options:
  --tags: Filter scenarios by tags
  --parallel: Run tests in parallel
  --workers: Number of parallel workers

Example:
  cpa run --tags @smoke --parallel --workers 4
""",
        }

        return docs.get(command, f"No help available for '{command}'")

    def get_examples_for_command(self, command: str) -> list[CodeExample]:
        """
        Get examples for a command.

        Args:
            command: Command name

        Returns:
            List of code examples
        """
        examples = {
            "init": [
                CodeExample(
                    title="Basic Project Initialization",
                    description="Create a basic test project",
                    code="cpa init",
                    language="bash",
                    explanation=[
                        "Creates a new project with default settings",
                        "Uses Behave framework",
                        "Generates basic project structure",
                    ],
                ),
                CodeExample(
                    title="Custom Project",
                    description="Create a project with custom settings",
                    code="cpa init --name ecommerce-tests --framework behave --template advanced",
                    language="bash",
                    explanation=[
                        "Creates project with custom name",
                        "Uses Behave framework",
                        "Uses advanced template with more features",
                    ],
                ),
            ],
            "ingest": [
                CodeExample(
                    title="Ingest Recording",
                    description="Convert a Playwright recording to BDD",
                    code="cpa ingest recordings/login.js",
                    language="bash",
                    explanation=[
                        "Parses the Playwright recording",
                        "Generates BDD scenarios",
                        "Stores in features/ directory",
                    ],
                ),
            ],
        }

        return examples.get(command, [])


# =============================================================================
# Tutorial System
# =============================================================================


class TutorialSystem:
    """
    Tutorial system for developers.

    Features:
    - Interactive tutorials
    - Step-by-step guides
    - Progress tracking
    - Code templates
    """

    def __init__(self) -> None:
        """Initialize the tutorial system."""
        self._tutorials: dict[str, DeveloperGuide] = {}
        self._load_tutorials()

    def _load_tutorials(self) -> None:
        """Load built-in tutorials."""
        # Getting Started Tutorial
        getting_started = DeveloperGuide(
            id="getting-started",
            title="Getting Started with Claude Playwright Agent",
            description="Learn the basics of using the agent framework",
            category="basics",
            content=[
                DocSection(
                    title="Introduction",
                    level=2,
                    content="""
Welcome to Claude Playwright Agent! This tutorial will guide you through
the basics of creating AI-powered test automation.
""",
                ),
                DocSection(
                    title="Installation",
                    level=2,
                    content="""
Install the framework:

```bash
pip install claude-playwright-agent
```

Install Playwright browsers:

```bash
playwright install chromium
```
""",
                ),
                DocSection(
                    title="Your First Project",
                    level=2,
                    content="""
Initialize your first project:

```bash
cpa init my-first-tests
```

This creates a project structure with all necessary files.
""",
                ),
            ],
            tags=["beginner", "basics"],
            difficulty="beginner",
            estimated_time=15,
        )

        self._tutorials["getting-started"] = getting_started

        # Advanced Features Tutorial
        advanced = DeveloperGuide(
            id="advanced-features",
            title="Advanced Features",
            description="Learn about advanced features like self-healing and skills",
            category="advanced",
            content=[
                DocSection(
                    title="Self-Healing Selectors",
                    level=2,
                    content="""
The framework includes automatic self-healing for broken selectors:

- Detects failed selectors
- Generates alternative selectors
- Applies repairs automatically
- Learns from successful heals

Enable self-healing in configuration:

```yaml
execution:
  self_healing: true
  auto_apply_threshold: 0.8
```
""",
                ),
                DocSection(
                    title="Skills System",
                    level=2,
                    content="""
Skills are reusable agent-based components:

List available skills:
```bash
cpa skills list
```

Create a custom skill:
```bash
cpa skills create my-skill
```

Install a skill:
```bash
cpa skills install ./path/to/skill
```
""",
                ),
            ],
            tags=["advanced", "skills", "self-healing"],
            difficulty="advanced",
            estimated_time=30,
        )

        self._tutorials["advanced-features"] = advanced

    def list_tutorials(
        self,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[DeveloperGuide]:
        """
        List available tutorials.

        Args:
            category: Filter by category
            difficulty: Filter by difficulty

        Returns:
            List of tutorials
        """
        tutorials = list(self._tutorials.values())

        if category:
            tutorials = [t for t in tutorials if t.category == category]

        if difficulty:
            tutorials = [t for t in tutorials if t.difficulty == difficulty]

        return tutorials

    def get_tutorial(self, tutorial_id: str) -> DeveloperGuide | None:
        """
        Get a tutorial by ID.

        Args:
            tutorial_id: Tutorial identifier

        Returns:
            DeveloperGuide or None
        """
        return self._tutorials.get(tutorial_id)


# =============================================================================
# Documentation Exporter
# =============================================================================


class DocumentationExporter:
    """
    Export documentation to various formats.

    Features:
    - Markdown export
    - HTML export
    - JSON export
    - PDF export (via markdown)
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Initialize the documentation exporter.

        Args:
            output_dir: Directory for exported documentation
        """
        self._output_dir = Path(output_dir) if output_dir else Path(".cpa/docs")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export_api_docs(
        self,
        docs: list[APIDocument],
        format: DocFormat = DocFormat.MARKDOWN,
    ) -> Path:
        """
        Export API documentation.

        Args:
            docs: List of API documents
            format: Output format

        Returns:
            Path to exported file
        """
        if format == DocFormat.MARKDOWN:
            return self._export_api_markdown(docs)
        elif format == DocFormat.JSON:
            return self._export_api_json(docs)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_api_markdown(self, docs: list[APIDocument]) -> Path:
        """Export API docs as markdown."""
        output_path = self._output_dir / "api.md"

        lines = [
            "# API Reference\n\n",
            "This document provides reference documentation for all public APIs.\n\n",
        ]

        for doc in docs:
            lines.append(f"## {doc.name}\n\n")
            lines.append(f"**Type:** {doc.type}\n\n")

            if doc.signature:
                lines.append(f"```python\n{doc.signature}\n```\n\n")

            if doc.docstring:
                lines.append(f"{doc.docstring}\n\n")

            if doc.parameters:
                lines.append("**Parameters:**\n\n")
                for param in doc.parameters:
                    lines.append(f"- `{param['name']}`")
                    if param.get("type"):
                        lines.append(f" ({param['type']})")
                    if param.get("default"):
                        lines.append(f" = {param['default']}")
                    lines.append("\n")
                lines.append("\n")

            if doc.returns:
                lines.append(f"**Returns:** {doc.returns}\n\n")

            if doc.examples:
                lines.append("**Examples:**\n\n")
                for example in doc.examples:
                    lines.append(f"```python\n{example}\n```\n\n")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _export_api_json(self, docs: list[APIDocument]) -> Path:
        """Export API docs as JSON."""
        output_path = self._output_dir / "api.json"

        data = {
            "api_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "apis": [doc.to_dict() for doc in docs],
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path

    def export_guide(self, guide: DeveloperGuide, format: DocFormat = DocFormat.MARKDOWN) -> Path:
        """
        Export a developer guide.

        Args:
            guide: Guide to export
            format: Output format

        Returns:
            Path to exported file
        """
        filename = f"{guide.id}.{format.value}"
        output_path = self._output_dir / filename

        if format == DocFormat.MARKDOWN:
            markdown = f"# {guide.title}\n\n"
            markdown += f"{guide.description}\n\n"
            markdown += f"**Difficulty:** {guide.difficulty}\n\n"
            markdown += f"**Est. Time:** {guide.estimated_time} min\n\n"

            if guide.tags:
                markdown += f"**Tags:** {', '.join(guide.tags)}\n\n"

            for section in guide.content:
                markdown += section.to_markdown()

            output_path.write_text(markdown, encoding="utf-8")

        return output_path


# =============================================================================
# Documentation Builder
# =============================================================================


class DocumentationBuilder:
    """
    Build complete documentation for the project.

    Features:
    - Generate all documentation types
    - Create index pages
    - Export to multiple formats
    """

    def __init__(
        self,
        project_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """
        Initialize the documentation builder.

        Args:
            project_path: Path to project root
            output_dir: Documentation output directory
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._output_dir = output_dir or (self._project_path / ".cpa" / "docs")

        self._api_generator = APIDocGenerator(self._project_path)
        self._arch_generator = ArchitectureDocGenerator(self._project_path)
        self._help_system = InteractiveHelpSystem()
        self._tutorial_system = TutorialSystem()
        self._exporter = DocumentationExporter(self._output_dir)

    def build_all(self, format: DocFormat = DocFormat.MARKDOWN) -> dict[str, Path]:
        """
        Build all documentation.

        Args:
            format: Output format

        Returns:
            Dictionary mapping doc type to output path
        """
        results = {}

        # Generate API docs for key modules
        api_docs = self._generate_api_docs()
        api_path = self._exporter.export_api_docs(api_docs, format)
        results["api"] = api_path

        # Generate architecture docs
        arch_doc = self._arch_generator.generate_architecture_doc()
        arch_path = self._output_dir / f"architecture.{format.value}"
        arch_path.write_text(arch_doc.to_markdown(), encoding="utf-8")
        results["architecture"] = arch_path

        # Export tutorials
        for tutorial in self._tutorial_system.list_tutorials():
            tutorial_path = self._exporter.export_guide(tutorial, format)
            results[f"tutorial_{tutorial.id}"] = tutorial_path

        # Generate index
        index_path = self._generate_index(format)
        results["index"] = index_path

        return results

    def _generate_api_docs(self) -> list[APIDocument]:
        """Generate API documentation for all modules."""
        all_docs = []

        # Document key modules
        modules_to_doc = [
            "src/claude_playwright_agent/agents/execution.py",
            "src/claude_playwright_agent/agents/orchestrator.py",
            "src/claude_playwright_agent/agents/self_healing.py",
            "src/claude_playwright_agent/skills/loader.py",
            "src/claude_playwright_agent/state/manager.py",
        ]

        for module_path_str in modules_to_doc:
            module_path = self._project_path / module_path_str
            if module_path.exists():
                docs = self._api_generator.generate_module_docs(module_path)
                all_docs.extend(docs)

        return all_docs

    def _generate_index(self, format: DocFormat) -> Path:
        """Generate documentation index."""
        index_path = self._output_dir / f"index.{format.value}"

        if format == DocFormat.MARKDOWN:
            markdown = """# Claude Playwright Agent Documentation

Welcome to the Claude Playwright Agent documentation!

## Table of Contents

- [API Reference](api.md)
- [Architecture](architecture.md)
- [Tutorials](#tutorials)

## Tutorials

"""

            # Add tutorial links
            for tutorial in self._tutorial_system.list_tutorials():
                markdown += f"- [{tutorial.title}]({tutorial.id}.md) - {tutorial.description}\n"

            index_path.write_text(markdown, encoding="utf-8")

        return index_path


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_docs(
    project_path: Path | str | None = None,
    output_format: DocFormat = DocFormat.MARKDOWN,
) -> dict[str, Path]:
    """
    Generate all documentation for a project.

    Args:
        project_path: Path to project root
        output_format: Documentation format

    Returns:
        Dictionary mapping doc type to output path
    """
    builder = DocumentationBuilder(
        project_path=Path(project_path) if project_path else None,
    )
    return builder.build_all(output_format)


def get_help(command: str) -> str:
    """
    Get help text for a command.

    Args:
        command: Command name

    Returns:
        Help text
    """
    system = InteractiveHelpSystem()
    return system.get_help_for_command(command)


def list_tutorials(
    category: str | None = None,
    difficulty: str | None = None,
) -> list[DeveloperGuide]:
    """
    List available tutorials.

    Args:
        category: Filter by category
        difficulty: Filter by difficulty

    Returns:
        List of tutorials
    """
    system = TutorialSystem()
    return system.list_tutorials(category, difficulty)
