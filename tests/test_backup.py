"""Tests for envault.backup module."""

import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.backup import (
    BackupError,
    create_backup,
    list_backups,
    restore_backup,
    delete_backup,
)


@pytest.fixture
def vault_path(tmp_path):
    vp = tmp_path / "vault.json"
    v = Vault(str(vp), password="secret")
    v.set("KEY1", "value1")
    v.set("KEY2", "value2")
    return str(vp)


class TestCreateBackup:
    def test_creates_backup_file(self, vault_path):
        meta = create_backup(vault_path)
        assert Path(meta["path"]).exists()

    def test_returns_metadata_dict(self, vault_path):
        meta = create_backup(vault_path)
        assert "timestamp" in meta
        assert "filename" in meta
        assert "path" in meta
        assert "label" in meta

    def test_label_in_filename(self, vault_path):
        meta = create_backup(vault_path, label="before-rotation")
        assert "before-rotation" in meta["filename"]

    def test_empty_label_omitted_from_filename(self, vault_path):
        meta = create_backup(vault_path, label="")
        # filename should be backup_<ts>.json, no trailing underscore
        assert meta["filename"].endswith(".json")
        parts = meta["filename"].replace(".json", "").split("_")
        assert len(parts) == 2  # ['backup', timestamp]

    def test_raises_if_vault_missing(self, tmp_path):
        with pytest.raises(BackupError, match="Vault file not found"):
            create_backup(str(tmp_path / "nonexistent.json"))

    def test_backup_content_matches_vault(self, vault_path):
        meta = create_backup(vault_path)
        original = Path(vault_path).read_bytes()
        backup = Path(meta["path"]).read_bytes()
        assert original == backup


class TestListBackups:
    def test_empty_when_no_backups(self, vault_path):
        assert list_backups(vault_path) == []

    def test_returns_one_entry_after_create(self, vault_path):
        create_backup(vault_path)
        entries = list_backups(vault_path)
        assert len(entries) == 1

    def test_returns_multiple_sorted(self, vault_path):
        create_backup(vault_path, label="first")
        create_backup(vault_path, label="second")
        entries = list_backups(vault_path)
        assert len(entries) == 2
        assert entries[0]["filename"] < entries[1]["filename"]


class TestRestoreBackup:
    def test_restores_previous_state(self, vault_path, tmp_path):
        meta = create_backup(vault_path)
        # Overwrite vault with new data
        v = Vault(vault_path, password="secret")
        v.set("KEY3", "value3")
        original_bytes = Path(meta["path"]).read_bytes()
        restore_backup(vault_path, meta["filename"])
        assert Path(vault_path).read_bytes() == original_bytes

    def test_raises_on_missing_backup(self, vault_path):
        with pytest.raises(BackupError, match="Backup not found"):
            restore_backup(vault_path, "backup_nonexistent.json")


class TestDeleteBackup:
    def test_removes_backup_file(self, vault_path):
        meta = create_backup(vault_path)
        delete_backup(vault_path, meta["filename"])
        assert not Path(meta["path"]).exists()

    def test_raises_on_missing_backup(self, vault_path):
        with pytest.raises(BackupError, match="Backup not found"):
            delete_backup(vault_path, "backup_ghost.json")
