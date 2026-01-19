"""
Scenario Analyzer Module (AI-Powered).

Analyzes test scenarios for patterns, duplicates, and optimization opportunities.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScenarioPattern:
    """Detected pattern in scenarios."""

    name: str
    occurrences: int
    steps: List[str]
    recommendation: str
    priority: str


@dataclass
class ScenarioAnalysis:
    """Analysis results for a scenario."""

    scenario_id: str
    name: str
    complexity_score: float
    patterns: List[ScenarioPattern]
    duplicates: List[str]
    suggestions: List[str]
    reusable_steps: List[str]


class ScenarioAnalyzer:
    """
    AI-powered scenario analyzer for test optimization.

    Features:
    - Pattern detection across scenarios
    - Duplicate identification
    - Reusable step extraction
    - Complexity scoring
    - Optimization suggestions
    """

    def __init__(self):
        """Initialize the scenario analyzer."""
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.patterns: List[ScenarioPattern] = []

    def add_scenario(self, scenario_id: str, scenario_data: Dict[str, Any]) -> None:
        """
        Add a scenario for analysis.

        Args:
            scenario_id: Unique identifier for the scenario
            scenario_data: Scenario data including name, steps, tags
        """
        self.scenarios[scenario_id] = scenario_data

    def analyze_scenario(self, scenario_id: str) -> ScenarioAnalysis:
        """
        Analyze a single scenario.

        Args:
            scenario_id: ID of the scenario to analyze

        Returns:
            ScenarioAnalysis with results
        """
        if scenario_id not in self.scenarios:
            return ScenarioAnalysis(
                scenario_id=scenario_id,
                name="Unknown",
                complexity_score=0.0,
                patterns=[],
                duplicates=[],
                suggestions=[],
                reusable_steps=[],
            )

        scenario = self.scenarios[scenario_id]
        steps = scenario.get("steps", [])
        tags = scenario.get("tags", [])

        complexity = self._calculate_complexity(steps)
        patterns = self._detect_patterns(scenario)
        duplicates = self._find_duplicates(scenario_id)
        suggestions = self._generate_suggestions(scenario)
        reusable = self._identify_reusable_steps(steps)

        return ScenarioAnalysis(
            scenario_id=scenario_id,
            name=scenario.get("name", ""),
            complexity_score=complexity,
            patterns=patterns,
            duplicates=duplicates,
            suggestions=suggestions,
            reusable_steps=reusable,
        )

    def _calculate_complexity(self, steps: List[str]) -> float:
        """
        Calculate complexity score for a scenario.

        Args:
            steps: List of scenario steps

        Returns:
            Complexity score from 0 to 100
        """
        if not steps:
            return 0.0

        base_score = len(steps) * 5

        complex_keywords = ["wait", "loop", "conditional", "assert", "validate", "verify"]
        for step in steps:
            step_lower = step.lower()
            for keyword in complex_keywords:
                if keyword in step_lower:
                    base_score += 3

        return min(base_score, 100)

    def _detect_patterns(self, scenario: Dict[str, Any]) -> List[ScenarioPattern]:
        """
        Detect patterns in a scenario.

        Args:
            scenario: Scenario to analyze

        Returns:
            List of detected patterns
        """
        patterns = []
        steps = scenario.get("steps", [])
        tags = scenario.get("tags", [])

        if any(tag in tags for tag in ["@login", "@authentication", "@auth"]):
            patterns.append(
                ScenarioPattern(
                    name="Authentication Flow",
                    occurrences=1,
                    steps=["login", "authenticate"],
                    recommendation="Consider using authentication helper to reduce duplication",
                    priority="medium",
                )
            )

        if any("navigate" in step.lower() or "go to" in step.lower() for step in steps):
            patterns.append(
                ScenarioPattern(
                    name="Navigation Pattern",
                    occurrences=steps.count("navigate"),
                    steps=["navigate", "goto", "visit"],
                    recommendation="Use navigation helper for consistent page transitions",
                    priority="low",
                )
            )

        if any("fill" in step.lower() or "enter" in step.lower() for step in steps):
            form_steps = [s for s in steps if "fill" in s.lower() or "enter" in s.lower()]
            patterns.append(
                ScenarioPattern(
                    name="Form Input Pattern",
                    occurrences=len(form_steps),
                    steps=form_steps[:3],
                    recommendation="Consider creating page object methods for form operations",
                    priority="medium",
                )
            )

        return patterns

    def _find_duplicates(self, scenario_id: str) -> List[str]:
        """
        Find duplicate scenarios.

        Args:
            scenario_id: ID of the scenario to check

        Returns:
            List of duplicate scenario IDs
        """
        if scenario_id not in self.scenarios:
            return []

        current = self.scenarios[scenario_id]
        current_steps = set(current.get("steps", []))
        duplicates = []

        for sid, scenario in self.scenarios.items():
            if sid == scenario_id:
                continue

            other_steps = set(scenario.get("steps", []))
            similarity = len(current_steps & other_steps) / len(current_steps | other_steps)

            if similarity > 0.8:
                duplicates.append(sid)

        return duplicates

    def _generate_suggestions(self, scenario: Dict[str, Any]) -> List[str]:
        """
        Generate optimization suggestions for a scenario.

        Args:
            scenario: Scenario to analyze

        Returns:
            List of suggestions
        """
        suggestions = []
        steps = scenario.get("steps", [])

        if len(steps) > 10:
            suggestions.append("Consider breaking this scenario into smaller, focused scenarios")

        if not any("@smoke" in step or "@regression" in step for step in scenario.get("tags", [])):
            suggestions.append("Add appropriate tags (@smoke, @regression) for test organization")

        if any("click" in step.lower() for step in steps):
            suggestions.append(
                "Use page object methods instead of direct selectors for better maintainability"
            )

        if not any("assert" in step.lower() or "verify" in step.lower() for step in steps):
            suggestions.append("Add assertions to validate expected outcomes")

        if any("wait" in step.lower() for step in steps):
            suggestions.append("Use wait_manager for dynamic waiting instead of fixed sleeps")

        return suggestions

    def _identify_reusable_steps(self, steps: List[str]) -> List[str]:
        """
        Identify potentially reusable steps.

        Args:
            steps: List of scenario steps

        Returns:
            List of reusable step patterns
        """
        reusable = []

        step_actions = {
            "login": ["login", "authenticate", "sign in"],
            "navigation": ["navigate", "goto", "visit", "go to"],
            "search": ["search", "find", "lookup"],
            "filter": ["filter", "sort", "search"],
            "form_submit": ["submit", "save", "update", "create"],
            "validation": ["assert", "verify", "validate", "check"],
        }

        for action, keywords in step_actions.items():
            for step in steps:
                if any(kw in step.lower() for kw in keywords):
                    reusable.append(action)
                    break

        return list(set(reusable))

    def get_full_analysis_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.

        Returns:
            Dictionary with overall analysis results
        """
        analyses = [self.analyze_scenario(sid) for sid in self.scenarios]

        total_complexity = sum(a.complexity_score for a in analyses)
        avg_complexity = total_complexity / len(analyses) if analyses else 0

        all_patterns = []
        all_duplicates = []
        all_suggestions = []
        all_reusable = []

        for analysis in analyses:
            all_patterns.extend(analysis.patterns)
            all_duplicates.extend(analysis.duplicates)
            all_suggestions.extend(analysis.suggestions)
            all_reusable.extend(analysis.reusable_steps)

        return {
            "total_scenarios": len(analyses),
            "average_complexity": f"{avg_complexity:.1f}",
            "high_complexity_scenarios": [
                {"id": a.scenario_id, "name": a.name, "score": a.complexity_score}
                for a in analyses
                if a.complexity_score > 50
            ],
            "detected_patterns": [
                {"name": p.name, "occurrences": p.occurrences, "priority": p.priority}
                for p in all_patterns
            ],
            "duplicate_groups": len(set(all_duplicates)),
            "optimization_suggestions": list(set(all_suggestions)),
            "recommended_reusable_components": list(set(all_reusable)),
        }
