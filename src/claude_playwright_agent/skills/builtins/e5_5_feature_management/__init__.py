"""
E5.5 - Feature File Management Skill.
"""

from dataclasses import dataclass, field

from .main import (
    FeatureFileContent,
    FeatureFileManagementAgent,
    FeatureFileMetadata,
    FileManagementContext,
    FileStatus,
    FileVersion,
)

# Missing class for test compatibility
@dataclass
class Feature:
    """Feature dataclass for test compatibility."""
    feature_id: str
    feature_name: str
    file_path: str
    scenarios: list[str] = field(default_factory=list)

# Aliases for test compatibility
FeatureFile = FeatureFileContent
FeatureManagementAgent = FeatureFileManagementAgent

__all__ = [
    "FeatureFileContent",
    "FeatureFileManagementAgent",
    "FeatureFileMetadata",
    "FileManagementContext",
    "FileStatus",
    "FileVersion",
    # Missing class
    "Feature",
    # Aliases
    "FeatureFile",
    "FeatureManagementAgent",
]
