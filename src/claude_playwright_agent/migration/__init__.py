"""
Migration utilities for Claude Playwright Agent.

This module provides:
- Version migration support
- Configuration migration
- State file migration
- Backup and rollback utilities
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from claude_playwright_agent.config.manager import ConfigManager
from claude_playwright_agent.state.manager import StateManager


# =============================================================================
# Migration Types
# =============================================================================


class MigrationType(Enum):
    """Types of migrations."""

    CONFIG = "config"
    STATE = "state"
    FILES = "files"
    DEPENDENCIES = "dependencies"


@total_ordering
class MigrationStatus(Enum):
    """Status of a migration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

    def __lt__(self, other: "MigrationStatus") -> bool:
        """Compare migration statuses for ordering."""
        order = [
            MigrationStatus.PENDING,
            MigrationStatus.IN_PROGRESS,
            MigrationStatus.COMPLETED,
            MigrationStatus.FAILED,
            MigrationStatus.ROLLED_BACK,
        ]
        return order.index(self) < order.index(other)


# =============================================================================
# Migration Models
# =============================================================================


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    migration_name: str
    from_version: str | None = None
    to_version: str | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    backup_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "migration_name": self.migration_name,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "backup_path": str(self.backup_path) if self.backup_path else None,
        }


@dataclass
class MigrationHistory:
    """History of migrations."""

    results: list[MigrationResult] = field(default_factory=list)

    def add(self, result: MigrationResult) -> None:
        """Add a migration result to history."""
        self.results.append(result)

    def get_latest(self) -> MigrationResult | None:
        """Get the latest migration result."""
        return self.results[-1] if self.results else None

    def get_successful(self) -> list[MigrationResult]:
        """Get all successful migrations."""
        return [r for r in self.results if r.success]

    def get_failed(self) -> list[MigrationResult]:
        """Get all failed migrations."""
        return [r for r in self.results if not r.success]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "migrations": [r.to_dict() for r in self.results],
            "total": len(self.results),
            "successful": len(self.get_successful()),
            "failed": len(self.get_failed()),
        }


# =============================================================================
# Base Migration Class
# =============================================================================


class Migration:
    """
    Base class for migrations.

    Migrations are versioned operations that transform project
    data from one state to another.
    """

    # Migration metadata - override in subclasses
    name: str = "base_migration"
    description: str = "Base migration"
    version: str = "0.0.0"
    migration_type: MigrationType = MigrationType.CONFIG
    required: bool = False

    def __init__(
        self,
        project_path: Path,
        console: Console | None = None,
    ) -> None:
        """
        Initialize the migration.

        Args:
            project_path: Path to the project
            console: Console for output (uses default if None)
        """
        self.project_path = project_path
        self.console = console or Console()
        self.backup_path: Path | None = None

    def pre_check(self) -> tuple[bool, str]:
        """
        Check if migration can be applied.

        Returns:
            Tuple of (can_apply, reason)
        """
        return True, ""

    def backup(self) -> Path:
        """
        Create a backup before migration.

        Returns:
            Path to backup directory
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f".cpa_backup_{self.name}_{timestamp}"
        backup_path = self.project_path / backup_name

        # Create backup directory
        backup_path.mkdir(exist_ok=True)

        # Backup .cpa directory
        cpa_dir = self.project_path / ".cpa"
        if cpa_dir.exists():
            backup_cpa = backup_path / ".cpa"
            shutil.copytree(cpa_dir, backup_cpa)

        self.backup_path = backup_path
        return backup_path

    def migrate(self) -> MigrationResult:
        """
        Perform the migration.

        Returns:
            MigrationResult with outcome
        """
        raise NotImplementedError(f"{self.__class__.__name__}.migrate() must be implemented")

    def rollback(self) -> None:
        """Rollback the migration using backup."""
        if self.backup_path and self.backup_path.exists():
            cpa_dir = self.project_path / ".cpa"

            # Remove existing .cpa directory
            if cpa_dir.exists():
                shutil.rmtree(cpa_dir)

            # Restore from backup
            backup_cpa = self.backup_path / ".cpa"
            if backup_cpa.exists():
                shutil.copytree(backup_cpa, cpa_dir)

    def cleanup_backup(self) -> None:
        """Remove the backup directory."""
        if self.backup_path and self.backup_path.exists():
            shutil.rmtree(self.backup_path)


# =============================================================================
# Configuration Migration
# =============================================================================


class ConfigMigration(Migration):
    """
    Migration for configuration files.

    Handles upgrades between different configuration formats.
    """

    name = "config_migration"
    description = "Configuration migration"
    version = "0.2.0"
    migration_type = MigrationType.CONFIG

    def migrate(self) -> MigrationResult:
        """
        Migrate configuration to current version.

        Returns:
            MigrationResult with outcome
        """
        try:
            # Load current config
            config = ConfigManager(self.project_path)

            # Get current version (default to 0.1.0)
            from_version = "0.1.0"
            try:
                from_version = config._metadata.get("version", "0.1.0")
            except Exception:
                pass

            # Apply migration logic based on version
            if from_version == "0.1.0":
                self._migrate_from_0_1_0(config)

            # Save updated config
            config.save()

            return MigrationResult(
                success=True,
                migration_name=self.name,
                from_version=from_version,
                to_version=self.version,
                message="Configuration migrated successfully",
            )

        except Exception as e:
            return MigrationResult(
                success=False,
                migration_name=self.name,
                message=f"Migration failed: {e}",
                details={"error": str(e)},
            )

    def _migrate_from_0_1_0(self, config: ConfigManager) -> None:
        """Migrate from version 0.1.0."""
        # Add any new configuration fields
        # This is a placeholder for actual migration logic
        pass


# =============================================================================
# State Migration
# =============================================================================


class StateMigration(Migration):
    """
    Migration for state files.

    Handles upgrades between different state formats.
    """

    name = "state_migration"
    description = "State migration"
    version = "0.2.0"
    migration_type = MigrationType.STATE

    def migrate(self) -> MigrationResult:
        """
        Migrate state to current version.

        Returns:
            MigrationResult with outcome
        """
        try:
            # Load current state
            state = StateManager(self.project_path)

            # Get current version
            from_version = state.get_project_metadata().version

            # Apply migration logic based on version
            if from_version == "0.1.0":
                self._migrate_from_0_1_0(state)

            return MigrationResult(
                success=True,
                migration_name=self.name,
                from_version=from_version,
                to_version=self.version,
                message="State migrated successfully",
            )

        except Exception as e:
            return MigrationResult(
                success=False,
                migration_name=self.name,
                message=f"Migration failed: {e}",
                details={"error": str(e)},
            )

    def _migrate_from_0_1_0(self, state: StateManager) -> None:
        """Migrate from version 0.1.0."""
        # Add any new state fields
        # This is a placeholder for actual migration logic
        pass


# =============================================================================
# Migration Manager
# =============================================================================


class MigrationManager:
    """
    Manager for applying migrations.

    Features:
    - Automatic migration detection
    - Backup creation
    - Rollback support
    - Migration history tracking
    """

    def __init__(
        self,
        project_path: Path,
        console: Console | None = None,
    ) -> None:
        """
        Initialize the migration manager.

        Args:
            project_path: Path to the project
            console: Console for output
        """
        self.project_path = project_path
        self.console = console or Console()
        self.history = MigrationHistory()
        self._load_history()

    def _load_history(self) -> None:
        """Load migration history from file."""
        history_file = self.project_path / ".cpa" / "migrations.json"

        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                for result_data in data.get("migrations", []):
                    result = MigrationResult(
                        success=result_data["success"],
                        migration_name=result_data["migration_name"],
                        from_version=result_data.get("from_version"),
                        to_version=result_data.get("to_version"),
                        message=result_data.get("message", ""),
                        details=result_data.get("details", {}),
                        timestamp=result_data.get("timestamp", ""),
                        backup_path=Path(result_data["backup_path"]) if result_data.get("backup_path") else None,
                    )
                    self.history.add(result)
            except Exception:
                pass  # Use empty history if file is corrupted

    def _save_history(self) -> None:
        """Save migration history to file."""
        history_file = self.project_path / ".cpa" / "migrations.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        history_file.write_text(
            json.dumps(self.history.to_dict(), indent=2),
            encoding="utf-8",
        )

    def get_available_migrations(self) -> list[Migration]:
        """
        Get list of available migrations.

        Returns:
            List of migration instances
        """
        return [
            ConfigMigration(self.project_path, self.console),
            StateMigration(self.project_path, self.console),
        ]

    def get_pending_migrations(self) -> list[Migration]:
        """
        Get list of pending migrations.

        Returns:
            List of migrations that haven't been applied
        """
        applied_names = {r.migration_name for r in self.history.results}
        return [m for m in self.get_available_migrations() if m.name not in applied_names]

    def apply_migration(self, migration: Migration) -> MigrationResult:
        """
        Apply a single migration.

        Args:
            migration: Migration to apply

        Returns:
            MigrationResult with outcome
        """
        self.console.print(f"[cyan]Applying migration: {migration.name}[/cyan]")

        # Pre-check
        can_apply, reason = migration.pre_check()
        if not can_apply:
            result = MigrationResult(
                success=False,
                migration_name=migration.name,
                message=f"Pre-check failed: {reason}",
            )
            self.history.add(result)
            self._save_history()
            return result

        # Create backup
        try:
            backup_path = migration.backup()
            self.console.print(f"[dim]Backup created: {backup_path}[/dim]")
        except Exception as e:
            result = MigrationResult(
                success=False,
                migration_name=migration.name,
                message=f"Backup failed: {e}",
            )
            self.history.add(result)
            self._save_history()
            return result

        # Apply migration
        try:
            result = migration.migrate()
            result.backup_path = backup_path

            if result.success:
                self.console.print(f"[green]✓ Migration completed[/green]")
            else:
                self.console.print(f"[red]✗ Migration failed: {result.message}[/red]")
                # Rollback on failure
                try:
                    migration.rollback()
                    self.console.print("[dim]Rolled back to backup[/dim]")
                except Exception:
                    pass

        except Exception as e:
            result = MigrationResult(
                success=False,
                migration_name=migration.name,
                message=f"Migration error: {e}",
            )
            # Rollback on exception
            try:
                migration.rollback()
                self.console.print("[dim]Rolled back to backup[/dim]")
            except Exception:
                pass

        # Add to history and save
        self.history.add(result)
        self._save_history()

        return result

    def apply_all(self, progress: Progress | None = None) -> list[MigrationResult]:
        """
        Apply all pending migrations.

        Args:
            progress: Optional progress tracker

        Returns:
            List of migration results
        """
        pending = self.get_pending_migrations()

        if not pending:
            self.console.print("[green]No pending migrations[/green]")
            return []

        results = []
        for migration in pending:
            result = self.apply_migration(migration)
            results.append(result)

            if not result.success and migration.required:
                self.console.print("[red]Required migration failed, stopping[/red]")
                break

        return results

    def rollback_migration(self, migration_name: str) -> bool:
        """
        Rollback a specific migration.

        Args:
            migration_name: Name of migration to rollback

        Returns:
            True if rollback was successful
        """
        # Find the migration result
        for result in self.history.results:
            if result.migration_name == migration_name and result.success:
                # Find the migration instance
                for migration in self.get_available_migrations():
                    if migration.name == migration_name:
                        try:
                            migration.rollback()
                            self.console.print(f"[green]Rolled back: {migration_name}[/green]")
                            return True
                        except Exception as e:
                            self.console.print(f"[red]Rollback failed: {e}[/red]")
                            return False

        self.console.print(f"[red]Migration not found or not applied: {migration_name}[/red]")
        return False

    def list_history(self) -> MigrationHistory:
        """
        Get migration history.

        Returns:
            MigrationHistory with all migrations
        """
        return self.history


# =============================================================================
# Convenience Functions
# =============================================================================


def check_migrations(project_path: Path) -> list[Migration]:
    """
    Check for available migrations.

    Args:
        project_path: Path to the project

    Returns:
        List of pending migrations
    """
    manager = MigrationManager(project_path)
    return manager.get_pending_migrations()


def apply_migrations(
    project_path: Path,
    console: Console | None = None,
) -> list[MigrationResult]:
    """
    Apply all pending migrations.

    Args:
        project_path: Path to the project
        console: Optional console for output

    Returns:
        List of migration results
    """
    manager = MigrationManager(project_path, console)
    return manager.apply_all()


def rollback_migration(
    project_path: Path,
    migration_name: str,
    console: Console | None = None,
) -> bool:
    """
    Rollback a specific migration.

    Args:
        project_path: Path to the project
        migration_name: Name of migration to rollback
        console: Optional console for output

    Returns:
        True if rollback was successful
    """
    manager = MigrationManager(project_path, console)
    return manager.rollback_migration(migration_name)


# =============================================================================
# Module Exports
# =============================================================================

# Import from utils.py (E8.3 additional utilities)
from .utils import (
    MigrationRecord as UtilsMigrationRecord,
    MigrationStep,
    MigrationExecutor,
    StateMigrator,
    ConfigMigrator,
    DataMigrator,
    create_migration_executor,
    migrate_state as migrate_state_utils,
    migrate_config as migrate_config_utils,
)

__all__ = [
    # Enums
    "MigrationType",
    "MigrationStatus",
    # Models
    "MigrationResult",
    "MigrationHistory",
    # Base classes
    "Migration",
    "ConfigMigration",
    "StateMigration",
    # Manager
    "MigrationManager",
    # Convenience functions
    "check_migrations",
    "apply_migrations",
    "rollback_migration",
    # Additional utilities from utils.py (E8.3)
    "UtilsMigrationRecord",
    "MigrationStep",
    "MigrationExecutor",
    "StateMigrator",
    "ConfigMigrator",
    "DataMigrator",
    "create_migration_executor",
    "migrate_state_utils",
    "migrate_config_utils",
]
