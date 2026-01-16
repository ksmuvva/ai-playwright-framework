"""
Tests for Visual Regression Module.

Tests cover:
- Screenshot capture
- Baseline management
- Image comparison
- Diff generation
- Report generation
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from claude_playwright_agent.visual_regression import (
    VisualRegressionEngine,
    ScreenshotCapture,
    ScreenshotConfig,
    ComparisonStatus,
    ComparisonResult,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for testing."""
    return tmp_path / "visual"


@pytest.fixture
def engine(temp_dir: Path) -> VisualRegressionEngine:
    """Create visual regression engine."""
    baseline_dir = temp_dir / "baseline"
    output_dir = temp_dir / "output"
    return VisualRegressionEngine(
        baseline_dir=baseline_dir,
        output_dir=output_dir,
        threshold=0.1,
    )


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    from PIL import Image

    img_path = tmp_path / "sample.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_image_different(tmp_path: Path) -> Path:
    """Create a different sample test image."""
    from PIL import Image

    img_path = tmp_path / "sample_different.png"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)
    return img_path


# =============================================================================
# VisualRegressionEngine Tests
# =============================================================================


class TestVisualRegressionEngine:
    """Tests for VisualRegressionEngine class."""

    def test_initialization(self, temp_dir: Path) -> None:
        """Test engine initialization."""
        engine = VisualRegressionEngine(
            baseline_dir=temp_dir / "baseline",
            output_dir=temp_dir / "output",
        )

        assert engine.baseline_dir == temp_dir / "baseline"
        assert engine.output_dir == temp_dir / "output"
        assert engine.threshold == 0.1
        assert engine.baseline_dir.exists()
        assert engine.output_dir.exists()

    def test_get_baseline_path(self, engine: VisualRegressionEngine) -> None:
        """Test getting baseline path."""
        path = engine.get_baseline_path("test_name")
        assert path == engine.baseline_dir / "test_name.png"

    def test_get_current_path(self, engine: VisualRegressionEngine) -> None:
        """Test getting current path."""
        path = engine.get_current_path("test_name")
        assert path == engine.output_dir / "current" / "test_name.png"

    def test_get_diff_path(self, engine: VisualRegressionEngine) -> None:
        """Test getting diff path."""
        path = engine.get_diff_path("test_name")
        assert path == engine.output_dir / "diff" / "test_name.png"

    def test_baseline_exists_false(self, engine: VisualRegressionEngine) -> None:
        """Test baseline_exists returns False when no baseline."""
        assert not engine.baseline_exists("nonexistent")

    def test_save_baseline(self, engine: VisualRegressionEngine, sample_image: Path) -> None:
        """Test saving baseline."""
        baseline_path = engine.save_baseline(sample_image, "test_baseline")

        assert baseline_path.exists()
        assert baseline_path == engine.get_baseline_path("test_baseline")
        assert engine.baseline_exists("test_baseline")

    def test_compare_creates_baseline_if_missing(
        self, engine: VisualRegressionEngine, sample_image: Path
    ) -> None:
        """Test compare creates baseline if missing."""
        result = engine.compare(sample_image, "new_test")

        assert result.status == ComparisonStatus.IDENTICAL
        assert result.metadata.get("created") is True
        assert engine.baseline_exists("new_test")

    def test_compare_identical_images(
        self, engine: VisualRegressionEngine, sample_image: Path
    ) -> None:
        """Test compare with identical images."""
        # First call creates baseline
        engine.compare(sample_image, "identical_test")

        # Second call compares with baseline
        result = engine.compare(sample_image, "identical_test")

        assert result.status == ComparisonStatus.IDENTICAL
        assert result.similarity_score == 1.0
        assert result.diff_pixels == 0

    def test_compare_different_images(
        self, engine: VisualRegressionEngine, sample_image: Path, sample_image_different: Path
    ) -> None:
        """Test compare with different images."""
        # Create baseline
        engine.compare(sample_image, "different_test")

        # Compare with different image
        result = engine.compare(sample_image_different, "different_test")

        assert result.status == ComparisonStatus.DIFFERENT
        assert result.similarity_score < 1.0
        assert result.diff_pixels > 0

    def test_compare_update_baseline(
        self, engine: VisualRegressionEngine, sample_image: Path, sample_image_different: Path
    ) -> None:
        """Test compare with update_baseline flag."""
        # Create baseline
        engine.compare(sample_image, "update_test")

        # Update with different image
        result = engine.compare(sample_image_different, "update_test", update_baseline=True)

        assert result.status == ComparisonStatus.IDENTICAL
        assert result.metadata.get("created") is True

    def test_generate_report(self, engine: VisualRegressionEngine) -> None:
        """Test generating comparison report."""
        results = [
            ComparisonResult(
                status=ComparisonStatus.IDENTICAL,
                similarity_score=1.0,
                diff_pixels=0,
                total_pixels=10000,
                diff_percentage=0.0,
            ),
            ComparisonResult(
                status=ComparisonStatus.DIFFERENT,
                similarity_score=0.85,
                diff_pixels=1500,
                total_pixels=10000,
                diff_percentage=15.0,
            ),
        ]

        report = engine.generate_report(results)

        assert report["summary"]["total"] == 2
        assert report["summary"]["identical"] == 1
        assert report["summary"]["different"] == 1
        assert report["summary"]["pass_rate"] == 50.0
        assert len(report["results"]) == 2


# =============================================================================
# ScreenshotConfig Tests
# =============================================================================


class TestScreenshotConfig:
    """Tests for ScreenshotConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = ScreenshotConfig()

        assert config.full_page is True
        assert config.animations == "disabled"
        assert config.mask == []
        assert config.clip is None
        assert config.timeout == 30000

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ScreenshotConfig(
            full_page=False,
            animations="allowed",
            timeout=60000,
        )

        assert config.full_page is False
        assert config.animations == "allowed"
        assert config.timeout == 60000


# =============================================================================
# ScreenshotCapture Tests
# =============================================================================


class TestScreenshotCapture:
    """Tests for ScreenshotCapture class."""

    def test_capture_creates_mock_page(
        self, temp_dir: Path, sample_image: Path
    ) -> None:
        """Test capture with mock page."""
        # Create mock page
        mock_page = MagicMock()
        mock_page.screenshot = MagicMock()

        config = ScreenshotConfig()
        ScreenshotCapture.capture(mock_page, "test", temp_dir, config)

        # Verify screenshot was called
        mock_page.screenshot.assert_called_once()
        call_args = mock_page.screenshot.call_args
        assert "path" in call_args.kwargs
        assert "test.png" in call_args.kwargs["path"]

    def test_capture_element(
        self, temp_dir: Path
    ) -> None:
        """Test capturing element screenshot."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_page.locator = MagicMock(return_value=mock_element)

        config = ScreenshotConfig()
        ScreenshotCapture.capture_element(
            mock_page, "#my-element", "element_test", temp_dir, config
        )

        # Verify locator was called
        mock_page.locator.assert_called_once_with("#my-element")
        # Verify element screenshot was called
        mock_element.screenshot.assert_called_once()


# =============================================================================
# ComparisonResult Tests
# =============================================================================


class TestComparisonResult:
    """Tests for ComparisonResult class."""

    def test_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = ComparisonResult(
            status=ComparisonStatus.DIFFERENT,
            similarity_score=0.85,
            diff_pixels=1500,
            total_pixels=10000,
            diff_percentage=15.0,
            metadata={"test": "value"},
        )

        data = result.to_dict()

        assert data["status"] == "different"
        assert data["similarity_score"] == 0.85
        assert data["diff_pixels"] == 1500
        assert data["total_pixels"] == 10000
        assert data["diff_percentage"] == 15.0
        assert data["metadata"]["test"] == "value"


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_compare_nonexistent_baseline(self, engine: VisualRegressionEngine) -> None:
        """Test compare with nonexistent baseline file."""
        # Create a fake current file
        current_path = engine.get_current_path("test")
        current_path.parent.mkdir(parents=True, exist_ok=True)

        from PIL import Image
        img = Image.new("RGB", (10, 10), color="white")
        img.save(current_path)

        # This should create baseline, not error
        result = engine.compare(current_path, "test")
        assert result.status == ComparisonStatus.IDENTICAL

    def test_empty_results_report(self, engine: VisualRegressionEngine) -> None:
        """Test report with no results."""
        report = engine.generate_report([])

        assert report["summary"]["total"] == 0
        assert report["summary"]["identical"] == 0
        assert report["summary"]["pass_rate"] == 0.0
        assert report["results"] == []

    def test_threshold_affects_status(
        self, engine: VisualRegressionEngine, sample_image: Path, sample_image_different: Path
    ) -> None:
        """Test that threshold affects comparison status."""
        # Create low-threshold engine (strict)
        strict_engine = VisualRegressionEngine(
            baseline_dir=engine.baseline_dir,
            output_dir=engine.output_dir,
            threshold=0.01,  # Very strict
        )

        # Create baseline
        strict_engine.compare(sample_image, "threshold_test")

        # Compare with different image
        result = strict_engine.compare(sample_image_different, "threshold_test")

        # With strict threshold, even small differences should fail
        assert result.status in (ComparisonStatus.DIFFERENT, ComparisonStatus.SIMILAR)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for visual regression."""

    def test_full_workflow(
        self, engine: VisualRegressionEngine, sample_image: Path
    ) -> None:
        """Test complete visual regression workflow."""
        test_name = "full_workflow_test"

        # Step 1: Create baseline
        result1 = engine.compare(sample_image, test_name)
        assert result1.status == ComparisonStatus.IDENTICAL

        # Step 2: Compare with same image (baseline exists)
        result2 = engine.compare(sample_image, test_name)
        assert result2.status == ComparisonStatus.IDENTICAL
        assert result2.baseline_path is not None

        # Step 3: Generate report
        report = engine.generate_report([result1, result2])
        assert report["summary"]["total"] == 2
        assert report["summary"]["pass_rate"] == 100.0

    def test_multiple_comparisons(
        self, engine: VisualRegressionEngine, sample_image: Path, sample_image_different: Path
    ) -> None:
        """Test comparing multiple screenshots."""
        results = []

        # Test 1: Create baseline
        results.append(engine.compare(sample_image, "test1"))

        # Test 2: Compare with same
        results.append(engine.compare(sample_image, "test1"))

        # Test 3: Different image
        results.append(engine.compare(sample_image_different, "test1"))

        # Test 4: New baseline
        results.append(engine.compare(sample_image, "test2"))

        report = engine.generate_report(results)

        assert report["summary"]["total"] == 4
        assert report["summary"]["identical"] >= 2
