"""
Visual Regression Testing Module for Claude Playwright Agent.

This module provides visual regression testing capabilities:
- Screenshot capture and comparison
- Baseline image management
- Diff generation and visualization
- Pixel-perfect and fuzzy matching
- Visual report generation
"""

from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import json


class ComparisonStatus(str, Enum):
    """Status of visual comparison."""
    IDENTICAL = "identical"
    SIMILAR = "similar"
    DIFFERENT = "different"
    ERROR = "error"


@dataclass
class ComparisonResult:
    """Result of visual comparison."""
    status: ComparisonStatus
    similarity_score: float  # 0.0 to 1.0
    diff_pixels: int
    total_pixels: int
    diff_percentage: float
    baseline_path: Optional[Path] = None
    current_path: Optional[Path] = None
    diff_path: Optional[Path] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "similarity_score": self.similarity_score,
            "diff_pixels": self.diff_pixels,
            "total_pixels": self.total_pixels,
            "diff_percentage": self.diff_percentage,
            "baseline_path": str(self.baseline_path) if self.baseline_path else None,
            "current_path": str(self.current_path) if self.current_path else None,
            "diff_path": str(self.diff_path) if self.diff_path else None,
            "metadata": self.metadata,
        }


@dataclass
class ScreenshotConfig:
    """Configuration for screenshot capture."""
    full_page: bool = True
    capture_beyond_viewport: bool = True
    animations: str = "disabled"  # disabled, allowed
    mask: list[dict[str, Any]] = field(default_factory=list)
    clip: Optional[dict[str, int]] = None
    timeout: int = 30000


class VisualRegressionEngine:
    """Engine for visual regression testing."""

    def __init__(
        self,
        baseline_dir: Path,
        output_dir: Path,
        threshold: float = 0.1,
        pixel_threshold: int = 10,
    ):
        """
        Initialize the visual regression engine.

        Args:
            baseline_dir: Directory for baseline images
            output_dir: Directory for output (current, diff) images
            threshold: Similarity threshold (0.0 to 1.0)
            pixel_threshold: Pixel difference threshold
        """
        self.baseline_dir = Path(baseline_dir)
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.pixel_threshold = pixel_threshold

        # Create directories
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "current").mkdir(exist_ok=True)
        (self.output_dir / "diff").mkdir(exist_ok=True)

    def get_baseline_path(self, name: str) -> Path:
        """Get path for baseline image."""
        return self.baseline_dir / f"{name}.png"

    def get_current_path(self, name: str) -> Path:
        """Get path for current screenshot."""
        return self.output_dir / "current" / f"{name}.png"

    def get_diff_path(self, name: str) -> Path:
        """Get path for diff image."""
        return self.output_dir / "diff" / f"{name}.png"

    def baseline_exists(self, name: str) -> bool:
        """Check if baseline exists."""
        return self.get_baseline_path(name).exists()

    def save_baseline(self, image_path: Path, name: str) -> Path:
        """
        Save an image as baseline.

        Args:
            image_path: Path to source image
            name: Baseline name

        Returns:
            Path to saved baseline
        """
        import shutil
        baseline_path = self.get_baseline_path(name)
        shutil.copy(image_path, baseline_path)
        return baseline_path

    def compare_images(
        self,
        baseline_path: Path,
        current_path: Path,
        name: str,
    ) -> ComparisonResult:
        """
        Compare two images.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            name: Test name for output files

        Returns:
            ComparisonResult with comparison details
        """
        try:
            from PIL import Image, ImageChops, ImageDraw

            # Load images
            baseline = Image.open(baseline_path)
            current = Image.open(current_path)

            # Ensure same size
            if baseline.size != current.size:
                # Resize to match baseline
                current = current.resize(baseline.size)

            # Calculate difference
            diff = ImageChops.difference(baseline, current)

            # Get statistics
            total_pixels = baseline.width * baseline.height
            diff_pixels = sum(1 for pixel in diff.getdata() if sum(pixel) > self.pixel_threshold * 3)
            diff_percentage = (diff_pixels / total_pixels) * 100
            similarity_score = 1.0 - (diff_percentage / 100.0)

            # Determine status
            if diff_pixels == 0:
                status = ComparisonStatus.IDENTICAL
            elif similarity_score >= (1.0 - self.threshold):
                status = ComparisonStatus.SIMILAR
            else:
                status = ComparisonStatus.DIFFERENT

            # Generate diff image
            diff_path = self.get_diff_path(name)
            if diff_pixels > 0:
                # Create colored diff image
                diff_colored = Image.new("RGB", baseline.size, (0, 0, 0))
                baseline_rgba = baseline.convert("RGBA")
                current_rgba = current.convert("RGBA")

                # Paste baseline as background
                diff_colored.paste(baseline, (0, 0))

                # Highlight differences in red
                diff_mask = diff.convert("L").point(lambda x: 255 if x > self.pixel_threshold else 0)
                diff_layer = Image.new("RGBA", baseline.size, (255, 0, 0, 128))
                diff_colored.paste(diff_layer, (0, 0), diff_mask)

                diff_colored.save(diff_path)
            else:
                # No diff, save baseline as reference
                baseline.save(diff_path)

            return ComparisonResult(
                status=status,
                similarity_score=similarity_score,
                diff_pixels=diff_pixels,
                total_pixels=total_pixels,
                diff_percentage=diff_percentage,
                baseline_path=baseline_path,
                current_path=current_path,
                diff_path=diff_path,
                metadata={
                    "baseline_size": baseline.size,
                    "current_size": current.size,
                },
            )

        except Exception as e:
            return ComparisonResult(
                status=ComparisonStatus.ERROR,
                similarity_score=0.0,
                diff_pixels=0,
                total_pixels=0,
                diff_percentage=0.0,
                baseline_path=baseline_path,
                current_path=current_path,
                metadata={"error": str(e)},
            )

    def compare(
        self,
        current_path: Path,
        name: str,
        update_baseline: bool = False,
    ) -> ComparisonResult:
        """
        Compare current screenshot with baseline.

        Args:
            current_path: Path to current screenshot
            name: Test name
            update_baseline: If True, update baseline with current

        Returns:
            ComparisonResult with comparison details
        """
        baseline_path = self.get_baseline_path(name)

        # If no baseline, create it
        if not baseline_path.exists() or update_baseline:
            self.save_baseline(current_path, name)
            return ComparisonResult(
                status=ComparisonStatus.IDENTICAL,
                similarity_score=1.0,
                diff_pixels=0,
                total_pixels=0,
                diff_percentage=0.0,
                baseline_path=baseline_path,
                current_path=current_path,
                metadata={"created": True},
            )

        # Compare with baseline
        return self.compare_images(baseline_path, current_path, name)

    def generate_report(self, results: list[ComparisonResult]) -> dict[str, Any]:
        """
        Generate a visual regression report.

        Args:
            results: List of comparison results

        Returns:
            Report dictionary
        """
        total = len(results)
        identical = sum(1 for r in results if r.status == ComparisonStatus.IDENTICAL)
        similar = sum(1 for r in results if r.status == ComparisonStatus.SIMILAR)
        different = sum(1 for r in results if r.status == ComparisonStatus.DIFFERENT)
        errors = sum(1 for r in results if r.status == ComparisonStatus.ERROR)

        avg_similarity = (
            sum(r.similarity_score for r in results) / total
            if total > 0 else 0.0
        )

        return {
            "summary": {
                "total": total,
                "identical": identical,
                "similar": similar,
                "different": different,
                "errors": errors,
                "pass_rate": ((identical + similar) / total * 100) if total > 0 else 0.0,
                "avg_similarity": avg_similarity,
            },
            "results": [r.to_dict() for r in results],
        }


class ScreenshotCapture:
    """Capture screenshots using Playwright."""

    @staticmethod
    def capture(
        page,
        name: str,
        output_dir: Path,
        config: ScreenshotConfig,
    ) -> Path:
        """
        Capture a screenshot.

        Args:
            page: Playwright Page object
            name: Screenshot name
            output_dir: Output directory
            config: Screenshot configuration

        Returns:
            Path to captured screenshot
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{name}.png"

        options = {
            "path": str(output_path),
            "full_page": config.full_page,
            "type": "png",
        }

        if config.animations == "disabled":
            options["animations"] = "disabled"

        if config.mask:
            options["mask"] = config.mask

        if config.clip:
            options["clip"] = config.clip

        page.screenshot(**options)
        return output_path

    @staticmethod
    def capture_element(
        page,
        selector: str,
        name: str,
        output_dir: Path,
        config: ScreenshotConfig,
    ) -> Path:
        """
        Capture a screenshot of an element.

        Args:
            page: Playwright Page object
            selector: Element selector
            name: Screenshot name
            output_dir: Output directory
            config: Screenshot configuration

        Returns:
            Path to captured screenshot
        """
        element = page.locator(selector)
        element.screenshot(path=str(output_dir / f"{name}.png"))
        return output_dir / f"{name}.png"


# Export main components
__all__ = [
    "VisualRegressionEngine",
    "ComparisonStatus",
    "ComparisonResult",
    "ScreenshotConfig",
    "ScreenshotCapture",
]
