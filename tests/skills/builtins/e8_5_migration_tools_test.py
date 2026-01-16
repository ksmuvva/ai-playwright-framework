"""Unit tests for E8.5 - Migration Tools skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.e8_5_migration_tools import (
    BackupRecord,
    MigrationRecord,
    MigrationToolsAgent,
)
from claude_playwright_agent.agents.base import BaseAgent


class TestMigrationRecord:
    @pytest.mark.unit
    def test_migration_record_creation(self):
        record = MigrationRecord(
            record_id="mig_001",
            from_version="1.0.0",
            to_version="2.0.0",
        )
        assert record.from_version == "1.0.0"


class TestBackupRecord:
    @pytest.mark.unit
    def test_backup_record_creation(self):
        record = BackupRecord(
            backup_id="bak_001",
            backup_path="/backup.zip",
        )
        assert record.backup_path == "/backup.zip"


class TestMigrationToolsAgent:
    @pytest.fixture
    def agent(self):
        return MigrationToolsAgent()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        assert agent.name == "e8_5_migration_tools"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_create_backup(self, agent, temp_project_path):
        context = {"project_path": str(temp_project_path)}
        result = await agent.run("backup", context)
        assert "backup" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_restore_backup(self, agent, temp_project_path):
        backup_path = temp_project_path / "backup.zip"
        context = {"backup_path": str(backup_path)}
        result = await agent.run("restore", context)
        assert "restored" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_migrate_state(self, agent):
        context = {"to_version": "2.0.0"}
        result = await agent.run("migrate", context)
        assert "migrated" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        result = await agent.run("invalid", {})
        assert "unknown task type" in result.lower()
