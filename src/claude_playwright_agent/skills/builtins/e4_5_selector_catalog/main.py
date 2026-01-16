"""
E4.5 - Selector Catalog Management Skill.

This skill provides selector catalog management functionality:
- Selector registration with context
- Selector lookup and retrieval
- Catalog version control
- Selector lifecycle tracking
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class SelectorStatus(str, Enum):
    """Selector lifecycle status."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    STABLE = "stable"
    FRAGILE = "fragile"
    ARCHIVED = "archived"


@dataclass
class SelectorEntry:
    """
    A selector entry in the catalog.

    Attributes:
        entry_id: Unique entry identifier
        selector: Raw selector string
        selector_type: Type of selector
        status: Current status
        stability: Stability rating
        contexts: List of contexts where selector is used
        first_seen: When selector was first seen
        last_seen: When selector was last seen
        usage_count: Number of times used
        version: Selector version
        aliases: Alternative selectors
        metadata: Additional metadata
    """

    entry_id: str = field(default_factory=lambda: f"entry_{uuid.uuid4().hex[:8]}")
    selector: str = ""
    selector_type: str = ""
    status: SelectorStatus = SelectorStatus.ACTIVE
    stability: str = "moderate"
    contexts: list[dict[str, Any]] = field(default_factory=list)
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 1
    version: int = 1
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "status": self.status.value,
            "stability": self.stability,
            "contexts": self.contexts,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "usage_count": self.usage_count,
            "version": self.version,
            "aliases": self.aliases,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectorEntry":
        """Create from dictionary."""
        return cls(
            entry_id=data.get("entry_id", ""),
            selector=data.get("selector", ""),
            selector_type=data.get("selector_type", ""),
            status=SelectorStatus(data.get("status", SelectorStatus.ACTIVE)),
            stability=data.get("stability", "moderate"),
            contexts=data.get("contexts", []),
            first_seen=data.get("first_seen", ""),
            last_seen=data.get("last_seen", ""),
            usage_count=data.get("usage_count", 1),
            version=data.get("version", 1),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CatalogVersion:
    """
    A version of the selector catalog.

    Attributes:
        version_id: Unique version identifier
        version_number: Version number
        entries: Entries in this version
        created_at: When version was created
        created_by: What workflow created this version
        entry_count: Number of entries
        context: Version creation context
    """

    version_id: str = field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:8]}")
    version_number: int = 1
    entries: dict[str, SelectorEntry] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = ""
    entry_count: int = 0
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
            "created_at": self.created_at,
            "created_by": self.created_by,
            "entry_count": self.entry_count,
            "context": self.context,
        }


@dataclass
class CatalogContext:
    """
    Context for catalog operations.

    Attributes:
        operation_id: Unique operation identifier
        workflow_id: Associated workflow ID
        operation_type: Type of operation
        entries_affected: Number of entries affected
        version_before: Version before operation
        version_after: Version after operation
        operation_timestamp: When operation occurred
        context_preserved: Whether context was preserved
    """

    operation_id: str = field(default_factory=lambda: f"op_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    operation_type: str = ""
    entries_affected: int = 0
    version_before: int = 0
    version_after: int = 0
    operation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "workflow_id": self.workflow_id,
            "operation_type": self.operation_type,
            "entries_affected": self.entries_affected,
            "version_before": self.version_before,
            "version_after": self.version_after,
            "operation_timestamp": self.operation_timestamp,
            "context_preserved": self.context_preserved,
        }


class SelectorCatalogAgent(BaseAgent):
    """
    Selector Catalog Management Agent.

    This agent provides:
    1. Selector registration with context
    2. Selector lookup and retrieval
    3. Catalog version control
    4. Selector lifecycle tracking
    """

    name = "e4_5_selector_catalog"
    version = "1.0.0"
    description = "E4.5 - Selector Catalog Management"

    def __init__(self, **kwargs) -> None:
        """Initialize the selector catalog agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E4.5 - Selector Catalog Management agent for the Playwright test automation framework. You help users with e4.5 - selector catalog management tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._current_version: CatalogVersion = CatalogVersion()
        self._version_history: list[CatalogVersion] = []
        self._operation_history: list[CatalogContext] = []
        self._catalog_path: Path | None = None

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
        Execute selector catalog task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the catalog operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "register_selector":
            return await self._register_selector(context, execution_context)
        elif task_type == "lookup_selector":
            return await self._lookup_selector(context, execution_context)
        elif task_type == "update_selector":
            return await self._update_selector(context, execution_context)
        elif task_type == "create_version":
            return await self._create_version(context, execution_context)
        elif task_type == "load_catalog":
            return await self._load_catalog(context, execution_context)
        elif task_type == "save_catalog":
            return await self._save_catalog(context, execution_context)
        elif task_type == "get_catalog_context":
            return await self._get_catalog_context(context, execution_context)
        elif task_type == "search_selectors":
            return await self._search_selectors(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _register_selector(self, context: dict[str, Any], execution_context: Any) -> str:
        """Register a selector with full context."""
        selector = context.get("selector")
        selector_context = context.get("selector_context", {})
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        if not selector:
            return "Error: selector is required"

        raw_selector = selector.get("raw", selector) if isinstance(selector, dict) else selector
        selector_type = selector.get("type", "unknown") if isinstance(selector, dict) else "unknown"

        # Check if selector already exists
        for entry in self._current_version.entries.values():
            if entry.selector == raw_selector:
                # Update existing entry
                entry.last_seen = datetime.now().isoformat()
                entry.usage_count += 1
                entry.contexts.append(selector_context)
                return f"Updated existing selector entry: {entry.entry_id}"

        # Create new entry
        entry = SelectorEntry(
            selector=raw_selector,
            selector_type=selector_type,
            contexts=[selector_context],
            metadata={
                "workflow_id": workflow_id,
                "source": context.get("source", "unknown"),
            },
        )

        self._current_version.entries[entry.entry_id] = entry
        self._current_version.entry_count = len(self._current_version.entries)

        return f"Registered selector: {entry.entry_id}"

    async def _lookup_selector(self, context: dict[str, Any], execution_context: Any) -> str:
        """Look up a selector in the catalog."""
        selector = context.get("selector")

        if not selector:
            return "Error: selector is required"

        raw_selector = selector.get("raw", selector) if isinstance(selector, dict) else selector

        # Search for exact match
        for entry in self._current_version.entries.values():
            if entry.selector == raw_selector:
                return (
                    f"Found selector '{entry.entry_id}': "
                    f"status={entry.status.value}, "
                    f"stability={entry.stability}, "
                    f"usage_count={entry.usage_count}"
                )

        return f"Selector not found in catalog"

    async def _update_selector(self, context: dict[str, Any], execution_context: Any) -> str:
        """Update a selector entry."""
        entry_id = context.get("entry_id")
        updates = context.get("updates", {})

        if not entry_id:
            return "Error: entry_id is required"

        entry = self._current_version.entries.get(entry_id)
        if not entry:
            return f"Error: Entry '{entry_id}' not found"

        # Apply updates
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.last_seen = datetime.now().isoformat()

        return f"Updated selector entry: {entry_id}"

    async def _create_version(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a new catalog version."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))

        # Create operation context
        operation_context = CatalogContext(
            workflow_id=workflow_id,
            operation_type="create_version",
            version_before=self._current_version.version_number,
        )

        # Save current version to history
        self._version_history.append(self._current_version)

        # Create new version
        new_version = CatalogVersion(
            version_number=self._current_version.version_number + 1,
            entries=self._current_version.entries.copy(),
            created_by=workflow_id,
            entry_count=len(self._current_version.entries),
        )

        self._current_version = new_version

        operation_context.version_after = self._current_version.version_number
        operation_context.entries_affected = self._current_version.entry_count
        self._operation_history.append(operation_context)

        return f"Created catalog version: {self._current_version.version_number}"

    async def _load_catalog(self, context: dict[str, Any], execution_context: Any) -> str:
        """Load catalog from file."""
        catalog_path = context.get("catalog_path")

        if not catalog_path:
            return "Error: catalog_path is required"

        path = Path(catalog_path)
        if not path.exists():
            return f"Error: Catalog file not found: {catalog_path}"

        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            # Load current version
            current_data = data.get("current_version", {})
            self._current_version = CatalogVersion(
                version_id=current_data.get("version_id", ""),
                version_number=current_data.get("version_number", 1),
                created_at=current_data.get("created_at", ""),
                created_by=current_data.get("created_by", ""),
                entry_count=current_data.get("entry_count", 0),
            )

            # Load entries
            for entry_data in current_data.get("entries", {}).values():
                entry = SelectorEntry.from_dict(entry_data)
                self._current_version.entries[entry.entry_id] = entry

            self._catalog_path = path

            return f"Loaded catalog: {self._current_version.entry_count} entries, version {self._current_version.version_number}"

        except Exception as e:
            return f"Error loading catalog: {e}"

    async def _save_catalog(self, context: dict[str, Any], execution_context: Any) -> str:
        """Save catalog to file."""
        catalog_path = context.get("catalog_path")

        if not catalog_path:
            return "Error: catalog_path is required"

        path = Path(catalog_path)

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {
                "current_version": self._current_version.to_dict(),
                "version_history": [v.to_dict() for v in self._version_history],
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "total_versions": len(self._version_history) + 1,
                },
            }

            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._catalog_path = path

            return f"Saved catalog to: {catalog_path}"

        except Exception as e:
            return f"Error saving catalog: {e}"

    async def _get_catalog_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get catalog operation context."""
        operation_id = context.get("operation_id")

        if not operation_id:
            return "Error: operation_id is required"

        for operation_context in self._operation_history:
            if operation_context.operation_id == operation_id:
                return (
                    f"Operation '{operation_id}': "
                    f"{operation_context.operation_type}, "
                    f"v{operation_context.version_before} -> v{operation_context.version_after}"
                )

        return f"Error: Operation context '{operation_id}' not found"

    async def _search_selectors(self, context: dict[str, Any], execution_context: Any) -> str:
        """Search selectors by criteria."""
        criteria = context.get("criteria", {})

        results = []
        for entry in self._current_version.entries.values():
            match = True

            # Filter by status
            if "status" in criteria and entry.status.value != criteria["status"]:
                match = False

            # Filter by selector type
            if "selector_type" in criteria and entry.selector_type != criteria["selector_type"]:
                match = False

            # Filter by stability
            if "stability" in criteria and entry.stability != criteria["stability"]:
                match = False

            # Filter by minimum usage
            if "min_usage" in criteria and entry.usage_count < criteria["min_usage"]:
                match = False

            if match:
                results.append(entry)

        return f"Found {len(results)} selector(s) matching criteria"

    def get_current_version(self) -> CatalogVersion:
        """Get current catalog version."""
        return self._current_version

    def get_version_history(self) -> list[CatalogVersion]:
        """Get version history."""
        return self._version_history.copy()

    def get_operation_history(self) -> list[CatalogContext]:
        """Get operation history."""
        return self._operation_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

