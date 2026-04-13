"""Tests for envault.archive."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.archive import (
    ArchiveError,
    _archive_path,
    archive_key,
    restore_key,
    list_archived,
    purge_archived,
)

_DUMMY_ENTRY = {"salt": "abc", "ciphertext": "xyz"}


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


class TestArchiveKey:
    def test_creates_archive_file(self, vault_path: str) -> None:
        archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        assert _archive_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: str) -> None:
        result = archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        assert result["key"] == "MY_KEY"
        assert result["archived"] is True
        assert result["entry"] == _DUMMY_ENTRY

    def test_stores_entry_in_file(self, vault_path: str) -> None:
        archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        data = json.loads(_archive_path(vault_path).read_text())
        assert data["MY_KEY"] == _DUMMY_ENTRY

    def test_raises_on_empty_key(self, vault_path: str) -> None:
        with pytest.raises(ArchiveError, match="empty"):
            archive_key(vault_path, "", _DUMMY_ENTRY)

    def test_raises_on_duplicate_archive(self, vault_path: str) -> None:
        archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        with pytest.raises(ArchiveError, match="already archived"):
            archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)

    def test_accumulates_multiple_keys(self, vault_path: str) -> None:
        archive_key(vault_path, "KEY_A", _DUMMY_ENTRY)
        archive_key(vault_path, "KEY_B", _DUMMY_ENTRY)
        assert set(list_archived(vault_path)) == {"KEY_A", "KEY_B"}


class TestRestoreKey:
    def test_returns_entry_on_restore(self, vault_path: str) -> None:
        archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        result = restore_key(vault_path, "MY_KEY")
        assert result["restored"] is True
        assert result["entry"] == _DUMMY_ENTRY

    def test_removes_key_from_archive(self, vault_path: str) -> None:
        archive_key(vault_path, "MY_KEY", _DUMMY_ENTRY)
        restore_key(vault_path, "MY_KEY")
        assert "MY_KEY" not in list_archived(vault_path)

    def test_raises_when_key_not_archived(self, vault_path: str) -> None:
        with pytest.raises(ArchiveError, match="not in the archive"):
            restore_key(vault_path, "MISSING")


class TestListArchived:
    def test_empty_when_no_archive_file(self, vault_path: str) -> None:
        assert list_archived(vault_path) == []

    def test_lists_all_archived_keys(self, vault_path: str) -> None:
        archive_key(vault_path, "A", _DUMMY_ENTRY)
        archive_key(vault_path, "B", _DUMMY_ENTRY)
        assert sorted(list_archived(vault_path)) == ["A", "B"]


class TestPurgeArchived:
    def test_purge_single_key(self, vault_path: str) -> None:
        archive_key(vault_path, "A", _DUMMY_ENTRY)
        archive_key(vault_path, "B", _DUMMY_ENTRY)
        count = purge_archived(vault_path, key="A")
        assert count == 1
        assert list_archived(vault_path) == ["B"]

    def test_purge_all_keys(self, vault_path: str) -> None:
        archive_key(vault_path, "A", _DUMMY_ENTRY)
        archive_key(vault_path, "B", _DUMMY_ENTRY)
        count = purge_archived(vault_path)
        assert count == 2
        assert list_archived(vault_path) == []

    def test_purge_missing_key_raises(self, vault_path: str) -> None:
        with pytest.raises(ArchiveError, match="not in the archive"):
            purge_archived(vault_path, key="MISSING")
