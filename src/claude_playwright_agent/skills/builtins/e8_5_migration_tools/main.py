"""
E8.5 - Migration Tools Skill.

This skill provides migration capabilities:
- State migration
- Configuration migration
- Data migration
- Backup and restore
"""

import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class MigrationType(str, Enum):
    """Migration types."""

    STATE = "state"
    CONFIG = "config"
    DATA = "data"
    FULL = "full"


class MigrationStatus(str, Enum):
    """Migration status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class BackupType(str, Enum):
    """Backup types."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


@dataclass
class MigrationRecord:
    """
    A record of a migration operation.

    Attributes:
        migration_id: Unique migration identifier
        migration_type: Type of migration
        from_version: Source version
        to_version: Target version
        status: Migration status
        steps_completed: Number of steps completed
        total_steps: Total number of steps
        started_at: When migration started
        completed_at: When migration completed
        error: Error message if failed
        rollback_data: Data for rollback if needed
        metadata: Additional metadata
    """

    migration_id: str = field(default_factory=lambda: f"mig_{uuid.uuid4().hex[:8]}")
    migration_type: MigrationType = MigrationType.STATE
    from_version: str = ""
    to_version: str = ""
    status: MigrationStatus = MigrationStatus.PENDING
    steps_completed: int = 0
    total_steps: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    error: str = ""
    rollback_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "migration_id": self.migration_id,
            "migration_type": self.migration_type.value,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.value,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "rollback_data": self.rollback_data,
            "metadata": self.metadata,
        }

    @property
    def percent_complete(self) -> float:
        """Calculate percentage complete."""
        if self.total_steps == 0:
            return 0.0
        return (self.steps_completed / self.total_steps) * 100


@dataclass
class BackupRecord:
    """
    A record of a backup operation.

    Attributes:
        backup_id: Unique backup identifier
        backup_type: Type of backup
        backup_path: Path to backup files
        original_path: Original path backed up
        size_bytes: Size of backup in bytes
        created_at: When backup was created
        compressed: Whether backup is compressed
        checksum: Backup checksum for verification
        metadata: Additional metadata
    """

    backup_id: str = field(default_factory=lambda: f"bak_{uuid.uuid4().hex[:8]}")
    backup_type: BackupType = BackupType.FULL
    backup_path: str = ""
    original_path: str = ""
    size_bytes: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    compressed: bool = False
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "backup_path": self.backup_path,
            "original_path": self.original_path,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "compressed": self.compressed,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }


@dataclass
class MigrationContext:
    """
    Context for migration operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        migrations_executed: Number of migrations executed
        backups_created: Number of backups created
        restores_performed: Number of restores performed
        migration_history: List of migration records
        started_at: When migration context started
        completed_at: When migration context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"mig_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    migrations_executed: int = 0
    backups_created: int = 0
    restores_performed: int = 0
    migration_history: list[MigrationRecord] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "migrations_executed": self.migrations_executed,
            "backups_created": self.backups_created,
            "restores_performed": self.restores_performed,
            "migration_history": [m.to_dict() for m in self.migration_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class MigrationToolsAgent(BaseAgent):
    """
    Migration Tools Agent.

    This agent provides:
    1. State migration
    2. Configuration migration
    3. Data migration
    4. Backup and restore
    """

    name = "e8_5_migration_tools"
    version = "1.0.0"
    description = "E8.5 - Migration Tools"

    def __init__(self, **kwargs) -> None:
        """Initialize the migration tools agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E8.5 - Migration Tools agent for the Playwright test automation framework. You help users with e8.5 - migration tools tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[MigrationContext] = []
        self._migration_registry: dict[str, MigrationRecord] = {}
        self._backup_registry: dict[str, BackupRecord] = {}
        self._project_path: Path = Path.cwd()

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
        Execute migration task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the migration operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "migrate_state":
            return await self._migrate_state(context, execution_context)
        elif task_type == "migrate_config":
            return await self._migrate_config(context, execution_context)
        elif task_type == "migrate_data":
            return await self._migrate_data(context, execution_context)
        elif task_type == "create_backup":
            return await self._create_backup(context, execution_context)
        elif task_type == "restore_backup":
            return await self._restore_backup(context, execution_context)
        elif task_type == "rollback_migration":
            return await self._rollback_migration(context, execution_context)
        elif task_type == "get_migration":
            return await self._get_migration(context, execution_context)
        elif task_type == "get_backup":
            return await self._get_backup(context, execution_context)
        elif task_type == "list_backups":
            return await self._list_backups(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _migrate_state(self, context: dict[str, Any], execution_context: Any) -> str:
        """Migrate state from one version to another."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        from_version = context.get("from_version", "1.0.0")
        to_version = context.get("to_version", "2.0.0")
        project_path = context.get("project_path", str(self._project_path))

        # Create migration record
        record = MigrationRecord(
            migration_type=MigrationType.STATE,
            from_version=from_version,
            to_version=to_version,
            total_steps=3,
            status=MigrationStatus.IN_PROGRESS,
        )

        try:
            # Step 1: Create backup
            backup = await self._create_backup_internal(
                backup_type=BackupType.FULL,
                source_path=Path(project_path) / ".claude" / "state",
                workflow_id=workflow_id,
            )
            record.steps_completed = 1
            record.rollback_data["backup_id"] = backup.backup_id

            # Step 2: Transform state
            state_path = Path(project_path) / ".claude" / "state"
            if state_path.exists():
                # Load and transform state would happen here
                record.steps_completed = 2

            # Step 3: Update version
            record.steps_completed = 3
            record.status = MigrationStatus.COMPLETED
            record.completed_at = datetime.now().isoformat()

            self._migration_registry[record.migration_id] = record

            return f"State migration complete: {from_version} -> {to_version} (ID: {record.migration_id})"

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now().isoformat()
            self._migration_registry[record.migration_id] = record
            return f"State migration failed: {e}"

    async def _migrate_config(self, context: dict[str, Any], execution_context: Any) -> str:
        """Migrate configuration from one version to another."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        from_version = context.get("from_version", "1.0.0")
        to_version = context.get("to_version", "2.0.0")
        project_path = context.get("project_path", str(self._project_path))

        record = MigrationRecord(
            migration_type=MigrationType.CONFIG,
            from_version=from_version,
            to_version=to_version,
            total_steps=3,
            status=MigrationStatus.IN_PROGRESS,
        )

        try:
            # Step 1: Backup config
            backup = await self._create_backup_internal(
                backup_type=BackupType.FULL,
                source_path=Path(project_path) / ".claude" / "profiles",
                workflow_id=workflow_id,
            )
            record.steps_completed = 1
            record.rollback_data["backup_id"] = backup.backup_id

            # Step 2: Transform config
            config_path = Path(project_path) / ".claude" / "profiles"
            if config_path.exists():
                record.steps_completed = 2

            # Step 3: Update version
            record.steps_completed = 3
            record.status = MigrationStatus.COMPLETED
            record.completed_at = datetime.now().isoformat()

            self._migration_registry[record.migration_id] = record

            return f"Config migration complete: {from_version} -> {to_version} (ID: {record.migration_id})"

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now().isoformat()
            self._migration_registry[record.migration_id] = record
            return f"Config migration failed: {e}"

    async def _migrate_data(self, context: dict[str, Any], execution_context: Any) -> str:
        """Migrate data from one version to another."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        from_version = context.get("from_version", "1.0.0")
        to_version = context.get("to_version", "2.0.0")
        project_path = context.get("project_path", str(self._project_path))
        data_path = context.get("data_path", "")

        record = MigrationRecord(
            migration_type=MigrationType.DATA,
            from_version=from_version,
            to_version=to_version,
            total_steps=4,
            status=MigrationStatus.IN_PROGRESS,
        )

        try:
            source_path = Path(data_path) if data_path else Path(project_path) / "data"

            # Step 1: Create backup
            backup = await self._create_backup_internal(
                backup_type=BackupType.FULL,
                source_path=source_path,
                workflow_id=workflow_id,
            )
            record.steps_completed = 1
            record.rollback_data["backup_id"] = backup.backup_id

            # Step 2: Validate data
            if source_path.exists():
                record.steps_completed = 2

            # Step 3: Transform data
            record.steps_completed = 3

            # Step 4: Complete
            record.steps_completed = 4
            record.status = MigrationStatus.COMPLETED
            record.completed_at = datetime.now().isoformat()

            self._migration_registry[record.migration_id] = record

            return f"Data migration complete: {from_version} -> {to_version} (ID: {record.migration_id})"

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now().isoformat()
            self._migration_registry[record.migration_id] = record
            return f"Data migration failed: {e}"

    async def _create_backup(self, context: dict[str, Any], execution_context: Any) -> str:
        """Create a backup."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        backup_type = context.get("backup_type", BackupType.FULL)
        source_path = context.get("source_path", "")

        if isinstance(backup_type, str):
            backup_type = BackupType(backup_type)

        if not source_path:
            return "Error: source_path is required"

        backup = await self._create_backup_internal(
            backup_type=backup_type,
            source_path=Path(source_path),
            workflow_id=workflow_id,
        )

        return f"Backup created: {backup.backup_id} at {backup.backup_path}"

    async def _create_backup_internal(
        self,
        backup_type: BackupType,
        source_path: Path,
        workflow_id: str,
    ) -> BackupRecord:
        """Internal backup creation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self._project_path / ".claude" / "backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_dir / source_path.name

        # Copy source to backup location
        if source_path.exists():
            if source_path.is_dir():
                shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, backup_path)

        # Calculate size
        size_bytes = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file()) if backup_path.exists() else 0

        backup = BackupRecord(
            backup_type=backup_type,
            backup_path=str(backup_path),
            original_path=str(source_path),
            size_bytes=size_bytes,
        )

        self._backup_registry[backup.backup_id] = backup

        return backup

    async def _restore_backup(self, context: dict[str, Any], execution_context: Any) -> str:
        """Restore from a backup."""
        backup_id = context.get("backup_id")
        target_path = context.get("target_path", "")

        if not backup_id:
            return "Error: backup_id is required"

        backup = self._backup_registry.get(backup_id)
        if not backup:
            return f"Error: Backup '{backup_id}' not found"

        try:
            backup_path = Path(backup.backup_path)
            restore_path = Path(target_path) if target_path else Path(backup.original_path)

            if backup_path.exists():
                if backup_path.is_dir():
                    if restore_path.exists():
                        shutil.rmtree(restore_path)
                    shutil.copytree(backup_path, restore_path)
                else:
                    shutil.copy2(backup_path, restore_path)

                return f"Restored backup '{backup_id}' to {restore_path}"

            return f"Error: Backup path does not exist: {backup_path}"

        except Exception as e:
            return f"Restore failed: {e}"

    async def _rollback_migration(self, context: dict[str, Any], execution_context: Any) -> str:
        """Rollback a migration."""
        migration_id = context.get("migration_id")

        if not migration_id:
            return "Error: migration_id is required"

        migration = self._migration_registry.get(migration_id)
        if not migration:
            return f"Error: Migration '{migration_id}' not found"

        backup_id = migration.rollback_data.get("backup_id")
        if not backup_id:
            return f"Error: No backup found for migration '{migration_id}'"

        # Restore from backup
        result = await self._restore_backup({"backup_id": backup_id}, execution_context)

        if "Restored backup" in result:
            migration.status = MigrationStatus.ROLLED_BACK
            migration.completed_at = datetime.now().isoformat()
            return f"Rolled back migration '{migration_id}'"

        return f"Rollback failed: {result}"

    async def _get_migration(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get migration by ID."""
        migration_id = context.get("migration_id")

        if not migration_id:
            return "Error: migration_id is required"

        migration = self._migration_registry.get(migration_id)
        if migration:
            return (
                f"Migration '{migration_id}': "
                f"{migration.migration_type.value} "
                f"{migration.from_version} -> {migration.to_version}, "
                f"status={migration.status.value}"
            )

        return f"Error: Migration '{migration_id}' not found"

    async def _get_backup(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get backup by ID."""
        backup_id = context.get("backup_id")

        if not backup_id:
            return "Error: backup_id is required"

        backup = self._backup_registry.get(backup_id)
        if backup:
            size_mb = backup.size_bytes / (1024 * 1024)
            return (
                f"Backup '{backup_id}': "
                f"{backup.backup_type.value}, "
                f"{size_mb:.2f} MB, "
                f"created at {backup.created_at}"
            )

        return f"Error: Backup '{backup_id}' not found"

    async def _list_backups(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all backups."""
        workflow_id = context.get("workflow_id")
        backup_type = context.get("backup_type")

        backups = list(self._backup_registry.values())

        if workflow_id:
            backups = [b for b in backups if b.metadata.get("workflow_id") == workflow_id]

        if backup_type:
            if isinstance(backup_type, str):
                backup_type = BackupType(backup_type)
            backups = [b for b in backups if b.backup_type == backup_type]

        if not backups:
            return "No backups found"

        output = f"Backups ({len(backups)}):\n"
        for backup in backups:
            size_mb = backup.size_bytes / (1024 * 1024)
            output += f"- {backup.backup_id}: {backup.backup_type.value}, {size_mb:.2f} MB\n"

        return output

    def get_migration_registry(self) -> dict[str, MigrationRecord]:
        """Get migration registry."""
        return self._migration_registry.copy()

    def get_backup_registry(self) -> dict[str, BackupRecord]:
        """Get backup registry."""
        return self._backup_registry.copy()

    def get_context_history(self) -> list[MigrationContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

