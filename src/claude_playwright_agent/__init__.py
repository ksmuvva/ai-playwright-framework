"""
Claude Playwright Agent

AI-powered test automation framework powered by Claude Agent SDK.
"""

__version__ = "0.1.0"
__author__ = "Claude Playwright Agent Team"
__email__ = "dev@claudeplaywright.ai"

from claude_playwright_agent.agents import TestAgent, DebugAgent, ReportAgent
from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.state import StateManager

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "ConfigManager",
    "StateManager",
    "TestAgent",
    "DebugAgent",
    "ReportAgent",
]
