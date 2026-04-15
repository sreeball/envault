"""Tests for envault.trigger."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from envault.trigger import (
    add_trigger, remove_trigger, fire_triggers, list_triggers,
    TriggerError, _triggers_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestAddTrigger:
    def test_creates_triggers_file(self, vault_path):
        add_trigger(vault_path, "DB_PASS", "set", "echo changed")
        assert _triggers_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = add_trigger(vault_path, "DB_PASS", "set", "echo changed")
        assert entry["key"] == "DB_PASS"
        assert entry["event"] == "set"
        assert entry["command"] == "echo changed"

    def test_accumulates_commands(self, vault_path):
        add_trigger(vault_path, "KEY", "set", "echo a")
        add_trigger(vault_path, "KEY", "set", "echo b")
        data = json.loads(_triggers_path(vault_path).read_text())
        assert "echo a" in data["KEY"]["set"]
        assert "echo b" in data["KEY"]["set"]

    def test_no_duplicate_commands(self, vault_path):
        add_trigger(vault_path, "KEY", "delete", "echo x")
        add_trigger(vault_path, "KEY", "delete", "echo x")
        data = json.loads(_triggers_path(vault_path).read_text())
        assert data["KEY"]["delete"].count("echo x") == 1

    def test_raises_on_invalid_event(self, vault_path):
        with pytest.raises(TriggerError, match="Invalid event"):
            add_trigger(vault_path, "KEY", "explode", "echo x")

    def test_raises_on_empty_command(self, vault_path):
        with pytest.raises(TriggerError, match="empty"):
            add_trigger(vault_path, "KEY", "set", "   ")


class TestRemoveTrigger:
    def test_removes_existing_trigger(self, vault_path):
        add_trigger(vault_path, "KEY", "set", "echo hi")
        result = remove_trigger(vault_path, "KEY", "set", "echo hi")
        assert result is True
        data = json.loads(_triggers_path(vault_path).read_text())
        assert "KEY" not in data

    def test_returns_false_when_not_found(self, vault_path):
        result = remove_trigger(vault_path, "MISSING", "set", "echo hi")
        assert result is False

    def test_cleans_up_empty_event_and_key(self, vault_path):
        add_trigger(vault_path, "KEY", "rotate", "echo r")
        remove_trigger(vault_path, "KEY", "rotate", "echo r")
        data = json.loads(_triggers_path(vault_path).read_text())
        assert "KEY" not in data


class TestFireTriggers:
    def test_runs_registered_command(self, vault_path):
        add_trigger(vault_path, "KEY", "set", "echo hello")
        results = fire_triggers(vault_path, "KEY", "set")
        assert len(results) == 1
        assert results[0]["returncode"] == 0
        assert results[0]["stdout"] == "hello"

    def test_returns_empty_list_when_no_triggers(self, vault_path):
        results = fire_triggers(vault_path, "NONE", "set")
        assert results == []

    def test_captures_nonzero_returncode(self, vault_path):
        add_trigger(vault_path, "KEY", "expire", "exit 42")
        results = fire_triggers(vault_path, "KEY", "expire")
        assert results[0]["returncode"] == 42


class TestListTriggers:
    def test_returns_all_triggers(self, vault_path):
        add_trigger(vault_path, "A", "set", "echo a")
        add_trigger(vault_path, "B", "delete", "echo b")
        data = list_triggers(vault_path)
        assert "A" in data
        assert "B" in data

    def test_filters_by_key(self, vault_path):
        add_trigger(vault_path, "A", "set", "echo a")
        add_trigger(vault_path, "B", "set", "echo b")
        data = list_triggers(vault_path, key="A")
        assert "A" in data
        assert "B" not in data

    def test_empty_when_no_file(self, vault_path):
        data = list_triggers(vault_path)
        assert data == {}
