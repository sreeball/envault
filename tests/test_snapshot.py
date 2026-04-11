"""Tests for envault.snapshot."""

import json
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "vault.db")
    v = Vault(path, PASSWORD)
    v.set("KEY_A", "alpha")
    v.set("KEY_B", "beta")
    return path


class TestCreateSnapshot:
    def test_creates_snapshot_file(self, vault_path):
        result = create_snapshot(vault_path, PASSWORD)
        assert Path(result["snapshot"]).exists()

    def test_returns_metadata(self, vault_path):
        result = create_snapshot(vault_path, PASSWORD)
        assert result["count"] == 2
        assert result["timestamp"]

    def test_label_in_filename(self, vault_path):
        result = create_snapshot(vault_path, PASSWORD, label="before-deploy")
        assert "before-deploy" in result["snapshot"]
        assert result["label"] == "before-deploy"

    def test_snapshot_contains_secrets(self, vault_path):
        result = create_snapshot(vault_path, PASSWORD)
        data = json.loads(Path(result["snapshot"]).read_text())
        assert data["secrets"]["KEY_A"] == "alpha"
        assert data["secrets"]["KEY_B"] == "beta"


class TestListSnapshots:
    def test_empty_when_no_snapshots(self, vault_path):
        assert list_snapshots(vault_path) == []

    def test_returns_one_entry_per_snapshot(self, vault_path):
        create_snapshot(vault_path, PASSWORD)
        create_snapshot(vault_path, PASSWORD)
        snaps = list_snapshots(vault_path)
        assert len(snaps) == 2

    def test_entry_has_expected_keys(self, vault_path):
        create_snapshot(vault_path, PASSWORD, label="v1")
        snap = list_snapshots(vault_path)[0]
        assert {"file", "timestamp", "label", "count"} <= snap.keys()

    def test_newest_first(self, vault_path):
        r1 = create_snapshot(vault_path, PASSWORD)
        r2 = create_snapshot(vault_path, PASSWORD)
        snaps = list_snapshots(vault_path)
        # Filenames sort lexicographically; newest has greater timestamp string
        assert snaps[0]["file"] >= snaps[1]["file"]


class TestRestoreSnapshot:
    def test_restores_secrets(self, vault_path):
        snap = create_snapshot(vault_path, PASSWORD)
        # Mutate vault
        Vault(vault_path, PASSWORD).set("KEY_A", "changed")
        restore_snapshot(vault_path, PASSWORD, snap["snapshot"])
        assert Vault(vault_path, PASSWORD).get("KEY_A") == "alpha"

    def test_returns_restore_metadata(self, vault_path):
        snap = create_snapshot(vault_path, PASSWORD)
        result = restore_snapshot(vault_path, PASSWORD, snap["snapshot"])
        assert result["restored"] == 2
        assert result["from"] == snap["snapshot"]

    def test_raises_on_missing_file(self, vault_path):
        with pytest.raises(SnapshotError, match="not found"):
            restore_snapshot(vault_path, PASSWORD, "/nonexistent/snap.json")


class TestDeleteSnapshot:
    def test_removes_file(self, vault_path):
        snap = create_snapshot(vault_path, PASSWORD)
        delete_snapshot(vault_path, snap["snapshot"])
        assert not Path(snap["snapshot"]).exists()

    def test_raises_on_missing_file(self, vault_path):
        with pytest.raises(SnapshotError, match="not found"):
            delete_snapshot(vault_path, "/nonexistent/snap.json")
