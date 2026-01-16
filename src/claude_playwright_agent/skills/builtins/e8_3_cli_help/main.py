"""
E8.3 - CLI Help & Documentation Skill.

This skill provides help and documentation capabilities:
- Command help generation
- Documentation rendering
- Example generation
- Interactive guidance
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class HelpFormat(str, Enum):
    """Help output formats."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class HelpCategory(str, Enum):
    """Help categories."""

    COMMANDS = "commands"
    AGENTS = "agents"
    SKILLS = "skills"
    CONFIG = "config"
    WORKFLOWS = "workflows"
    EXAMPLES = "examples"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class HelpTopic:
    """
    A help topic with content.

    Attributes:
        topic_id: Unique topic identifier
        title: Topic title
        category: Topic category
        content: Help content
        examples: List of examples
        related_topics: Related topic IDs
        aliases: Alternative names
        metadata: Additional metadata
        created_at: When topic was created
        updated_at: When topic was last updated
    """

    topic_id: str = field(default_factory=lambda: f"topic_{uuid.uuid4().hex[:8]}")
    title: str = ""
    category: HelpCategory = HelpCategory.COMMANDS
    content: str = ""
    examples: list[str] = field(default_factory=list)
    related_topics: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "category": self.category.value,
            "content": self.content,
            "examples": self.examples,
            "related_topics": self.related_topics,
            "aliases": self.aliases,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class HelpSection:
    """
    A section within help documentation.

    Attributes:
        section_id: Unique section identifier
        title: Section title
        content: Section content
        order: Display order
        subsections: List of subsection IDs
        topics: List of topic IDs
        metadata: Additional metadata
    """

    section_id: str = field(default_factory=lambda: f"section_{uuid.uuid4().hex[:8]}")
    title: str = ""
    content: str = ""
    order: int = 0
    subsections: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "subsections": self.subsections,
            "topics": self.topics,
            "metadata": self.metadata,
        }


@dataclass
class DocumentationContext:
    """
    Context for documentation operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        topics_generated: Number of topics generated
        sections_created: Number of sections created
        examples_added: Number of examples added
        format: Output format used
        started_at: When documentation started
        completed_at: When documentation completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"doc_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    topics_generated: int = 0
    sections_created: int = 0
    examples_added: int = 0
    format: HelpFormat = HelpFormat.MARKDOWN
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "topics_generated": self.topics_generated,
            "sections_created": self.sections_created,
            "examples_added": self.examples_added,
            "format": self.format.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


@dataclass
class Example:
    """
    A usage example.

    Attributes:
        example_id: Unique example identifier
        title: Example title
        description: Example description
        command: Command to run
        code: Code example
        expected_output: Expected output
        category: Example category
        difficulty: Difficulty level (beginner, intermediate, advanced)
        tags: Example tags
    """

    example_id: str = field(default_factory=lambda: f"ex_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    command: str = ""
    code: str = ""
    expected_output: str = ""
    category: str = ""
    difficulty: str = "beginner"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "example_id": self.example_id,
            "title": self.title,
            "description": self.description,
            "command": self.command,
            "code": self.code,
            "expected_output": self.expected_output,
            "category": self.category,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }


class CLIHelpAgent(BaseAgent):
    """
    CLI Help and Documentation Agent.

    This agent provides:
    1. Command help generation
    2. Documentation rendering
    3. Example generation
    4. Interactive guidance
    """

    name = "e8_3_cli_help"
    version = "1.0.0"
    description = "E8.3 - CLI Help & Documentation"

    def __init__(self, **kwargs) -> None:
        """Initialize the CLI help agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E8.3 - CLI Help & Documentation agent for the Playwright test automation framework. You help users with e8.3 - cli help & documentation tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[DocumentationContext] = []
        self._topic_registry: dict[str, HelpTopic] = {}
        self._section_registry: dict[str, HelpSection] = {}
        self._example_registry: dict[str, Example] = {}

        # Initialize built-in help topics
        self._initialize_builtin_topics()

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
        Execute help task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the help operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "get_help":
            return await self._get_help(context, execution_context)
        elif task_type == "get_command_help":
            return await self._get_command_help(context, execution_context)
        elif task_type == "list_topics":
            return await self._list_topics(context, execution_context)
        elif task_type == "get_topic":
            return await self._get_topic(context, execution_context)
        elif task_type == "search_help":
            return await self._search_help(context, execution_context)
        elif task_type == "generate_example":
            return await self._generate_example(context, execution_context)
        elif task_type == "get_examples":
            return await self._get_examples(context, execution_context)
        elif task_type == "render_documentation":
            return await self._render_documentation(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    def _initialize_builtin_topics(self) -> None:
        """Initialize built-in help topics."""

        # Main commands topic
        main_commands = HelpTopic(
            title="Main Commands",
            category=HelpCategory.COMMANDS,
            content="""The Claude Playwright Agent provides several main commands:

- `init`: Initialize a new project
- `ingest`: Ingest Playwright recordings
- `run`: Run workflows or tests
- `status`: Show project status
- `config`: Manage configuration

Run `cpa <command> --help` for more information on each command.
""",
            examples=[
                "cpa init my-project",
                "cpa ingest recordings/login.js",
                "cpa run workflow full",
            ],
        )
        self._topic_registry[main_commands.topic_id] = main_commands

        # Agents topic
        agents = HelpTopic(
            title="Agents",
            category=HelpCategory.AGENTS,
            content="""The system uses specialized agents for different tasks:

- **IngestionAgent**: Parses Playwright recordings
- **DeduplicationAgent**: Identifies duplicate selectors
- **BDDConversionAgent**: Converts to Gherkin scenarios
- **ExecutionAgent**: Runs BDD tests
- **HealingAgent**: Fixes broken selectors

Each agent preserves full context throughout its operations.
""",
        )
        self._topic_registry[agents.topic_id] = agents

        # Skills topic
        skills = HelpTopic(
            title="Skills",
            category=HelpCategory.SKILLS,
            content="""Skills are modular components that provide specific capabilities:

- **E1**: Framework Foundation (state, config, logging, etc.)
- **E2**: Agent Orchestration (lifecycle, messaging)
- **E3**: Recording Processing (parsing, validation)
- **E4**: Intelligent Deduplication
- **E5**: BDD Conversion Engine
- **E7**: Skills Architecture

Each skill maintains context through its lifecycle.
""",
        )
        self._topic_registry[skills.topic_id] = skills

        # Configuration topic
        config = HelpTopic(
            title="Configuration",
            category=HelpCategory.CONFIG,
            content="""Configuration is managed through profiles:

```bash
# View current profile
cpa config profile current

# List all profiles
cpa config profile list

# Create new profile
cpa config profile create dev

# Set configuration values
cpa config set framework.type behave
```

Configuration is stored in `.claude/profiles/`.
""",
        )
        self._topic_registry[config.topic_id] = config

        # Troubleshooting topic
        troubleshooting = HelpTopic(
            title="Troubleshooting",
            category=HelpCategory.TROUBLESHOOTING,
            content="""Common issues and solutions:

**Recording parsing fails**
- Ensure the recording file is valid JSON
- Check that it was exported from Playwright

**Tests fail to run**
- Verify Playwright browsers are installed: `playwright install`
- Check that framework dependencies are installed

**State corruption**
- Run `cpa state restore` to recover from backup
- Check `.claude/state/backups/` for available backups

**Context loss**
- Check logs for context propagation errors
- Verify all agents are properly initialized
""",
        )
        self._topic_registry[troubleshooting.topic_id] = troubleshooting

    async def _get_help(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get general help."""
        format_type = context.get("format", "text")

        if format_type == "markdown":
            return """# Claude Playwright Agent

A comprehensive BDD testing framework powered by Claude and Playwright.

## Quick Start

```bash
# Initialize a project
cpa init my-project

# Ingest a recording
cpa ingest recordings/login.js

# Run tests
cpa run workflow test

# Get help
cpa --help
cpa <command> --help
```

## Main Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new project |
| `ingest` | Ingest Playwright recordings |
| `run` | Run workflows or tests |
| `status` | Show project status |
| `config` | Manage configuration |

## Getting More Help

- `cpa help commands` - List all commands
- `cpa help agents` - Learn about agents
- `cpa help skills` - Learn about skills
- `cpa help config` - Configuration guide
- `cpa help troubleshooting` - Common issues

## Documentation

Full documentation available at: https://github.com/anthropics/claude-playwright-agent
"""
        else:
            return """Claude Playwright Agent - BDD Testing Framework

Main commands:
  init       Initialize a new project
  ingest     Ingest Playwright recordings
  run        Run workflows or tests
  status     Show project status
  config     Manage configuration

Get help on specific topics:
  cpa help commands
  cpa help agents
  cpa help skills
  cpa help config
  cpa help troubleshooting

Online: https://github.com/anthropics/claude-playwright-agent
"""

    async def _get_command_help(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get help for a specific command."""
        command = context.get("command")

        if not command:
            return "Error: command is required"

        help_texts = {
            "init": """Initialize a new project.

Usage:
  cpa init <project-name> [options]

Options:
  --framework TYPE    Framework type (behave, pytest-bdd)
  --template NAME     Use specific template
  --verbose           Show detailed output

Examples:
  cpa init my-project
  cpa init my-project --framework behave
""",
            "ingest": """Ingest a Playwright recording.

Usage:
  cpa ingest <recording-path> [options]

Options:
  --project-path PATH   Project directory
  --verbose             Show detailed output
  --no-progress         Disable progress bar

The ingest command runs the full pipeline:
1. Parse the recording
2. Deduplicate selectors
3. Generate BDD scenarios
4. Update project state

Examples:
  cpa ingest recordings/login.js
  cpa ingest recordings/*.js --verbose
""",
            "run": """Run workflows or tests.

Usage:
  cpa run <workflow> [options]

Workflows:
  full       Run complete pipeline
  ingest     Run ingestion only
  convert    Run BDD conversion only
  test       Run tests only

Options:
  --project-path PATH   Project directory
  --framework TYPE      Override framework
  --tags TAGS           Filter by tags

Examples:
  cpa run workflow full
  cpa run workflow test --tags @smoke
""",
            "status": """Show project status.

Usage:
  cpa status [options]

Options:
  --json       Output as JSON
  --verbose    Show detailed status

Displays:
- Project configuration
- State information
- Agent status
- Skill status
- Recent activity
""",
            "config": """Manage configuration.

Usage:
  cpa config <command> [options]

Commands:
  get <key>           Get configuration value
  set <key> <value>   Set configuration value
  profile <subcmd>    Profile management

Examples:
  cpa config get framework.type
  cpa config set framework.type behave
  cpa config profile current
""",
        }

        return help_texts.get(command, f"No help available for '{command}'")

    async def _list_topics(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all help topics."""
        category = context.get("category")

        topics = list(self._topic_registry.values())

        if category:
            if isinstance(category, str):
                category = HelpCategory(category)
            topics = [t for t in topics if t.category == category]

        topic_list = "\n".join(f"- {t.title}" for t in topics)
        return f"Help topics ({len(topics)}):\n{topic_list}"

    async def _get_topic(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get a specific help topic."""
        topic_id = context.get("topic_id")
        title = context.get("title")

        if topic_id:
            topic = self._topic_registry.get(topic_id)
            if topic:
                output = f"# {topic.title}\n\n{topic.content}"
                if topic.examples:
                    output += "\n\n## Examples\n\n"
                    for example in topic.examples:
                        output += f"- `{example}`\n"
                return output

        if title:
            for topic in self._topic_registry.values():
                if topic.title.lower() == title.lower():
                    output = f"# {topic.title}\n\n{topic.content}"
                    if topic.examples:
                        output += "\n\n## Examples\n\n"
                        for example in topic.examples:
                            output += f"- `{example}`\n"
                    return output

        return "Error: topic not found"

    async def _search_help(self, context: dict[str, Any], execution_context: Any) -> str:
        """Search help topics."""
        query = context.get("query", "").lower()

        if not query:
            return "Error: query is required"

        matching = []
        for topic in self._topic_registry.values():
            if (
                query in topic.title.lower()
                or query in topic.content.lower()
                or any(query in ex.lower() for ex in topic.examples)
            ):
                matching.append(topic.title)

        if matching:
            return f"Found {len(matching)} topic(s):\n" + "\n".join(f"- {t}" for t in matching)

        return "No topics found"

    async def _generate_example(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate a usage example."""
        category = context.get("category", "")
        difficulty = context.get("difficulty", "beginner")

        examples = {
            "ingest": Example(
                title="Ingest a Playwright Recording",
                description="Ingest a recording file into your project",
                command="cpa ingest recordings/login.js",
                code="""# The ingest command will:
# 1. Parse the recording
# 2. Deduplicate selectors
# 3. Generate BDD scenarios
# 4. Update project state

cpa ingest recordings/login.js --verbose
""",
                expected_output="[10:00:00] Starting ingestion pipeline...\n[10:00:01] Parsed recording.js...\n[10:00:02] Found 3 element groups\n[10:00:03] Generated 2 scenarios\n[10:00:04] Complete!",
                category="ingest",
                difficulty="beginner",
                tags=["ingest", "recording", "pipeline"],
            ),
            "workflow": Example(
                title="Run Full Workflow",
                description="Run the complete pipeline from ingest to test",
                command="cpa run workflow full",
                code='''# Run the full pipeline
cpa run workflow full

# This will:
# - Ingest all recordings
# - Deduplicate selectors
# - Generate BDD scenarios
# - Run tests
# - Generate report''',
                expected_output="Running full workflow...\nComplete!",
                category="workflow",
                difficulty="beginner",
                tags=["workflow", "pipeline"],
            ),
        }

        if category in examples:
            ex = examples[category]
            if difficulty and ex.difficulty != difficulty:
                return f"No {difficulty} example found for '{category}'"
            return f"Example: {ex.title}\n\n{ex.description}\n\nCommand:\n{ex.command}\n\n{ex.code}"

        return f"No example found for '{category}'"

    async def _get_examples(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all examples or filter by category."""
        category = context.get("category")

        examples = list(self._example_registry.values())

        if category:
            examples = [e for e in examples if e.category == category]

        if not examples:
            return "No examples found"

        output = f"Examples ({len(examples)}):\n\n"
        for ex in examples:
            output += f"- {ex.title} ({ex.difficulty})\n"
            output += f"  {ex.description}\n\n"

        return output

    async def _render_documentation(self, context: dict[str, Any], execution_context: Any) -> str:
        """Render full documentation."""
        format_type = context.get("format", "markdown")

        sections = list(self._section_registry.values())
        sections.sort(key=lambda s: s.order)

        if format_type == "markdown":
            output = "# Claude Playwright Agent Documentation\n\n"
            for section in sections:
                output += f"## {section.title}\n\n{section.content}\n\n"
            return output

        return "Documentation rendering complete"

    def get_topic_registry(self) -> dict[str, HelpTopic]:
        """Get topic registry."""
        return self._topic_registry.copy()

    def get_example_registry(self) -> dict[str, Example]:
        """Get example registry."""
        return self._example_registry.copy()

    def get_context_history(self) -> list[DocumentationContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

