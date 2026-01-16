"""
E3.4 - Selector Analysis & Enhancement Skill.

This skill provides selector analysis and enhancement:
- Selector fragility analysis
- Robust fallback selector generation
- Selector enhancement suggestions
- Context-aware selector optimization
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class SelectorStability(str, Enum):
    """Selector stability levels."""

    STABLE = "stable"
    MODERATE = "moderate"
    FRAGILE = "fragile"
    CRITICAL = "critical"


class SelectorIssue(str, Enum):
    """Types of selector issues."""

    DYNAMIC_CLASSES = "dynamic_classes"
    DYNAMIC_IDS = "dynamic_ids"
    NESTED_SELECTORS = "nested_selectors"
    INDEX_BASED = "index_based"
    FRAGILE_ATTRIBUTES = "fragile_attributes"
    NO_FALLBACKS = "no_fallbacks"
    LONG_CHAINS = "long_chains"


@dataclass
class SelectorIssueDetail:
    """
    Detail about a selector issue.

    Attributes:
        issue_type: Type of issue
        severity: Issue severity
        description: Issue description
        suggestion: Suggested fix
        location: Location in selector
    """

    issue_type: SelectorIssue
    severity: str = "warning"
    description: str = ""
    suggestion: str = ""
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
            "location": self.location,
        }


@dataclass
class EnhancedSelector:
    """
    An enhanced selector with context.

    Attributes:
        selector_id: Unique selector identifier
        original_selector: Original selector from recording
        primary_selector: Primary (most stable) selector
        fallback_selectors: List of fallback selectors
        stability: Stability rating
        issues: List of identified issues
        enhancement_suggestions: List of enhancement suggestions
        context: Selector usage context
        confidence: Confidence in this selector
        generated_at: When selector was enhanced
    """

    selector_id: str = field(default_factory=lambda: f"sel_enh_{uuid.uuid4().hex[:8]}")
    original_selector: str = ""
    primary_selector: str = ""
    fallback_selectors: list[str] = field(default_factory=list)
    stability: SelectorStability = SelectorStability.MODERATE
    issues: list[SelectorIssueDetail] = field(default_factory=list)
    enhancement_suggestions: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector_id": self.selector_id,
            "original_selector": self.original_selector,
            "primary_selector": self.primary_selector,
            "fallback_selectors": self.fallback_selectors,
            "stability": self.stability.value,
            "issues": [i.to_dict() for i in self.issues],
            "enhancement_suggestions": self.enhancement_suggestions,
            "context": self.context,
            "confidence": self.confidence,
            "generated_at": self.generated_at,
        }


@dataclass
class SelectorAnalysisContext:
    """
    Context for selector analysis.

    Attributes:
        analysis_id: Unique analysis identifier
        recording_id: Associated recording ID
        extraction_id: Associated extraction ID
        analysis_started: When analysis started
        analysis_completed: When analysis completed
        total_selectors: Number of selectors analyzed
        stable_selectors: Number of stable selectors
        fragile_selectors: Number of fragile selectors
        issues_found: Total issues found
        metadata: Additional analysis metadata
    """

    analysis_id: str = field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}")
    recording_id: str = ""
    extraction_id: str = ""
    analysis_started: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_completed: str = ""
    total_selectors: int = 0
    stable_selectors: int = 0
    fragile_selectors: int = 0
    issues_found: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "recording_id": self.recording_id,
            "extraction_id": self.extraction_id,
            "analysis_started": self.analysis_started,
            "analysis_completed": self.analysis_completed,
            "total_selectors": self.total_selectors,
            "stable_selectors": self.stable_selectors,
            "fragile_selectors": self.fragile_selectors,
            "issues_found": self.issues_found,
            "metadata": self.metadata,
        }


class SelectorAnalysisAgent(BaseAgent):
    """
    Selector Analysis and Enhancement Agent.

    This agent provides:
    1. Selector fragility analysis
    2. Robust fallback selector generation
    3. Selector enhancement suggestions
    4. Context-aware selector optimization
    """

    name = "e3_4_selector_analysis"
    version = "1.0.0"
    description = "E3.4 - Selector Analysis & Enhancement"

    def __init__(self, **kwargs) -> None:
        """Initialize the selector analysis agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E3.4 - Selector Analysis & Enhancement agent for the Playwright test automation framework. You help users with e3.4 - selector analysis & enhancement tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._analysis_history: list[SelectorAnalysisContext] = []

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
        Execute selector analysis task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the analysis operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "analyze_selector":
            return await self._analyze_selector(context, execution_context)
        elif task_type == "enhance_selector":
            return await self._enhance_selector(context, execution_context)
        elif task_type == "generate_fallbacks":
            return await self._generate_fallbacks(context, execution_context)
        elif task_type == "assess_stability":
            return await self._assess_stability(context, execution_context)
        elif task_type == "batch_analyze":
            return await self._batch_analyze(context, execution_context)
        elif task_type == "get_analysis_context":
            return await self._get_analysis_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _analyze_selector(self, context: dict[str, Any], execution_context: Any) -> str:
        """Analyze a single selector with context."""
        selector = context.get("selector")
        recording_id = context.get("recording_id", "")
        selector_context = context.get("selector_context", {})

        if not selector:
            return "Error: selector is required"

        # Analyze selector
        enhanced_selector = EnhancedSelector(
            original_selector=selector,
            context={
                "recording_id": recording_id,
                **selector_context,
            },
        )

        # Detect issues
        issues = self._detect_selector_issues(selector)
        enhanced_selector.issues = issues

        # Assess stability
        stability = self._assess_selector_stability(selector, issues)
        enhanced_selector.stability = stability

        # Generate primary selector (might be the same or improved)
        enhanced_selector.primary_selector = self._improve_selector(selector, issues)

        # Generate suggestions
        suggestions = self._generate_enhancement_suggestions(selector, issues)
        enhanced_selector.enhancement_suggestions = suggestions

        return f"Selector analyzed: stability={stability.value}, issues={len(issues)}"

    async def _enhance_selector(self, context: dict[str, Any], execution_context: Any) -> str:
        """Enhance a selector with fallbacks."""
        selector = context.get("selector")

        if not selector:
            return "Error: selector is required"

        # Create enhanced selector
        enhanced_selector = EnhancedSelector(
            original_selector=selector,
            primary_selector=selector,
        )

        # Analyze and generate fallbacks
        issues = self._detect_selector_issues(selector)
        fallbacks = self._generate_all_fallbacks(selector, issues)
        enhanced_selector.fallback_selectors = fallbacks

        # Choose best primary
        if fallbacks:
            enhanced_selector.primary_selector = self._choose_best_selector(selector, fallbacks)

        # Update stability
        enhanced_selector.stability = self._assess_selector_stability(
            enhanced_selector.primary_selector,
            []
        )

        return f"Selector enhanced with {len(fallbacks)} fallback(s)"

    async def _generate_fallbacks(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate fallback selectors for a selector."""
        selector = context.get("selector")
        max_fallbacks = context.get("max_fallbacks", 5)

        if not selector:
            return "Error: selector is required"

        issues = self._detect_selector_issues(selector)
        fallbacks = self._generate_all_fallbacks(selector, issues)

        # Limit fallbacks
        fallbacks = fallbacks[:max_fallbacks]

        return f"Generated {len(fallbacks)} fallback(s): {fallbacks[:3]}"

    async def _assess_stability(self, context: dict[str, Any], execution_context: Any) -> str:
        """Assess selector stability."""
        selector = context.get("selector")

        if not selector:
            return "Error: selector is required"

        issues = self._detect_selector_issues(selector)
        stability = self._assess_selector_stability(selector, issues)

        return f"Selector stability: {stability.value}"

    async def _batch_analyze(self, context: dict[str, Any], execution_context: Any) -> str:
        """Analyze multiple selectors with context tracking."""
        selectors = context.get("selectors", [])
        recording_id = context.get("recording_id", "")
        extraction_id = context.get("extraction_id", getattr(execution_context, "extraction_id", execution_context.get("extraction_id", "")))

        if not selectors:
            return "Error: selectors list is required"

        # Create analysis context
        analysis_context = SelectorAnalysisContext(
            recording_id=recording_id,
            extraction_id=extraction_id,
        )

        enhanced_selectors = []

        for selector in selectors:
            enhanced = EnhancedSelector(
                original_selector=selector,
                context={
                    "recording_id": recording_id,
                },
            )

            # Analyze
            issues = self._detect_selector_issues(selector)
            enhanced.issues = issues
            enhanced.stability = self._assess_selector_stability(selector, issues)
            enhanced.primary_selector = self._improve_selector(selector, issues)
            enhanced.fallback_selectors = self._generate_all_fallbacks(selector, issues)

            enhanced_selectors.append(enhanced)

            # Update counts
            analysis_context.total_selectors += 1
            if enhanced.stability in (SelectorStability.STABLE,):
                analysis_context.stable_selectors += 1
            else:
                analysis_context.fragile_selectors += 1
            analysis_context.issues_found += len(issues)

        analysis_context.analysis_completed = datetime.now().isoformat()
        self._analysis_history.append(analysis_context)

        return f"Analyzed {len(selectors)} selector(s): {analysis_context.stable_selectors} stable, {analysis_context.fragile_selectors} fragile"

    async def _get_analysis_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get analysis context."""
        analysis_id = context.get("analysis_id")

        if not analysis_id:
            return "Error: analysis_id is required"

        for analysis_context in self._analysis_history:
            if analysis_context.analysis_id == analysis_id:
                return (
                    f"Analysis '{analysis_id}': {analysis_context.total_selectors} selectors, "
                    f"{analysis_context.issues_found} issues"
                )

        return f"Error: Analysis context '{analysis_id}' not found"

    def _detect_selector_issues(self, selector: str) -> list[SelectorIssueDetail]:
        """Detect issues in a selector."""
        issues = []

        # Check for dynamic classes
        if re.search(r'class=["\'][^"\']*[\d]{8,}[^"\']*["\']', selector):
            issues.append(SelectorIssueDetail(
                issue_type=SelectorIssue.DYNAMIC_CLASSES,
                description="Selector contains potentially dynamic class names",
                suggestion="Use more stable attributes like data-testid",
                location="class attribute",
            ))

        # Check for dynamic IDs
        if re.search(r'id=["\'][^"\']*[\d]{8,}[^"\']*["\']', selector):
            issues.append(SelectorIssueDetail(
                issue_type=SelectorIssue.DYNAMIC_IDS,
                description="Selector contains potentially dynamic ID values",
                suggestion="Use data-testid or other stable attributes",
                location="id attribute",
            ))

        # Check for index-based selectors
        if ":nth-of-type" in selector or ":nth-child" in selector:
            issues.append(SelectorIssueDetail(
                issue_type=SelectorIssue.INDEX_BASED,
                description="Selector uses index-based selection",
                suggestion="Use attributes or text content instead",
                location="pseudo-class",
            ))

        # Check for long selector chains
        chain_length = len(selector.split(" "))
        if chain_length > 5:
            issues.append(SelectorIssueDetail(
                issue_type=SelectorIssue.LONG_CHAINS,
                description=f"Selector chain is long ({chain_length} elements)",
                suggestion="Shorten selector chain or use data-testid",
                location="entire selector",
            ))

        return issues

    def _assess_selector_stability(self, selector: str, issues: list) -> SelectorStability:
        """Assess selector stability."""
        # Best indicators
        if "data-testid" in selector or "data-test" in selector:
            return SelectorStability.STABLE

        # Good indicators
        if "id=" in selector or "#" in selector:
            if any(i.issue_type == SelectorIssue.DYNAMIC_IDS for i in issues):
                return SelectorStability.FRAGILE
            return SelectorStability.MODERATE

        # Poor indicators
        if len(issues) == 0:
            return SelectorStability.MODERATE
        elif len(issues) <= 2:
            return SelectorStability.FRAGILE
        else:
            return SelectorStability.CRITICAL

    def _improve_selector(self, selector: str, issues: list) -> str:
        """Improve a selector based on detected issues."""
        # If no issues, return as-is
        if not issues:
            return selector

        # Try to add data-testid suggestion
        for issue in issues:
            if issue.issue_type in (SelectorIssue.DYNAMIC_CLASSES, SelectorIssue.DYNAMIC_IDS):
                # Suggest data-testid
                return f"[data-testid={self._extract_test_id_from_selector(selector)}]"

        return selector

    def _extract_test_id_from_selector(self, selector: str) -> str:
        """Extract a test ID from selector."""
        # Remove common prefixes
        cleaned = selector.replace("#", "").replace(".", "").replace("[", "").replace("]", "")
        # Extract alphanumeric parts
        parts = re.split(r'[\s>+~]', cleaned)
        if parts:
            # Use the last meaningful part
            return parts[-1].replace('"', "").replace("'", "")
        return "element"

    def _generate_enhancement_suggestions(self, selector: str, issues: list) -> list[str]:
        """Generate enhancement suggestions."""
        suggestions = []

        for issue in issues:
            suggestions.append(issue.suggestion)

        if "data-testid" not in selector.lower():
            suggestions.append("Add data-testid attribute to element for stable selection")

        return suggestions

    def _generate_all_fallbacks(self, selector: str, issues: list) -> list[str]:
        """Generate all fallback selectors."""
        fallbacks = []

        # Original selector
        fallbacks.append(selector)

        # Generate text-based fallback
        text_match = re.search(r'text["\']=(.+?)["\']', selector)
        if text_match:
            fallbacks.append(text_match.group(0))
        else:
            # Try to extract text from selector
            if "=" in selector:
                parts = selector.split("=")
                if len(parts) > 1:
                    value = parts[-1].strip("'\"]")
                    if value and not value.startswith("{"):
                        fallbacks.append(f'text="{value}"')

        # Generate aria-based fallback
        if "aria-" not in selector.lower():
            aria_fallback = self._generate_aria_fallback(selector)
            if aria_fallback:
                fallbacks.append(aria_fallback)

        # Generate role-based fallback
        role_fallback = self._generate_role_fallback(selector)
        if role_fallback:
            fallbacks.append(role_fallback)

        # Generate label-based fallback
        label_fallback = self._generate_label_fallback(selector)
        if label_fallback:
            fallbacks.append(label_fallback)

        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for fb in fallbacks:
            if fb not in seen:
                seen.add(fb)
                unique_fallbacks.append(fb)

        return unique_fallbacks

    def _generate_aria_fallback(self, selector: str) -> str | None:
        """Generate ARIA-based fallback selector."""
        # Try to extract element info and create aria selector
        if "=" in selector:
            parts = selector.split("=")
            if len(parts) > 1:
                attr = parts[-2].split("[")[-1]
                value = parts[-1].strip("'\"]")
                if attr and value:
                    return f'[aria-{attr}="{value}"]'
        return None

    def _generate_role_fallback(self, selector: str) -> str | None:
        """Generate role-based fallback selector."""
        # Infer role from selector
        if "button" in selector.lower():
            return 'getByRole("button")'
        elif "input" in selector.lower():
            return 'getByRole("textbox")'
        elif "link" in selector.lower() or "a>" in selector:
            return 'getByRole("link")'
        return None

    def _generate_label_fallback(self, selector: str) -> str | None:
        """Generate label-based fallback selector."""
        # Try to extract label
        if "=" in selector:
            parts = selector.split("=")
            if len(parts) > 1:
                value = parts[-1].strip("'\"]")
                if value and len(value) < 50:
                    return f'getByText("{value}")'
        return None

    def _choose_best_selector(self, original: str, fallbacks: list[str]) -> str:
        """Choose the best selector from original and fallbacks."""
        # Prioritize: data-testid > text > role > aria > original
        priority = ["data-testid", "text=", "getByRole", "aria-"]

        for fb in fallbacks:
            for p in priority:
                if p in fb:
                    return fb

        return fallbacks[0] if fallbacks else original

    def get_analysis_history(self) -> list[SelectorAnalysisContext]:
        """Get analysis history."""
        return self._analysis_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

