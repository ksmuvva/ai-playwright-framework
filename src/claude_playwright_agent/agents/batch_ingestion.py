"""
Batch recording ingestion for Claude Playwright Agent.

This module implements:
- Batch processing of multiple recordings
- Parallel ingestion with worker pools
- Progress tracking and reporting
- Error handling and recovery
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

# =============================================================================
# Batch Ingestion Types
# =============================================================================


class BatchStatus(str, Enum):
    """Status of batch ingestion."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class RecordingTask:
    """
    Single recording task in a batch.

    Attributes:
        path: Path to recording file
        status: Current status
        result: Processing result
        error: Error message if failed
        started_at: When processing started
        completed_at: When processing completed
    """

    path: Path
    status: BatchStatus = BatchStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class BatchResult:
    """
    Result of batch ingestion.

    Attributes:
        batch_id: Unique batch identifier
        status: Overall batch status
        tasks: List of all tasks
        total_tasks: Total number of tasks
        completed_tasks: Number of completed tasks
        failed_tasks: Number of failed tasks
        started_at: When batch started
        completed_at: When batch completed
    """

    batch_id: str
    status: BatchStatus = BatchStatus.PENDING
    tasks: list[RecordingTask] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_id": self.batch_id,
            "status": self.status.value,
            "total_tasks": len(self.tasks),
            "completed_tasks": sum(1 for t in self.tasks if t.status == BatchStatus.COMPLETED),
            "failed_tasks": sum(1 for t in self.tasks if t.status == BatchStatus.FAILED),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "tasks": [t.to_dict() for t in self.tasks],
        }


# =============================================================================
# Batch Ingestion Engine
# =============================================================================


class BatchIngestionEngine:
    """
    Engine for batch processing of Playwright recordings.

    Features:
    - Parallel processing with configurable workers
    - Progress tracking per recording
    - Error handling and recovery
    - Callback hooks for events
    - Resource-aware scheduling
    """

    def __init__(
        self,
        max_workers: int = 4,
        progress_callback: Callable[[BatchResult], Awaitable[None]] | None = None,
    ) -> None:
        """
        Initialize the batch engine.

        Args:
            max_workers: Maximum parallel workers
            progress_callback: Optional callback for progress updates
        """
        self._max_workers = max_workers
        self._progress_callback = progress_callback
        self._active_batches: dict[str, BatchResult] = {}

    async def ingest_batch(
        self,
        recording_paths: list[Path],
        process_func: Callable[[Path], Awaitable[dict[str, Any]]],
        batch_id: str = "",
        continue_on_error: bool = True,
    ) -> BatchResult:
        """
        Process a batch of recordings.

        Args:
            recording_paths: List of recording file paths
            process_func: Async function to process each recording
            batch_id: Optional batch identifier
            continue_on_error: Whether to continue on individual failures

        Returns:
            BatchResult with all task results
        """
        import uuid
        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:8]}"

        # Create batch result
        result = BatchResult(
            batch_id=batch_id,
            status=BatchStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )

        # Create tasks
        for path in recording_paths:
            result.tasks.append(RecordingTask(path=path))

        self._active_batches[batch_id] = result

        # Create semaphore to limit concurrent workers
        semaphore = asyncio.Semaphore(self._max_workers)

        async def process_task(task: RecordingTask) -> None:
            """Process a single task."""
            async with semaphore:
                try:
                    task.status = BatchStatus.RUNNING
                    task.started_at = datetime.now().isoformat()

                    # Process the recording
                    task_result = await process_func(task.path)
                    task.result = task_result
                    task.status = BatchStatus.COMPLETED

                except Exception as e:
                    task.status = BatchStatus.FAILED
                    task.error = str(e)

                    if not continue_on_error:
                        raise

                finally:
                    task.completed_at = datetime.now().isoformat()

                    # Notify progress callback
                    if self._progress_callback:
                        await self._progress_callback(result)

        # Run all tasks concurrently
        tasks = [process_task(t) for t in result.tasks]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            result.status = BatchStatus.FAILED
        else:
            # Determine final status
            failed = sum(1 for t in result.tasks if t.status == BatchStatus.FAILED)
            if failed == 0:
                result.status = BatchStatus.COMPLETED
            elif failed == len(result.tasks):
                result.status = BatchStatus.FAILED
            else:
                result.status = BatchStatus.PARTIAL

        result.completed_at = datetime.now().isoformat()

        # Notify final callback
        if self._progress_callback:
            await self._progress_callback(result)

        return result

    def get_batch_status(self, batch_id: str) -> BatchResult | None:
        """
        Get status of a batch.

        Args:
            batch_id: Batch identifier

        Returns:
            BatchResult or None if not found
        """
        return self._active_batches.get(batch_id)

    def get_all_batches(self) -> dict[str, BatchResult]:
        """Get all active and completed batches."""
        return self._active_batches.copy()


# =============================================================================
# Smart Recording Merger
# =============================================================================


class RecordingMerger:
    """
    Merge multiple recordings intelligently.

    Features:
    - Deduplicate common setup/teardown
    - Merge action sequences
    - Identify shared page contexts
    - Resolve conflicts
    """

    def __init__(self) -> None:
        """Initialize the merger."""

    async def merge_recordings(
        self,
        recording_paths: list[Path],
        output_path: Path,
        merge_strategy: str = "sequential",
    ) -> dict[str, Any]:
        """
        Merge multiple recordings into one.

        Args:
            recording_paths: List of recording file paths
            output_path: Where to write merged recording
            merge_strategy: How to merge (sequential, smart, etc.)

        Returns:
            Merge result with statistics
        """
        # Read all recordings
        recordings = []
        for path in recording_paths:
            try:
                content = path.read_text(encoding="utf-8")
                recordings.append({
                    "path": str(path),
                    "content": content,
                })
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to read {path}: {e}",
                }

        # Apply merge strategy
        if merge_strategy == "sequential":
            merged = self._merge_sequential(recordings)
        elif merge_strategy == "smart":
            merged = self._merge_smart(recordings)
        else:
            return {
                "success": False,
                "error": f"Unknown merge strategy: {merge_strategy}",
            }

        # Write merged recording
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(merged, encoding="utf-8")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write output: {e}",
            }

        return {
            "success": True,
            "input_recordings": len(recordings),
            "output_path": str(output_path),
            "merge_strategy": merge_strategy,
        }

    def _merge_sequential(self, recordings: list[dict[str, Any]]) -> str:
        """
        Merge recordings sequentially.

        Keeps all actions in order, with minimal deduplication.
        """
        merged_parts = []

        for i, recording in enumerate(recordings):
            content = recording["content"]

            if i == 0:
                # First recording - include everything
                merged_parts.append(content)
            else:
                # Subsequent recordings - exclude common setup
                # Remove duplicate goto/close commands
                lines = content.split('\n')
                filtered_lines = []

                for line in lines:
                    # Skip common setup that's already in merged
                    if 'page.goto' in line and i > 0:
                        continue
                    if 'browser.close' in line:
                        continue
                    if 'await context.close' in line:
                        continue

                    filtered_lines.append(line)

                merged_parts.append('\n'.join(filtered_lines))

        return '\n'.join(merged_parts)

    def _merge_smart(self, recordings: list[dict[str, Any]]) -> str:
        """
        Merge recordings intelligently.

        Analyzes and deduplicates actions across recordings.
        """
        # For now, use sequential merge
        # TODO: Implement smart deduplication based on action similarity
        return self._merge_sequential(recordings)

    def analyze_similarity(
        self,
        recording1: Path,
        recording2: Path,
    ) -> dict[str, Any]:
        """
        Analyze similarity between two recordings.

        Args:
            recording1: First recording path
            recording2: Second recording path

        Returns:
            Similarity analysis result
        """
        try:
            content1 = recording1.read_text(encoding="utf-8")
            content2 = recording2.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

        # Simple similarity based on common lines
        lines1 = set(content1.split('\n'))
        lines2 = set(content2.split('\n'))

        intersection = lines1 & lines2
        union = lines1 | lines2

        if not union:
            similarity = 0.0
        else:
            similarity = len(intersection) / len(union)

        return {
            "success": True,
            "similarity": round(similarity, 3),
            "common_lines": len(intersection),
            "total_unique_lines": len(union),
        }
