"""
E6.1 - Advanced Recording Techniques Skill.

This skill provides advanced recording capabilities:
- Video recording
- Screenshot capture
- Trace recording
- Artifact management
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class RecordingType(str, Enum):
    """Recording types."""

    VIDEO = "video"
    SCREENSHOT = "screenshot"
    TRACE = "trace"
    HAR = "har"
    NETWORK = "network"


class CaptureTrigger(str, Enum):
    """Capture triggers."""

    ON_START = "on_start"
    ON_END = "on_end"
    ON_ERROR = "on_error"
    ON_STEP = "on_step"
    MANUAL = "manual"
    INTERVAL = "interval"


@dataclass
class RecordingArtifact:
    """
    A recording artifact.

    Attributes:
        artifact_id: Unique artifact identifier
        recording_type: Type of recording
        file_path: Path to artifact file
        file_size_bytes: File size in bytes
        duration_ms: Recording duration in milliseconds
        captured_at: When artifact was captured
        trigger: What triggered the capture
        context_id: Associated context ID
        test_name: Associated test name
        metadata: Additional metadata
    """

    artifact_id: str = field(default_factory=lambda: f"artifact_{uuid.uuid4().hex[:8]}")
    recording_type: RecordingType = RecordingType.VIDEO
    file_path: str = ""
    file_size_bytes: int = 0
    duration_ms: int = 0
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())
    trigger: CaptureTrigger = CaptureTrigger.MANUAL
    context_id: str = ""
    test_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "recording_type": self.recording_type.value,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "duration_ms": self.duration_ms,
            "captured_at": self.captured_at,
            "trigger": self.trigger.value,
            "context_id": self.context_id,
            "test_name": self.test_name,
            "metadata": self.metadata,
        }


@dataclass
class RecordingConfig:
    """
    Configuration for recording.

    Attributes:
        config_id: Unique config identifier
        record_video: Whether to record video
        record_screenshots: Whether to capture screenshots
        record_trace: Whether to record trace
        screenshot_triggers: When to capture screenshots
        video_quality: Video quality setting
        screenshot_format: Screenshot format (png, jpeg)
        trace_level: Trace detail level
        output_dir: Output directory for recordings
    """

    config_id: str = field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:8]}")
    record_video: bool = True
    record_screenshots: bool = True
    record_trace: bool = True
    screenshot_triggers: list[CaptureTrigger] = field(default_factory=list)
    video_quality: str = "medium"
    screenshot_format: str = "png"
    trace_level: str = "basic"
    output_dir: str = "artifacts/recordings"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "record_video": self.record_video,
            "record_screenshots": self.record_screenshots,
            "record_trace": self.record_trace,
            "screenshot_triggers": [t.value for t in self.screenshot_triggers],
            "video_quality": self.video_quality,
            "screenshot_format": self.screenshot_format,
            "trace_level": self.trace_level,
            "output_dir": self.output_dir,
        }


@dataclass
class RecordingSession:
    """
    A recording session.

    Attributes:
        session_id: Unique session identifier
        workflow_id: Associated workflow ID
        test_name: Test name
        started_at: When session started
        completed_at: When session completed
        artifacts: List of artifacts created
        config: Recording configuration used
        status: Session status
    """

    session_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    test_name: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    artifacts: list[RecordingArtifact] = field(default_factory=list)
    config: RecordingConfig = field(default_factory=RecordingConfig)
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "test_name": self.test_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "config": self.config.to_dict(),
            "status": self.status,
        }


@dataclass
class RecordingContext:
    """
    Context for recording operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        sessions_created: Number of sessions created
        artifacts_captured: Number of artifacts captured
        total_size_bytes: Total size of all artifacts
        session_history: List of recording sessions
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"rec_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    sessions_created: int = 0
    artifacts_captured: int = 0
    total_size_bytes: int = 0
    session_history: list[RecordingSession] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "sessions_created": self.sessions_created,
            "artifacts_captured": self.artifacts_captured,
            "total_size_bytes": self.total_size_bytes,
            "session_history": [s.to_dict() for s in self.session_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class AdvancedRecordingAgent(BaseAgent):
    """
    Advanced Recording Agent.

    This agent provides:
    1. Video recording
    2. Screenshot capture
    3. Trace recording
    4. Artifact management
    """

    name = "e6_1_advanced_recording"
    version = "1.0.0"
    description = "E6.1 - Advanced Recording Techniques"

    def __init__(self, **kwargs) -> None:
        """Initialize the advanced recording agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E6.1 - Advanced Recording Techniques agent for the Playwright test automation framework. You help users with e6.1 - advanced recording techniques tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[RecordingContext] = []
        self._session_registry: dict[str, RecordingSession] = {}
        self._artifact_registry: dict[str, RecordingArtifact] = {}

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
        Execute recording task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the recording operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "start_session":
            return await self._start_session(context, execution_context)
        elif task_type == "stop_session":
            return await self._stop_session(context, execution_context)
        elif task_type == "capture_screenshot":
            return await self._capture_screenshot(context, execution_context)
        elif task_type == "capture_video":
            return await self._capture_video(context, execution_context)
        elif task_type == "capture_trace":
            return await self._capture_trace(context, execution_context)
        elif task_type == "get_artifact":
            return await self._get_artifact(context, execution_context)
        elif task_type == "list_artifacts":
            return await self._list_artifacts(context, execution_context)
        elif task_type == "get_session":
            return await self._get_session(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _start_session(self, context: dict[str, Any], execution_context: Any) -> str:
        """Start a recording session."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        test_name = context.get("test_name", "")
        record_video = context.get("record_video", True)
        record_screenshots = context.get("record_screenshots", True)
        record_trace = context.get("record_trace", True)

        # Create config
        config = RecordingConfig(
            record_video=record_video,
            record_screenshots=record_screenshots,
            record_trace=record_trace,
        )

        # Create session
        session = RecordingSession(
            workflow_id=workflow_id,
            test_name=test_name,
            config=config,
        )

        self._session_registry[session.session_id] = session

        return f"Started recording session '{session.session_id}' for '{test_name}'"

    async def _stop_session(self, context: dict[str, Any], execution_context: Any) -> str:
        """Stop a recording session."""
        session_id = context.get("session_id")

        if not session_id:
            return "Error: session_id is required"

        session = self._session_registry.get(session_id)
        if not session:
            return f"Error: Session '{session_id}' not found"

        session.completed_at = datetime.now().isoformat()
        session.status = "completed"

        artifact_count = len(session.artifacts)
        total_size = sum(a.file_size_bytes for a in session.artifacts)

        return f"Stopped session '{session_id}': {artifact_count} artifact(s), {total_size} bytes"

    async def _capture_screenshot(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture a screenshot."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        session_id = context.get("session_id")
        test_name = context.get("test_name", "")
        trigger = context.get("trigger", CaptureTrigger.MANUAL)

        if isinstance(trigger, str):
            trigger = CaptureTrigger(trigger)

        # Create artifact
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{test_name}_{timestamp}.png"
        output_dir = context.get("output_dir", "artifacts/screenshots")
        file_path = str(Path(output_dir) / filename)

        artifact = RecordingArtifact(
            recording_type=RecordingType.SCREENSHOT,
            file_path=file_path,
            file_size_bytes=102400,  # Simulated
            trigger=trigger,
            context_id=workflow_id,
            test_name=test_name,
        )

        self._artifact_registry[artifact.artifact_id] = artifact

        # Add to session if provided
        if session_id:
            session = self._session_registry.get(session_id)
            if session:
                session.artifacts.append(artifact)

        return f"Captured screenshot: {filename} (ID: {artifact.artifact_id})"

    async def _capture_video(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture video recording."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        session_id = context.get("session_id")
        test_name = context.get("test_name", "")
        duration_ms = context.get("duration_ms", 5000)

        # Create artifact
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{test_name}_{timestamp}.webm"
        output_dir = context.get("output_dir", "artifacts/videos")
        file_path = str(Path(output_dir) / filename)

        artifact = RecordingArtifact(
            recording_type=RecordingType.VIDEO,
            file_path=file_path,
            file_size_bytes=duration_ms * 1024,  # Simulated
            duration_ms=duration_ms,
            trigger=CaptureTrigger.ON_END,
            context_id=workflow_id,
            test_name=test_name,
        )

        self._artifact_registry[artifact.artifact_id] = artifact

        # Add to session if provided
        if session_id:
            session = self._session_registry.get(session_id)
            if session:
                session.artifacts.append(artifact)

        return f"Captured video: {filename} ({duration_ms}ms, ID: {artifact.artifact_id})"

    async def _capture_trace(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture trace recording."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        session_id = context.get("session_id")
        test_name = context.get("test_name", "")

        # Create artifact
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{test_name}_{timestamp}.zip"
        output_dir = context.get("output_dir", "artifacts/traces")
        file_path = str(Path(output_dir) / filename)

        artifact = RecordingArtifact(
            recording_type=RecordingType.TRACE,
            file_path=file_path,
            file_size_bytes=204800,  # Simulated
            trigger=CaptureTrigger.ON_END,
            context_id=workflow_id,
            test_name=test_name,
        )

        self._artifact_registry[artifact.artifact_id] = artifact

        # Add to session if provided
        if session_id:
            session = self._session_registry.get(session_id)
            if session:
                session.artifacts.append(artifact)

        return f"Captured trace: {filename} (ID: {artifact.artifact_id})"

    async def _get_artifact(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get artifact by ID."""
        artifact_id = context.get("artifact_id")

        if not artifact_id:
            return "Error: artifact_id is required"

        artifact = self._artifact_registry.get(artifact_id)
        if artifact:
            size_kb = artifact.file_size_bytes / 1024
            return (
                f"Artifact '{artifact_id}': "
                f"{artifact.recording_type.value}, "
                f"{size_kb:.1f} KB, "
                f"{artifact.file_path}"
            )

        return f"Error: Artifact '{artifact_id}' not found"

    async def _list_artifacts(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all artifacts or filter by session."""
        session_id = context.get("session_id")
        recording_type = context.get("recording_type")

        artifacts = list(self._artifact_registry.values())

        if session_id:
            session = self._session_registry.get(session_id)
            if session:
                artifacts = session.artifacts

        if recording_type:
            if isinstance(recording_type, str):
                recording_type = RecordingType(recording_type)
            artifacts = [a for a in artifacts if a.recording_type == recording_type]

        if not artifacts:
            return "No artifacts found"

        output = f"Artifacts ({len(artifacts)}):\n"
        for artifact in artifacts:
            output += f"- {artifact.recording_type.value}: {artifact.file_path}\n"

        return output

    async def _get_session(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get session by ID."""
        session_id = context.get("session_id")

        if not session_id:
            return "Error: session_id is required"

        session = self._session_registry.get(session_id)
        if session:
            return (
                f"Session '{session_id}': "
                f"{session.test_name}, "
                f"{len(session.artifacts)} artifact(s), "
                f"status={session.status}"
            )

        return f"Error: Session '{session_id}' not found"

    def get_session_registry(self) -> dict[str, RecordingSession]:
        """Get session registry."""
        return self._session_registry.copy()

    def get_artifact_registry(self) -> dict[str, RecordingArtifact]:
        """Get artifact registry."""
        return self._artifact_registry.copy()

    def get_context_history(self) -> list[RecordingContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

