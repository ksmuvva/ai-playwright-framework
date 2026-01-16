"""
E3.4 - Selector Analysis & Enhancement Skill.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any

from .main import (
    EnhancedSelector,
    SelectorAnalysisAgent,
    SelectorAnalysisContext,
    SelectorIssue,
    SelectorIssueDetail,
    SelectorStability,
)

# Missing class for test compatibility
class SelectorType(str, Enum):
    """Selector type enum."""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ROLE = "role"

# Aliases for test compatibility
SelectorInfo = SelectorAnalysisContext

__all__ = [
    "EnhancedSelector",
    "SelectorAnalysisAgent",
    "SelectorAnalysisContext",
    "SelectorIssue",
    "SelectorIssueDetail",
    "SelectorStability",
    # Missing class
    "SelectorType",
    # Alias
    "SelectorInfo",
]
