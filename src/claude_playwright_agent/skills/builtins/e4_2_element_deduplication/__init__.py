"""
E4.2 - Element Deduplication Logic Skill.
"""

from .main import (
    DeduplicationContext,
    ElementDeduplicationAgent,
    ElementGroup,
    ElementMatch,
    ElementSignature,
    SimilarityMetric,
)

# Aliases for test compatibility
ElementCluster = ElementGroup
SimilarityScore = SimilarityMetric

__all__ = [
    "DeduplicationContext",
    "ElementDeduplicationAgent",
    "ElementGroup",
    "ElementMatch",
    "ElementSignature",
    "SimilarityMetric",
    # Aliases
    "ElementCluster",
    "SimilarityScore",
]
