"""
Feature file management for BDD tests.

This module provides:
- Feature file writing and organization
- Feature file reading and parsing
- Feature file updates
- Feature metadata management
"""

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.bdd.gherkin import (
    GherkinScenario,
    GherkinStep,
    StepKeyword,
)


# =============================================================================
# Feature Models
# =============================================================================


@dataclass
class FeatureMetadata:
    """
    Metadata for a feature file.

    Tracks:
    - File location
    - Scenario count
    - Tags
    - Dependencies
    """

    file_path: str = ""
    feature_name: str = ""
    scenario_count: int = 0
    step_count: int = 0
    tags: set[str] = field(default_factory=set)
    has_background: bool = False
    background_step_count: int = 0
    dependencies: set[str] = field(default_factory=set)
    last_modified: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "feature_name": self.feature_name,
            "scenario_count": self.scenario_count,
            "step_count": self.step_count,
            "tags": list(self.tags),
            "has_background": self.has_background,
            "background_step_count": self.background_step_count,
            "dependencies": list(self.dependencies),
            "last_modified": self.last_modified,
        }


@dataclass
class FeatureFile:
    """
    Complete feature file representation.

    Contains:
    - Feature header
    - Background (optional)
    - Scenarios
    - Metadata
    """

    path: str
    name: str
    description: str = ""
    background: list[GherkinStep] = field(default_factory=list)
    scenarios: list[GherkinScenario] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    @property
    def total_steps(self) -> int:
        """Total steps including background."""
        bg_steps = len(self.background)
        scenario_steps = sum(len(s.steps) for s in self.scenarios)
        return bg_steps + scenario_steps

    def to_gherkin(self) -> str:
        """Convert to Gherkin format."""
        lines = []

        # Tags
        if self.tags:
            tags_line = "  " + " ".join(sorted(self.tags))
            lines.append(tags_line)

        # Feature header
        lines.append(f"  Feature: {self.name}")

        # Description
        if self.description:
            for desc_line in self.description.split("\n"):
                lines.append(f"    {desc_line}")

        # Background
        if self.background:
            lines.append("")
            lines.append("  Background:")
            for step in self.background:
                lines.append(step.to_gherkin())

        # Scenarios
        for scenario in self.scenarios:
            lines.append("")
            lines.extend(scenario.to_gherkin().split("\n"))

        return "\n".join(lines)


# =============================================================================
# Feature File Manager
# =============================================================================


class FeatureFileManager:
    """
    Manage feature files for BDD tests.

    Features:
    - Write feature files with proper formatting
    - Read and parse feature files
    - Organize features by domain
    - Track feature metadata
    """

    def __init__(
        self,
        output_dir: Path,
        indent_size: int = 2,
    ) -> None:
        """
        Initialize the feature file manager.

        Args:
            output_dir: Directory for feature files
            indent_size: Indentation size
        """
        self.output_dir = Path(output_dir)
        self.indent_size = indent_size
        self._metadata: dict[str, FeatureMetadata] = {}

    # =========================================================================
    # Feature Writing
    # =========================================================================

    def write_feature_file(
        self,
        feature: dict[str, Any],
    ) -> Path | None:
        """
        Write a feature file.

        Args:
            feature: Feature dictionary with name, description, scenarios, background

        Returns:
            Path to created file or None
        """
        try:
            # Generate file name
            file_name = self._generate_file_name(feature["name"])
            file_path = self.output_dir / f"{file_name}.feature"

            # Create content
            content = self._format_feature_content(feature)

            # Ensure directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding="utf-8")

            # Update metadata
            self._update_metadata(file_path, feature)

            return file_path

        except Exception as e:
            print(f"Error writing feature file: {e}")
            return None

    def write_feature(
        self,
        feature: FeatureFile,
    ) -> Path | None:
        """
        Write a FeatureFile object.

        Args:
            feature: FeatureFile to write

        Returns:
            Path to created file or None
        """
        # Convert to dictionary format
        feature_dict = {
            "name": feature.name,
            "description": feature.description,
            "scenarios": feature.scenarios,
            "background": feature.background,
            "tags": feature.tags,
        }

        return self.write_feature_file(feature_dict)

    def _generate_file_name(self, feature_name: str) -> str:
        """
        Generate file name from feature name.

        Args:
            feature_name: Feature name

        Returns:
            File name
        """
        import re

        # Remove "Feature:" prefix if present
        name = feature_name.replace("Feature:", "").strip()

        # Convert to lowercase with underscores
        name = re.sub(r'[\s\-]+', '_', name)
        name = re.sub(r'[^a-z0-9_]', '', name.lower())

        return name or "feature"

    def _format_feature_content(
        self,
        feature: dict[str, Any],
    ) -> str:
        """
        Format feature content as Gherkin.

        Args:
            feature: Feature dictionary

        Returns:
            Formatted Gherkin content
        """
        lines = []
        indent = " " * self.indent_size

        # Tags
        tags = feature.get("tags", set())
        if tags:
            if isinstance(tags, list):
                tags = set(tags)
            tags_line = f"{indent}{indent.join(sorted(tags))}"
            lines.append(tags_line)

        # Feature header
        name = feature["name"]
        if not name.startswith("Feature:"):
            name = f"Feature: {name}"
        lines.append(f"{indent}{name}")

        # Description
        description = feature.get("description", "")
        if description:
            for desc_line in description.split("\n"):
                lines.append(f"{indent}{indent}{desc_line}")

        # Background
        background = feature.get("background")
        if background and background.get("steps"):
            lines.append("")
            lines.append(f"{indent}Background:")
            for step in background["steps"]:
                lines.append(f"{indent}{indent}{self._format_step(step)}")

        # Scenarios
        scenarios = feature.get("scenarios", [])
        for scenario in scenarios:
            lines.append("")
            lines.extend(self._format_scenario(scenario, indent).split("\n"))

        return "\n".join(lines)

    def _format_scenario(
        self,
        scenario: GherkinScenario,
        indent: str,
    ) -> str:
        """
        Format a scenario as Gherkin.

        Args:
            scenario: GherkinScenario
            indent: Indentation string

        Returns:
            Formatted scenario string
        """
        lines = []

        # Tags
        if scenario.tags:
            tags_line = f"{indent}{indent.join(sorted(scenario.tags))}"
            lines.append(tags_line)

        # Scenario header
        scenario_type = "Scenario Outline" if scenario.is_outline else "Scenario"
        lines.append(f"{indent}{scenario_type}: {scenario.name}")

        # Description
        if scenario.description:
            lines.append(f"{indent}{indent}{scenario.description}")

        # Steps
        for step in scenario.steps:
            lines.append(f"{indent}{indent}{self._format_step(step)}")

        # Examples for scenario outline
        if scenario.is_outline and hasattr(scenario, "examples"):
            examples = scenario.examples
            if examples:
                lines.append("")
                lines.append(f"{indent}{indent}Examples:")
                headers = " | ".join(examples.get("parameter_names", []))
                lines.append(f"{indent}{indent}{indent}| {headers} |")
                for example in examples.get("data", []):
                    values = " | ".join(str(example.get(p, "")) for p in examples.get("parameter_names", []))
                    lines.append(f"{indent}{indent}{indent}| {values} |")

        return "\n".join(lines)

    def _format_step(self, step: GherkinStep) -> str:
        """
        Format a step as Gherkin.

        Args:
            step: GherkinStep or step dict

        Returns:
            Formatted step string
        """
        if isinstance(step, GherkinStep):
            return step.to_gherkin().strip()
        else:
            # Handle dict format
            keyword = step.get("keyword", "When")
            text = step.get("text", "")
            return f"    {keyword} {text}"

    # =========================================================================
    # Feature Reading
    # =========================================================================

    def read_feature_file(
        self,
        file_path: Path | str,
    ) -> FeatureFile | None:
        """
        Read and parse a feature file.

        Args:
            file_path: Path to feature file

        Returns:
            FeatureFile or None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            content = path.read_text(encoding="utf-8")
            return self._parse_feature_content(content, path)

        except Exception as e:
            print(f"Error reading feature file: {e}")
            return None

    def _parse_feature_content(
        self,
        content: str,
        file_path: Path,
    ) -> FeatureFile | None:
        """
        Parse Gherkin feature content.

        Args:
            content: Gherkin content
            file_path: File path

        Returns:
            Parsed FeatureFile
        """
        # Simple parser for feature files
        lines = content.split("\n")

        feature = FeatureFile(
            path=str(file_path),
            name="Unknown",
        )

        current_section = "feature"
        current_scenario: GherkinScenario | None = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Tags
            if stripped.startswith("@"):
                tag = stripped.split()[0]
                if current_section == "feature" or not current_scenario:
                    feature.tags.add(tag)
                elif current_scenario:
                    current_scenario.tags.append(tag)
                continue

            # Feature header
            if stripped.startswith("Feature:"):
                feature.name = stripped.replace("Feature:", "").strip()
                current_section = "feature"
                continue

            # Background
            if stripped.startswith("Background:"):
                current_section = "background"
                continue

            # Scenario header
            if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
                if current_scenario:
                    feature.scenarios.append(current_scenario)

                scenario_type = "Scenario Outline:" in stripped
                name = stripped.replace("Scenario Outline:", "").replace("Scenario:", "").strip()

                current_scenario = GherkinScenario(
                    name=name,
                    scenario_id=f"scenario_{hash(name)}",
                    is_outline=scenario_type,
                )
                current_section = "scenario"
                continue

            # Step
            if any(stripped.startswith(k.value) for k in StepKeyword):
                if current_scenario:
                    keyword = StepKeyword.WHEN
                    for kw in StepKeyword:
                        if stripped.startswith(kw.value):
                            keyword = kw
                            break

                    text = stripped.replace(keyword.value, "",).strip()
                    step = GherkinStep(
                        keyword=keyword,
                        text=text,
                    )
                    current_scenario.add_step(step)

        # Add last scenario
        if current_scenario:
            feature.scenarios.append(current_scenario)

        return feature

    # =========================================================================
    # Metadata Management
    # =========================================================================

    def _update_metadata(
        self,
        file_path: Path,
        feature: dict[str, Any],
    ) -> None:
        """
        Update metadata for a feature file.

        Args:
            file_path: Path to feature file
            feature: Feature dictionary
        """
        scenarios = feature.get("scenarios", [])
        background = feature.get("background")
        tags = feature.get("tags", set())
        if isinstance(tags, list):
            tags = set(tags)

        metadata = FeatureMetadata(
            file_path=str(file_path),
            feature_name=feature["name"],
            scenario_count=len(scenarios),
            step_count=sum(len(s.steps) for s in scenarios),
            tags=tags,
            has_background=bool(background and background.get("steps")),
            background_step_count=len(background.get("steps", [])) if background else 0,
        )

        self._metadata[str(file_path)] = metadata

    def get_metadata(
        self,
        file_path: Path | str,
    ) -> FeatureMetadata | None:
        """
        Get metadata for a feature file.

        Args:
            file_path: Path to feature file

        Returns:
            FeatureMetadata or None
        """
        return self._metadata.get(str(file_path))

    def get_all_metadata(self) -> dict[str, FeatureMetadata]:
        """Get all feature metadata."""
        return self._metadata.copy()

    # =========================================================================
    # Feature Organization
    # =========================================================================

    def organize_features_by_domain(
        self,
        features: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Organize features by domain/tag.

        Args:
            features: List of feature dictionaries

        Returns:
            Dictionary mapping domains to features
        """
        domains: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for feature in features:
            tags = feature.get("tags", set())
            if isinstance(tags, list):
                tags = set(tags)

            # Determine domain from tags or name
            domain = "general"

            # Check for domain-specific tags
            domain_tags = ["@auth", "@checkout", "@search", "@profile", "@api"]
            for tag in domain_tags:
                if tag in tags:
                    domain = tag.replace("@", "")
                    break

            # Check name
            for tag in domain_tags:
                if tag.replace("@", "") in feature["name"].lower():
                    domain = tag.replace("@", "")
                    break

            domains[domain].append(feature)

        return dict(domains)

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get feature file statistics."""
        total_features = len(self._metadata)
        total_scenarios = sum(m.scenario_count for m in self._metadata.values())
        total_steps = sum(m.step_count for m in self._metadata.values())

        # Tag distribution
        all_tags: dict[str, int] = defaultdict(int)
        for metadata in self._metadata.values():
            for tag in metadata.tags:
                all_tags[tag] += 1

        # Background usage
        features_with_background = sum(
            1 for m in self._metadata.values() if m.has_background
        )

        return {
            "total_features": total_features,
            "total_scenarios": total_scenarios,
            "total_steps": total_steps,
            "avg_scenarios_per_feature": total_scenarios / total_features if total_features > 0 else 0,
            "avg_steps_per_scenario": total_steps / total_scenarios if total_scenarios > 0 else 0,
            "features_with_background": features_with_background,
            "background_ratio": features_with_background / total_features if total_features > 0 else 0,
            "tag_distribution": dict(all_tags),
        }
