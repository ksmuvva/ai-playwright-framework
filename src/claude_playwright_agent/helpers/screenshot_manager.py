"""
Screenshot Manager Module.

Provides screenshot capture and comparison utilities.
Supports full-page screenshots, failure capture, and comparison reports.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import Page
from dataclasses import dataclass


@dataclass
class ScreenshotConfig:
    """Configuration for screenshot capture."""

    output_dir: str = "reports/screenshots"
    full_page: bool = True
    capture_on_failure: bool = True
    step_screenshots: bool = True
    comparison_enabled: bool = False
    threshold: float = 0.01


class ScreenshotManager:
    """
    Screenshot manager for capturing and managing test evidence.

    Features:
    - Named screenshot capture
    - Failure auto-capture
    - Step-by-step screenshots
    - Comparison reports
    - Organized output structure
    """

    def __init__(self, config: Optional[ScreenshotConfig] = None):
        """
        Initialize the screenshot manager.

        Args:
            config: Screenshot configuration
        """
        self.config = config or ScreenshotConfig()
        self.screenshots_dir = Path(self.config.output_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create screenshot directories if they don't exist."""
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        (self.screenshots_dir / "failures").mkdir(exist_ok=True)
        (self.screenshots_dir / "steps").mkdir(exist_ok=True)
        (self.screenshots_dir / "baseline").mkdir(exist_ok=True)
        (self.screenshots_dir / "diff").mkdir(exist_ok=True)

    async def capture_screenshot(
        self,
        page: Page,
        name: str,
        full_page: bool = None,
        output_dir: str = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Capture a screenshot with a given name.

        Args:
            page: Playwright page object
            name: Name for the screenshot (no extension)
            full_page: Whether to capture full page
            output_dir: Override output directory
            context: Additional context for filename

        Returns:
            Path to the captured screenshot
        """
        full_page = full_page if full_page is not None else self.config.full_page
        output_dir = Path(output_dir or self.screenshots_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_str = f"_{context['step']}" if context and "step" in context else ""
        filename = f"{name}{context_str}_{timestamp}.png"

        screenshot_path = output_dir / filename

        try:
            await page.screenshot(path=str(screenshot_path), full_page=full_page)
            return str(screenshot_path)
        except Exception as e:
            print(f"Failed to capture screenshot '{name}': {e}")
            return ""

    async def capture_on_failure(self, page: Page, test_name: str, error_message: str) -> str:
        """
        Capture screenshot when a test fails.

        Args:
            page: Playwright page object
            test_name: Name of the failing test
            error_message: Error message from the failure

        Returns:
            Path to the failure screenshot
        """
        if not self.config.capture_on_failure:
            return ""

        output_dir = self.screenshots_dir / "failures"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = "".join(c if c.isalnum() else "_" for c in test_name)
        filename = f"FAILURE_{safe_test_name}_{timestamp}.png"

        try:
            await page.screenshot(path=str(output_dir / filename), full_page=True)
            return str(output_dir / filename)
        except Exception:
            return ""

    async def capture_step_screenshot(self, page: Page, step_name: str, step_number: int) -> str:
        """
        Capture screenshot for a specific test step.

        Args:
            page: Playwright page object
            step_name: Name of the step
            step_number: Step number in the test

        Returns:
            Path to the step screenshot
        """
        if not self.config.step_screenshots:
            return ""

        context = {"step": str(step_number).zfill(2)}
        return await self.capture_screenshot(
            page=page,
            name=f"step_{step_name}",
            output_dir=str(self.screenshots_dir / "steps"),
            context=context,
        )

    async def create_comparison_report(
        self, baseline_name: str, current_name: str, output_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a comparison report between two screenshots.

        Note: This is a placeholder. Full visual regression requires
        additional libraries like Pillow or OpenCV.

        Args:
            baseline_name: Name of the baseline screenshot
            current_name: Name of the current screenshot
            output_name: Name for the diff output

        Returns:
            Dictionary with paths to comparison images
        """
        baseline_path = self.screenshots_dir / "baseline" / f"{baseline_name}.png"
        current_path = self.screenshots_dir / "steps" / f"{current_name}.png"
        diff_path = self.screenshots_dir / "diff"

        result = {
            "baseline": str(baseline_path) if baseline_path.exists() else None,
            "current": str(current_path) if current_path.exists() else None,
            "diff": None,
            "similarity": None,
        }

        if baseline_path.exists() and current_path.exists():
            try:
                from PIL import Image
                import math

                img1 = Image.open(baseline_path)
                img2 = Image.open(current_path)

                if img1.size != img2.size:
                    img2 = img2.resize(img1.size)

                diff = Image.new("RGB", img1.size, "white")
                pixels1 = img1.load()
                pixels2 = img2.load()
                diff_pixels = diff.load()

                total_diff = 0
                for y in range(img1.size[1]):
                    for x in range(img1.size[0]):
                        r1, g1, b1 = pixels1[x, y]
                        r2, g2, b2 = pixels2[x, y]

                        pixel_diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
                        total_diff += pixel_diff

                        if pixel_diff > 30:
                            diff_pixels[x, y] = (255, 0, 0)
                        else:
                            diff_pixels[x, y] = (r1, g1, b1)

                max_diff = img1.size[0] * img1.size[1] * 255 * 3
                similarity = 1 - (total_diff / max_diff)

                result["similarity"] = f"{similarity * 100:.2f}%"
                result["diff"] = str(diff_path / f"diff_{output_name or 'comparison'}.png")

                diff.save(result["diff"])

            except ImportError:
                result["diff"] = "PIL not available for comparison"
            except Exception as e:
                result["diff"] = f"Comparison error: {str(e)}"

        return result

    def get_screenshot_list(self, category: str = "steps") -> List[Dict[str, Any]]:
        """
        Get list of screenshots in a category.

        Args:
            category: Screenshot category (steps, failures, baseline)

        Returns:
            List of screenshot information dictionaries
        """
        category_dir = self.screenshots_dir / category
        if not category_dir.exists():
            return []

        screenshots = []
        for filepath in category_dir.glob("*.png"):
            stat = filepath.stat()
            screenshots.append(
                {
                    "name": filepath.stem,
                    "path": str(filepath),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                }
            )

        return sorted(screenshots, key=lambda x: x["created"], reverse=True)

    def calculate_checksum(self, filepath: str) -> str:
        """
        Calculate MD5 checksum of a screenshot file.

        Args:
            filepath: Path to the screenshot file

        Returns:
            MD5 checksum string
        """
        if not Path(filepath).exists():
            return ""

        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
