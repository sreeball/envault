"""Tests for envault.history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.history import (
    HistoryError,
    _history_path,
    all_keys_with_history,
    clear_history,
    get_history,
    record_change,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "vault.json"
    p.write_text(json.dumps({}))
    return p


class TestRecordChange:
    def test_creates_history_file(self, vault_path: Path) -> None:
        record_change(vault_path, "DB_PASS", "set")
        assert _history_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: Path) -> None:
        entry = record_change(vault_path, "DB_PASS", "set")
        assert entry["action"] == "set"
        assert entry["actor"] == "user"
        assert "timestamp" in entry

    def test_custom_actor_and_note(self, vault_path: Path) -> None:
        entry = record_change(vault_path, "API_KEY", "rotate", actor="ci", note="weekly")
        assert entry["actor"] == "ci"
        assert entry["note"] == "weekly"

    def test_accumulates_entries(self, vault_path: Path) -> None:
        record_change(vault_path, "X", "set")
        record_change(vault_path, "X", "set")
        record_change(vault_path, "X", "delete")
        history = get_history(vault_path, "X")
        assert len(history) == 3

    def test_multiple_keys_independent(self, vault_path: Path) -> None:
        record_change(vault_path, "A", "set")
        record_change(vault_path, "B", "import")
        assert len(get_history(vault_path, "A")) == 1
        assert len(get_history(vault_path, "B")) == 1

    def test_invalid_action_raises(self, vault_path: Path) -> None:
        with pytest.raises(HistoryError, match="Invalid action"):
            record_change(vault_path, "X", "unknown")

    def test_all_valid_actions_accepted(self, vault_path: Path) -> None:
        for action in ("set", "delete", "rotate", "import"):
            record_change(vault_path, "K", action)
        assert len(get_history(vault_path, "K")) == 4


class TestGetHistory:
    def test_returns_empty_list_for_unknown_key(self, vault_path: Path) -> None:
        assert get_history(vault_path, "MISSING") == []

    def test_returns_empty_when_no_history_file(self, vault_path: Path) -> None:
        assert get_history(vault_path, "X") == []


class TestClearHistory:
    def test_removes_all_entries_for_key(self, vault_path: Path) -> None:
        record_change(vault_path, "K", "set")
        record_change(vault_path, "K", "set")
        removed = clear_history(vault_path, "K")
        assert removed == 2
        assert get_history(vault_path, "K") == []

    def test_returns_zero_for_unknown_key(self, vault_path: Path) -> None:
        assert clear_history(vault_path, "NOPE") == 0

    def test_does_not_affect_other_keys(self, vault_path: Path) -> None:
        record_change(vault_path, "A", "set")
        record_change(vault_path, "B", "set")
        clear_history(vault_path, "A")
        assert len(get_history(vault_path, "B")) == 1


class TestAllKeysWithHistory:
    def test_returns_sorted_keys(self, vault_path: Path) -> None:
        record_change(vault_path, "Z", "set")
        record_change(vault_path, "A", "set")
        record_change(vault_path, "M", "set")
        assert all_keys_with_history(vault_path) == ["A", "M", "Z"]

    def test_empty_when_no_history(self, vault_path: Path) -> None:
        assert all_keys_with_history(vault_path) == []
