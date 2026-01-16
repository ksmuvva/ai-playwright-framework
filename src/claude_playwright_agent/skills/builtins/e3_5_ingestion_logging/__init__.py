"""
E3.5 - Ingestion Logging & Tracking Skill.
"""

from .main import (
    IngestionLoggingAgent,
    IngestionMetrics,
    LogLevel,
    LoggingContext,
    PipelineLogEntry,
    PipelineStage,
    ProgressTracker,
)

# Aliases for test compatibility
LogEntry = PipelineLogEntry

__all__ = [
    "IngestionLoggingAgent",
    "IngestionMetrics",
    "LogLevel",
    "LoggingContext",
    "PipelineLogEntry",
    "PipelineStage",
    "ProgressTracker",
    # Alias
    "LogEntry",
]
