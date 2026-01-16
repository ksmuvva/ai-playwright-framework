"""
E7.2 - Skill Manifest Parser Skill.

This skill provides manifest parsing functionality:
- YAML manifest parsing with context
- Manifest validation
- Checksum computation
- Parse error tracking
"""

import uuid
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from claude_playwright_agent.agents.base import BaseAgent


class ValidationSeverity(str, Enum):
    """Severity of validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ParseStage(str, Enum):
    """Manifest parsing stages."""

    INITIALIZED = "initialized"
    READING = "reading"
    PARSING = "parsing"
    VALIDATING = "validating"
    COMPUTING = "computing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ValidationError:
    """
    A validation error with context.

    Attributes:
        error_id: Unique error identifier
        field: Field with error
        message: Error message
        severity: Error severity
        validation_context: Context at validation time
        suggestion: Suggested fix
    """

    error_id: str = dataclass_field(default_factory=lambda: f"err_{uuid.uuid4().hex[:8]}")
    field: str = ""
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    validation_context: dict[str, Any] = dataclass_field(default_factory=lambda: {})
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "validation_context": self.validation_context,
            "suggestion": self.suggestion,
        }


@dataclass
class ParsedManifest:
    """
    A parsed manifest with context.

    Attributes:
        parse_id: Unique parse identifier
        manifest_path: Path to manifest file
        raw_content: Raw YAML content
        parsed_data: Parsed YAML data
        validation_errors: List of validation errors
        checksum: Computed checksum
        parse_stage: Current parsing stage
        parse_context: Context at parse time
        parsed_at: When manifest was parsed
    """

    parse_id: str = dataclass_field(default_factory=lambda: f"parse_{uuid.uuid4().hex[:8]}")
    manifest_path: str = ""
    raw_content: str = ""
    parsed_data: dict[str, Any] = dataclass_field(default_factory=dict)
    validation_errors: list[ValidationError] = dataclass_field(default_factory=list)
    checksum: str = ""
    parse_stage: ParseStage = ParseStage.INITIALIZED
    parse_context: dict[str, Any] = dataclass_field(default_factory=dict)
    parsed_at: str = dataclass_field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parse_id": self.parse_id,
            "manifest_path": self.manifest_path,
            "parsed_data": self.parsed_data,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "checksum": self.checksum,
            "parse_stage": self.parse_stage.value,
            "parse_context": self.parse_context,
            "parsed_at": self.parsed_at,
        }


@dataclass
class ParserContext:
    """
    Context for manifest parsing operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        manifests_parsed: Number of manifests parsed
        manifests_failed: Number of manifests that failed
        total_errors: Total validation errors
        parse_history: List of parse operations
        started_at: When context was created
        completed_at: When context was completed
        context_preserved: Whether context was preserved
    """

    context_id: str = dataclass_field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    manifests_parsed: int = 0
    manifests_failed: int = 0
    total_errors: int = 0
    parse_history: list[str] = dataclass_field(default_factory=list)
    started_at: str = dataclass_field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "manifests_parsed": self.manifests_parsed,
            "manifests_failed": self.manifests_failed,
            "total_errors": self.total_errors,
            "parse_history": self.parse_history,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class ManifestParserAgent(BaseAgent):
    """
    Manifest Parser Agent.

    This agent provides:
    1. YAML manifest parsing with context
    2. Manifest validation
    3. Checksum computation
    4. Parse error tracking
    """

    name = "e7_2_manifest_parser"
    version = "1.0.0"
    description = "E7.2 - Skill Manifest Parser"

    # Required fields in manifest
    REQUIRED_FIELDS = ["name", "version", "description"]

    def __init__(self, **kwargs) -> None:
        """Initialize the manifest parser agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E7.2 - Skill Manifest Parser agent for the Playwright test automation framework. You help users with e7.2 - skill manifest parser tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[ParserContext] = []
        self._parsed_manifests: dict[str, ParsedManifest] = {}

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
        Execute manifest parsing task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the parsing operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "parse_manifest":
            return await self._parse_manifest(context, execution_context)
        elif task_type == "validate_manifest":
            return await self._validate_manifest(context, execution_context)
        elif task_type == "compute_checksum":
            return await self._compute_checksum(context, execution_context)
        elif task_type == "parse_string":
            return await self._parse_string(context, execution_context)
        elif task_type == "get_parsed_manifest":
            return await self._get_parsed_manifest(context, execution_context)
        elif task_type == "get_parser_context":
            return await self._get_parser_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _parse_manifest(self, context: dict[str, Any], execution_context: Any) -> str:
        """Parse a manifest file with context."""
        manifest_path = context.get("manifest_path")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not manifest_path:
            return "Error: manifest_path is required"

        path = Path(manifest_path)
        if not path.exists():
            return f"Error: Manifest file not found: {manifest_path}"

        # Create parsed manifest
        parsed = ParsedManifest(
            manifest_path=str(path),
            parse_context={
                "workflow_id": workflow_id,
            },
        )

        # Read file
        parsed.parse_stage = ParseStage.READING
        try:
            parsed.raw_content = path.read_text(encoding="utf-8")
        except Exception as e:
            parsed.parse_stage = ParseStage.FAILED
            parsed.validation_errors.append(ValidationError(
                field="file",
                message=f"Failed to read file: {e}",
                severity=ValidationSeverity.ERROR,
            ))
            return f"Error reading file: {e}"

        # Parse YAML
        parsed.parse_stage = ParseStage.PARSING
        try:
            parsed.parsed_data = yaml.safe_load(parsed.raw_content)
        except yaml.YAMLError as e:
            parsed.parse_stage = ParseStage.FAILED
            parsed.validation_errors.append(ValidationError(
                field="yaml",
                message=f"YAML parsing error: {e}",
                severity=ValidationSeverity.ERROR,
            ))
            return f"YAML parsing error: {e}"

        # Validate
        parsed.parse_stage = ParseStage.VALIDATING
        errors = self._validate_data(parsed.parsed_data)
        parsed.validation_errors = errors

        # Compute checksum
        parsed.parse_stage = ParseStage.COMPUTING
        parsed.checksum = self._compute_checksum_from_content(parsed.raw_content)

        # Complete
        parsed.parse_stage = ParseStage.COMPLETED
        parsed.parsed_at = datetime.now().isoformat()

        self._parsed_manifests[parsed.parse_id] = parsed

        if errors:
            return f"Parsed with {len(errors)} error(s)"

        return f"Parsed manifest: {parsed.parsed_data.get('name', 'unknown')}"

    async def _validate_manifest(self, context: dict[str, Any], execution_context: Any) -> str:
        """Validate a manifest."""
        manifest_data = context.get("manifest_data")

        if not manifest_data:
            return "Error: manifest_data is required"

        errors = self._validate_data(manifest_data)

        return f"Validation result: {len(errors)} error(s)"

    async def _compute_checksum(self, context: dict[str, Any], execution_context: Any) -> str:
        """Compute checksum for manifest."""
        content = context.get("content")

        if not content:
            return "Error: content is required"

        checksum = self._compute_checksum_from_content(content)

        return f"Checksum: {checksum[:16]}..."

    async def _parse_string(self, context: dict[str, Any], execution_context: Any) -> str:
        """Parse manifest from string."""
        content = context.get("content")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not content:
            return "Error: content is required"

        # Create parsed manifest
        parsed = ParsedManifest(
            raw_content=content,
            parse_context={
                "workflow_id": workflow_id,
                "from_string": True,
            },
        )

        # Parse YAML
        try:
            parsed.parsed_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return f"YAML parsing error: {e}"

        # Validate
        errors = self._validate_data(parsed.parsed_data)
        parsed.validation_errors = errors

        # Compute checksum
        parsed.checksum = self._compute_checksum_from_content(content)
        parsed.parse_stage = ParseStage.COMPLETED

        self._parsed_manifests[parsed.parse_id] = parsed

        if errors:
            return f"Parsed with {len(errors)} error(s)"

        return f"Parsed manifest from string: {parsed.parsed_data.get('name', 'unknown')}"

    async def _get_parsed_manifest(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get parsed manifest by ID."""
        parse_id = context.get("parse_id")

        if not parse_id:
            return "Error: parse_id is required"

        parsed = self._parsed_manifests.get(parse_id)
        if parsed:
            return (
                f"Manifest '{parsed.parsed_data.get('name', 'unknown')}': "
                f"{len(parsed.validation_errors)} error(s), "
                f"stage={parsed.parse_stage.value}"
            )

        return f"Error: Parsed manifest '{parse_id}' not found"

    async def _get_parser_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get parser context."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for parser_context in self._context_history:
            if parser_context.context_id == context_id:
                return (
                    f"Parser context '{context_id}': "
                    f"{parser_context.manifests_parsed} parsed, "
                    f"{parser_context.manifests_failed} failed"
                )

        return f"Error: Parser context '{context_id}' not found"

    def _validate_data(self, data: dict[str, Any]) -> list[ValidationError]:
        """Validate manifest data."""
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(ValidationError(
                    field=field,
                    message=f"Missing required field: {field}",
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Add '{field}: <value>' to manifest",
                ))

        # Validate field types
        if "name" in data:
            if not isinstance(data["name"], str):
                errors.append(ValidationError(
                    field="name",
                    message="Field 'name' must be a string",
                    severity=ValidationSeverity.ERROR,
                ))
            elif not data["name"][0].isalpha():
                errors.append(ValidationError(
                    field="name",
                    message="Field 'name' must start with a letter",
                    severity=ValidationSeverity.ERROR,
                ))

        if "version" in data and not isinstance(data["version"], str):
            errors.append(ValidationError(
                field="version",
                message="Field 'version' must be a string",
                severity=ValidationSeverity.ERROR,
            ))

        if "dependencies" in data:
            if not isinstance(data["dependencies"], list):
                errors.append(ValidationError(
                    field="dependencies",
                    message="Field 'dependencies' must be a list",
                    severity=ValidationSeverity.ERROR,
                ))

        return errors

    def _compute_checksum_from_content(self, content: str) -> str:
        """Compute checksum of content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()

    def get_parsed_manifests(self) -> dict[str, ParsedManifest]:
        """Get parsed manifests cache."""
        return self._parsed_manifests.copy()

    def get_context_history(self) -> list[ParserContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

