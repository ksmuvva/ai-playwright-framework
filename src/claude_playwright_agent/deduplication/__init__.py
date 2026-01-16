"""
Deduplication module for identifying common elements and components.

This module provides:
- Element deduplication across recordings
- Component extraction and grouping
- Page object generation
- Selector catalog management
"""

from claude_playwright_agent.deduplication.agent import (
    DeduplicationAgent,
    DeduplicationConfig,
    DeduplicationResult,
)
from claude_playwright_agent.deduplication.logic import (
    DeduplicationLogic,
    ElementGroup,
    ElementContext,
)
from claude_playwright_agent.deduplication.selector_catalog import SelectorCatalog
from claude_playwright_agent.deduplication.page_objects import PageObjectGenerator

__all__ = [
    "DeduplicationAgent",
    "DeduplicationConfig",
    "DeduplicationResult",
    "DeduplicationLogic",
    "ElementGroup",
    "ElementContext",
    "SelectorCatalog",
    "PageObjectGenerator",
]
