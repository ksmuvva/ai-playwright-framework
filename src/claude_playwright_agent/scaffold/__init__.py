"""
Project Scaffolding Module for Claude Playwright Agent.

This module provides template-based project scaffolding with:
- Multiple project templates (basic, advanced, ecommerce, custom)
- Framework-specific templates (behave, pytest-bdd)
- Template file generation
- Configuration file creation
- CI/CD pipeline generation
- Custom template support
- Template validation
"""

from claude_playwright_agent.scaffold.manager import TemplateManager
from claude_playwright_agent.scaffold.models import (
    ScaffoldContext,
    ScaffoldOptions,
    TemplateMetadata,
    ProjectTemplate,
    FrameworkType,
)
from claude_playwright_agent.scaffold.cicd import (
    CICDTemplateGenerator,
    CIConfig,
    CIPlatform,
    TestFramework as CICTestFramework,
    generate_ci_config,
)

__all__ = [
    "TemplateManager",
    "ScaffoldContext",
    "ScaffoldOptions",
    "TemplateMetadata",
    "ProjectTemplate",
    "FrameworkType",
    "CICDTemplateGenerator",
    "CIConfig",
    "CIPlatform",
    "CICTestFramework",
    "generate_ci_config",
]
