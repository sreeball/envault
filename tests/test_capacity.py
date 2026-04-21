"""Tests for envault.capacity."""

from __future__ import annotations

import json
import pytest

from envault.capacity import (
    CapacityError,
    set_capacity,
    get_capacity,
    remove_capacity,
    list_capacity,
    _capacity_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetCapacity:
    def test_creates_capacity_file(self, vault_path):
        set_capacity(vault_path, "API_KEY", 128)
        assert _capacity_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_capacity(vault_path, "API_KEY", 64)
        assert entry["key"] == "API_KEY"
        assert entry["max_length"] == 64

    def test_stores_entry_in_file(self, vault_path):
        set_capacity(vault_path, "TOKEN", 256)
        raw = json.loads(_capacity_path(vault_path).read_text())
        assert "TOKEN" in raw
        assert raw["TOKEN"]["max_length"] == 256

    def test_stores_note(self, vault_path):
        set_capacity(vault_path, "DB_PASS", 32, note="bcrypt limit")
        entry = get_capacity(vault_path, "DB_PASS")
        assert entry["note"] == "bcrypt limit"

    def test_empty_note_allowed(self, vault_path):
        entry = set_capacity(vault_path, "X", 10)
        assert entry["note"] == ""

    def test_raises_on_zero_max_length(self, vault_path):
        with pytest.raises(CapacityError):
            set_capacity(vault_path, "KEY", 0)

    def test_raises_on_negative_max_length(self, vault_path):
        with pytest.raises(CapacityError):
            set_capacity(vault_path, "KEY", -5)

    def test_overwrites_existing_entry(self, vault_path):
        set_capacity(vault_path, "KEY", 50)
        set_capacity(vault_path, "KEY", 100)
        entry = get_capacity(vault_path, "KEY")
        assert entry["max_length"] == 100

    def test_accumulates_multiple_keys(self, vault_path):
        set_capacity(vault_path, "A", 10)
        set_capacity(vault_path, "B", 20)
        all_caps = list_capacity(vault_path)
        assert "A" in all_caps and "B" in all_caps


class TestGetCapacity:
    def test_returns_none_when_not_set(self, vault_path):
        assert get_capacity(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_capacity(vault_path, "K", 99)
        entry = get_capacity(vault_path, "K")
        assert entry is not None
        assert entry["max_length"] == 99


class TestRemoveCapacity:
    def test_removes_existing_entry(self, vault_path):
        set_capacity(vault_path, "K", 10)
        result = remove_capacity(vault_path, "K")
        assert result is True
        assert get_capacity(vault_path, "K") is None

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_capacity(vault_path, "GHOST") is False


class TestListCapacity:
    def test_empty_when_no_file(self, vault_path):
        assert list_capacity(vault_path) == {}

    def test_lists_all_entries(self, vault_path):
        set_capacity(vault_path, "X", 1)
        set_capacity(vault_path, "Y", 2)
        result = list_capacity(vault_path)
        assert set(result.keys()) == {"X", "Y"}
