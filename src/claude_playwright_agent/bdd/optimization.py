"""
Scenario optimization for BDD tests.

This module provides:
- Background step extraction
- Automatic tag generation
- Scenario deduplication
- Step pattern analysis
"""

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.bdd.gherkin import (
    GherkinScenario,
    GherkinStep,
    StepKeyword,
)


# =============================================================================
# Optimization Models
# =============================================================================


@dataclass
class BackgroundSteps:
    """
    Common steps that can be extracted to a background.

    Maintains context about where these steps are used.
    """

    steps: list[GherkinStep] = field(default_factory=list)
    usage_count: int = 0
    feature_key: str = ""
    contexts: list[str] = field(default_factory=list)  # recording_ids

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": [s.to_dict() for s in self.steps],
            "usage_count": self.usage_count,
            "feature_key": self.feature_key,
            "contexts": self.contexts,
        }


@dataclass
class TagSuggestion:
    """
    Suggested tag for a scenario.

    Includes confidence score and reasoning.
    """

    tag: str
    confidence: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tag": self.tag,
            "confidence": self.confidence,
            "reason": self.reason,
        }


# =============================================================================
# Scenario Optimizer
# =============================================================================


class ScenarioOptimizer:
    """
    Optimize Gherkin scenarios for better maintainability.

    Features:
    - Extract common steps to backgrounds
    - Generate meaningful tags
    - Identify duplicate scenarios
    - Suggest scenario outlines
    """

    # Common action patterns for tagging
    TAG_PATTERNS = {
        "@authentication": {"login", "logout", "signin", "signout", "auth"},
        "@registration": {"register", "signup", "sign up", "create account"},
        "@search": {"search", "find", "lookup", "query"},
        "@navigation": {"navigate", "go to", "visit", "open"},
        "@form": {"fill", "enter", "input", "type into", "submit"},
        "@checkout": {"checkout", "payment", "purchase", "buy"},
        "@cart": {"cart", "basket", "add to cart", "remove from"},
        "@profile": {"profile", "account", "settings", "preferences"},
        "@api": {"api", "endpoint", "response", "request"},
        "@smoke": {},  # Added manually for quick smoke tests
        "@regression": {},  # Added manually for full regression
        "@integration": {},  # Added manually for integration tests
    }

    # Common background patterns
    BACKGROUND_TEMPLATES = {
        "navigation": [
            StepKeyword.GIVEN,
            "the user is on the homepage",
        ],
        "authentication": [
            StepKeyword.GIVEN,
            "the user is logged in",
        ],
        "setup": [
            StepKeyword.GIVEN,
            "the application is initialized",
        ],
    }

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self._backgrounds: dict[str, BackgroundSteps] = {}
        self._tag_cache: dict[str, list[TagSuggestion]] = {}

    # =========================================================================
    # Background Extraction
    # =========================================================================

    def extract_common_backgrounds(
        self,
        scenarios: list[GherkinScenario],
        min_occurrence: int = 2,
        max_steps: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Extract common step sequences as backgrounds.

        Args:
            scenarios: List of scenarios to analyze
            min_occurrence: Minimum times a sequence must appear
            max_steps: Maximum steps in a background

        Returns:
            List of background dictionaries
        """
        # Collect all step sequences
        sequences: dict[str, list[tuple[int, GherkinScenario]]] = {}

        for scenario in scenarios:
            # Get first N steps as potential background
            for n in range(1, min(max_steps + 1, len(scenario.steps) + 1)):
                sequence = tuple(scenario.steps[:n])
                sequence_hash = self._hash_sequence(sequence)

                if sequence_hash not in sequences:
                    sequences[sequence_hash] = []
                sequences[sequence_hash].append((n, scenario))

        # Find common sequences
        backgrounds = []

        for seq_hash, occurrences in sequences.items():
            if len(occurrences) >= min_occurrence:
                # Get the sequence from first occurrence
                first_scenario = occurrences[0][1]
                n_steps = occurrences[0][0]
                steps = list(first_scenario.steps[:n_steps])

                # Determine feature key
                feature_keys = {s.feature_file for _, s in occurrences}
                feature_key = feature_keys.pop() if len(feature_keys) == 1 else "common"

                background = BackgroundSteps(
                    steps=steps,
                    usage_count=len(occurrences),
                    feature_key=feature_key,
                    contexts=[s.recording_id for _, s in occurrences],
                )

                # Cache for later use
                self._backgrounds[seq_hash] = background

                backgrounds.append({
                    "hash": seq_hash,
                    "steps": steps,
                    "usage_count": len(occurrences),
                    "feature_key": feature_key,
                    "step_count": n_steps,
                })

        # Sort by usage (most common first)
        backgrounds.sort(key=lambda b: b["usage_count"], reverse=True)

        return backgrounds

    def extract_feature_background(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, Any] | None:
        """
        Extract a background for a specific feature.

        Args:
            scenarios: Scenarios in the feature

        Returns:
            Background dictionary or None
        """
        if len(scenarios) < 2:
            return None

        # Find common prefix of steps
        common_steps = self._find_common_step_prefix(scenarios)

        if len(common_steps) < 2:
            return None

        return {
            "steps": common_steps,
            "usage_count": len(scenarios),
        }

    def should_apply_background(
        self,
        scenario: GherkinScenario,
        background: dict[str, Any],
    ) -> bool:
        """
        Check if a background should be applied to a scenario.

        Args:
            scenario: Scenario to check
            background: Background dictionary

        Returns:
            True if background should be applied
        """
        bg_steps = background.get("steps", [])
        scenario_steps = scenario.steps[:len(bg_steps)]

        # Check if scenario starts with background steps
        for i, bg_step in enumerate(bg_steps):
            if i >= len(scenario_steps):
                return False
            if scenario_steps[i].text != bg_step.text:
                return False

        return True

    def _find_common_step_prefix(
        self,
        scenarios: list[GherkinScenario],
    ) -> list[GherkinStep]:
        """
        Find common step prefix across scenarios.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            List of common steps
        """
        if not scenarios:
            return []

        # Use first scenario as reference
        ref_steps = scenarios[0].steps
        common_len = 0

        # Find how many steps match
        for i, step in enumerate(ref_steps):
            all_match = True
            for scenario in scenarios[1:]:
                if i >= len(scenario.steps):
                    all_match = False
                    break
                if scenario.steps[i].text != step.text:
                    all_match = False
                    break

            if all_match:
                common_len = i + 1
            else:
                break

        return list(ref_steps[:common_len])

    def _hash_sequence(self, steps: tuple[GherkinStep, ...]) -> str:
        """Hash a step sequence for comparison."""
        step_texts = "|".join(s.text for s in steps)
        return hashlib.sha256(step_texts.encode()).hexdigest()[:12]

    # =========================================================================
    # Tag Generation
    # =========================================================================

    def generate_tags(
        self,
        scenario: GherkinScenario,
    ) -> list[str]:
        """
        Generate relevant tags for a scenario.

        Args:
            scenario: Scenario to analyze

        Returns:
            List of suggested tags
        """
        tags = []

        # Analyze scenario name
        name_lower = scenario.name.lower()
        for tag, keywords in self.TAG_PATTERNS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    tags.append(tag)
                    break

        # Analyze steps
        step_texts = " ".join(s.text.lower() for s in scenario.steps)

        for tag, keywords in self.TAG_PATTERNS.items():
            if tag in tags:
                continue
            for keyword in keywords:
                if keyword in step_texts:
                    tags.append(tag)
                    break

        # Add page-specific tags
        if scenario.steps:
            first_step = scenario.steps[0]
            if "navigate" in first_step.text.lower():
                tags.append("@navigation")

        # Add complexity tags
        if len(scenario.steps) > 10:
            tags.append("@complex")
        elif len(scenario.steps) <= 3:
            tags.append("@simple")

        # Deduplicate
        return list(set(tags))

    def generate_tag_suggestions(
        self,
        scenario: GherkinScenario,
    ) -> list[TagSuggestion]:
        """
        Generate detailed tag suggestions with confidence.

        Args:
            scenario: Scenario to analyze

        Returns:
            List of tag suggestions
        """
        suggestions = []

        # Check each tag pattern
        for tag, keywords in self.TAG_PATTERNS.items():
            confidence = 0.0
            reasons = []

            # Check name
            name_lower = scenario.name.lower()
            for keyword in keywords:
                if keyword in name_lower:
                    confidence += 0.4
                    reasons.append(f"Keyword '{keyword}' in scenario name")

            # Check steps
            step_texts = " ".join(s.text.lower() for s in scenario.steps)
            for keyword in keywords:
                if keyword in step_texts:
                    confidence += 0.3
                    reasons.append(f"Keyword '{keyword}' in steps")

            # Add suggestion if confident enough
            if confidence >= 0.4:
                suggestions.append(TagSuggestion(
                    tag=tag,
                    confidence=min(confidence, 1.0),
                    reason="; ".join(reasons),
                ))

        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions

    # =========================================================================
    # Scenario Analysis
    # =========================================================================

    def find_duplicate_scenarios(
        self,
        scenarios: list[GherkinScenario],
    ) -> list[list[GherkinScenario]]:
        """
        Find duplicate or very similar scenarios.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            List of duplicate scenario groups
        """
        duplicates = []
        seen: dict[str, list[GherkinScenario]] = {}

        for scenario in scenarios:
            # Create signature based on steps
            signature = self._create_scenario_signature(scenario)

            if signature not in seen:
                seen[signature] = []
            seen[signature].append(scenario)

        # Find groups with more than one scenario
        for scenarios_group in seen.values():
            if len(scenarios_group) > 1:
                duplicates.append(scenarios_group)

        return duplicates

    def suggest_scenario_outline(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, Any] | None:
        """
        Suggest converting scenarios to a scenario outline.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            Outline suggestion or None
        """
        if len(scenarios) < 2:
            return None

        # Check if scenarios have similar structure
        first_scenario = scenarios[0]

        # All scenarios should have same step count
        if not all(len(s.steps) == len(first_scenario.steps) for s in scenarios):
            return None

        # Find parameter positions
        param_positions = self._find_parameter_positions(scenarios)

        if not param_positions:
            return None

        # Generate examples
        examples = []
        for scenario in scenarios:
            example = {}
            for pos, param_name in param_positions.items():
                example[param_name] = scenario.steps[pos].text
            examples.append(example)

        return {
            "base_scenario": first_scenario,
            "parameter_positions": param_positions,
            "examples": examples,
        }

    def _create_scenario_signature(self, scenario: GherkinScenario) -> str:
        """
        Create signature for scenario comparison.

        Args:
            scenario: Scenario to signature

        Returns:
            Scenario signature
        """
        # Normalize steps for comparison
        normalized = []
        for step in scenario.steps:
            # Remove quoted values (parameters)
            import re
            normalized_text = re.sub(r'"[^"]*"', '""', step.text)
            normalized_text = re.sub(r"'[^']*'", "''", normalized_text)
            normalized.append(normalized_text)

        return "|".join(normalized)

    def _find_parameter_positions(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[int, str]:
        """
        Find positions that vary across scenarios.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            Dictionary mapping positions to parameter names
        """
        param_positions = {}

        if not scenarios:
            return param_positions

        # Compare each step position
        for i in range(len(scenarios[0].steps)):
            # Get all texts at this position
            texts = [s.steps[i].text for s in scenarios if i < len(s.steps)]

            # Check if texts vary
            if len(set(texts)) > 1:
                # This is a parameter position
                param_name = f"param_{i}"
                param_positions[i] = param_name

        return param_positions

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_optimization_stats(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, Any]:
        """
        Get optimization statistics for scenarios.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            Statistics dictionary
        """
        # Background potential
        backgrounds = self.extract_common_backgrounds(scenarios)
        background_steps = sum(len(b.get("steps", [])) for b in backgrounds)
        total_steps = sum(len(s.steps) for s in scenarios)
        background_ratio = background_steps / total_steps if total_steps > 0 else 0

        # Tag coverage
        all_tags = set()
        for scenario in scenarios:
            all_tags.update(scenario.tags)

        # Duplicates
        duplicates = self.find_duplicate_scenarios(scenarios)

        # Average complexity
        avg_steps = total_steps / len(scenarios) if scenarios else 0

        return {
            "total_scenarios": len(scenarios),
            "total_steps": total_steps,
            "avg_steps_per_scenario": avg_steps,
            "backgrounds_found": len(backgrounds),
            "background_steps_savings": background_steps,
            "background_ratio": background_ratio,
            "unique_tags": len(all_tags),
            "duplicate_groups": len(duplicates),
            "duplicate_scenarios": sum(len(d) for d in duplicates),
            "complexity_distribution": self._get_complexity_distribution(scenarios),
        }

    def _get_complexity_distribution(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, int]:
        """
        Get complexity distribution of scenarios.

        Args:
            scenarios: Scenarios to analyze

        Returns:
            Dictionary mapping complexity levels to counts
        """
        distribution = {
            "simple": 0,    # <= 3 steps
            "medium": 0,    # 4-7 steps
            "complex": 0,   # 8-12 steps
            "very_complex": 0,  # > 12 steps
        }

        for scenario in scenarios:
            steps = len(scenario.steps)
            if steps <= 3:
                distribution["simple"] += 1
            elif steps <= 7:
                distribution["medium"] += 1
            elif steps <= 12:
                distribution["complex"] += 1
            else:
                distribution["very_complex"] += 1

        return distribution
