"""
E4.2 - Element Deduplication Logic Skill.

This skill provides element deduplication logic:
- Element matching with similarity scoring
- Context-aware element grouping
- Element relationship tracking
- Semantic element comparison
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class SimilarityMetric(str, Enum):
    """Similarity metrics for element comparison."""

    EXACT_MATCH = "exact_match"
    SELECTOR_SIMILARITY = "selector_similarity"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    CONTEXTUAL = "contextual"


@dataclass
class ElementSignature:
    """
    Unique signature for an element.

    Attributes:
        signature_id: Unique signature identifier
        selector_hash: Hash of selector
        context_hash: Hash of context
        combined_hash: Combined hash for uniqueness
        raw_selector: Raw selector string
        selector_type: Selector type
        created_at: When signature was created
    """

    signature_id: str = field(default_factory=lambda: f"sig_{uuid.uuid4().hex[:8]}")
    selector_hash: str = ""
    context_hash: str = ""
    combined_hash: str = ""
    raw_selector: str = ""
    selector_type: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signature_id": self.signature_id,
            "selector_hash": self.selector_hash,
            "context_hash": self.context_hash,
            "combined_hash": self.combined_hash,
            "raw_selector": self.raw_selector,
            "selector_type": self.selector_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_element(cls, element: dict[str, Any], context: dict[str, Any]) -> "ElementSignature":
        """Create signature from element and context."""
        selector = element.get("selector", {})
        raw_selector = selector.get("raw", "")
        selector_type = selector.get("type", "unknown")

        # Hash selector
        selector_hash = hashlib.md5(raw_selector.encode()).hexdigest()

        # Hash context
        context_str = str(sorted(context.items()))
        context_hash = hashlib.md5(context_str.encode()).hexdigest()

        # Combined hash
        combined = f"{selector_hash}:{context_hash}"
        combined_hash = hashlib.md5(combined.encode()).hexdigest()

        return cls(
            selector_hash=selector_hash,
            context_hash=context_hash,
            combined_hash=combined_hash,
            raw_selector=raw_selector,
            selector_type=selector_type,
        )


@dataclass
class ElementMatch:
    """
    A match between two elements.

    Attributes:
        match_id: Unique match identifier
        element_a_id: First element ID
        element_b_id: Second element ID
        similarity_score: Similarity score (0-1)
        match_type: Type of similarity
        match_context: Context at time of match
        confidence: Confidence in match
        timestamp: When match was detected
    """

    match_id: str = field(default_factory=lambda: f"match_{uuid.uuid4().hex[:8]}")
    element_a_id: str = ""
    element_b_id: str = ""
    similarity_score: float = 0.0
    match_type: SimilarityMetric = SimilarityMetric.SELECTOR_SIMILARITY
    match_context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "match_id": self.match_id,
            "element_a_id": self.element_a_id,
            "element_b_id": self.element_b_id,
            "similarity_score": self.similarity_score,
            "match_type": self.match_type.value,
            "match_context": self.match_context,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ElementGroup:
    """
    A group of similar elements.

    Attributes:
        group_id: Unique group identifier
        group_name: Suggested name for group
        element_ids: List of element IDs in group
        representative_selector: Representative selector
        similarity_threshold: Threshold used for grouping
        grouping_context: Context at time of grouping
        contexts: List of contexts for each element
        created_at: When group was created
    """

    group_id: str = field(default_factory=lambda: f"group_{uuid.uuid4().hex[:8]}")
    group_name: str = ""
    element_ids: list[str] = field(default_factory=list)
    representative_selector: str = ""
    similarity_threshold: float = 0.8
    grouping_context: dict[str, Any] = field(default_factory=dict)
    contexts: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "element_ids": self.element_ids,
            "representative_selector": self.representative_selector,
            "similarity_threshold": self.similarity_threshold,
            "grouping_context": self.grouping_context,
            "contexts": self.contexts,
            "created_at": self.created_at,
        }


@dataclass
class DeduplicationContext:
    """
    Context for element deduplication.

    Attributes:
        dedup_id: Unique deduplication identifier
        workflow_id: Associated workflow ID
        elements_analyzed: Number of elements analyzed
        matches_found: Number of matches found
        groups_created: Number of groups created
        deduplication_ratio: Ratio of elements to groups
        element_signatures: Element signatures
        element_groups: Created element groups
        started_at: When deduplication started
        completed_at: When deduplication completed
    """

    dedup_id: str = field(default_factory=lambda: f"dedup_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    elements_analyzed: int = 0
    matches_found: int = 0
    groups_created: int = 0
    deduplication_ratio: float = 0.0
    element_signatures: list[ElementSignature] = field(default_factory=list)
    element_groups: list[ElementGroup] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dedup_id": self.dedup_id,
            "workflow_id": self.workflow_id,
            "elements_analyzed": self.elements_analyzed,
            "matches_found": self.matches_found,
            "groups_created": self.groups_created,
            "deduplication_ratio": self.deduplication_ratio,
            "element_signatures": [s.to_dict() for s in self.element_signatures],
            "element_groups": [g.to_dict() for g in self.element_groups],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class ElementDeduplicationAgent(BaseAgent):
    """
    Element Deduplication Agent.

    This agent provides:
    1. Element matching with similarity scoring
    2. Context-aware element grouping
    3. Element relationship tracking
    4. Semantic element comparison
    """

    name = "e4_2_element_deduplication"
    version = "1.0.0"
    description = "E4.2 - Element Deduplication Logic"

    DEFAULT_SIMILARITY_THRESHOLD = 0.8

    def __init__(self, **kwargs) -> None:
        """Initialize the element deduplication agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E4.2 - Element Deduplication Logic agent for the Playwright test automation framework. You help users with e4.2 - element deduplication logic tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._deduplication_history: list[DeduplicationContext] = []
        self._element_registry: dict[str, dict[str, Any]] = {}
        self._signature_cache: dict[str, ElementSignature] = {}

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
        Execute element deduplication task.

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

        if task_type == "match_elements":
            return await self._match_elements(context, execution_context)
        elif task_type == "group_elements":
            return await self._group_elements(context, execution_context)
        elif task_type == "calculate_similarity":
            return await self._calculate_similarity(context, execution_context)
        elif task_type == "create_signature":
            return await self._create_signature(context, execution_context)
        elif task_type == "find_duplicates":
            return await self._find_duplicates(context, execution_context)
        elif task_type == "get_deduplication_context":
            return await self._get_deduplication_context(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _match_elements(self, context: dict[str, Any], execution_context: Any) -> str:
        """Match elements with similarity scoring."""
        elements = context.get("elements", [])
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not elements or len(elements) < 2:
            return "Error: at least 2 elements required for matching"

        matches = []

        # Compare each pair
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                element_a = elements[i]
                element_b = elements[j]

                # Calculate similarity
                similarity = self._calculate_element_similarity(element_a, element_b)

                if similarity >= self.DEFAULT_SIMILARITY_THRESHOLD:
                    match = ElementMatch(
                        element_a_id=element_a.get("element_id", f"element_{i}"),
                        element_b_id=element_b.get("element_id", f"element_{j}"),
                        similarity_score=similarity,
                        match_type=SimilarityMetric.SELECTOR_SIMILARITY,
                        match_context={
                            "workflow_id": workflow_id,
                            "recording_id": element_a.get("recording_id", ""),
                        },
                        confidence=similarity,
                    )
                    matches.append(match)

        return f"Found {len(matches)} match(es) with similarity >= {self.DEFAULT_SIMILARITY_THRESHOLD}"

    async def _group_elements(self, context: dict[str, Any], execution_context: Any) -> str:
        """Group similar elements with context tracking."""
        elements = context.get("elements", [])
        threshold = context.get("threshold", self.DEFAULT_SIMILARITY_THRESHOLD)
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not elements:
            return "Error: elements list is required"

        # Create deduplication context
        dedup_context = DeduplicationContext(
            workflow_id=workflow_id,
            elements_analyzed=len(elements),
        )

        # Create signatures for all elements
        signatures = []
        for element in elements:
            element_context = {
                "recording_id": element.get("recording_id", ""),
                "page_url": element.get("page_url", ""),
                "action_type": element.get("action_type", ""),
            }
            signature = ElementSignature.from_element(element, element_context)
            signatures.append(signature)
            self._signature_cache[signature.signature_id] = signature

        dedup_context.element_signatures = signatures

        # Group by similarity
        groups = self._group_by_similarity(elements, signatures, threshold, workflow_id)
        dedup_context.element_groups = groups
        dedup_context.groups_created = len(groups)
        dedup_context.completed_at = datetime.now().isoformat()

        if len(elements) > 0:
            dedup_context.deduplication_ratio = len(groups) / len(elements)

        self._deduplication_history.append(dedup_context)

        return f"Grouped {len(elements)} element(s) into {len(groups)} group(s)"

    async def _calculate_similarity(self, context: dict[str, Any], execution_context: Any) -> str:
        """Calculate similarity between two elements."""
        element_a = context.get("element_a")
        element_b = context.get("element_b")

        if not element_a or not element_b:
            return "Error: element_a and element_b are required"

        similarity = self._calculate_element_similarity(element_a, element_b)

        return f"Similarity: {similarity:.2f}"

    async def _create_signature(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create element signature."""
        element = context.get("element")
        element_context = context.get("element_context", {})

        if not element:
            return "Error: element is required"

        signature = ElementSignature.from_element(element, element_context)
        self._signature_cache[signature.signature_id] = signature

        return f"Created signature: {signature.signature_id}"

    async def _find_duplicates(self, context: dict[str, Any], execution_context: Any) -> str:
        """Find duplicate elements."""
        elements = context.get("elements", [])

        if not elements:
            return "Error: elements list is required"

        # Group by exact selector match
        selector_groups: dict[str, list[dict[str, Any]]] = {}
        for element in elements:
            selector = element.get("selector", {}).get("raw", "")
            if selector not in selector_groups:
                selector_groups[selector] = []
            selector_groups[selector].append(element)

        # Find duplicates
        duplicates = {s: elems for s, elems in selector_groups.items() if len(elems) > 1}

        return f"Found {len(duplicates)} duplicate selector(s) affecting {sum(len(e) for e in duplicates.values())} element(s)"

    async def _get_deduplication_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get deduplication context."""
        dedup_id = context.get("dedup_id")

        if not dedup_id:
            return "Error: dedup_id is required"

        for dedup_context in self._deduplication_history:
            if dedup_context.dedup_id == dedup_id:
                return (
                    f"Deduplication '{dedup_id}': "
                    f"{dedup_context.elements_analyzed} elements, "
                    f"{dedup_context.groups_created} groups, "
                    f"{dedup_context.deduplication_ratio:.2f} ratio"
                )

        return f"Error: Deduplication context '{dedup_id}' not found"

    def _calculate_element_similarity(self, element_a: dict[str, Any], element_b: dict[str, Any]) -> float:
        """Calculate similarity between two elements."""
        selector_a = element_a.get("selector", {})
        selector_b = element_b.get("selector", {})

        # Exact match
        if selector_a.get("raw") == selector_b.get("raw"):
            return 1.0

        # Selector similarity
        raw_a = selector_a.get("raw", "")
        raw_b = selector_b.get("raw", "")

        # Simple similarity based on common parts
        similarity = 0.0

        # Same selector type
        if selector_a.get("type") == selector_b.get("type"):
            similarity += 0.3

        # Common parts in selector
        parts_a = set(raw_a.replace('"', "'").split("'"))
        parts_b = set(raw_b.replace('"', "'").split("'"))

        if parts_a and parts_b:
            intersection = len(parts_a & parts_b)
            union = len(parts_a | parts_b)
            similarity += (intersection / union) * 0.7

        return min(similarity, 1.0)

    def _group_by_similarity(
        self,
        elements: list[dict[str, Any]],
        signatures: list[ElementSignature],
        threshold: float,
        workflow_id: str,
    ) -> list[ElementGroup]:
        """Group elements by similarity."""
        groups = []
        assigned_indices = set()

        for i, signature in enumerate(signatures):
            if i in assigned_indices:
                continue

            # Create new group
            group = ElementGroup(
                group_name=f"group_{len(groups)}",
                element_ids=[elements[i].get("element_id", f"element_{i}")],
                representative_selector=signature.raw_selector,
                similarity_threshold=threshold,
                grouping_context={"workflow_id": workflow_id},
                contexts=[{"element_index": i, "signature_id": signature.signature_id}],
            )

            # Find similar elements
            for j in range(i + 1, len(elements)):
                if j in assigned_indices:
                    continue

                similarity = self._calculate_element_similarity(elements[i], elements[j])
                if similarity >= threshold:
                    group.element_ids.append(elements[j].get("element_id", f"element_{j}"))
                    group.contexts.append({"element_index": j, "signature_id": signatures[j].signature_id})
                    assigned_indices.add(j)

            assigned_indices.add(i)
            groups.append(group)

        return groups

    def get_deduplication_history(self) -> list[DeduplicationContext]:
        """Get deduplication history."""
        return self._deduplication_history.copy()

    def get_signature_cache(self) -> dict[str, ElementSignature]:
        """Get signature cache."""
        return self._signature_cache.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

