"""
Migration Utilities for Claude Playwright Agent.

This module implements:
- State migration between versions
- Configuration migration
- Data schema migration
- Rollback support
- Migration history tracking
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import hashlib


# =============================================================================
# Migration Models
# =============================================================================


class MigrationStatus(str, Enum):
    """Status of a migration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationType(str, Enum):
    """Types of migrations."""

    STATE = "state"           # State data migration
    CONFIG = "config"         # Configuration migration
    SCHEMA = "schema"         # Schema migration
    DATA = "data"             # Generic data migration


@dataclass
class MigrationRecord:
    """
    Record of a migration execution.

    Attributes:
        id: Unique migration identifier
        name: Migration name
        type: Migration type
        from_version: Source version
        to_version: Target version
        status: Migration status
        started_at: When migration started
        completed_at: When migration completed
        error: Error message if failed
        checksum: Checksum of data before migration
        rollback_checksum: Checksum for rollback
    """

    id: str
    name: str
    type: MigrationType
    from_version: str
    to_version: str
    status: MigrationStatus = MigrationStatus.PENDING
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    error: str = ""
    checksum: str = ""
    rollback_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "checksum": self.checksum,
            "rollback_checksum": self.rollback_checksum,
        }


@dataclass
class MigrationStep:
    """
    A single step in a migration.

    Attributes:
        name: Step name
        description: Step description
        migrate_func: Function to execute migration
        rollback_func: Function to rollback migration
        depends_on: Steps this step depends on
    """

    name: str
    description: str
    migrate_func: Callable[[], Any]
    rollback_func: Callable[[], Any] | None = None
    depends_on: list[str] = field(default_factory=list)


# =============================================================================
# Migration Executor
# =============================================================================


class MigrationExecutor:
    """
    Execute and manage migrations.

    Features:
    - Execute migrations with rollback support
    - Track migration history
    - Validate migrations
    - Dry-run mode
    """

    def __init__(
        self,
        project_path: Path | None = None,
        backup_dir: Path | None = None,
    ) -> None:
        """
        Initialize the migration executor.

        Args:
            project_path: Path to project root
            backup_dir: Directory for migration backups
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._backup_dir = backup_dir or (self._project_path / ".cpa" / "backups")
        self._history: list[MigrationRecord] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load migration history from disk."""
        history_file = self._backup_dir / "migration_history.json"

        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                for record in data:
                    self._history.append(MigrationRecord(
                        id=record["id"],
                        name=record["name"],
                        type=MigrationType(record["type"]),
                        from_version=record["from_version"],
                        to_version=record["to_version"],
                        status=MigrationStatus(record["status"]),
                        started_at=record["started_at"],
                        completed_at=record.get("completed_at", ""),
                        error=record.get("error", ""),
                        checksum=record.get("checksum", ""),
                        rollback_checksum=record.get("rollback_checksum", ""),
                    ))
            except Exception:
                pass

    def _save_history(self) -> None:
        """Save migration history to disk."""
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        history_file = self._backup_dir / "migration_history.json"

        data = [r.to_dict() for r in self._history]
        history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def execute_migration(
        self,
        name: str,
        migrate_func: Callable[[], Any],
        from_version: str,
        to_version: str,
        migration_type: MigrationType = MigrationType.STATE,
        rollback_func: Callable[[], Any] | None = None,
        dry_run: bool = False,
    ) -> MigrationRecord:
        """
        Execute a migration.

        Args:
            name: Migration name
            migrate_func: Function to execute migration
            from_version: Source version
            to_version: Target version
            migration_type: Type of migration
            rollback_func: Optional rollback function
            dry_run: If True, don't actually execute

        Returns:
            Migration record
        """
        import uuid
        record = MigrationRecord(
            id=f"migration_{uuid.uuid4().hex[:8]}",
            name=name,
            type=migration_type,
            from_version=from_version,
            to_version=to_version,
        )

        # Create backup before migration
        if not dry_run:
            checksum = self._create_backup()
            record.checksum = checksum

        record.status = MigrationStatus.RUNNING
        self._history.append(record)

        try:
            if dry_run:
                print(f"[DRY RUN] Would execute migration: {name}")
                print(f"[DRY RUN] From {from_version} -> {to_version}")
            else:
                result = migrate_func()
                print(f"Migration '{name}' completed successfully")

            record.status = MigrationStatus.COMPLETED
            record.completed_at = datetime.now().isoformat()

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now().isoformat()
            print(f"Migration '{name}' failed: {e}")

            # Attempt rollback if available
            if rollback_func and not dry_run:
                try:
                    rollback_func()
                    record.status = MigrationStatus.ROLLED_BACK
                    print(f"Migration '{name}' rolled back")
                except Exception as rb_err:
                    print(f"Rollback failed: {rb_err}")

        self._save_history()
        return record

    def execute_multi_step_migration(
        self,
        name: str,
        steps: list[MigrationStep],
        from_version: str,
        to_version: str,
        migration_type: MigrationType = MigrationType.STATE,
        dry_run: bool = False,
    ) -> list[MigrationRecord]:
        """
        Execute a multi-step migration.

        Args:
            name: Migration name
            steps: List of migration steps
            from_version: Source version
            to_version: Target version
            migration_type: Type of migration
            dry_run: If True, don't actually execute

        Returns:
            List of migration records
        """
        records: list[MigrationRecord] = []
        completed_steps: set[str] = set()

        for step in steps:
            # Check dependencies
            if step.depends_on:
                if not all(dep in completed_steps for dep in step.depends_on):
                    print(f"Skipping step '{step.name}' - dependencies not met")
                    continue

            record = self.execute_migration(
                name=f"{name}:{step.name}",
                migrate_func=step.migrate_func,
                from_version=from_version,
                to_version=to_version,
                migration_type=migration_type,
                rollback_func=step.rollback_func,
                dry_run=dry_run,
            )
            records.append(record)

            if record.status == MigrationStatus.COMPLETED:
                completed_steps.add(step.name)
            elif record.status in (MigrationStatus.FAILED, MigrationStatus.ROLLED_BACK):
                print(f"Migration stopped at step '{step.name}'")
                break

        return records

    def rollback_migration(self, record_id: str) -> bool:
        """
        Rollback a migration by ID.

        Args:
            record_id: Migration record ID

        Returns:
            True if rollback was successful
        """
        # Find the record
        record = None
        for r in self._history:
            if r.id == record_id:
                record = r
                break

        if not record:
            print(f"Migration record not found: {record_id}")
            return False

        # Restore from backup
        return self._restore_backup(record.checksum)

    def get_history(self) -> list[MigrationRecord]:
        """Get migration history."""
        return self._history.copy()

    def get_last_migration(self) -> MigrationRecord | None:
        """Get the last migration record."""
        if self._history:
            return self._history[-1]
        return None

    def _create_backup(self) -> str:
        """
        Create a backup of current state.

        Returns:
            Checksum of backed up data
        """
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / timestamp

        # Copy state files
        state_files = [
            self._project_path / ".cpa" / "state.json",
            self._project_path / ".cpa" / "config.json",
        ]

        for file_path in state_files:
            if file_path.exists():
                dest = backup_path / file_path.name
                shutil.copy2(file_path, dest)

        # Calculate checksum
        checksum = self._calculate_backup_checksum(backup_path)

        # Store checksum
        (backup_path / "checksum.txt").write_text(checksum)

        return checksum

    def _restore_backup(self, checksum: str) -> bool:
        """
        Restore from backup by checksum.

        Args:
            checksum: Checksum of backup to restore

        Returns:
            True if restore was successful
        """
        # Find backup by checksum
        for backup_path in self._backup_dir.iterdir():
            if not backup_path.is_dir():
                continue

            checksum_file = backup_path / "checksum.txt"
            if checksum_file.exists():
                if checksum_file.read_text().strip() == checksum:
                    # Restore files
                    for file_path in backup_path.glob("*"):
                        if file_path.is_file() and file_path.name != "checksum.txt":
                            dest = self._project_path / ".cpa" / file_path.name
                            shutil.copy2(file_path, dest)
                    return True

        return False

    def _calculate_backup_checksum(self, backup_path: Path) -> str:
        """Calculate checksum of backup directory."""
        hasher = hashlib.sha256()

        for file_path in sorted(backup_path.glob("*")):
            if file_path.is_file():
                hasher.update(file_path.read_bytes())

        return hasher.hexdigest()


# =============================================================================
# State Migrator
# =============================================================================


class StateMigrator:
    """
    Migrate state data between versions.

    Features:
    - Transform state structure
    - Add/remove fields
    - Update values
    - Validate migrated state
    """

    def __init__(self) -> None:
        """Initialize the state migrator."""
        self._transformations: dict[tuple[str, str], Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_transformation(
        self,
        from_version: str,
        to_version: str,
        transform_func: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """
        Register a state transformation.

        Args:
            from_version: Source version
            to_version: Target version
            transform_func: Function to transform state
        """
        self._transformations[(from_version, to_version)] = transform_func

    def migrate(
        self,
        state: dict[str, Any],
        from_version: str,
        to_version: str,
    ) -> dict[str, Any]:
        """
        Migrate state from one version to another.

        Args:
            state: Current state
            from_version: Current version
            to_version: Target version

        Returns:
            Migrated state
        """
        key = (from_version, to_version)

        if key in self._transformations:
            return self._transformations[key](state)

        # Try to find a path through intermediate versions
        return self._find_migration_path(state, from_version, to_version)

    def _find_migration_path(
        self,
        state: dict[str, Any],
        from_version: str,
        to_version: str,
        visited: set[str] | None = None,
    ) -> dict[str, Any]:
        """Find a migration path through intermediate versions."""
        if visited is None:
            visited = set()

        if from_version in visited:
            raise ValueError(f"Circular migration detected: {from_version}")

        visited.add(from_version)

        # Check for direct transformation
        key = (from_version, to_version)
        if key in self._transformations:
            return self._transformations[key](state)

        # Try to find intermediate version
        for (fv, tv), func in self._transformations.items():
            if fv == from_version and tv not in visited:
                try:
                    # Migrate to intermediate version
                    intermediate_state = func(state)
                    # Then migrate from intermediate to target
                    return self._find_migration_path(
                        intermediate_state, tv, to_version, visited
                    )
                except Exception:
                    continue

        raise ValueError(f"No migration path from {from_version} to {to_version}")


# =============================================================================
# Configuration Migrator
# =============================================================================


class ConfigMigrator:
    """
    Migrate configuration between versions.

    Features:
    - Rename configuration keys
    - Change value types
    - Add default values
    - Remove deprecated keys
    """

    def __init__(self) -> None:
        """Initialize the configuration migrator."""
        self._migrations: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def register_migration(
        self,
        to_version: str,
        migrate_func: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Register a configuration migration.

        Args:
            to_version: Target version
            migrate_func: Function to migrate configuration
        """
        if to_version not in self._migrations:
            self._migrations[to_version] = []
        self._migrations[to_version].append(migrate_func)

    def migrate(
        self,
        config: dict[str, Any],
        from_version: str,
        to_version: str,
    ) -> dict[str, Any]:
        """
        Migrate configuration from one version to another.

        Args:
            config: Current configuration
            from_version: Current version
            to_version: Target version

        Returns:
            Migrated configuration
        """
        # Apply all migrations for versions > from_version up to to_version
        for version, migrations in sorted(self._migrations.items()):
            if self._compare_versions(version, from_version) > 0 and \
               self._compare_versions(version, to_version) <= 0:
                for migrate_func in migrations:
                    migrate_func(config)

        return config

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings."""
        from claude_playwright_agent.skills.versioning import compare_versions
        return compare_versions(v1, v2)


# =============================================================================
# Data Migrator
# =============================================================================


class DataMigrator:
    """
    Migrate data files between schemas.

    Features:
    - Transform data structure
    - Convert data types
    - Validate migrated data
    - Batch processing
    """

    def __init__(self) -> None:
        """Initialize the data migrator."""
        self._schemas: dict[str, dict[str, Any]] = {}

    def register_schema(
        self,
        version: str,
        schema: dict[str, Any],
    ) -> None:
        """
        Register a data schema for a version.

        Args:
            version: Schema version
            schema: Schema definition
        """
        self._schemas[version] = schema

    def migrate(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        from_version: str,
        to_version: str,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Migrate data between schema versions.

        Args:
            data: Data to migrate
            from_version: Current schema version
            to_version: Target schema version

        Returns:
            Migrated data
        """
        # Get schemas
        from_schema = self._schemas.get(from_version)
        to_schema = self._schemas.get(to_version)

        if not from_schema:
            raise ValueError(f"Unknown schema version: {from_version}")
        if not to_schema:
            raise ValueError(f"Unknown schema version: {to_version}")

        # Check if schemas are compatible
        if from_schema == to_schema:
            return data

        # Apply transformations based on schema differences
        return self._transform_data(data, from_schema, to_schema)

    def _transform_data(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        from_schema: dict[str, Any],
        to_schema: dict[str, Any],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Transform data based on schema differences."""
        # Handle list of records
        if isinstance(data, list):
            return [
                self._transform_record(record, from_schema, to_schema)
                for record in data
            ]

        # Handle single record
        return self._transform_record(data, from_schema, to_schema)

    def _transform_record(
        self,
        record: dict[str, Any],
        from_schema: dict[str, Any],
        to_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Transform a single record."""
        result = {}

        # Copy fields that exist in both schemas
        for key in to_schema:
            if key in record:
                # Apply type conversion if needed
                to_type = to_schema[key].get("type")
                from_type = from_schema.get(key, {}).get("type")

                if to_type and from_type != to_type:
                    result[key] = self._convert_type(record[key], to_type)
                else:
                    result[key] = record[key]
            elif "default" in to_schema[key]:
                # Use default value
                result[key] = to_schema[key]["default"]

        return result

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            return int(value)
        elif target_type == "float":
            return float(value)
        elif target_type == "boolean":
            return bool(value)
        elif target_type == "array":
            return list(value) if not isinstance(value, list) else value
        elif target_type == "object":
            return dict(value) if not isinstance(value, dict) else value
        else:
            return value


# =============================================================================
# Convenience Functions
# =============================================================================


def create_migration_executor(
    project_path: Path | str | None = None,
) -> MigrationExecutor:
    """
    Create a migration executor.

    Args:
        project_path: Optional project path

    Returns:
        MigrationExecutor instance
    """
    return MigrationExecutor(project_path=Path(project_path) if project_path else None)


def migrate_state(
    state: dict[str, Any],
    from_version: str,
    to_version: str,
) -> dict[str, Any]:
    """
    Migrate state between versions.

    Args:
        state: Current state
        from_version: Current version
        to_version: Target version

    Returns:
        Migrated state
    """
    migrator = StateMigrator()
    return migrator.migrate(state, from_version, to_version)


def migrate_config(
    config: dict[str, Any],
    from_version: str,
    to_version: str,
) -> dict[str, Any]:
    """
    Migrate configuration between versions.

    Args:
        config: Current configuration
        from_version: Current version
        to_version: Target version

    Returns:
        Migrated configuration
    """
    migrator = ConfigMigrator()
    return migrator.migrate(config, from_version, to_version)
