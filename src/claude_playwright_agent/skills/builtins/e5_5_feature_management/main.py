"""
E5.5 - Feature File Management Skill.

This skill provides feature file management functionality:
- Feature file creation
- File content management
- Version tracking
- File lifecycle tracking
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class FileStatus(str, Enum):
    """Feature file status."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class FeatureFileMetadata:
    """
    Metadata for a feature file.

    Attributes:
        file_id: Unique file identifier
        file_name: File name
        file_path: Full file path
        feature_name: Feature name
        scenario_count: Number of scenarios
        last_modified: Last modification time
        file_status: File status
        version: File version
        checksum: File checksum
        metadata_context: Additional context
    """

    file_id: str = field(default_factory=lambda: f"file_{uuid.uuid4().hex[:8]}")
    file_name: str = ""
    file_path: str = ""
    feature_name: str = ""
    scenario_count: int = 0
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    file_status: FileStatus = FileStatus.DRAFT
    version: int = 1
    checksum: str = ""
    metadata_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "feature_name": self.feature_name,
            "scenario_count": self.scenario_count,
            "last_modified": self.last_modified,
            "file_status": self.file_status.value,
            "version": self.version,
            "checksum": self.checksum,
            "metadata_context": self.metadata_context,
        }


@dataclass
class FeatureFileContent:
    """
    Content of a feature file.

    Attributes:
        content_id: Unique content identifier
        raw_content: Raw Gherkin content
        feature_line: Feature declaration line
        description_lines: Description lines
        scenario_blocks: Scenario blocks
        background_block: Background block
        content_context: Context at content creation
        generated_at: When content was generated
    """

    content_id: str = field(default_factory=lambda: f"content_{uuid.uuid4().hex[:8]}")
    raw_content: str = ""
    feature_line: str = ""
    description_lines: list[str] = field(default_factory=list)
    scenario_blocks: list[str] = field(default_factory=list)
    background_block: str = ""
    content_context: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_id": self.content_id,
            "raw_content": self.raw_content,
            "feature_line": self.feature_line,
            "description_lines": self.description_lines,
            "scenario_blocks": self.scenario_blocks,
            "background_block": self.background_block,
            "content_context": self.content_context,
            "generated_at": self.generated_at,
        }


@dataclass
class FileVersion:
    """
    A version of a feature file.

    Attributes:
        version_id: Unique version identifier
        version_number: Version number
        file_content: File content at this version
        change_description: Description of changes
        created_at: When version was created
        created_by: What workflow created this version
        version_context: Context at version creation
    """

    version_id: str = field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:8]}")
    version_number: int = 1
    file_content: FeatureFileContent | None = None
    change_description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = ""
    version_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "file_content": self.file_content.to_dict() if self.file_content else None,
            "change_description": self.change_description,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "version_context": self.version_context,
        }


@dataclass
class FileManagementContext:
    """
    Context for file management operations.

    Attributes:
        operation_id: Unique operation identifier
        workflow_id: Associated workflow ID
        operation_type: Type of operation
        files_affected: Number of files affected
        version_before: Version before operation
        version_after: Version after operation
        operation_timestamp: When operation occurred
        context_preserved: Whether context was preserved
    """

    operation_id: str = field(default_factory=lambda: f"op_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    operation_type: str = ""
    files_affected: int = 0
    version_before: int = 0
    version_after: int = 0
    operation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "workflow_id": self.workflow_id,
            "operation_type": self.operation_type,
            "files_affected": self.files_affected,
            "version_before": self.version_before,
            "version_after": self.version_after,
            "operation_timestamp": self.operation_timestamp,
            "context_preserved": self.context_preserved,
        }


class FeatureFileManagementAgent(BaseAgent):
    """
    Feature File Management Agent.

    This agent provides:
    1. Feature file creation
    2. File content management
    3. Version tracking
    4. File lifecycle tracking
    """

    name = "e5_5_feature_management"
    version = "1.0.0"
    description = "E5.5 - Feature File Management"

    def __init__(self, **kwargs) -> None:
        """Initialize the feature file management agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E5.5 - Feature File Management agent for the Playwright test automation framework. You help users with e5.5 - feature file management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._file_registry: dict[str, FeatureFileMetadata] = {}
        self._content_registry: dict[str, FeatureFileContent] = {}
        self._version_history: dict[str, list[FileVersion]] = {}
        self._operation_history: list[FileManagementContext] = []

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
        Execute feature file management task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the management operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "create_feature_file":
            return await self._create_feature_file(context, execution_context)
        elif task_type == "save_feature_file":
            return await self._save_feature_file(context, execution_context)
        elif task_type == "load_feature_file":
            return await self._load_feature_file(context, execution_context)
        elif task_type == "update_content":
            return await self._update_content(context, execution_context)
        elif task_type == "create_version":
            return await self._create_version(context, execution_context)
        elif task_type == "get_file_metadata":
            return await self._get_file_metadata(context, execution_context)
        elif task_type == "get_file_content":
            return await self._get_file_content(context, execution_context)
        elif task_type == "get_management_context":
            return await self._get_management_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _create_feature_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a new feature file with context."""
        feature_name = context.get("feature_name", "Feature")
        scenarios = context.get("scenarios", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        output_dir = context.get("output_dir", "features")

        if not scenarios:
            return "Error: scenarios list is required"

        # Create file content
        content = FeatureFileContent(
            feature_line=f"Feature: {feature_name}",
            description_lines=["  Auto-generated from recording"],
            content_context={
                "workflow_id": workflow_id,
                "scenario_count": len(scenarios),
            },
        )

        # Generate scenario blocks
        for scenario in scenarios:
            scenario_name = scenario.get("name", "Scenario")
            steps = scenario.get("steps", [])

            block = f"  Scenario: {scenario_name}\n"
            for step in steps:
                keyword = step.get("keyword", "When")
                text = step.get("text", "")
                block += f"    {keyword} {text}\n"

            content.scenario_blocks.append(block)

        # Build raw content
        raw_lines = [content.feature_line]
        if content.description_lines:
            raw_lines.extend(content.description_lines)
        raw_lines.append("")
        raw_lines.extend(content.scenario_blocks)

        content.raw_content = "\n".join(raw_lines)

        # Create file metadata
        file_name = self._to_file_name(feature_name)
        metadata = FeatureFileMetadata(
            file_name=file_name,
            file_path=str(Path(output_dir) / file_name),
            feature_name=feature_name,
            scenario_count=len(scenarios),
            file_status=FileStatus.DRAFT,
            metadata_context={
                "workflow_id": workflow_id,
                "auto_generated": True,
            },
        )

        # Store registries
        self._file_registry[metadata.file_id] = metadata
        self._content_registry[content.content_id] = content
        self._version_history[metadata.file_id] = []

        return f"Created feature file: {metadata.file_name} ({metadata.scenario_count} scenario(s))"

    async def _save_feature_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Save feature file to disk."""
        file_id = context.get("file_id")

        if not file_id:
            return "Error: file_id is required"

        metadata = self._file_registry.get(file_id)
        if not metadata:
            return f"Error: File metadata '{file_id}' not found"

        # Find content
        content = None
        for c in self._content_registry.values():
            if c.content_context.get("workflow_id") == metadata.metadata_context.get("workflow_id"):
                content = c
                break

        if not content:
            return "Error: No content found for file"

        # Write to disk
        file_path = Path(metadata.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content.raw_content, encoding="utf-8")

        metadata.last_modified = datetime.now().isoformat()

        return f"Saved feature file to: {metadata.file_path}"

    async def _load_feature_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Load feature file from disk."""
        file_path = context.get("file_path")

        if not file_path:
            return "Error: file_path is required"

        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"

        content_text = path.read_text(encoding="utf-8")

        # Parse content
        content = FeatureFileContent(
            raw_content=content_text,
            content_context={
                "loaded_from": str(path),
            },
        )

        # Extract feature line
        for line in content_text.split("\n"):
            if line.startswith("Feature:"):
                content.feature_line = line
                break

        self._content_registry[content.content_id] = content

        return f"Loaded feature file: {file_path}"

    async def _update_content(self, context: dict[str, Any], execution_context: Any) -> str:
        """Update feature file content."""
        file_id = context.get("file_id")
        content_updates = context.get("content_updates", {})

        if not file_id:
            return "Error: file_id is required"

        metadata = self._file_registry.get(file_id)
        if not metadata:
            return f"Error: File metadata '{file_id}' not found"

        # Find and update content
        for content in self._content_registry.values():
            if content.content_context.get("workflow_id") == metadata.metadata_context.get("workflow_id"):
                for key, value in content_updates.items():
                    if hasattr(content, key):
                        setattr(content, key, value)

                # Regenerate raw content
                raw_lines = [content.feature_line]
                if content.description_lines:
                    raw_lines.extend(content.description_lines)
                raw_lines.append("")
                raw_lines.extend(content.scenario_blocks)

                content.raw_content = "\n".join(raw_lines)
                break

        metadata.last_modified = datetime.now().isoformat()

        return f"Updated content for file: {metadata.file_name}"

    async def _create_version(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a new version of feature file."""
        file_id = context.get("file_id")
        change_description = context.get("change_description", "")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not file_id:
            return "Error: file_id is required"

        # Get current version
        versions = self._version_history.get(file_id, [])
        current_version = len(versions) + 1

        # Find content
        content = None
        for c in self._content_registry.values():
            if c.content_context.get("workflow_id") == workflow_id:
                content = c
                break

        # Create version
        version = FileVersion(
            version_number=current_version,
            file_content=content,
            change_description=change_description,
            created_by=workflow_id,
            version_context={
                "file_id": file_id,
            },
        )

        versions.append(version)
        self._version_history[file_id] = versions

        # Update metadata
        metadata = self._file_registry.get(file_id)
        if metadata:
            metadata.version = current_version

        return f"Created version {current_version} for file"

    async def _get_file_metadata(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get file metadata."""
        file_id = context.get("file_id")

        if not file_id:
            return "Error: file_id is required"

        metadata = self._file_registry.get(file_id)
        if metadata:
            return (
                f"File '{metadata.file_name}': "
                f"status={metadata.file_status.value}, "
                f"version={metadata.version}, "
                f"{metadata.scenario_count} scenario(s)"
            )

        return f"Error: File metadata '{file_id}' not found"

    async def _get_file_content(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get file content."""
        content_id = context.get("content_id")

        if not content_id:
            return "Error: content_id is required"

        content = self._content_registry.get(content_id)
        if content:
            return f"Content: {len(content.raw_content)} character(s), {len(content.scenario_blocks)} scenario(s)"

        return f"Error: Content '{content_id}' not found"

    async def _get_management_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get management context."""
        operation_id = context.get("operation_id")

        if not operation_id:
            return "Error: operation_id is required"

        for management_context in self._operation_history:
            if management_context.operation_id == operation_id:
                return (
                    f"Operation '{operation_id}': "
                    f"{management_context.operation_type}, "
                    f"v{management_context.version_before} -> v{management_context.version_after}"
                )

        return f"Error: Management context '{operation_id}' not found"

    def _to_file_name(self, feature_name: str) -> str:
        """Convert feature name to file name."""
        import re

        # Convert to lowercase, replace spaces with underscores
        name = feature_name.lower().replace(" ", "_")
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)

        return f"{name}.feature"

    def get_file_registry(self) -> dict[str, FeatureFileMetadata]:
        """Get file registry."""
        return self._file_registry.copy()

    def get_content_registry(self) -> dict[str, FeatureFileContent]:
        """Get content registry."""
        return self._content_registry.copy()

    def get_version_history(self) -> dict[str, list[FileVersion]]:
        """Get version history."""
        return self._version_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

