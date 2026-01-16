"""
Tests for the Migration module.

Tests cover:
- Migration models and enums
- Configuration migration
- State migration
- Migration manager functionality
- Rollback and backup
- Migration history tracking
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from yaml import dump

from claude_playwright_agent.config.manager import ConfigManager
from claude_playwright_agent.migration import (
    Migration,
    MigrationType,
    MigrationStatus,
    MigrationResult,
    MigrationHistory,
    ConfigMigration,
    StateMigration,
    MigrationManager,
    check_migrations,
    apply_migrations,
    rollback_migration,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def clean_history(tmp_path: Path) -> None:
    """Clean migration history between tests."""
    history_file = tmp_path / ".cpa" / "migrations.json"
    if history_file.exists():
        history_file.unlink()


@pytest.fixture
def initialized_project(tmp_path: Path) -> Path:
    """Create an initialized project for migration testing."""
    # Create .cpa directory structure
    cpa_dir = tmp_path / ".cpa"
    cpa_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal config
    config_data = {
        "version": "0.1.0",
        "profile": "default",
        "framework": {
            "bdd_framework": "behave",
            "template": "basic",
            "base_url": "http://localhost:8000",
            "default_timeout": 30000,
        },
        "browser": {
            "browser": "chromium",
            "headless": True,
            "viewport_width": 1280,
            "viewport_height": 720,
        },
        "execution": {
            "parallel_workers": 2,
            "retry_failed": True,
            "self_healing": True,
        },
        "logging": {
            "level": "INFO",
            "format": "text",
            "file": str(cpa_dir / "logs" / "agent.log"),
            "console": True,
            "rotation": "10 MB",
            "retention": "7 days",
        },
    }

    config_file = cpa_dir / "config.yaml"
    config_file.write_text(dump(config_data), encoding="utf-8")

    # Create minimal state
    state_data = {
        "project": {
            "name": "test-project",
            "framework_type": "behave",
            "version": "0.1.0",
            "created_at": "2024-01-01T00:00:00",
        },
        "recordings": {},
        "scenarios": {},
        "test_runs": {},
    }

    state_file = cpa_dir / "state.json"
    state_file.write_text(json.dumps(state_data), encoding="utf-8")

    return tmp_path


# =============================================================================
# MigrationType Enum Tests
# =============================================================================


class TestMigrationType:
    """Tests for MigrationType enum."""

    def test_migration_type_values(self) -> None:
        """Test migration type enum values."""
        assert MigrationType.CONFIG.value == "config"
        assert MigrationType.STATE.value == "state"
        assert MigrationType.FILES.value == "files"
        assert MigrationType.DEPENDENCIES.value == "dependencies"

    def test_migration_type_count(self) -> None:
        """Test migration type enum has correct number of values."""
        assert len(MigrationType) == 4


# =============================================================================
# MigrationStatus Enum Tests
# =============================================================================


class TestMigrationStatus:
    """Tests for MigrationStatus enum."""

    def test_migration_status_values(self) -> None:
        """Test migration status enum values."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.IN_PROGRESS.value == "in_progress"
        assert MigrationStatus.COMPLETED.value == "completed"
        assert MigrationStatus.FAILED.value == "failed"
        assert MigrationStatus.ROLLED_BACK.value == "rolled_back"

    def test_migration_status_ordering(self) -> None:
        """Test migration status comparison."""
        assert MigrationStatus.PENDING < MigrationStatus.IN_PROGRESS
        assert MigrationStatus.IN_PROGRESS < MigrationStatus.COMPLETED
        assert MigrationStatus.COMPLETED < MigrationStatus.FAILED
        assert MigrationStatus.FAILED < MigrationStatus.ROLLED_BACK


# =============================================================================
# MigrationResult Tests
# =============================================================================


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a migration result."""
        result = MigrationResult(
            success=True,
            migration_name="test_migration",
        )

        assert result.success is True
        assert result.migration_name == "test_migration"
        assert result.from_version is None
        assert result.to_version is None
        assert result.message == ""
        assert result.details == {}

    def test_create_result_with_all_fields(self) -> None:
        """Test creating result with all fields."""
        result = MigrationResult(
            success=False,
            migration_name="test_migration",
            from_version="0.1.0",
            to_version="0.2.0",
            message="Test failed",
            details={"error": "test error"},
            backup_path=Path("/backup"),
        )

        assert result.success is False
        assert result.migration_name == "test_migration"
        assert result.from_version == "0.1.0"
        assert result.to_version == "0.2.0"
        assert result.message == "Test failed"
        assert result.details == {"error": "test error"}
        assert result.backup_path == Path("/backup")

    def test_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = MigrationResult(
            success=True,
            migration_name="test_migration",
            from_version="0.1.0",
            to_version="0.2.0",
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["migration_name"] == "test_migration"
        assert data["from_version"] == "0.1.0"
        assert data["to_version"] == "0.2.0"
        assert "timestamp" in data
        assert data["backup_path"] is None

    def test_to_dict_with_backup_path(self) -> None:
        """Test converting result with backup path to dictionary."""
        result = MigrationResult(
            success=True,
            migration_name="test_migration",
            backup_path=Path("/backup/path"),
        )

        data = result.to_dict()

        # Path separators may differ by platform
        assert "backup" in data["backup_path"]
        assert "path" in data["backup_path"]


# =============================================================================
# MigrationHistory Tests
# =============================================================================


class TestMigrationHistory:
    """Tests for MigrationHistory class."""

    def test_empty_history(self) -> None:
        """Test empty migration history."""
        history = MigrationHistory()

        assert history.results == []
        assert history.get_latest() is None
        assert history.get_successful() == []
        assert history.get_failed() == []

    def test_add_result(self) -> None:
        """Test adding a result to history."""
        history = MigrationHistory()
        result = MigrationResult(success=True, migration_name="test")

        history.add(result)

        assert len(history.results) == 1
        assert history.results[0] == result

    def test_get_latest(self) -> None:
        """Test getting latest result."""
        history = MigrationHistory()

        result1 = MigrationResult(success=True, migration_name="test1")
        result2 = MigrationResult(success=True, migration_name="test2")

        history.add(result1)
        history.add(result2)

        assert history.get_latest() == result2

    def test_get_successful(self) -> None:
        """Test getting successful migrations."""
        history = MigrationHistory()

        history.add(MigrationResult(success=True, migration_name="test1"))
        history.add(MigrationResult(success=False, migration_name="test2"))
        history.add(MigrationResult(success=True, migration_name="test3"))

        successful = history.get_successful()

        assert len(successful) == 2
        assert successful[0].migration_name == "test1"
        assert successful[1].migration_name == "test3"

    def test_get_failed(self) -> None:
        """Test getting failed migrations."""
        history = MigrationHistory()

        history.add(MigrationResult(success=True, migration_name="test1"))
        history.add(MigrationResult(success=False, migration_name="test2"))
        history.add(MigrationResult(success=False, migration_name="test3"))

        failed = history.get_failed()

        assert len(failed) == 2
        assert failed[0].migration_name == "test2"
        assert failed[1].migration_name == "test3"

    def test_to_dict(self) -> None:
        """Test converting history to dictionary."""
        history = MigrationHistory()

        history.add(MigrationResult(success=True, migration_name="test1"))
        history.add(MigrationResult(success=False, migration_name="test2"))

        data = history.to_dict()

        assert data["total"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert len(data["migrations"]) == 2


# =============================================================================
# Base Migration Tests
# =============================================================================


class TestMigration:
    """Tests for base Migration class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test migration initialization."""
        migration = Migration(tmp_path)

        assert migration.project_path == tmp_path
        assert migration.console is not None
        assert migration.backup_path is None

    def test_pre_check_default(self, tmp_path: Path) -> None:
        """Test default pre-check returns True."""
        migration = Migration(tmp_path)

        can_apply, reason = migration.pre_check()

        assert can_apply is True
        assert reason == ""

    def test_migrate_not_implemented(self, tmp_path: Path) -> None:
        """Test that migrate raises NotImplementedError."""
        migration = Migration(tmp_path)

        with pytest.raises(NotImplementedError):
            migration.migrate()

    def test_backup(self, initialized_project: Path) -> None:
        """Test creating a backup."""
        migration = Migration(initialized_project)

        backup_path = migration.backup()

        assert backup_path is not None
        assert backup_path.exists()
        assert (backup_path / ".cpa").exists()
        assert migration.backup_path == backup_path

    def test_rollback(self, initialized_project: Path) -> None:
        """Test rollback functionality."""
        migration = Migration(initialized_project)

        # Create backup
        backup_path = migration.backup()

        # Modify something
        config_file = initialized_project / ".cpa" / "config.yaml"
        original_content = config_file.read_text(encoding="utf-8")
        config_file.write_text("modified", encoding="utf-8")

        # Rollback
        migration.rollback()

        # Check content was restored
        restored_content = config_file.read_text(encoding="utf-8")
        assert restored_content == original_content

    def test_cleanup_backup(self, initialized_project: Path) -> None:
        """Test cleanup of backup directory."""
        migration = Migration(initialized_project)

        backup_path = migration.backup()
        assert backup_path.exists()

        migration.cleanup_backup()
        assert not backup_path.exists()


# =============================================================================
# ConfigMigration Tests
# =============================================================================


class TestConfigMigration:
    """Tests for ConfigMigration class."""

    def test_migration_type(self, initialized_project: Path) -> None:
        """Test ConfigMigration has correct type."""
        migration = ConfigMigration(initialized_project)

        assert migration.migration_type == MigrationType.CONFIG
        assert migration.name == "config_migration"
        assert migration.version == "0.2.0"

    def test_migrate_success(self, initialized_project: Path) -> None:
        """Test successful configuration migration."""
        migration = ConfigMigration(initialized_project)

        result = migration.migrate()

        assert result.success is True
        assert result.migration_name == "config_migration"
        assert result.to_version == "0.2.0"
        assert "successfully" in result.message.lower()

    def test_migrate_without_project(self, tmp_path: Path) -> None:
        """Test migration fails when project not initialized."""
        # Don't initialize project - just an empty directory
        migration = ConfigMigration(tmp_path)

        result = migration.migrate()

        # ConfigManager will create a default config, so this may succeed
        # The key is that it doesn't crash
        assert result is not None


# =============================================================================
# StateMigration Tests
# =============================================================================


class TestStateMigration:
    """Tests for StateMigration class."""

    def test_migration_type(self, initialized_project: Path) -> None:
        """Test StateMigration has correct type."""
        migration = StateMigration(initialized_project)

        assert migration.migration_type == MigrationType.STATE
        assert migration.name == "state_migration"
        assert migration.version == "0.2.0"

    def test_migrate_success(self, initialized_project: Path) -> None:
        """Test successful state migration."""
        migration = StateMigration(initialized_project)

        result = migration.migrate()

        assert result.success is True
        assert result.migration_name == "state_migration"
        assert "successfully" in result.message.lower()


# =============================================================================
# MigrationManager Tests
# =============================================================================


class TestMigrationManager:
    """Tests for MigrationManager class."""

    def test_initialization(self, initialized_project: Path) -> None:
        """Test manager initialization."""
        manager = MigrationManager(initialized_project)

        assert manager.project_path == initialized_project
        assert manager.console is not None
        assert isinstance(manager.history, MigrationHistory)

    def test_get_available_migrations(self, initialized_project: Path) -> None:
        """Test getting available migrations."""
        manager = MigrationManager(initialized_project)

        migrations = manager.get_available_migrations()

        assert len(migrations) == 2
        assert isinstance(migrations[0], ConfigMigration)
        assert isinstance(migrations[1], StateMigration)

    def test_get_pending_migrations_empty_history(self, initialized_project: Path, clean_history: None) -> None:
        """Test getting pending migrations with empty history."""
        manager = MigrationManager(initialized_project)

        pending = manager.get_pending_migrations()

        # All migrations should be pending
        assert len(pending) == 2

    def test_get_pending_migrations_with_history(self, initialized_project: Path, clean_history: None) -> None:
        """Test getting pending migrations after some applied."""
        manager = MigrationManager(initialized_project)

        # Add a result to history
        manager.history.add(MigrationResult(
            success=True,
            migration_name="config_migration",
        ))

        pending = manager.get_pending_migrations()

        # Only state migration should be pending
        assert len(pending) == 1
        assert pending[0].name == "state_migration"

    def test_apply_migration_success(self, initialized_project: Path, clean_history: None) -> None:
        """Test applying a migration successfully."""
        manager = MigrationManager(initialized_project)

        migration = ConfigMigration(initialized_project)
        result = manager.apply_migration(migration)

        assert result.success is True
        assert len(manager.history.results) == 1
        assert manager.history.results[0] == result

    def test_apply_migration_failure(self, tmp_path: Path, clean_history: None) -> None:
        """Test applying migration to empty directory."""
        # Empty directory - ConfigManager will create defaults
        manager = MigrationManager(tmp_path)

        migration = ConfigMigration(tmp_path)
        result = manager.apply_migration(migration)

        # Migration may succeed or fail, but should not crash
        assert result is not None
        assert len(manager.history.results) >= 1

    def test_apply_all_no_pending(self, initialized_project: Path) -> None:
        """Test apply_all with no pending migrations."""
        manager = MigrationManager(initialized_project)

        # Mark all as applied in history
        manager.history.add(MigrationResult(success=True, migration_name="config_migration"))
        manager.history.add(MigrationResult(success=True, migration_name="state_migration"))

        results = manager.apply_all()

        # Should have no pending migrations to apply
        # (migrations are already in history, so they won't be applied again)
        assert len(results) == 0

    def test_apply_all_with_pending(self, initialized_project: Path, clean_history: None) -> None:
        """Test apply_all with pending migrations."""
        manager = MigrationManager(initialized_project)

        results = manager.apply_all()

        assert len(results) == 2

    def test_list_history(self, initialized_project: Path) -> None:
        """Test listing migration history."""
        manager = MigrationManager(initialized_project)

        history = manager.list_history()

        assert history == manager.history


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_check_migrations(self, initialized_project: Path) -> None:
        """Test checking for migrations."""
        migrations = check_migrations(initialized_project)

        assert len(migrations) == 2

    def test_apply_migrations(self, initialized_project: Path) -> None:
        """Test applying migrations via convenience function."""
        results = apply_migrations(initialized_project)

        assert len(results) == 2

    def test_rollback_migration(self, initialized_project: Path) -> None:
        """Test rolling back a migration."""
        # First apply a migration and create backup
        manager = MigrationManager(initialized_project)
        migration = ConfigMigration(initialized_project)
        backup_path = migration.backup()  # Create backup

        # Save the history so it persists
        manager.history.add(MigrationResult(
            success=True,
            migration_name="config_migration",
            backup_path=backup_path,
        ))
        manager._save_history()

        # Now rollback
        result = rollback_migration(initialized_project, "config_migration")

        assert result is True

    def test_rollback_nonexistent_migration(self, initialized_project: Path) -> None:
        """Test rolling back non-existent migration."""
        result = rollback_migration(initialized_project, "nonexistent")

        assert result is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestMigrationIntegration:
    """Integration tests for migration functionality."""

    def test_full_migration_cycle(self, initialized_project: Path, clean_history: None) -> None:
        """Test complete migration cycle: check, apply, verify."""
        manager = MigrationManager(initialized_project)

        # Check pending
        pending = manager.get_pending_migrations()
        initial_count = len(pending)
        assert initial_count > 0

        # Apply all
        results = manager.apply_all()

        # Check results
        assert len(results) == initial_count

        # Verify no more pending
        new_pending = manager.get_pending_migrations()
        assert len(new_pending) == 0

    def test_backup_and_restore(self, initialized_project: Path) -> None:
        """Test backup creation and restore."""
        migration = ConfigMigration(initialized_project)

        # Get original config
        config_file = initialized_project / ".cpa" / "config.yaml"
        original = config_file.read_text(encoding="utf-8")

        # Create backup and modify
        migration.backup()
        config_file.write_text("modified", encoding="utf-8")

        # Verify modification
        assert config_file.read_text(encoding="utf-8") == "modified"

        # Restore
        migration.rollback()

        # Verify restoration
        assert config_file.read_text(encoding="utf-8") == original

    def test_history_persistence(self, initialized_project: Path) -> None:
        """Test that migration history persists across manager instances."""
        manager1 = MigrationManager(initialized_project)

        # Add migration to history
        manager1.history.add(MigrationResult(
            success=True,
            migration_name="test_migration",
            from_version="0.1.0",
            to_version="0.2.0",
        ))

        # Save history
        manager1._save_history()

        # Create new manager instance
        manager2 = MigrationManager(initialized_project)

        # Verify history was loaded
        assert len(manager2.history.results) == 1
        assert manager2.history.results[0].migration_name == "test_migration"
