"""
BDD Conversion Agent for converting recordings to executable BDD tests.

This agent:
- Loads deduplicated data from state
- Converts actions to Gherkin scenarios with context
- Optimizes scenarios (backgrounds, tags)
- Generates feature files
- Generates step definitions
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from claude_playwright_agent.bdd.gherkin import (
    GherkinGenerator,
    GherkinScenario,
    GherkinStep,
    ActionStepMapper,
)
from claude_playwright_agent.bdd.steps import StepDefinitionGenerator, StepGenConfig
from claude_playwright_agent.bdd.optimization import ScenarioOptimizer
from claude_playwright_agent.bdd.features import FeatureFileManager
from claude_playwright_agent.state.manager import StateManager


# =============================================================================
# Agent Configuration
# =============================================================================


class BDDConversionConfig(BaseModel):
    """Configuration for BDD conversion agent."""

    framework: str = Field(
        default="behave",
        description="BDD framework (behave or pytest-bdd)"
    )
    use_async: bool = Field(
        default=True,
        description="Generate async/await code"
    )
    include_type_hints: bool = Field(
        default=True,
        description="Include type hints in generated code"
    )
    include_docstrings: bool = Field(
        default=True,
        description="Include docstrings in generated code"
    )
    feature_output_dir: str = Field(
        default="features",
        description="Output directory for feature files"
    )
    steps_output_dir: str = Field(
        default="features/steps",
        description="Output directory for step definitions"
    )
    extract_backgrounds: bool = Field(
        default=True,
        description="Extract common steps to backgrounds"
    )
    auto_tag_scenarios: bool = Field(
        default=True,
        description="Automatically tag scenarios based on content"
    )
    group_by_feature: bool = Field(
        default=True,
        description="Group scenarios into features"
    )
    feature_naming: str = Field(
        default="page_based",
        description="Feature naming strategy: page_based, action_based, url_based"
    )


# =============================================================================
# Conversion Result
# =============================================================================


class BDDConversionResult(BaseModel):
    """Result of BDD conversion process."""

    success: bool = Field(..., description="Whether conversion succeeded")
    total_scenarios: int = Field(default=0, description="Total scenarios generated")
    total_features: int = Field(default=0, description="Total feature files created")
    total_steps: int = Field(default=0, description="Total step definitions created")
    backgrounds_extracted: int = Field(default=0, description="Backgrounds extracted")
    tags_added: int = Field(default=0, description="Tags added to scenarios")
    scenarios_by_recording: dict[str, int] = Field(
        default_factory=dict,
        description="Scenarios generated per recording"
    )
    features_created: list[str] = Field(
        default_factory=list,
        description="Feature file paths created"
    )
    step_files_created: list[str] = Field(
        default_factory=list,
        description="Step definition file paths created"
    )
    stats: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed statistics"
    )


# =============================================================================
# BDD Conversion Agent
# =============================================================================


class BDDConversionAgent:
    """
    Agent for converting recordings to BDD tests.

    Process:
    1. Load deduplicated data from state
    2. Load recording data from state
    3. Convert actions to Gherkin scenarios with context
    4. Optimize scenarios (extract backgrounds, add tags)
    5. Generate feature files
    6. Generate step definitions
    7. Update state with results
    """

    def __init__(
        self,
        project_path: Path,
        config: BDDConversionConfig | None = None,
    ) -> None:
        """
        Initialize the BDD conversion agent.

        Args:
            project_path: Path to the project
            config: Optional BDD conversion configuration
        """
        self.agent_id = "bdd_conversion_agent"
        self.agent_type = "bdd_conversion"
        self.project_path = project_path

        self.config = config or BDDConversionConfig()
        self.gherkin_gen = GherkinGenerator()
        self.step_gen = StepDefinitionGenerator(StepGenConfig(
            framework=self.config.framework,
            use_async=self.config.use_async,
            include_type_hints=self.config.include_type_hints,
            include_docstrings=self.config.include_docstrings,
        ))
        self.optimizer = ScenarioOptimizer()
        self.feature_mgr = FeatureFileManager(
            output_dir=project_path / self.config.feature_output_dir,
        )

    # =========================================================================
    # Main Processing
    # =========================================================================

    def run(self) -> BDDConversionResult:
        """
        Run the BDD conversion process.

        Returns:
            BDDConversionResult with outcomes
        """
        try:
            # Load state
            state = StateManager(self.project_path)

            # Load deduplicated data
            dedup_data = self._load_deduplicated_data(state)

            # Load recordings
            recordings = state.get_recordings()

            if not recordings:
                return BDDConversionResult(
                    success=True,
                    total_scenarios=0,
                    total_features=0,
                )

            # Generate scenarios from recordings
            scenarios = self._generate_scenarios_from_recordings(
                recordings,
                state,
                dedup_data,
            )

            if not scenarios:
                return BDDConversionResult(
                    success=True,
                    total_scenarios=0,
                    total_features=0,
                )

            # Optimize scenarios
            if self.config.extract_backgrounds or self.config.auto_tag_scenarios:
                scenarios = self._optimize_scenarios(scenarios)

            # Group scenarios into features
            features = self._group_scenarios_into_features(scenarios)

            # Generate feature files
            feature_files = self._generate_feature_files(features)

            # Generate step definitions
            step_files = self._generate_step_definitions(scenarios)

            # Update state
            self._update_state(state, scenarios, features, feature_files, step_files)

            # Calculate statistics
            total_steps = sum(len(s.steps) for s in scenarios)
            backgrounds_extracted = sum(
                1 for f in features if f.get("background")
            )
            tags_added = sum(len(s.tags) for s in scenarios)

            return BDDConversionResult(
                success=True,
                total_scenarios=len(scenarios),
                total_features=len(features),
                total_steps=total_steps,
                backgrounds_extracted=backgrounds_extracted,
                tags_added=tags_added,
                scenarios_by_recording=self._count_by_recording(scenarios),
                features_created=feature_files,
                step_files_created=step_files,
                stats={
                    "framework": self.config.framework,
                    "use_async": self.config.use_async,
                    "avg_steps_per_scenario": total_steps / len(scenarios) if scenarios else 0,
                },
            )

        except Exception as e:
            return BDDConversionResult(
                success=False,
                stats={"error": str(e)},
            )

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_deduplicated_data(
        self,
        state: StateManager,
    ) -> dict[str, Any]:
        """
        Load deduplicated data from state.

        Args:
            state: State manager

        Returns:
            Dictionary with deduplicated data
        """
        return {
            "selector_catalog": state._state.selector_catalog,
            "components": state._state.components,
            "page_objects": state._state.page_objects,
        }

    # =========================================================================
    # Scenario Generation
    # =========================================================================

    def _generate_scenarios_from_recordings(
        self,
        recordings: list[Any],
        state: StateManager,
        dedup_data: dict[str, Any],
    ) -> list[GherkinScenario]:
        """
        Generate Gherkin scenarios from recordings.

        Args:
            recordings: List of recording objects
            state: State manager
            dedup_data: Deduplicated data

        Returns:
            List of GherkinScenario objects
        """
        scenarios = []

        for recording in recordings:
            # Get recording data
            recording_data = state._state.recordings_data.get(recording.recording_id, {})

            actions = recording_data.get("actions", [])
            urls = recording_data.get("urls_visited", [])
            start_url = urls[0] if urls else ""

            if not actions:
                continue

            # Generate scenario name
            scenario_name = self._generate_scenario_name(recording, actions)

            # Get element names from dedup data
            element_names = self._get_element_names(dedup_data, recording.recording_id)

            # Generate scenario
            scenario = self.gherkin_gen.generate_scenario(
                name=scenario_name,
                actions=actions,
                recording_id=recording.recording_id,
                page_url=start_url,
                tags=self._generate_initial_tags(recording, actions),
                element_names=element_names,
            )

            # Set feature file reference
            scenario.feature_file = self._determine_feature_file(
                recording.recording_id,
                start_url,
            )

            scenarios.append(scenario)

        return scenarios

    def _generate_scenario_name(
        self,
        recording: Any,
        actions: list[dict[str, Any]],
    ) -> str:
        """
        Generate a descriptive scenario name.

        Args:
            recording: Recording object
            actions: List of actions

        Returns:
            Scenario name
        """
        # Use recording file name as base
        base_name = Path(recording.file_path).stem

        # Clean up name
        import re
        name = re.sub(r'[_-]', ' ', base_name)
        name = re.sub(r'([A-Z])', r' \1', name)
        name = ' '.join(word.capitalize() for word in name.split())

        return name or "Test Scenario"

    def _get_element_names(
        self,
        dedup_data: dict[str, Any],
        recording_id: str,
    ) -> dict[str, str]:
        """
        Get element names from deduplicated data.

        Args:
            dedup_data: Deduplicated data
            recording_id: Recording ID

        Returns:
            Dictionary mapping selector hashes to element names
        """
        element_names = {}

        # Get from selector catalog (ComponentElement objects)
        for entry_id, entry in dedup_data.get("selector_catalog", {}).items():
            if recording_id in entry.recordings:
                # Use metadata to get element name
                name = entry.metadata.get("name_suggestion", "")
                if name:
                    # Create hash from selector
                    import hashlib
                    selector_hash = hashlib.sha256(entry.selector.encode()).hexdigest()[:16]
                    element_names[selector_hash] = name

        return element_names

    def _generate_initial_tags(
        self,
        recording: Any,
        actions: list[dict[str, Any]],
    ) -> list[str]:
        """
        Generate initial tags for a scenario.

        Args:
            recording: Recording object
            actions: List of actions

        Returns:
            List of tags
        """
        tags = []

        # Add status tag
        if recording.status == "completed":
            tags.append("@ready")
        else:
            tags.append(f"@{recording.status}")

        # Analyze actions for tags
        action_types = {a.get("action_type") for a in actions}

        if "fill" in action_types or "type" in action_types:
            tags.append("@form")
        if "click" in action_types:
            tags.append("@interaction")
        if "check" in action_types or "uncheck" in action_types:
            tags.append("@checkbox")

        return tags

    def _determine_feature_file(
        self,
        recording_id: str,
        page_url: str,
    ) -> str:
        """
        Determine which feature file a scenario belongs to.

        Args:
            recording_id: Recording ID
            page_url: Page URL

        Returns:
            Feature file name
        """
        if self.config.feature_naming == "url_based":
            # Extract domain/path for feature name
            from urllib.parse import urlparse
            parsed = urlparse(page_url)
            path_part = parsed.path.replace("/", "_").strip("_")
            return f"{parsed.netloc}_{path_part}" if path_part else parsed.netloc

        elif self.config.feature_naming == "action_based":
            return f"test_feature"

        else:  # page_based (default)
            # Use page title or URL path
            from urllib.parse import urlparse
            parsed = urlparse(page_url)
            path_parts = [p for p in parsed.path.split("/") if p]
            if path_parts:
                return path_parts[-1]
            return "homepage"

    def _count_by_recording(
        self,
        scenarios: list[GherkinScenario],
    ) -> dict[str, int]:
        """
        Count scenarios per recording.

        Args:
            scenarios: List of scenarios

        Returns:
            Dictionary mapping recording IDs to scenario counts
        """
        counts: dict[str, int] = {}
        for scenario in scenarios:
            counts[scenario.recording_id] = counts.get(scenario.recording_id, 0) + 1
        return counts

    # =========================================================================
    # Scenario Optimization
    # =========================================================================

    def _optimize_scenarios(
        self,
        scenarios: list[GherkinScenario],
    ) -> list[GherkinScenario]:
        """
        Optimize scenarios.

        Args:
            scenarios: List of scenarios

        Returns:
            Optimized scenarios
        """
        if self.config.extract_backgrounds:
            # Extract common steps to backgrounds
            backgrounds = self.optimizer.extract_common_backgrounds(scenarios)
            # Apply backgrounds to scenarios
            for scenario in scenarios:
                for feature_background in backgrounds:
                    if self.optimizer.should_apply_background(scenario, feature_background):
                        scenario.background_steps = feature_background["steps"]

        if self.config.auto_tag_scenarios:
            # Auto-tag scenarios based on content
            for scenario in scenarios:
                tags = self.optimizer.generate_tags(scenario)
                scenario.tags.extend(tags)
                scenario.tags = list(set(scenario.tags))  # Deduplicate

        return scenarios

    # =========================================================================
    # Feature Grouping
    # =========================================================================

    def _group_scenarios_into_features(
        self,
        scenarios: list[GherkinScenario],
    ) -> list[dict[str, Any]]:
        """
        Group scenarios into features.

        Args:
            scenarios: List of scenarios

        Returns:
            List of feature dictionaries
        """
        if not self.config.group_by_feature:
            # Each scenario gets its own feature
            return [
                {
                    "name": f"Feature: {scenario.name}",
                    "description": "",
                    "scenarios": [scenario],
                    "background": None,
                }
                for scenario in scenarios
            ]

        # Group scenarios by feature file
        feature_groups: dict[str, list[GherkinScenario]] = {}
        for scenario in scenarios:
            feature_key = scenario.feature_file or "default"
            if feature_key not in feature_groups:
                feature_groups[feature_key] = []
            feature_groups[feature_key].append(scenario)

        # Create feature dictionaries
        features = []
        for feature_name, feature_scenarios in feature_groups.items():
            # Extract background for this feature
            background = None
            if self.config.extract_backgrounds:
                background = self.optimizer.extract_feature_background(feature_scenarios)

            features.append({
                "name": self._format_feature_name(feature_name),
                "description": self._generate_feature_description(feature_scenarios),
                "scenarios": feature_scenarios,
                "background": background,
            })

        return features

    def _format_feature_name(self, feature_key: str) -> str:
        """
        Format feature key into proper feature name.

        Args:
            feature_key: Feature key

        Returns:
            Formatted feature name
        """
        import re
        # Convert snake_case or kebab-case to Title Case
        name = re.sub(r'[_-]', ' ', feature_key)
        name = ' '.join(word.capitalize() for word in name.split())
        return f"Feature: {name}" if not name.startswith("Feature:") else name

    def _generate_feature_description(
        self,
        scenarios: list[GherkinScenario],
    ) -> str:
        """
        Generate feature description from scenarios.

        Args:
            scenarios: List of scenarios

        Returns:
            Feature description
        """
        if not scenarios:
            return ""

        # Collect unique tags
        all_tags = set()
        for scenario in scenarios:
            all_tags.update(scenario.tags)

        # Build description
        desc_parts = []
        if all_tags:
            desc_parts.append(f"Tags: {', '.join(sorted(all_tags))}")
        desc_parts.append(f"Scenarios: {len(scenarios)}")

        return "\n    ".join(desc_parts)

    # =========================================================================
    # File Generation
    # =========================================================================

    def _generate_feature_files(
        self,
        features: list[dict[str, Any]],
    ) -> list[str]:
        """
        Generate feature files.

        Args:
            features: List of feature dictionaries

        Returns:
            List of file paths created
        """
        created_files = []

        for feature in features:
            file_path = self.feature_mgr.write_feature_file(feature)
            if file_path:
                created_files.append(str(file_path))

        return created_files

    def _generate_step_definitions(
        self,
        scenarios: list[GherkinScenario],
    ) -> list[str]:
        """
        Generate step definition files.

        Args:
            scenarios: List of scenarios

        Returns:
            List of file paths created
        """
        created_files = []

        # Group scenarios by feature for step files
        feature_groups: dict[str, list[GherkinScenario]] = {}
        for scenario in scenarios:
            feature_key = scenario.feature_file or "default"
            if feature_key not in feature_groups:
                feature_groups[feature_key] = []
            feature_groups[feature_key].append(scenario)

        # Generate step file for each feature
        for feature_key, feature_scenarios in feature_groups.items():
            output_file = (
                self.project_path /
                self.config.steps_output_dir /
                f"{feature_key}_steps.py"
            )

            for scenario in feature_scenarios:
                self.step_gen.generate_from_scenario(scenario, output_file)

            created_files.append(str(output_file))

        return created_files

    # =========================================================================
    # State Update
    # =========================================================================

    def _update_state(
        self,
        state: StateManager,
        scenarios: list[GherkinScenario],
        features: list[dict[str, Any]],
        feature_files: list[str],
        step_files: list[str],
    ) -> None:
        """
        Update state with conversion results.

        Args:
            state: State manager
            scenarios: Generated scenarios
            features: Generated features
            feature_files: Feature file paths
            step_files: Step file paths
        """
        # Update scenarios in state
        for scenario in scenarios:
            from claude_playwright_agent.state.models import Scenario

            state.add_scenario(Scenario(
                scenario_id=scenario.scenario_id,
                feature_file=scenario.feature_file,
                scenario_name=scenario.name,
                recording_source=scenario.recording_id,
                tags=scenario.tags,
                line_number=scenario.line_number,
                steps_count=len(scenario.steps),
            ))

        # Save state
        state.save()


# =============================================================================
# Convenience Functions
# =============================================================================


def run_bdd_conversion(
    project_path: Path,
    config: BDDConversionConfig | None = None,
) -> BDDConversionResult:
    """
    Run BDD conversion on a project.

    Args:
        project_path: Path to the project
        config: Optional BDD conversion configuration

    Returns:
        BDDConversionResult with outcomes
    """
    agent = BDDConversionAgent(project_path, config)
    return agent.run()
