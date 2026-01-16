"""
E4.1 - Deduplication Agent Skill.

This skill provides deduplication agent functionality:
- Recording analysis with context tracking
- Pattern detection across recordings
- Selector frequency analysis
- Reusable element identification
"""

import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class AnalysisStage(str, Enum):
    """Deduplication analysis stages."""

    INITIALIZED = "initialized"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    GROUPING = "grouping"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SelectorFrequency:
    """
    Frequency data for a selector.

    Attributes:
        selector_id: Unique selector identifier
        raw_selector: Raw selector string
        count: Number of occurrences
        recordings: List of recording IDs where found
        contexts: List of context snapshots for each occurrence
        confidence: Confidence score (0-1)
        analyzed_at: When analysis was performed
    """

    selector_id: str = field(default_factory=lambda: f"sel_freq_{uuid.uuid4().hex[:8]}")
    raw_selector: str = ""
    count: int = 0
    recordings: list[str] = field(default_factory=list)
    contexts: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector_id": self.selector_id,
            "raw_selector": self.raw_selector,
            "count": self.count,
            "recordings": self.recordings,
            "contexts": self.contexts,
            "confidence": self.confidence,
            "analyzed_at": self.analyzed_at,
        }


@dataclass
class PatternMatch:
    """
    A matched pattern across recordings.

    Attributes:
        match_id: Unique match identifier
        pattern_type: Type of pattern (selector, action_sequence, url)
        pattern_value: Pattern value
        occurrences: List of occurrence data with context
        strength: Match strength (0-1)
        deduplication_context: Context for deduplication decision
    """

    match_id: str = field(default_factory=lambda: f"match_{uuid.uuid4().hex[:8]}")
    pattern_type: str = ""
    pattern_value: str = ""
    occurrences: list[dict[str, Any]] = field(default_factory=list)
    strength: float = 0.0
    deduplication_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "match_id": self.match_id,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "occurrences": self.occurrences,
            "strength": self.strength,
            "deduplication_context": self.deduplication_context,
        }


@dataclass
class DeduplicationAnalysisContext:
    """
    Context for deduplication analysis.

    Attributes:
        analysis_id: Unique analysis identifier
        workflow_id: Associated workflow ID
        recording_ids: List of recording IDs being analyzed
        current_stage: Current analysis stage
        total_selectors: Total selectors found
        unique_selectors: Unique selectors found
        repeated_selectors: Repeated selectors found
        patterns: List of pattern matches
        started_at: When analysis started
        completed_at: When analysis completed
        context_preserved: Whether context was preserved
    """

    analysis_id: str = field(default_factory=lambda: f"dedup_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    recording_ids: list[str] = field(default_factory=list)
    current_stage: AnalysisStage = AnalysisStage.INITIALIZED
    total_selectors: int = 0
    unique_selectors: int = 0
    repeated_selectors: int = 0
    patterns: list[PatternMatch] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "workflow_id": self.workflow_id,
            "recording_ids": self.recording_ids,
            "current_stage": self.current_stage.value,
            "total_selectors": self.total_selectors,
            "unique_selectors": self.unique_selectors,
            "repeated_selectors": self.repeated_selectors,
            "patterns": [p.to_dict() for p in self.patterns],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class DeduplicationAgent(BaseAgent):
    """
    Deduplication Agent.

    This agent provides:
    1. Recording analysis with context tracking
    2. Pattern detection across recordings
    3. Selector frequency analysis
    4. Reusable element identification
    """

    name = "e4_1_deduplication_agent"
    version = "1.0.0"
    description = "E4.1 - Deduplication Agent"

    # Minimum threshold for considering a pattern as "repeated"
    MIN_SELECTOR_COUNT = 2
    MIN_CONFIDENCE = 0.5

    def __init__(self, **kwargs) -> None:
        """Initialize the deduplication agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E4.1 - Deduplication Agent agent for the Playwright test automation framework. You help users with e4.1 - deduplication agent tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._selector_counts: Counter = Counter()
        self._selector_sources: dict[str, set[str]] = defaultdict(set)
        self._selector_contexts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._analysis_history: list[DeduplicationAnalysisContext] = []

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute deduplication task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the deduplication operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "analyze_recordings":
            return await self._analyze_recordings(context, execution_context)
        elif task_type == "find_repeated_selectors":
            return await self._find_repeated_selectors(context, execution_context)
        elif task_type == "calculate_frequency":
            return await self._calculate_frequency(context, execution_context)
        elif task_type == "detect_patterns":
            return await self._detect_patterns(context, execution_context)
        elif task_type == "get_analysis_context":
            return await self._get_analysis_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _analyze_recordings(self, context: dict[str, Any], execution_context: Any) -> str:
        """Analyze multiple recordings with full context tracking."""
        recordings = context.get("recordings", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not recordings:
            return "Error: recordings list is required"

        # Create analysis context
        analysis_context = DeduplicationAnalysisContext(
            workflow_id=workflow_id,
            recording_ids=[r.get("recording_id", r.get("test_name", f"recording_{i}"))
                          for i, r in enumerate(recordings)],
        )

        # Reset state
        self._selector_counts = Counter()
        self._selector_sources = defaultdict(set)
        self._selector_contexts = defaultdict(list)

        # Advance stage
        analysis_context.current_stage = AnalysisStage.COLLECTING

        # Collect selectors with context from each recording
        for recording in recordings:
            recording_id = recording.get("recording_id", recording.get("test_name", ""))
            actions = recording.get("actions", [])

            for action in actions:
                selector = action.get("selector", {})
                raw_selector = selector.get("raw", "")

                if raw_selector:
                    self._selector_counts[raw_selector] += 1
                    self._selector_sources[raw_selector].add(recording_id)

                    # Preserve context for this occurrence
                    self._selector_contexts[raw_selector].append({
                        "recording_id": recording_id,
                        "action_type": action.get("action_type", ""),
                        "page_url": action.get("page_url", ""),
                        "line_number": action.get("line_number", -1),
                        "timestamp": action.get("timestamp", datetime.now().isoformat()),
                    })

        # Advance stage
        analysis_context.current_stage = AnalysisStage.ANALYZING
        analysis_context.total_selectors = sum(self._selector_counts.values())
        analysis_context.unique_selectors = len(self._selector_counts)

        # Find repeated selectors
        repeated = [s for s, c in self._selector_counts.items() if c >= self.MIN_SELECTOR_COUNT]
        analysis_context.repeated_selectors = len(repeated)

        # Generate pattern matches
        for raw_selector in repeated:
            count = self._selector_counts[raw_selector]
            max_count = max(self._selector_counts.values()) if self._selector_counts else 1
            confidence = min(count / max_count, 1.0)

            pattern_match = PatternMatch(
                pattern_type="selector",
                pattern_value=raw_selector,
                occurrences=[
                    {
                        "recording_id": rec_id,
                        "context": ctx,
                    }
                    for rec_id, ctx in zip(self._selector_sources[raw_selector],
                                         self._selector_contexts[raw_selector])
                ],
                strength=confidence,
                deduplication_context={
                    "workflow_id": workflow_id,
                    "analysis_id": analysis_context.analysis_id,
                    "selector_count": count,
                },
            )
            analysis_context.patterns.append(pattern_match)

        # Complete analysis
        analysis_context.current_stage = AnalysisStage.COMPLETED
        analysis_context.completed_at = datetime.now().isoformat()

        self._analysis_history.append(analysis_context)

        return (
            f"Analyzed {len(recordings)} recording(s): "
            f"{analysis_context.unique_selectors} unique selectors, "
            f"{analysis_context.repeated_selectors} repeated, "
            f"{len(analysis_context.patterns)} patterns found"
        )

    async def _find_repeated_selectors(self, context: dict[str, Any], execution_context: Any) -> str:
        """Find repeated selectors with context."""
        min_count = context.get("min_count", self.MIN_SELECTOR_COUNT)

        repeated = [
            (selector, count, list(self._selector_sources[selector]))
            for selector, count in self._selector_counts.items()
            if count >= min_count
        ]

        # Sort by frequency
        repeated.sort(key=lambda x: x[1], reverse=True)

        return (
            f"Found {len(repeated)} repeated selector(s): "
            f"{[(s, c) for s, c, _ in repeated[:5]]}"
        )

    async def _calculate_frequency(self, context: dict[str, Any], execution_context: Any) -> str:
        """Calculate selector frequency with context."""
        selector = context.get("selector")

        if not selector:
            return "Error: selector is required"

        raw = selector.get("raw", selector) if isinstance(selector, dict) else selector
        count = self._selector_counts.get(raw, 0)
        sources = list(self._selector_sources.get(raw, set()))
        contexts = self._selector_contexts.get(raw, [])

        return f"Selector '{raw}' appears {count} time(s) in {len(sources)} recording(s)"

    async def _detect_patterns(self, context: dict[str, Any], execution_context: Any) -> str:
        """Detect patterns with context."""
        pattern_type = context.get("pattern_type", "selector")

        if pattern_type == "selector":
            patterns = [
                {
                    "type": "selector",
                    "value": selector,
                    "count": count,
                    "sources": list(sources),
                    "contexts": self._selector_contexts[selector],
                }
                for selector, count, sources in [
                    (s, c, self._selector_sources[s])
                    for s, c in self._selector_counts.items()
                    if c >= self.MIN_SELECTOR_COUNT
                ][:10]  # Top 10
            ]
            return f"Detected {len(patterns)} selector pattern(s)"

        return f"Pattern type '{pattern_type}' not yet supported"

    async def _get_analysis_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get analysis context."""
        analysis_id = context.get("analysis_id")

        if not analysis_id:
            return "Error: analysis_id is required"

        for analysis_context in self._analysis_history:
            if analysis_context.analysis_id == analysis_id:
                return (
                    f"Analysis '{analysis_id}': "
                    f"{analysis_context.unique_selectors} unique, "
                    f"{analysis_context.repeated_selectors} repeated, "
                    f"{len(analysis_context.patterns)} patterns"
                )

        return f"Error: Analysis context '{analysis_id}' not found"

    def get_selector_counts(self) -> Counter:
        """Get selector frequency counts."""
        return self._selector_counts.copy()

    def get_analysis_history(self) -> list[DeduplicationAnalysisContext]:
        """Get analysis history."""
        return self._analysis_history.copy()

    def get_selector_contexts(self, selector: str) -> list[dict[str, Any]]:
        """Get contexts for a specific selector."""
        return self._selector_contexts.get(selector, []).copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

