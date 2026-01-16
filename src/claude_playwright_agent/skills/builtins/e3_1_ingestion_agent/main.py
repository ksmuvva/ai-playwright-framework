"""
E3.1 - Ingestion Agent Skill.

This skill provides Playwright recording ingestion:
- Recording file ingestion with context
- File validation and metadata extraction
- Context propagation through pipeline
- Integration with parser and logging
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class IngestionContext:
    """
    Context for recording ingestion.

    Attributes:
        ingestion_id: Unique ingestion identifier
        workflow_id: Associated workflow ID
        recording_path: Path to recording file
        recording_name: Name of the recording
        file_hash: Hash of the recording file
        file_size: Size of the recording file
        ingestion_started: When ingestion started
        ingestion_completed: When ingestion completed
        pipeline_stage: Current pipeline stage
        previous_context: Context from previous stage
        metadata: Additional ingestion metadata
        error_context: Error information if ingestion failed
    """

    ingestion_id: str = field(default_factory=lambda: f"ingest_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_path: str = ""
    recording_name: str = ""
    file_hash: str = ""
    file_size: int = 0
    ingestion_started: str = field(default_factory=lambda: datetime.now().isoformat())
    ingestion_completed: str = ""
    pipeline_stage: str = "initialized"
    previous_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_context: dict[str, Any] = field(default_factory=dict)

    def advance_stage(self, new_stage: str) -> None:
        """Advance to the next pipeline stage."""
        self.previous_context[self.pipeline_stage] = {
            "completed_at": datetime.now().isoformat(),
        }
        self.pipeline_stage = new_stage
        self.metadata[f"entered_{new_stage}_at"] = datetime.now().isoformat()

    def set_error(self, error_message: str, stage: str = "") -> None:
        """Record error context."""
        self.error_context = {
            "message": error_message,
            "stage": stage or self.pipeline_stage,
            "timestamp": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ingestion_id": self.ingestion_id,
            "workflow_id": self.workflow_id,
            "recording_path": self.recording_path,
            "recording_name": self.recording_name,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "ingestion_started": self.ingestion_started,
            "ingestion_completed": self.ingestion_completed,
            "pipeline_stage": self.pipeline_stage,
            "previous_context": self.previous_context,
            "metadata": self.metadata,
            "error_context": self.error_context,
        }


@dataclass
class IngestionResult:
    """
    Result of recording ingestion.

    Attributes:
        success: Whether ingestion succeeded
        ingestion_id: Ingestion identifier
        recording_path: Path to recording file
        recording_data: Parsed recording data
        summary: Ingestion summary
        context: Final ingestion context
        next_stages: Recommended next pipeline stages
    """

    success: bool
    ingestion_id: str
    recording_path: str = ""
    recording_data: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    context: IngestionContext | None = None
    next_stages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "ingestion_id": self.ingestion_id,
            "recording_path": self.recording_path,
            "recording_data": self.recording_data,
            "summary": self.summary,
            "context": self.context.to_dict() if self.context else None,
            "next_stages": self.next_stages,
        }


class IngestionAgent(BaseAgent):
    """
    Recording Ingestion Agent.

    This agent provides:
    1. Recording file ingestion with context
    2. File validation and metadata extraction
    3. Context propagation through pipeline
    4. Integration with parser and logging
    """

    name = "e3_1_ingestion_agent"
    version = "1.0.0"
    description = "E3.1 - Ingestion Agent"

    def __init__(self, **kwargs) -> None:
        """Initialize the ingestion agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a E3.1 - Ingestion Agent agent for the Playwright test automation framework. You help users with e3.1 - ingestion agent tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._active_ingestions: dict[str, IngestionContext] = {}
        self._ingestion_history: list[IngestionContext] = []

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
        Execute ingestion task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the ingestion operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            # Create minimal context if not provided
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "ingest_file":
            return await self._ingest_file(context, execution_context)
        elif task_type == "validate_file":
            return await self._validate_file(context, execution_context)
        elif task_type == "extract_metadata":
            return await self._extract_metadata(context, execution_context)
        elif task_type == "get_ingestion_status":
            return await self._get_ingestion_status(context, execution_context)
        elif task_type == "abort_ingestion":
            return await self._abort_ingestion(context, execution_context)
        elif task_type == "get_ingestion_history":
            return await self._get_ingestion_history(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _ingest_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Ingest a recording file with full context tracking."""
        recording_path = context.get("recording_path")
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not recording_path:
            return "Error: recording_path is required"

        path = Path(recording_path)
        if not path.exists():
            return f"Error: Recording file not found: {recording_path}"

        # Create ingestion context
        ingestion_context = IngestionContext(
            workflow_id=workflow_id,
            recording_path=str(path.absolute()),
            recording_name=path.stem,
            file_size=path.stat().st_size,
            metadata={
                "ingested_by": getattr(execution_context, "task_id", execution_context.get("task_id", "unknown")),
                "project_path": str(path.parent.parent),
            },
        )

        # Calculate file hash
        try:
            file_content = path.read_bytes()
            ingestion_context.file_hash = hashlib.sha256(file_content).hexdigest()
        except Exception as e:
            ingestion_context.set_error(f"Failed to calculate file hash: {e}", "file_hash")
            return f"Error: {e}"

        # Store active ingestion
        self._active_ingestions[ingestion_context.ingestion_id] = ingestion_context
        ingestion_context.advance_stage("validated")

        # Parse recording (would call E3.2 skill in full implementation)
        from claude_playwright_agent.agents.playwright_parser import parse_recording

        try:
            parsed = parse_recording(path)
            ingestion_context.advance_stage("parsed")

            # Create result
            result = IngestionResult(
                success=True,
                ingestion_id=ingestion_context.ingestion_id,
                recording_path=str(path),
                recording_data=parsed.__dict__ if hasattr(parsed, "__dict__") else {},
                summary={
                    "test_name": getattr(parsed, "test_name", path.stem),
                    "total_actions": len(getattr(parsed, "actions", [])),
                    "unique_selectors": len(getattr(parsed, "selectors_used", [])),
                    "urls_visited": len(getattr(parsed, "urls_visited", [])),
                    "file_size": ingestion_context.file_size,
                },
                context=ingestion_context,
                next_stages=["action_extraction", "selector_analysis", "deduplication"],
            )

            ingestion_context.ingestion_completed = datetime.now().isoformat()
            ingestion_context.advance_stage("completed")

            # Move to history
            self._ingestion_history.append(ingestion_context)
            del self._active_ingestions[ingestion_context.ingestion_id]

            return f"Recording '{ingestion_context.recording_name}' ingested successfully as '{ingestion_context.ingestion_id}'"

        except Exception as e:
            ingestion_context.set_error(str(e), "parsing")
            return f"Error parsing recording: {e}"

    async def _validate_file(self, context: dict[str, Any], execution_context: Any) -> str:
        """Validate a recording file."""
        recording_path = context.get("recording_path")

        if not recording_path:
            return "Error: recording_path is required"

        path = Path(recording_path)

        # Validate file exists
        if not path.exists():
            return f"Error: File not found: {recording_path}"

        # Validate file extension
        if path.suffix != ".js":
            return f"Error: Unsupported file type: {path.suffix}"

        # Validate file size
        max_size = context.get("max_file_size", 10 * 1024 * 1024)  # 10MB default
        file_size = path.stat().st_size
        if file_size > max_size:
            return f"Error: File too large: {file_size} > {max_size}"

        return f"File '{recording_path}' is valid ({file_size} bytes)"

    async def _extract_metadata(self, context: dict[str, Any], execution_context: Any) -> str:
        """Extract metadata from a recording file."""
        recording_path = context.get("recording_path")

        if not recording_path:
            return "Error: recording_path is required"

        path = Path(recording_path)

        if not path.exists():
            return f"Error: File not found: {recording_path}"

        metadata = {
            "file_name": path.name,
            "file_stem": path.stem,
            "file_size": path.stat().st_size,
            "created": datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }

        return f"Metadata extracted: {len(metadata)} field(s)"

    async def _get_ingestion_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get status of an ingestion."""
        ingestion_id = context.get("ingestion_id")

        if not ingestion_id:
            return "Error: ingestion_id is required"

        if ingestion_id not in self._active_ingestions:
            return f"Error: Ingestion '{ingestion_id}' not found"

        ingestion_context = self._active_ingestions[ingestion_id]

        return (
            f"Ingestion '{ingestion_id}': stage={ingestion_context.pipeline_stage}, "
            f"recording={ingestion_context.recording_name}, "
            f"workflow={ingestion_context.workflow_id}"
        )

    async def _abort_ingestion(self, context: dict[str, Any], execution_context: Any) -> str:
        """Abort an active ingestion."""
        ingestion_id = context.get("ingestion_id")

        if not ingestion_id:
            return "Error: ingestion_id is required"

        if ingestion_id not in self._active_ingestions:
            return f"Error: Ingestion '{ingestion_id}' not found"

        ingestion_context = self._active_ingestions[ingestion_id]
        ingestion_context.set_error("Ingestion aborted by user", ingestion_context.pipeline_stage)
        ingestion_context.ingestion_completed = datetime.now().isoformat()

        # Move to history
        self._ingestion_history.append(ingestion_context)
        del self._active_ingestions[ingestion_id]

        return f"Ingestion '{ingestion_id}' aborted"

    async def _get_ingestion_history(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get ingestion history."""
        limit = context.get("limit", 10)

        history = self._ingestion_history[-limit:]

        return f"Ingestion history: {len(history)} record(s)"

    def get_ingestion_context(self, ingestion_id: str) -> IngestionContext | None:
        """Get ingestion context by ID."""
        return self._active_ingestions.get(ingestion_id)

    def get_active_ingestions(self) -> dict[str, IngestionContext]:
        """Get all active ingestions."""
        return self._active_ingestions.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

