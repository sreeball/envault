"""Tests for envault.version."""
import pytest
from pathlib import Path

from envault.version import (
    VersionError,
    get_versions,
    purge_versions,
    record_version,
    rollback,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.json")


class TestRecordVersion:
    def test_creates_versions_file(self, vault_path):
        record_version(vault_path, "DB_URL", "postgres://localhost/dev")
        versions_file = Path(vault_path).parent / ".envault_versions.json"
        assert versions_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = record_version(vault_path, "DB_URL", "postgres://localhost/dev")
        assert entry["key"] if "key" in entry else entry["value"] == "postgres://localhost/dev"
        assert entry["version"] == 1
        assert "recorded_at" in entry

    def test_version_increments(self, vault_path):
        record_version(vault_path, "API_KEY", "v1")
        record_version(vault_path, "API_KEY", "v2")
        entry = record_version(vault_path, "API_KEY", "v3")
        assert entry["version"] == 3

    def test_different_keys_are_independent(self, vault_path):
        record_version(vault_path, "A", "a1")
        record_version(vault_path, "A", "a2")
        entry_b = record_version(vault_path, "B", "b1")
        assert entry_b["version"] == 1

    def test_custom_actor(self, vault_path):
        entry = record_version(vault_path, "SECRET", "value", actor="ci-bot")
        assert entry["actor"] == "ci-bot"

    def test_default_actor_is_user(self, vault_path):
        entry = record_version(vault_path, "SECRET", "value")
        assert entry["actor"] == "user"


class TestGetVersions:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        assert get_versions(vault_path, "MISSING") == []

    def test_returns_all_entries_in_order(self, vault_path):
        record_version(vault_path, "K", "first")
        record_version(vault_path, "K", "second")
        entries = get_versions(vault_path, "K")
        assert len(entries) == 2
        assert entries[0]["value"] == "first"
        assert entries[1]["value"] == "second"


class TestRollback:
    def test_returns_correct_version(self, vault_path):
        record_version(vault_path, "K", "alpha")
        record_version(vault_path, "K", "beta")
        entry = rollback(vault_path, "K", 1)
        assert entry["value"] == "alpha"

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(VersionError, match="No version history"):
            rollback(vault_path, "GHOST", 1)

    def test_raises_on_out_of_range(self, vault_path):
        record_version(vault_path, "K", "only")
        with pytest.raises(VersionError, match="out of range"):
            rollback(vault_path, "K", 5)


class TestPurgeVersions:
    def test_removes_all_entries(self, vault_path):
        record_version(vault_path, "K", "v1")
        record_version(vault_path, "K", "v2")
        count = purge_versions(vault_path, "K")
        assert count == 2
        assert get_versions(vault_path, "K") == []

    def test_returns_zero_for_unknown_key(self, vault_path):
        assert purge_versions(vault_path, "GHOST") == 0

    def test_does_not_affect_other_keys(self, vault_path):
        record_version(vault_path, "A", "a")
        record_version(vault_path, "B", "b")
        purge_versions(vault_path, "A")
        assert len(get_versions(vault_path, "B")) == 1
