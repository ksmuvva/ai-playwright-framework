"""
Visual Regression Agent.

Provides visual regression testing capabilities:
- Baseline image management
- Screenshot comparison with pixel matching
- Diff image generation
- Threshold configuration
- Visual change detection
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from playwright.async_api import Page

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class VisualDiff:
    """Visual difference result."""

    baseline_path: str
    current_path: str
    diff_path: str
    similarity_percentage: float
    diff_percentage: float
    pixel_diff_count: int
    status: str


@dataclass
class VisualComparison:
    """Visual comparison result."""

    baseline_name: str
    current_screenshot: str
    baseline_screenshot: str
    diff_screenshot: Optional[str]
    is_match: bool
    diff_percentage: float
    threshold: float
    diffPixels: int
    total_pixels: int


class VisualRegressionAgent(BaseAgent):
    """
    Agent for visual regression testing and image comparison.

    Handles:
    - Baseline image capture and storage
    - Screenshot comparison with pixel matching
    - Diff image generation
    - Threshold-based pass/fail decisions
    - Baseline management (update, delete, list)
    """

    BASELINE_DIR = "visual_baseline"
    DIFF_DIR = "visual_diff"
    DEFAULT_THRESHOLD = 0.01

    def __init__(
        self,
        project_path: Optional[str] = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        """
        Initialize the visual regression agent.

        Args:
            project_path: Path to project root
            threshold: Default diff threshold (0.01 = 1%)
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._baseline_dir = self._project_path / self.BASELINE_DIR
        self._diff_dir = self._project_path / self.DIFF_DIR
        self._threshold = threshold
        self._ensure_directories()

        system_prompt = """You are the Visual Regression Testing Agent for Claude Playwright Agent.

Your role is to:
1. Capture and manage baseline screenshots
2. Compare current screenshots with baselines
3. Detect visual differences using pixel matching
4. Generate diff images highlighting changes
5. Manage threshold configurations

You provide:
- Pixel-accurate screenshot comparisons
- Detailed diff reports with metrics
- Visual diff images showing changes
- Recommendations for visual fixes"""

        super().__init__(system_prompt=system_prompt)

    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        self._baseline_dir.mkdir(parents=True, exist_ok=True)
        self._diff_dir.mkdir(parents=True, exist_ok=True)
        (self._baseline_dir / "metadata").mkdir(exist_ok=True)

    async def capture_baseline(
        self,
        page: Page,
        name: str,
        full_page: bool = True,
        viewport: Optional[dict[str, int]] = None,
    ) -> dict[str, Any]:
        """
        Capture a baseline screenshot.

        Args:
            page: Playwright page object
            name: Baseline name (used as filename)
            full_page: Whether to capture full page
            viewport: Optional viewport dimensions

        Returns:
            Baseline capture result with path
        """
        if viewport:
            await page.set_viewport_size(viewport)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self._baseline_dir / filename

        try:
            await page.screenshot(path=str(filepath), full_page=full_page)

            metadata = {
                "name": name,
                "filename": filename,
                "captured_at": datetime.now().isoformat(),
                "full_page": full_page,
                "viewport": viewport or {},
                "checksum": self._calculate_checksum(filepath),
            }

            metadata_path = self._baseline_dir / "metadata" / f"{name}.json"
            self._update_metadata(name, metadata)

            return {
                "success": True,
                "baseline_path": str(filepath),
                "name": name,
                "metadata": metadata,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to capture baseline: {e}",
                "name": name,
            }

    def _update_metadata(self, name: str, metadata: dict) -> None:
        """Update baseline metadata file."""
        metadata_path = self._baseline_dir / "metadata" / f"{name}.json"

        existing = {}
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                existing = json.load(f)

        existing[name] = metadata

        with open(metadata_path, "w") as f:
            json.dump(existing, f, indent=2)

    async def compare(
        self,
        current_screenshot: str,
        baseline_name: str,
        threshold: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Compare current screenshot with baseline.

        Args:
            current_screenshot: Path to current screenshot
            baseline_name: Name of baseline to compare against
            threshold: Optional override for diff threshold

        Returns:
            Comparison result with diff metrics
        """
        threshold = threshold or self._threshold

        baseline_files = list(self._baseline_dir.glob(f"{baseline_name}_*.png"))
        if not baseline_files:
            return {
                "success": False,
                "error": f"Baseline '{baseline_name}' not found",
                "baseline_name": baseline_name,
            }

        baseline_path = str(baseline_files[0])
        diff_path = str(
            self._diff_dir / f"diff_{baseline_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        try:
            diff_result = self._compare_images(baseline_path, current_screenshot, diff_path)

            comparison = VisualComparison(
                baseline_name=baseline_name,
                current_screenshot=current_screenshot,
                baseline_screenshot=baseline_path,
                diff_screenshot=diff_path if diff_result["diff_exists"] else None,
                is_match=diff_result["similarity"] >= (1 - threshold),
                diff_percentage=diff_result["diff_percentage"],
                threshold=threshold,
                diff_pixels=diff_result["diff_pixels"],
                total_pixels=diff_result["total_pixels"],
            )

            return {
                "success": True,
                "match": comparison.is_match,
                "baseline_name": baseline_name,
                "baseline_path": baseline_path,
                "current_path": current_screenshot,
                "diff_path": comparison.diff_screenshot,
                "similarity_percentage": round(comparison.similarity_percentage * 100, 2),
                "diff_percentage": round(comparison.diff_percentage * 100, 2),
                "diff_pixels": comparison.diff_pixels,
                "total_pixels": comparison.total_pixels,
                "threshold": threshold,
                "status": "passed" if comparison.is_match else "failed",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Comparison failed: {e}",
                "baseline_name": baseline_name,
            }

    def _compare_images(
        self, baseline_path: str, current_path: str, diff_path: str
    ) -> dict[str, Any]:
        """
        Compare two images and generate diff.

        Returns:
            Comparison metrics
        """
        try:
            from PIL import Image

            img1 = Image.open(baseline_path)
            img2 = Image.open(current_path)

            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            diff_img = Image.new("RGB", img1.size, "white")
            pixels1 = img1.load()
            pixels2 = img2.load()
            diff_pixels_img = diff_img.load()

            diff_pixels = 0
            total_pixels = img1.size[0] * img1.size[1]

            for y in range(img1.size[1]):
                for x in range(img1.size[0]):
                    r1, g1, b1 = pixels1[x, y]
                    r2, g2, b2 = pixels2[x, y]

                    diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)

                    if diff > 30:
                        diff_pixels += 1
                        diff_pixels_img[x, y] = (255, 0, 0)
                    else:
                        diff_pixels_img[x, y] = pixels1[x, y]

            diff_img.save(diff_path)

            return {
                "diff_exists": True,
                "diff_pixels": diff_pixels,
                "total_pixels": total_pixels,
                "diff_percentage": diff_pixels / total_pixels if total_pixels > 0 else 0,
                "similarity": 1 - (diff_pixels / total_pixels if total_pixels > 0 else 0),
            }

        except ImportError:
            return self._rough_compare(baseline_path, current_path)
        except Exception as e:
            return {"error": str(e)}

    def _rough_compare(self, baseline_path: str, current_path: str) -> dict[str, Any]:
        """Fallback comparison when PIL is not available."""
        baseline_hash = self._calculate_checksum(baseline_path)
        current_hash = self._calculate_checksum(current_path)

        return {
            "diff_exists": baseline_hash != current_hash,
            "diff_pixels": 0,
            "total_pixels": 0,
            "diff_percentage": 0.0 if baseline_hash == current_hash else 1.0,
            "similarity": 1.0 if baseline_hash == current_hash else 0.0,
        }

    def _calculate_checksum(self, filepath: Path | str) -> str:
        """Calculate MD5 checksum of a file."""
        filepath = Path(filepath)
        if not filepath.exists():
            return ""

        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    async def update_baseline(
        self, name: str, page: Page, full_page: bool = True
    ) -> dict[str, Any]:
        """
        Update an existing baseline with current screenshot.

        Args:
            name: Baseline name to update
            page: Playwright page object
            full_page: Whether to capture full page

        Returns:
            Update result
        """
        result = await self.capture_baseline(page, name, full_page)

        if result["success"]:
            old_files = list(self._baseline_dir.glob(f"{name}_*.png"))
            if len(old_files) > 1:
                old_files[0].unlink()

        return result

    def list_baselines(self) -> dict[str, Any]:
        """List all available baselines."""
        baselines = []
        metadata_dir = self._baseline_dir / "metadata"

        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob("*.json"):
                with open(metadata_file, "r") as f:
                    data = json.load(f)
                    for name, info in data.items():
                        baselines.append(info)

        return {
            "baselines": sorted(baselines, key=lambda x: x.get("captured_at", "")),
            "count": len(baselines),
        }

    def delete_baseline(self, name: str) -> dict[str, Any]:
        """
        Delete a baseline and its metadata.

        Args:
            name: Baseline name to delete

        Returns:
            Deletion result
        """
        files_deleted = 0

        for f in self._baseline_dir.glob(f"{name}_*.png"):
            f.unlink()
            files_deleted += 1

        metadata_path = self._baseline_dir / "metadata" / f"{name}.json"
        if metadata_path.exists():
            metadata_path.unlink()
            files_deleted += 1

        return {
            "success": files_deleted > 0,
            "name": name,
            "files_deleted": files_deleted,
        }

    async def compare_full_page(
        self,
        page: Page,
        baseline_name: str,
        full_page: bool = True,
        threshold: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Capture and compare in one operation.

        Args:
            page: Playwright page object
            baseline_name: Baseline name
            full_page: Whether to capture full page
            threshold: Optional threshold override

        Returns:
            Full comparison result
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_path = self._diff_dir / f"current_{baseline_name}_{timestamp}.png"

        await page.screenshot(path=str(current_path), full_page=full_page)

        return await self.compare(str(current_path), baseline_name, threshold)

    def get_diff_image(self, baseline_name: str) -> dict[str, Any]:
        """
        Get the latest diff image for a baseline.

        Args:
            baseline_name: Baseline name

        Returns:
            Diff image path if exists
        """
        diff_files = sorted(
            self._diff_dir.glob(f"diff_{baseline_name}_*.png"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if diff_files:
            return {
                "success": True,
                "diff_path": str(diff_files[0]),
            }

        return {
            "success": False,
            "error": "No diff found for baseline",
            "baseline_name": baseline_name,
        }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        action = input_data.get("action", "compare")

        if action == "capture_baseline":
            return await self.capture_baseline(
                page=input_data["page"],
                name=input_data["name"],
                full_page=input_data.get("full_page", True),
                viewport=input_data.get("viewport"),
            )
        elif action == "compare":
            return await self.compare(
                current_screenshot=input_data["current_screenshot"],
                baseline_name=input_data["baseline_name"],
                threshold=input_data.get("threshold"),
            )
        elif action == "compare_full_page":
            return await self.compare_full_page(
                page=input_data["page"],
                baseline_name=input_data["baseline_name"],
                full_page=input_data.get("full_page", True),
                threshold=input_data.get("threshold"),
            )
        elif action == "update_baseline":
            return await self.update_baseline(
                name=input_data["name"],
                page=input_data["page"],
                full_page=input_data.get("full_page", True),
            )
        elif action == "list_baselines":
            return self.list_baselines()
        elif action == "delete_baseline":
            return self.delete_baseline(name=input_data["name"])
        elif action == "get_diff":
            return self.get_diff_image(baseline_name=input_data["baseline_name"])
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
