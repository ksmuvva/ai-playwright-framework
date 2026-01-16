"""
E3.2 - Playwright Recording Parser Skill.
"""

from .main import (
    ActionContext,
    ActionType,
    ParserContext,
    PlaywrightParserAgent,
    SelectorContext,
    SelectorType,
)

# Aliases for test compatibility
ParseResult = ParserContext

__all__ = [
    "ActionContext",
    "ActionType",
    "ParserContext",
    "PlaywrightParserAgent",
    "SelectorContext",
    "SelectorType",
    # Alias
    "ParseResult",
]
