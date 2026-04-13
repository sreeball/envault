"""Tests for envault.priority."""
import json
import pytest
from pathlib import Path

from envault.priority import (
    PriorityError,
    set_priority,
    get_priority,
    remove_priority,
    list_by_priority,
    _priority_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestSetPriority:
    def test_creates_priority_file(self, vault_path):
        set_priority(vault_path, "API_KEY", "high")
        assert _priority_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = set_priority(vault_path, "API_KEY", "critical")
        assert result == {"key": "API_KEY", "priority": "critical"}

    def test_stores_level_in_file(self, vault_path):
        set_priority(vault_path, "DB_PASS", "normal")
        data = json.loads(_priority_path(vault_path).read_text())
        assert data["DB_PASS"] == "normal"

    def test_overwrites_existing_level(self, vault_path):
        set_priority(vault_path, "TOKEN", "low")
        set_priority(vault_path, "TOKEN", "high")
        data = json.loads(_priority_path(vault_path).read_text())
        assert data["TOKEN"] == "high"

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(PriorityError, match="Invalid priority"):
            set_priority(vault_path, "KEY", "urgent")


class TestGetPriority:
    def test_returns_level_when_set(self, vault_path):
        set_priority(vault_path, "API_KEY", "critical")
        assert get_priority(vault_path, "API_KEY") == "critical"

    def test_returns_none_when_unset(self, vault_path):
        assert get_priority(vault_path, "MISSING") is None


class TestRemovePriority:
    def test_removes_entry(self, vault_path):
        set_priority(vault_path, "API_KEY", "high")
        remove_priority(vault_path, "API_KEY")
        assert get_priority(vault_path, "API_KEY") is None

    def test_raises_when_key_not_found(self, vault_path):
        with pytest.raises(PriorityError, match="No priority set"):
            remove_priority(vault_path, "GHOST")


class TestListByPriority:
    def test_returns_all_entries(self, vault_path):
        set_priority(vault_path, "A", "low")
        set_priority(vault_path, "B", "critical")
        results = list_by_priority(vault_path)
        assert len(results) == 2

    def test_sorted_by_severity(self, vault_path):
        set_priority(vault_path, "A", "low")
        set_priority(vault_path, "B", "normal")
        set_priority(vault_path, "C", "critical")
        levels = [r["priority"] for r in list_by_priority(vault_path)]
        assert levels == ["critical", "normal", "low"]

    def test_filter_by_level(self, vault_path):
        set_priority(vault_path, "A", "high")
        set_priority(vault_path, "B", "low")
        results = list_by_priority(vault_path, level="high")
        assert all(r["priority"] == "high" for r in results)

    def test_filter_invalid_level_raises(self, vault_path):
        with pytest.raises(PriorityError, match="Invalid priority"):
            list_by_priority(vault_path, level="extreme")

    def test_empty_when_no_priorities(self, vault_path):
        assert list_by_priority(vault_path) == []
