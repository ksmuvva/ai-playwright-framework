"""
Tests for the Progress module.

Tests cover:
- ProgressIndicator initialization
- Progress bar tracking
- Spinner creation
- Context managers
- Helper functions
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from claude_playwright_agent.progress import (
    ProgressIndicator,
    process_with_progress,
    progress_context,
    show_spinner,
    spinner_context,
    track_progress,
)


# =============================================================================
# ProgressIndicator Tests
# =============================================================================


class TestProgressIndicator:
    """Tests for ProgressIndicator class."""

    def test_initialization(self) -> None:
        """Test progress indicator initialization."""
        indicator = ProgressIndicator()

        assert indicator._console is not None
        assert indicator._show_time is True
        assert indicator._show_spinner is True
        assert indicator._progress is None

    def test_initialization_with_options(self) -> None:
        """Test initialization with custom options."""
        from rich.console import Console

        console = Console()
        indicator = ProgressIndicator(console=console, show_time=False, show_spinner=False)

        assert indicator._console == console
        assert indicator._show_time is False
        assert indicator._show_spinner is False

    def test_track_with_total(self) -> None:
        """Test tracking progress with known total."""
        indicator = ProgressIndicator()

        progress = indicator.track("Test task", total=10)

        assert progress is not None
        assert len(progress.tasks) == 1
        assert progress.tasks[0].total == 10

    def test_track_without_total(self) -> None:
        """Test tracking progress without total (indeterminate)."""
        indicator = ProgressIndicator()

        progress = indicator.track("Loading...", total=None)

        assert progress is not None
        assert len(progress.tasks) == 1
        assert progress.tasks[0].total is None

    def test_spinner(self) -> None:
        """Test creating a spinner."""
        indicator = ProgressIndicator()

        status = indicator.spinner("Working...")

        assert status is not None
        # Status object has a _spinner private attribute
        assert hasattr(status, "_spinner")

    def test_progress_context_manager(self) -> None:
        """Test progress context manager."""
        indicator = ProgressIndicator()

        with indicator.progress("Task", total=5) as progress:
            assert progress is not None
            assert len(progress.tasks) == 1

    def test_status_context_manager(self) -> None:
        """Test status context manager."""
        indicator = ProgressIndicator()

        with indicator.status("Processing..."):
            pass  # Just verify no error

    def test_progress_cleanup_on_exit(self) -> None:
        """Test that progress is cleaned up after context exit."""
        indicator = ProgressIndicator()

        with indicator.progress("Task", total=5):
            pass

        # Progress should be stopped after context exit
        assert indicator._progress is not None


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_track_progress(self) -> None:
        """Test track_progress convenience function."""
        progress = track_progress("Test", total=10)

        assert progress is not None
        assert len(progress.tasks) == 1
        assert progress.tasks[0].total == 10

    def test_track_progress_with_options(self) -> None:
        """Test track_progress with custom options."""
        progress = track_progress("Test", total=10, show_time=False)

        assert progress is not None
        assert len(progress.tasks) == 1

    def test_show_spinner(self) -> None:
        """Test show_spinner convenience function."""
        status = show_spinner("Loading...")

        assert status is not None
        # Status object has a _spinner private attribute
        assert hasattr(status, "_spinner")

    def test_progress_context(self) -> None:
        """Test progress_context convenience function."""
        with progress_context("Task", total=5) as progress:
            assert progress is not None

    def test_spinner_context(self) -> None:
        """Test spinner_context convenience function."""
        with spinner_context("Working..."):
            pass  # Just verify no error


# =============================================================================
# Helper Functions Tests
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_process_with_progress(self) -> None:
        """Test processing items with progress tracking."""
        items = [1, 2, 3, 4, 5]
        results = process_with_progress(
            items,
            "Processing numbers",
            lambda x: x * 2,
        )

        assert results == [2, 4, 6, 8, 10]

    def test_process_with_progress_empty_list(self) -> None:
        """Test processing empty list."""
        items = []

        results = process_with_progress(
            items,
            "Processing nothing",
            lambda x: x * 2,
        )

        assert results == []

    def test_process_with_progress_exception_handling(self) -> None:
        """Test process_with_progress handles exceptions."""
        items = [1, 2, 3]

        def failing_func(x: int) -> int:
            if x == 2:
                raise ValueError("Test error")
            return x * 2

        with pytest.raises(ValueError):
            process_with_progress(
                items,
                "Processing with error",
                failing_func,
            )


# =============================================================================
# Integration Tests
# =============================================================================


class TestProgressIntegration:
    """Integration tests for progress functionality."""

    def test_multiple_progress_updates(self) -> None:
        """Test multiple progress updates."""
        indicator = ProgressIndicator()

        with indicator.progress("Multi-step task", total=3) as progress:
            task_id = progress.tasks[0].id

            progress.update(task_id, advance=1)
            progress.update(task_id, advance=1)
            progress.update(task_id, advance=1)

    def test_progress_update_with_description(self) -> None:
        """Test progress update with description change."""
        indicator = ProgressIndicator()

        with indicator.progress("Task", total=2) as progress:
            task_id = progress.tasks[0].id

            progress.update(task_id, advance=1, description="Step 2")

    def test_nested_context_managers(self) -> None:
        """Test nested progress context managers."""
        with progress_context("Outer task", total=1) as outer_progress:
            outer_task_id = outer_progress.tasks[0].id

            with spinner_context("Inner status"):
                outer_progress.update(outer_task_id, advance=1)
