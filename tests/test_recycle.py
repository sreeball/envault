"""Tests for envault.recycle."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.recycle import (
    RecycleError,
    _recycle_path,
    list_bin,
    purge,
    purge_all,
    restore,
    soft_delete,
)

FAKE_PAYLOAD = {"salt": "abc", "ciphertext": "xyz"}


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return p


class TestSoftDelete:
    def test_creates_recycle_file(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        assert _recycle_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: Path) -> None:
        entry = soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        assert entry["key"] == "MY_KEY"
        assert entry["payload"] == FAKE_PAYLOAD
        assert "deleted_at" in entry

    def test_stores_entry_in_file(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        data = json.loads(_recycle_path(vault_path).read_text())
        assert "MY_KEY" in data

    def test_raises_on_duplicate(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        with pytest.raises(RecycleError, match="already in the recycle bin"):
            soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)

    def test_multiple_keys(self, vault_path: Path) -> None:
        soft_delete(vault_path, "KEY_A", FAKE_PAYLOAD)
        soft_delete(vault_path, "KEY_B", FAKE_PAYLOAD)
        assert len(list_bin(vault_path)) == 2


class TestRestore:
    def test_returns_entry(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        entry = restore(vault_path, "MY_KEY")
        assert entry["key"] == "MY_KEY"

    def test_removes_from_bin(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        restore(vault_path, "MY_KEY")
        assert list_bin(vault_path) == []

    def test_raises_when_key_missing(self, vault_path: Path) -> None:
        with pytest.raises(RecycleError, match="not found in the recycle bin"):
            restore(vault_path, "GHOST")


class TestListBin:
    def test_empty_when_no_file(self, vault_path: Path) -> None:
        assert list_bin(vault_path) == []

    def test_lists_all_entries(self, vault_path: Path) -> None:
        soft_delete(vault_path, "A", FAKE_PAYLOAD)
        soft_delete(vault_path, "B", FAKE_PAYLOAD)
        keys = {e["key"] for e in list_bin(vault_path)}
        assert keys == {"A", "B"}


class TestPurge:
    def test_removes_single_key(self, vault_path: Path) -> None:
        soft_delete(vault_path, "MY_KEY", FAKE_PAYLOAD)
        purge(vault_path, "MY_KEY")
        assert list_bin(vault_path) == []

    def test_raises_when_key_missing(self, vault_path: Path) -> None:
        with pytest.raises(RecycleError, match="not found in the recycle bin"):
            purge(vault_path, "GHOST")


class TestPurgeAll:
    def test_returns_count(self, vault_path: Path) -> None:
        soft_delete(vault_path, "A", FAKE_PAYLOAD)
        soft_delete(vault_path, "B", FAKE_PAYLOAD)
        assert purge_all(vault_path) == 2

    def test_bin_empty_afterwards(self, vault_path: Path) -> None:
        soft_delete(vault_path, "A", FAKE_PAYLOAD)
        purge_all(vault_path)
        assert list_bin(vault_path) == []

    def test_returns_zero_when_already_empty(self, vault_path: Path) -> None:
        assert purge_all(vault_path) == 0
