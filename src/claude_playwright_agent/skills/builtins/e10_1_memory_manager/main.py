"""
E10.1 - Memory Management System Skill.

This skill provides a multi-layered memory system for AI agents:
- Short-term memory: Session-based working memory (ephemeral)
- Long-term memory: Persistent knowledge across sessions
- Semantic memory: Concepts, patterns, and general knowledge
- Episodic memory: Specific events and test executions
- Working memory: Current task context and state

The memory system enables agents to:
1. Remember previous test executions and outcomes
2. Learn from patterns and failures
3. Recall successful strategies
4. Maintain context across long workflows
5. Provide intelligent suggestions based on history
"""

import asyncio
import json
import pickle
import sqlite3
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import uuid


class MemoryType(str, Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"      # Working memory, session-based
    LONG_TERM = "long_term"        # Persistent knowledge
    SEMANTIC = "semantic"           # Concepts and patterns
    EPISODIC = "episodic"           # Specific events
    WORKING = "working"             # Current task context


class MemoryPriority(str, Enum):
    """Priority levels for memory entries"""
    CRITICAL = "critical"           # Must remember
    HIGH = "high"                   # Important
    MEDIUM = "medium"               # Normal
    LOW = "low"                     # Optional


@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.SHORT_TERM
    priority: MemoryPriority = MemoryPriority.MEDIUM
    key: str = ""                   # Unique key for retrieval
    value: Any = None               # The stored data
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    embedding: Optional[float] = None  # For semantic similarity
    tags: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    associated_memories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def touch(self):
        """Update access time and count"""
        self.accessed_at = datetime.now().isoformat()
        self.access_count += 1

    def is_expired(self) -> bool:
        """Check if memory entry has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)

    def add_tag(self, tag: str):
        """Add a tag to the memory"""
        if tag not in self.tags:
            self.tags.append(tag)

    def associate(self, memory_id: str):
        """Associate with another memory"""
        if memory_id not in self.associated_memories:
            self.associated_memories.append(memory_id)


@dataclass
class MemoryQuery:
    """Query for memory retrieval"""
    type: Optional[MemoryType] = None
    priority: Optional[MemoryPriority] = None
    key: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    context_filter: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    min_similarity: float = 0.0
    time_range: Optional[Tuple[datetime, datetime]] = None


class MemoryManager:
    """
    Multi-layered memory management system.

    Provides four types of memory:
    1. Short-term: Ephemeral working memory (limited capacity, fast access)
    2. Long-term: Persistent storage (unlimited capacity, slower)
    3. Semantic: Conceptual knowledge with similarity search
    4. Episodic: Event-based memory with temporal context
    5. Working: Current task context (very fast, very limited)
    """

    def __init__(
        self,
        persist_to_disk: bool = True,
        memory_db_path: str = ".cpa/memory.db",
        max_short_term: int = 1000,
        max_long_term: int = 10000,
        consolidation_interval: int = 3600
    ):
        """
        Initialize the memory manager.

        Args:
            persist_to_disk: Whether to persist long-term memory to disk
            memory_db_path: Path to SQLite database
            max_short_term: Maximum short-term memory entries
            max_long_term: Maximum long-term memory entries
            consolidation_interval: Seconds between consolidation runs
        """
        self.persist_to_disk = persist_to_disk
        self.memory_db_path = Path(memory_db_path)
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        self.consolidation_interval = consolidation_interval

        # Memory stores
        self.short_term_memory: Dict[str, MemoryEntry] = {}
        self.long_term_memory: Dict[str, MemoryEntry] = {}
        self.semantic_memory: Dict[str, MemoryEntry] = {}
        self.episodic_memory: Dict[str, MemoryEntry] = {}
        self.working_memory: Dict[str, MemoryEntry] = {}

        # Statistics
        self.stats = {
            "total_memories": 0,
            "short_term_count": 0,
            "long_term_count": 0,
            "semantic_count": 0,
            "episodic_count": 0,
            "working_count": 0,
            "total_retrievals": 0,
            "total_stores": 0,
            "consolidations": 0,
        }

        # Initialize database
        if self.persist_to_disk:
            self._init_database()

        # Start consolidation task
        self._consolidation_task = None

    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        self.memory_db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.memory_db_path), check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                key TEXT,
                value TEXT NOT NULL,
                context TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                expires_at TEXT,
                associated_memories TEXT
            )
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON memories(type);
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_key ON memories(key);
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at);
        """)
        self.conn.commit()

    async def store(
        self,
        key: str,
        value: Any,
        type: MemoryType = MemoryType.SHORT_TERM,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        ttl: Optional[int] = None,
    ) -> MemoryEntry:
        """
        Store a value in memory.

        Args:
            key: Unique identifier for the memory
            value: Data to store
            type: Memory type (short-term, long-term, etc.)
            priority: Importance level
            context: Additional context information
            metadata: Optional metadata
            tags: Optional tags for categorization
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            The created MemoryEntry
        """
        # Calculate expiration
        expires_at = None
        if ttl:
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()

        # Create memory entry
        entry = MemoryEntry(
            key=key,
            value=value,
            type=type,
            priority=priority,
            context=context or {},
            metadata=metadata or {},
            tags=tags or [],
            expires_at=expires_at,
        )

        # Store in appropriate memory
        if type == MemoryType.SHORT_TERM:
            self._store_short_term(entry)
        elif type == MemoryType.LONG_TERM:
            await self._store_long_term(entry)
        elif type == MemoryType.SEMANTIC:
            await self._store_semantic(entry)
        elif type == MemoryType.EPISODIC:
            await self._store_episodic(entry)
        elif type == MemoryType.WORKING:
            self._store_working(entry)

        self.stats["total_stores"] += 1
        self.stats["total_memories"] += 1

        return entry

    def _store_short_term(self, entry: MemoryEntry):
        """Store in short-term memory with capacity management"""
        # Evict if at capacity
        if len(self.short_term_memory) >= self.max_short_term:
            self._evict_short_term()

        self.short_term_memory[entry.id] = entry
        self.stats["short_term_count"] = len(self.short_term_memory)

    def _store_working(self, entry: MemoryEntry):
        """Store in working memory (very limited capacity)"""
        # Working memory is very limited (default ~7 items)
        if len(self.working_memory) > 50:
            # Remove least recently used
            oldest = min(self.working_memory.values(), key=lambda x: x.accessed_at)
            del self.working_memory[oldest.id]

        self.working_memory[entry.id] = entry
        self.stats["working_count"] = len(self.working_memory)

    async def _store_long_term(self, entry: MemoryEntry):
        """Store in long-term persistent memory"""
        # Check capacity
        if len(self.long_term_memory) >= self.max_long_term:
            await self._evict_long_term()

        self.long_term_memory[entry.id] = entry
        self.stats["long_term_count"] = len(self.long_term_memory)

        # Persist to disk
        if self.persist_to_disk:
            self._persist_entry(entry)

    async def _store_semantic(self, entry: MemoryEntry):
        """Store in semantic memory (conceptual knowledge)"""
        self.semantic_memory[entry.id] = entry
        self.stats["semantic_count"] = len(self.semantic_memory)

        if self.persist_to_disk:
            self._persist_entry(entry)

    async def _store_episodic(self, entry: MemoryEntry):
        """Store in episodic memory (events)"""
        self.episodic_memory[entry.id] = entry
        self.stats["episodic_count"] = len(self.episodic_memory)

        if self.persist_to_disk:
            self._persist_entry(entry)

    def _persist_entry(self, entry: MemoryEntry):
        """Persist memory entry to database"""
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, type, priority, key, value, context, metadata, created_at,
                 accessed_at, access_count, tags, expires_at, associated_memories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.type.value,
                    entry.priority.value,
                    entry.key,
                    json.dumps(entry.value),
                    json.dumps(entry.context),
                    json.dumps(entry.metadata),
                    entry.created_at,
                    entry.accessed_at,
                    entry.access_count,
                    json.dumps(entry.tags),
                    entry.expires_at,
                    json.dumps(entry.associated_memories),
                ),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error persisting memory: {e}")

    async def retrieve(
        self,
        key: str,
        type: Optional[MemoryType] = None,
    ) -> Optional[MemoryEntry]:
        """
        Retrieve a memory by key.

        Args:
            key: The memory key
            type: Optional memory type filter

        Returns:
            The MemoryEntry if found, None otherwise
        """
        # Search in specified memory type or all memories
        memories_to_search = []
        if type == MemoryType.SHORT_TERM or type is None:
            memories_to_search.extend(self.short_term_memory.values())
        if type == MemoryType.LONG_TERM or type is None:
            memories_to_search.extend(self.long_term_memory.values())
        if type == MemoryType.SEMANTIC or type is None:
            memories_to_search.extend(self.semantic_memory.values())
        if type == MemoryType.EPISODIC or type is None:
            memories_to_search.extend(self.episodic_memory.values())
        if type == MemoryType.WORKING or type is None:
            memories_to_search.extend(self.working_memory.values())

        # Find matching key
        for entry in memories_to_search:
            if entry.key == key and not entry.is_expired():
                entry.touch()
                self.stats["total_retrievals"] += 1
                return entry

        return None

    async def search(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Search memories based on criteria.

        Args:
            query: MemoryQuery with search criteria

        Returns:
            List of matching MemoryEntries
        """
        results = []

        # Gather memories based on type filter
        memories = []
        if query.type is None or query.type == MemoryType.SHORT_TERM:
            memories.extend(self.short_term_memory.values())
        if query.type is None or query.type == MemoryType.LONG_TERM:
            memories.extend(self.long_term_memory.values())
        if query.type is None or query.type == MemoryType.SEMANTIC:
            memories.extend(self.semantic_memory.values())
        if query.type is None or query.type == MemoryType.EPISODIC:
            memories.extend(self.episodic_memory.values())
        if query.type is None or query.type == MemoryType.WORKING:
            memories.extend(self.working_memory.values())

        # Filter memories
        for entry in memories:
            # Skip expired
            if entry.is_expired():
                continue

            # Filter by key
            if query.key and entry.key != query.key:
                continue

            # Filter by priority
            if query.priority and entry.priority != query.priority:
                continue

            # Filter by tags
            if query.tags:
                if not any(tag in entry.tags for tag in query.tags):
                    continue

            # Filter by context
            if query.context_filter:
                match = True
                for k, v in query.context_filter.items():
                    if entry.context.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            # Filter by time range
            if query.time_range:
                created = datetime.fromisoformat(entry.created_at)
                if not (query.time_range[0] <= created <= query.time_range[1]):
                    continue

            results.append(entry)

        # Sort by access count and time
        results.sort(key=lambda x: (x.access_count, x.accessed_at), reverse=True)

        # Apply limit
        return results[: query.limit]

    async def recall_recent(
        self,
        count: int = 10,
        type: Optional[MemoryType] = None,
    ) -> List[MemoryEntry]:
        """
        Recall most recently accessed memories.

        Args:
            count: Number of memories to recall
            type: Optional memory type filter

        Returns:
            List of recently accessed MemoryEntries
        """
        query = MemoryQuery(limit=count, type=type)
        results = await self.search(query)
        return results

    async def recall_by_tags(
        self,
        tags: List[str],
        count: int = 10,
    ) -> List[MemoryEntry]:
        """
        Recall memories by tags.

        Args:
            tags: List of tags to search for
            count: Maximum number of results

        Returns:
            List of matching MemoryEntries
        """
        query = MemoryQuery(tags=tags, limit=count)
        return await self.search(query)

    async def consolidate(self):
        """
        Consolidate memories - move important short-term to long-term.
        """
        consolidation_count = 0

        # Find short-term memories that should be in long-term
        for entry in list(self.short_term_memory.values()):
            # Criteria for consolidation:
            # 1. High or critical priority
            # 2. Frequently accessed (> 5 times)
            # 3. Not expired
            should_consolidate = (
                entry.priority in [MemoryPriority.HIGH, MemoryPriority.CRITICAL]
                or entry.access_count > 5
            ) and not entry.is_expired()

            if should_consolidate:
                # Move to long-term
                del self.short_term_memory[entry.id]
                entry.type = MemoryType.LONG_TERM
                await self._store_long_term(entry)
                consolidation_count += 1

        self.stats["consolidations"] += 1
        self.stats["short_term_count"] = len(self.short_term_memory)
        self.stats["long_term_count"] = len(self.long_term_memory)

        return consolidation_count

    def _evict_short_term(self):
        """Evict least important memories from short-term storage"""
        # Sort by (priority, access_count, accessed_at)
        entries = list(self.short_term_memory.values())
        entries.sort(
            key=lambda x: (
                -1 if x.priority == MemoryPriority.CRITICAL else
                -1 if x.priority == MemoryPriority.HIGH else
                -1 if x.priority == MemoryPriority.MEDIUM else -2,
                x.access_count,
                x.accessed_at,
            )
        )

        # Remove lowest priority/least accessed
        to_remove = entries[len(entries) - self.max_short_term:]
        for entry in to_remove:
            del self.short_term_memory[entry.id]

    async def _evict_long_term(self):
        """Evict from long-term (offload to disk only)"""
        # Long-term doesn't truly evict, just relies on DB
        pass

    async def forget(self, key: str, type: Optional[MemoryType] = None) -> bool:
        """
        Remove a memory from storage.

        Args:
            key: The memory key
            type: Optional memory type

        Returns:
            True if memory was found and removed
        """
        entry = await self.retrieve(key, type)
        if entry:
            # Remove from appropriate store
            if entry.type == MemoryType.SHORT_TERM and entry.id in self.short_term_memory:
                del self.short_term_memory[entry.id]
            elif entry.type == MemoryType.LONG_TERM and entry.id in self.long_term_memory:
                del self.long_term_memory[entry.id]
            elif entry.type == MemoryType.SEMANTIC and entry.id in self.semantic_memory:
                del self.semantic_memory[entry.id]
            elif entry.type == MemoryType.EPISODIC and entry.id in self.episodic_memory:
                del self.episodic_memory[entry.id]
            elif entry.type == MemoryType.WORKING and entry.id in self.working_memory:
                del self.working_memory[entry.id]

            # Remove from database
            if self.persist_to_disk:
                self.conn.execute("DELETE FROM memories WHERE id = ?", (entry.id,))
                self.conn.commit()

            return True

        return False

    async def clear_expired(self) -> int:
        """
        Remove all expired memories.

        Returns:
            Number of memories removed
        """
        removed = 0

        for memory_dict in [
            self.short_term_memory,
            self.long_term_memory,
            self.semantic_memory,
            self.episodic_memory,
            self.working_memory,
        ]:
            expired_ids = [
                entry.id
                for entry in memory_dict.values()
                if entry.is_expired()
            ]

            for memory_id in expired_ids:
                del memory_dict[memory_id]
                removed += 1

        return removed

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            **self.stats,
            "short_term_capacity": f"{len(self.short_term_memory)}/{self.max_short_term}",
            "long_term_capacity": f"{len(self.long_term_memory)}/{self.max_long_term}",
            "working_memory_size": len(self.working_memory),
            "semantic_memory_size": len(self.semantic_memory),
            "episodic_memory_size": len(self.episodic_memory),
        }

    async def export_memories(
        self,
        output_path: str,
        type: Optional[MemoryType] = None,
    ) -> int:
        """
        Export memories to JSON file.

        Args:
            output_path: Path to output file
            type: Optional memory type filter

        Returns:
            Number of memories exported
        """
        query = MemoryQuery(limit=100000, type=type)
        memories = await self.search(query)

        output_data = {
            "export_date": datetime.now().isoformat(),
            "total_memories": len(memories),
            "memories": [entry.to_dict() for entry in memories],
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        return len(memories)

    async def import_memories(self, input_path: str) -> int:
        """
        Import memories from JSON file.

        Args:
            input_path: Path to input file

        Returns:
            Number of memories imported
        """
        with open(input_path, "r") as f:
            data = json.load(f)

        imported = 0
        for entry_data in data.get("memories", []):
            # Recreate MemoryEntry
            entry = MemoryEntry(**entry_data)

            # Store in appropriate memory
            if entry.type == MemoryType.SHORT_TERM:
                self._store_short_term(entry)
            elif entry.type == MemoryType.LONG_TERM:
                await self._store_long_term(entry)
            elif entry.type == MemoryType.SEMANTIC:
                await self._store_semantic(entry)
            elif entry.type == MemoryType.EPISODIC:
                await self._store_episodic(entry)
            elif entry.type == MemoryType.WORKING:
                self._store_working(entry)

            imported += 1

        return imported

    async def close(self):
        """Close the memory manager and cleanup resources"""
        if self.persist_to_disk and hasattr(self, 'conn'):
            self.conn.close()

        # Clear all memories
        self.short_term_memory.clear()
        self.long_term_memory.clear()
        self.semantic_memory.clear()
        self.episodic_memory.clear()
        self.working_memory.clear()


# Convenience functions for common memory operations

async def remember_test_execution(
    manager: MemoryManager,
    test_name: str,
    outcome: str,
    duration_ms: int,
    context: Optional[Dict[str, Any]] = None,
) -> MemoryEntry:
    """
    Remember a test execution in episodic memory.

    Args:
        manager: MemoryManager instance
        test_name: Name of the test
        outcome: Test outcome (passed, failed, skipped)
        duration_ms: Execution time in milliseconds
        context: Optional context (browser, environment, etc.)

    Returns:
        The created MemoryEntry
    """
    return await manager.store(
        key=f"test_execution:{test_name}",
        value={
            "test_name": test_name,
            "outcome": outcome,
            "duration_ms": duration_ms,
        },
        type=MemoryType.EPISODIC,
        priority=MemoryPriority.MEDIUM if outcome == "passed" else MemoryPriority.HIGH,
        tags=["test_execution", outcome],
        context=context or {},
    )


async def remember_selector_failure(
    manager: MemoryManager,
    selector: str,
    page_url: str,
    healing_strategy: str,
    success: bool,
) -> MemoryEntry:
    """
    Remember a selector failure and healing attempt.

    Args:
        manager: MemoryManager instance
        selector: The failed selector
        page_url: URL where it failed
        healing_strategy: Strategy used for healing
        success: Whether healing was successful

    Returns:
        The created MemoryEntry
    """
    return await manager.store(
        key=f"selector_failure:{selector}:{page_url}",
        value={
            "selector": selector,
            "page_url": page_url,
            "healing_strategy": healing_strategy,
            "success": success,
        },
        type=MemoryType.SEMANTIC,
        priority=MemoryPriority.HIGH if success else MemoryPriority.MEDIUM,
        tags=["selector_healing", "success" if success else "failed"],
    )


async def recall_similar_failures(
    manager: MemoryManager,
    selector: str,
    limit: int = 5,
) -> List[MemoryEntry]:
    """
    Recall similar selector failures.

    Args:
        manager: MemoryManager instance
        selector: Selector to find matches for
        limit: Maximum results

    Returns:
        List of similar failure memories
    """
    # Simple matching (could be enhanced with embeddings)
    return await manager.recall_by_tags(["selector_healing"], count=limit)


# Skill main entry point
async def memory_skill(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for memory skill.

    Args:
        input_data: Input parameters for the skill
            - action: "store", "retrieve", "search", "consolidate", "stats", etc.
            - Additional parameters based on action

    Returns:
        Dictionary with result
    """
    action = input_data.get("action", "store")

    # Initialize manager (in real use, would be singleton)
    manager = MemoryManager(
        persist_to_disk=input_data.get("persist_to_disk", True),
        memory_db_path=input_data.get("memory_db_path", ".cpa/memory.db"),
    )

    result = {"success": True, "data": None}

    if action == "store":
        entry = await manager.store(
            key=input_data["key"],
            value=input_data["value"],
            type=MemoryType(input_data.get("type", "short_term")),
            priority=MemoryPriority(input_data.get("priority", "medium")),
            context=input_data.get("context"),
            tags=input_data.get("tags"),
        )
        result["data"] = entry.to_dict()

    elif action == "retrieve":
        entry = await manager.retrieve(
            key=input_data["key"],
            type=MemoryType(input_data["type"]) if "type" in input_data else None,
        )
        result["data"] = entry.to_dict() if entry else None

    elif action == "search":
        query = MemoryQuery(
            type=MemoryType(input_data["type"]) if "type" in input_data else None,
            key=input_data.get("key"),
            tags=input_data.get("tags", []),
            limit=input_data.get("limit", 10),
        )
        results = await manager.search(query)
        result["data"] = [entry.to_dict() for entry in results]

    elif action == "stats":
        result["data"] = manager.get_statistics()

    elif action == "consolidate":
        count = await manager.consolidate()
        result["data"] = {"consolidated_count": count}

    elif action == "forget":
        success = await manager.forget(
            key=input_data["key"],
            type=MemoryType(input_data["type"]) if "type" in input_data else None,
        )
        result["success"] = success

    await manager.close()

    return result
