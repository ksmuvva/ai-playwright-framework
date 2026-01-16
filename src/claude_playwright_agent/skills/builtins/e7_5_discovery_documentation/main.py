"""
E7.5 - Skill Discovery & Documentation Skill.

This skill provides skill discovery and documentation:
- Skill discovery with metadata extraction
- Documentation generation
- Capability extraction
- Discovery context tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class DiscoveryScope(str, Enum):
    """Scope of skill discovery."""

    BUILTINS = "builtins"
    CUSTOM = "custom"
    ALL = "all"


@dataclass
class SkillMetadata:
    """
    Metadata extracted from a skill.

    Attributes:
        metadata_id: Unique metadata identifier
        skill_name: Name of the skill
        skill_path: Path to skill directory
        capabilities: List of capabilities
        dependencies: List of dependencies
        tags: Skill tags
        description: Skill description
        version: Skill version
        author: Skill author
        extracted_at: When metadata was extracted
        extraction_context: Context at extraction time
    """

    metadata_id: str = field(default_factory=lambda: f"meta_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    skill_path: str = ""
    capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    version: str = ""
    author: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    extraction_context: dict[str, Any] = field(default_factory=lambda: {})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata_id": self.metadata_id,
            "skill_name": self.skill_name,
            "skill_path": self.skill_path,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "extracted_at": self.extracted_at,
            "extraction_context": self.extraction_context,
        }


@dataclass
class SkillDocumentation:
    """
    Generated documentation for a skill.

    Attributes:
        doc_id: Unique documentation identifier
        skill_name: Name of the skill
        overview: Overview documentation
        capabilities: Capabilities documentation
        usage: Usage documentation
        examples: Example usage
        api_reference: API reference
        generated_at: When documentation was generated
        generation_context: Context at generation time
    """

    doc_id: str = field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    overview: str = ""
    capabilities: str = ""
    usage: str = ""
    examples: str = ""
    api_reference: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_context: dict[str, Any] = field(default_factory=lambda: {})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "skill_name": self.skill_name,
            "overview": self.overview,
            "capabilities": self.capabilities,
            "usage": self.usage,
            "examples": self.examples,
            "api_reference": self.api_reference,
            "generated_at": self.generated_at,
            "generation_context": self.generation_context,
        }


@dataclass
class DiscoveryContext:
    """
    Context for skill discovery operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        discovery_scope: Scope of discovery
        skills_discovered: Number of skills discovered
        metadata_extracted: Number of metadata extracted
        documentation_generated: Number of docs generated
        discovered_skills: List of discovered skill names
        started_at: When discovery started
        completed_at: When discovery completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    discovery_scope: DiscoveryScope = DiscoveryScope.ALL
    skills_discovered: int = 0
    metadata_extracted: int = 0
    documentation_generated: int = 0
    discovered_skills: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "discovery_scope": self.discovery_scope.value,
            "skills_discovered": self.skills_discovered,
            "metadata_extracted": self.metadata_extracted,
            "documentation_generated": self.documentation_generated,
            "discovered_skills": self.discovered_skills,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class SkillDiscoveryAgent(BaseAgent):
    """
    Skill Discovery and Documentation Agent.

    This agent provides:
    1. Skill discovery with metadata extraction
    2. Documentation generation
    3. Capability extraction
    4. Discovery context tracking
    """

    name = "e7_5_discovery_documentation"
    version = "1.0.0"
    description = "E7.5 - Skill Discovery & Documentation"

    def __init__(self, **kwargs) -> None:
        """Initialize the discovery agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E7.5 - Skill Discovery & Documentation agent for the Playwright test automation framework. You help users with e7.5 - skill discovery & documentation tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[DiscoveryContext] = []
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._documentation_cache: dict[str, SkillDocumentation] = {}
        self._builtin_path = Path(__file__).parent.parent.parent / "builtins"

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
        Execute discovery task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the discovery operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "discover_skills":
            return await self._discover_skills(context, execution_context)
        elif task_type == "extract_metadata":
            return await self._extract_metadata(context, execution_context)
        elif task_type == "generate_documentation":
            return await self._generate_documentation(context, execution_context)
        elif task_type == "get_capabilities":
            return await self._get_capabilities(context, execution_context)
        elif task_type == "search_skills":
            return await self._search_skills(context, execution_context)
        elif task_type == "get_discovery_context":
            return await self._get_discovery_context(context, execution_context)
        elif task_type == "get_metadata":
            return await self._get_metadata(context, execution_context)
        elif task_type == "get_documentation":
            return await self._get_documentation(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _discover_skills(self, context: dict[str, Any], execution_context: Any) -> str:
        """Discover skills with context tracking."""
        scope = context.get("scope", DiscoveryScope.ALL)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        scan_path = context.get("scan_path", "")

        # Create discovery context
        discovery_context = DiscoveryContext(
            workflow_id=workflow_id,
            discovery_scope=scope if isinstance(scope, DiscoveryScope) else DiscoveryScope(scope),
        )

        # Determine scan path
        if isinstance(scope, str):
            scope = DiscoveryScope(scope)

        if scan_path:
            scan_paths = [Path(scan_path)]
        elif scope == DiscoveryScope.BUILTINS:
            scan_paths = [self._builtin_path]
        elif scope == DiscoveryScope.CUSTOM:
            scan_paths = [Path.cwd() / "skills"]
        else:
            scan_paths = [self._builtin_path, Path.cwd() / "skills"]

        discovered = []

        # Scan for skills
        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            for item in scan_path.iterdir():
                if item.is_dir():
                    manifest_path = item / "skill.yaml"
                    if manifest_path.exists():
                        discovered.append(item.name)

        discovery_context.skills_discovered = len(discovered)
        discovery_context.discovered_skills = discovered
        discovery_context.completed_at = datetime.now().isoformat()

        self._context_history.append(discovery_context)

        return f"Discovered {len(discovered)} skill(s): {discovered[:5]}"

    async def _extract_metadata(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract metadata from skill."""
        skill_name = context.get("skill_name")
        skill_path = context.get("skill_path", "")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        # Determine path
        if not skill_path:
            skill_path = self._builtin_path / skill_name
        else:
            skill_path = Path(skill_path)

        manifest_path = skill_path / "skill.yaml"

        if not manifest_path.exists():
            return f"Error: Manifest not found for '{skill_name}'"

        # Parse manifest
        import yaml

        try:
            manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

            metadata = SkillMetadata(
                skill_name=skill_name,
                skill_path=str(skill_path),
                capabilities=manifest_data.get("capabilities", []),
                dependencies=manifest_data.get("dependencies", []),
                tags=manifest_data.get("tags", []),
                description=manifest_data.get("description", ""),
                version=manifest_data.get("version", ""),
                author=manifest_data.get("author", ""),
                extraction_context={
                    "workflow_id": workflow_id,
                },
            )

            self._metadata_cache[metadata.metadata_id] = metadata

            return f"Extracted metadata for '{skill_name}': {len(metadata.capabilities)} capability(ies)"

        except Exception as e:
            return f"Error extracting metadata: {e}"

    async def _generate_documentation(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate documentation for a skill."""
        skill_name = context.get("skill_name")
        metadata_id = context.get("metadata_id")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not skill_name:
            return "Error: skill_name is required"

        # Get metadata if provided
        metadata = None
        if metadata_id:
            metadata = self._metadata_cache.get(metadata_id)

        if not metadata:
            # Extract metadata first
            result = await self._extract_metadata({
                "skill_name": skill_name,
                "workflow_id": workflow_id,
            }, execution_context)

            # Get the extracted metadata
            for meta in self._metadata_cache.values():
                if meta.skill_name == skill_name:
                    metadata = meta
                    break

        # Generate documentation
        documentation = SkillDocumentation(
            skill_name=skill_name,
            overview=f"# {skill_name}\n\n{metadata.description if metadata else 'No description available'}",
            capabilities=self._generate_capabilities_section(metadata),
            usage=self._generate_usage_section(skill_name, metadata),
            examples=self._generate_examples_section(skill_name),
            api_reference=self._generate_api_section(skill_name, metadata),
            generation_context={
                "workflow_id": workflow_id,
                "metadata_id": metadata.metadata_id if metadata else "",
            },
        )

        self._documentation_cache[documentation.doc_id] = documentation

        return f"Generated documentation for '{skill_name}'"

    async def _get_capabilities(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get capabilities for a skill."""
        skill_name = context.get("skill_name")

        if not skill_name:
            return "Error: skill_name is required"

        # Find metadata
        for metadata in self._metadata_cache.values():
            if metadata.skill_name == skill_name:
                return f"Capabilities: {metadata.capabilities}"

        return f"Capabilities not found for '{skill_name}'"

    async def _search_skills(self, context: dict[str, Any], execution_context: Any) -> str:
        """Search for skills by criteria."""
        criteria = context.get("criteria", {})

        matching = []

        for metadata in self._metadata_cache.values():
            match = True

            # Filter by capability
            if "capability" in criteria:
                if criteria["capability"] not in metadata.capabilities:
                    match = False

            # Filter by tag
            if "tag" in criteria:
                if criteria["tag"] not in metadata.tags:
                    match = False

            # Filter by name pattern
            if "name_pattern" in criteria:
                import re
                pattern = criteria["name_pattern"]
                if not re.search(pattern, metadata.skill_name, re.IGNORECASE):
                    match = False

            if match:
                matching.append(metadata.skill_name)

        return f"Found {len(matching)} matching skill(s)"

    async def _get_discovery_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get discovery context."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for discovery_context in self._context_history:
            if discovery_context.context_id == context_id:
                return (
                    f"Discovery context '{context_id}': "
                    f"{discovery_context.skills_discovered} skill(s), "
                    f"scope={discovery_context.discovery_scope.value}"
                )

        return f"Error: Discovery context '{context_id}' not found"

    async def _get_metadata(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get metadata by ID or skill name."""
        metadata_id = context.get("metadata_id")
        skill_name = context.get("skill_name")

        if metadata_id:
            metadata = self._metadata_cache.get(metadata_id)
            if metadata:
                return f"Metadata for '{metadata.skill_name}': {len(metadata.capabilities)} capabilities"
            return f"Error: Metadata '{metadata_id}' not found"

        if skill_name:
            for metadata in self._metadata_cache.values():
                if metadata.skill_name == skill_name:
                    return f"Metadata: {len(metadata.capabilities)} capabilities, {len(metadata.dependencies)} dependencies"

        return "Error: Specify metadata_id or skill_name"

    async def _get_documentation(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get documentation by ID or skill name."""
        doc_id = context.get("doc_id")
        skill_name = context.get("skill_name")

        if doc_id:
            doc = self._documentation_cache.get(doc_id)
            if doc:
                return f"Documentation for '{doc.skill_name}': {len(doc.overview)} char overview"
            return f"Error: Documentation '{doc_id}' not found"

        if skill_name:
            for doc in self._documentation_cache.values():
                if doc.skill_name == skill_name:
                    return f"Documentation: {len(doc.overview)} char overview, {len(doc.usage)} char usage"

        return "Error: Specify doc_id or skill_name"

    def _generate_capabilities_section(self, metadata: SkillMetadata | None) -> str:
        """Generate capabilities documentation section."""
        if not metadata or not metadata.capabilities:
            return "## Capabilities\n\nNo specific capabilities documented."

        lines = ["## Capabilities\n\n"]
        for cap in metadata.capabilities:
            lines.append(f"- `{cap}`")
        return "\n".join(lines)

    def _generate_usage_section(self, skill_name: str, metadata: SkillMetadata | None) -> str:
        """Generate usage documentation section."""
        return f"""## Usage

The `{skill_name}` skill can be used via the skill system.

```python
# Example usage
from claude_playwright_agent.skills import get_skill

skill = get_skill("{skill_name}")
if skill and skill.enabled:
    # Use skill
    pass
```
"""

    def _generate_examples_section(self, skill_name: str) -> str:
        """Generate examples documentation section."""
        return f"""## Examples

### Basic Usage

```python
# Load and use the skill
await agent.run("{skill_name}", {{
    "task": "example_task",
    "context": {{}}
}})
```
"""

    def _generate_api_section(self, skill_name: str, metadata: SkillMetadata | None) -> str:
        """Generate API reference section."""
        sections = ["## API Reference\n\n"]
        sections.append(f"### Skill: {skill_name}\n\n")
        if metadata:
            sections.append(f"- **Version**: {metadata.version}\n")
            sections.append(f"- **Author**: {metadata.author}\n")
            sections.append(f"- **Dependencies**: {', '.join(metadata.dependencies) or 'none'}\n")
        return "".join(sections)

    def get_metadata_cache(self) -> dict[str, SkillMetadata]:
        """Get metadata cache."""
        return self._metadata_cache.copy()

    def get_documentation_cache(self) -> dict[str, SkillDocumentation]:
        """Get documentation cache."""
        return self._documentation_cache.copy()

    def get_context_history(self) -> list[DiscoveryContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

