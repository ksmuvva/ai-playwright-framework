"""
Progress indicators for long-running operations.

This module provides:
- Progress bars for tracked operations
- Spinners for indeterminate progress
- Status updates
- Context management for progress display
"""

from contextlib import contextmanager
from typing import Any, Callable, Iterator

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.status import Status


# =============================================================================
# Progress Context Manager
# =============================================================================


class ProgressIndicator:
    """
    Progress indicator for long-running operations.

    Features:
    - Progress bar with percentage
    - Spinner for indeterminate progress
    - Time elapsed/remaining
    - Custom status messages
    """

    def __init__(
        self,
        console: Console | None = None,
        show_time: bool = True,
        show_spinner: bool = True,
    ) -> None:
        """
        Initialize the progress indicator.

        Args:
            console: Console instance (uses default if None)
            show_time: Whether to show time columns
            show_spinner: Whether to show spinner
        """
        self._console = console or Console()
        self._show_time = show_time
        self._show_spinner = show_spinner
        self._progress: Progress | None = None

    def track(
        self,
        description: str,
        total: int | None = None,
    ) -> Progress:
        """
        Create a tracked progress bar.

        Args:
            description: Description of the task
            total: Total items (None for indeterminate)

        Returns:
            Progress instance
        """
        # Build columns list
        columns = []

        if self._show_spinner:
            columns.append(SpinnerColumn())

        columns.append(TextColumn("[progress.description]{task.description}"))

        if total is not None:
            columns.append(BarColumn())
            columns.append(TaskProgressColumn())

        if self._show_time:
            columns.append(TimeElapsedColumn())

            if total is not None:
                columns.append(TimeRemainingColumn())

        # Create progress instance
        self._progress = Progress(
            *columns,
            console=self._console,
            transient=False,
        )

        # Add task
        if total is not None:
            self._progress.add_task(description, total=total)
        else:
            self._progress.add_task(description, total=None)

        return self._progress

    @contextmanager
    def progress(
        self,
        description: str,
        total: int | None = None,
    ) -> Iterator[Progress]:
        """
        Context manager for progress tracking.

        Args:
            description: Description of the task
            total: Total items (None for indeterminate)

        Yields:
            Progress instance
        """
        progress = self.track(description, total=total)
        try:
            yield progress
        finally:
            progress.stop()

    def spinner(
        self,
        message: str,
    ) -> Status:
        """
        Create a spinner status.

        Args:
            message: Status message

        Returns:
            Status instance
        """
        return Status(message, console=self._console, spinner="dots")

    @contextmanager
    def status(
        self,
        message: str,
    ) -> Iterator[Status]:
        """
        Context manager for status display.

        Args:
            message: Status message

        Yields:
            Status instance
        """
        with self.spinner(message):
            yield


# =============================================================================
# Convenience Functions
# =============================================================================


def track_progress(
    description: str,
    total: int | None = None,
    console: Console | None = None,
    show_time: bool = True,
) -> Progress:
    """
    Create a progress bar for tracking.

    Args:
        description: Description of the task
        total: Total items (None for indeterminate)
        console: Console instance (uses default if None)
        show_time: Whether to show time columns

    Returns:
        Progress instance
    """
    indicator = ProgressIndicator(console=console, show_time=show_time)
    return indicator.track(description, total=total)


def show_spinner(
    message: str,
    console: Console | None = None,
) -> Status:
    """
    Show a spinner for indeterminate progress.

    Args:
        message: Status message
        console: Console instance (uses default if None)

    Returns:
        Status instance
    """
    indicator = ProgressIndicator(console=console)
    return indicator.spinner(message)


@contextmanager
def progress_context(
    description: str,
    total: int | None = None,
    console: Console | None = None,
) -> Iterator[Progress]:
    """
    Context manager for progress tracking.

    Args:
        description: Description of the task
        total: Total items (None for indeterminate)
        console: Console instance (uses default if None)

    Yields:
        Progress instance
    """
    indicator = ProgressIndicator(console=console)
    with indicator.progress(description, total=total) as progress:
        yield progress


@contextmanager
def spinner_context(
    message: str,
    console: Console | None = None,
) -> Iterator[Status]:
    """
    Context manager for status display.

    Args:
        message: Status message
        console: Console instance (uses default if None)

    Yields:
        Status instance
    """
    indicator = ProgressIndicator(console=console)
    with indicator.status(message):
        yield


# =============================================================================
# Helper Functions for Common Operations
# =============================================================================


def process_with_progress(
    items: list[Any],
    description: str,
    process_func: Callable[[Any], Any],
    console: Console | None = None,
) -> list[Any]:
    """
    Process items with progress tracking.

    Args:
        items: Items to process
        description: Description of the operation
        process_func: Function to process each item
        console: Console instance (uses default if None)

    Returns:
        List of processed results
    """
    results = []

    with progress_context(description, total=len(items), console=console) as progress:
        task_id = progress.tasks[0].id  # Get first task ID

        for item in items:
            result = process_func(item)
            results.append(result)
            progress.update(task_id, advance=1)

    return results


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "ProgressIndicator",
    "track_progress",
    "show_spinner",
    "progress_context",
    "spinner_context",
    "process_with_progress",
]
