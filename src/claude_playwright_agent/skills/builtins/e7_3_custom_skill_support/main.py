"""
E7.3 - Custom Skill Support Skill.

This skill provides custom skill scaffolding:
- Skill scaffolding with templates
- Template generation
- Project structure creation
- Creation context tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class TemplateType(str, Enum):
    """Types of skill templates."""

    FULL = "full"
    SIMPLE = "simple"
    MINIMAL = "minimal"


@dataclass
class SkillTemplate:
    """
    A skill template.

    Attributes:
        template_id: Unique template identifier
        template_type: Type of template
        name: Template name
        description: Template description
        manifest_template: YAML manifest template
        main_template: Main.py template
        init_template: __init__.py template
        created_at: When template was created
    """

    template_id: str = field(default_factory=lambda: f"tpl_{uuid.uuid4().hex[:8]}")
    template_type: TemplateType = TemplateType.FULL
    name: str = ""
    description: str = ""
    manifest_template: str = ""
    main_template: str = ""
    init_template: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "template_type": self.template_type.value,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
        }


@dataclass
class SkillScaffold:
    """
    A skill scaffold with generated files.

    Attributes:
        scaffold_id: Unique scaffold identifier
        skill_name: Name of skill
        output_dir: Output directory
        manifest_content: Generated manifest content
        main_content: Generated main.py content
        init_content: Generated __init__.py content
        creation_context: Context at creation time
        created_at: When scaffold was created
    """

    scaffold_id: str = field(default_factory=lambda: f"scaffold_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    output_dir: str = ""
    manifest_content: str = ""
    main_content: str = ""
    init_content: str = ""
    creation_context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scaffold_id": self.scaffold_id,
            "skill_name": self.skill_name,
            "output_dir": self.output_dir,
            "creation_context": self.creation_context,
            "created_at": self.created_at,
        }


@dataclass
class ScaffoldContext:
    """
    Context for skill scaffolding.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        skills_created: Number of skills created
        templates_used: Templates used
        output_directories: Output directories used
        scaffold_history: List of scaffold operations
        started_at: When context was created
        completed_at: When context was completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    skills_created: int = 0
    templates_used: list[str] = field(default_factory=list)
    output_directories: list[str] = field(default_factory=list)
    scaffold_history: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "skills_created": self.skills_created,
            "templates_used": self.templates_used,
            "output_directories": self.output_directories,
            "scaffold_history": self.scaffold_history,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class CustomSkillSupportAgent(BaseAgent):
    """
    Custom Skill Support Agent.

    This agent provides:
    1. Skill scaffolding with templates
    2. Template generation
    3. Project structure creation
    4. Creation context tracking
    """

    name = "e7_3_custom_skill_support"
    version = "1.0.0"
    description = "E7.3 - Custom Skill Support"

    def __init__(self, **kwargs) -> None:
        """Initialize the custom skill support agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E7.3 - Custom Skill Support agent for the Playwright test automation framework. You help users with e7.3 - custom skill support tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[ScaffoldContext] = []
        self._scaffold_cache: dict[str, SkillScaffold] = {}
        self._template_registry: dict[str, SkillTemplate] = {}
        self._initialize_templates()

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
        Execute custom skill support task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "scaffold_skill":
            return await self._scaffold_skill(context, execution_context)
        elif task_type == "create_skill_structure":
            return await self._create_skill_structure(context, execution_context)
        elif task_type == "generate_template":
            return await self._generate_template(context, execution_context)
        elif task_type == "write_skill_files":
            return await self._write_skill_files(context, execution_context)
        elif task_type == "get_scaffold":
            return await self._get_scaffold(context, execution_context)
        elif task_type == "get_scaffold_context":
            return await self._get_scaffold_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _scaffold_skill(self, context: dict[str, Any], execution_context: Any) -> str:
        """Scaffold a new custom skill."""
        skill_name = context.get("skill_name")
        skill_description = context.get("skill_description", "")
        output_dir = context.get("output_dir", "skills")
        template_type = context.get("template_type", TemplateType.FULL)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        # Get template
        if isinstance(template_type, str):
            template_type = TemplateType(template_type)

        template = self._template_registry.get(template_type.value, self._template_registry.get("full"))

        # Generate contents
        manifest_content = self._generate_manifest_content(skill_name, skill_description)
        main_content = self._generate_main_content(skill_name)
        init_content = self._generate_init_content(skill_name)

        # Create scaffold
        scaffold = SkillScaffold(
            skill_name=skill_name,
            output_dir=str(Path(output_dir) / skill_name),
            manifest_content=manifest_content,
            main_content=main_content,
            init_content=init_content,
            creation_context={
                "workflow_id": workflow_id,
                "template_type": template_type.value,
            },
        )

        self._scaffold_cache[scaffold.scaffold_id] = scaffold

        return f"Scaffolded skill: {skill_name} ({template_type.value} template)"

    async def _create_skill_structure(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create skill directory structure."""
        skill_name = context.get("skill_name")
        output_dir = context.get("output_dir", "skills")

        if not skill_name:
            return "Error: skill_name is required"

        skill_dir = Path(output_dir) / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        return f"Created skill directory: {skill_dir}"

    async def _generate_template(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate template content."""
        skill_name = context.get("skill_name")
        file_type = context.get("file_type", "manifest")

        if not skill_name:
            return "Error: skill_name is required"

        if file_type == "manifest":
            content = self._generate_manifest_content(skill_name)
        elif file_type == "main":
            content = self._generate_main_content(skill_name)
        elif file_type == "init":
            content = self._generate_init_content(skill_name)
        else:
            return f"Unknown file type: {file_type}"

        return f"Generated {file_type} template for {skill_name}"

    async def _write_skill_files(self, context: dict[str, Any], execution_context: Any) -> str:
        """Write skill files to disk."""
        scaffold_id = context.get("scaffold_id")

        if not scaffold_id:
            return "Error: scaffold_id is required"

        scaffold = self._scaffold_cache.get(scaffold_id)
        if not scaffold:
            return f"Error: Scaffold '{scaffold_id}' not found"

        output_path = Path(scaffold.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files_created = []

        # Write manifest
        manifest_path = output_path / "skill.yaml"
        manifest_path.write_text(scaffold.manifest_content, encoding="utf-8")
        files_created.append(str(manifest_path))

        # Write main.py
        main_path = output_path / "main.py"
        main_path.write_text(scaffold.main_content, encoding="utf-8")
        files_created.append(str(main_path))

        # Write __init__.py
        init_path = output_path / "__init__.py"
        init_path.write_text(scaffold.init_content, encoding="utf-8")
        files_created.append(str(init_path))

        return f"Wrote {len(files_created)} file(s) to {output_path}"

    async def _get_scaffold(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get scaffold by ID."""
        scaffold_id = context.get("scaffold_id")

        if not scaffold_id:
            return "Error: scaffold_id is required"

        scaffold = self._scaffold_cache.get(scaffold_id)
        if scaffold:
            return f"Scaffold '{scaffold.skill_name}': {scaffold.output_dir}"

        return f"Error: Scaffold '{scaffold_id}' not found"

    async def _get_scaffold_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get scaffold context."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for scaffold_context in self._context_history:
            if scaffold_context.context_id == context_id:
                return (
                    f"Scaffold context '{context_id}': "
                    f"{scaffold_context.skills_created} skill(s) created"
                )

        return f"Error: Scaffold context '{context_id}' not found"

    def _generate_manifest_content(self, skill_name: str, description: str = "") -> str:
        """Generate manifest YAML content."""
        return f"""name: {skill_name}
version: 1.0.0
description: {description or f"{skill_name} skill"}

author: Custom Skill
license: MIT

# Python dependencies
python_dependencies: []

# Skill dependencies
dependencies: []

# Tags for categorization
tags:
  - custom

# Capabilities
capabilities: []

# Settings
settings:
  enabled: true
"""

    def _generate_main_content(self, skill_name: str) -> str:
        """Generate main.py content. (Simplified version)"""
        # TODO: Implement code generation template
        class_name = "".join(word.capitalize() for word in skill_name.split("_"))
        return f"# Placeholder for {skill_name}\n"

    def _generate_init_content(self, skill_name: str) -> str:
        """Generate __init__.py content. (Simplified version)"""
        # TODO: Implement code generation template
        return f"# Placeholder for {skill_name}\n"

    def _initialize_templates(self) -> None:
        """Initialize template registry."""
        for template_type in TemplateType:
            template = SkillTemplate(
                template_type=template_type,
                name=f"{template_type.value}_template",
                description=f"{template_type.value} skill template",
            )
            self._template_registry[template_type.value] = template

    def get_scaffold_cache(self) -> dict[str, SkillScaffold]:
        """Get scaffold cache."""
        return self._scaffold_cache.copy()

    def get_template_registry(self) -> dict[str, SkillTemplate]:
        """Get template registry."""
        return self._template_registry.copy()

    def get_context_history(self) -> list[ScaffoldContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

