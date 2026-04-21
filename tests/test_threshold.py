"""Tests for envault.threshold."""

from __future__ import annotations

import json
import pytest

from envault.threshold import (
    ThresholdError,
    check_threshold,
    get_threshold,
    list_thresholds,
    remove_threshold,
    set_threshold,
    _threshold_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


class TestSetThreshold:
    def test_creates_threshold_file(self, vault_path):
        set_threshold(vault_path, "CPU_USAGE", "lt", 90.0)
        assert _threshold_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_threshold(vault_path, "MEM", "lte", 75.5, note="warn level")
        assert entry["operator"] == "lte"
        assert entry["value"] == 75.5
        assert entry["note"] == "warn level"

    def test_stores_entry_in_file(self, vault_path):
        set_threshold(vault_path, "DISK", "gt", 10.0)
        raw = json.loads(_threshold_path(vault_path).read_text())
        assert "DISK" in raw
        assert raw["DISK"]["operator"] == "gt"

    def test_raises_on_invalid_operator(self, vault_path):
        with pytest.raises(ThresholdError, match="Invalid operator"):
            set_threshold(vault_path, "X", "bad", 1.0)

    def test_overwrites_existing_threshold(self, vault_path):
        set_threshold(vault_path, "KEY", "lt", 50.0)
        set_threshold(vault_path, "KEY", "gt", 10.0)
        entry = get_threshold(vault_path, "KEY")
        assert entry["operator"] == "gt"
        assert entry["value"] == 10.0

    def test_empty_note_allowed(self, vault_path):
        entry = set_threshold(vault_path, "K", "eq", 0.0)
        assert entry["note"] == ""


class TestGetThreshold:
    def test_returns_none_when_missing(self, vault_path):
        assert get_threshold(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_threshold(vault_path, "A", "ne", 42.0)
        entry = get_threshold(vault_path, "A")
        assert entry is not None
        assert entry["value"] == 42.0


class TestRemoveThreshold:
    def test_returns_true_when_removed(self, vault_path):
        set_threshold(vault_path, "B", "gte", 5.0)
        assert remove_threshold(vault_path, "B") is True

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_threshold(vault_path, "GHOST") is False

    def test_entry_gone_after_remove(self, vault_path):
        set_threshold(vault_path, "C", "lt", 1.0)
        remove_threshold(vault_path, "C")
        assert get_threshold(vault_path, "C") is None


class TestListThresholds:
    def test_empty_when_no_file(self, vault_path):
        assert list_thresholds(vault_path) == []

    def test_includes_key_field(self, vault_path):
        set_threshold(vault_path, "D", "lt", 3.0)
        entries = list_thresholds(vault_path)
        assert any(e["key"] == "D" for e in entries)

    def test_multiple_entries(self, vault_path):
        set_threshold(vault_path, "E", "lt", 1.0)
        set_threshold(vault_path, "F", "gt", 2.0)
        assert len(list_thresholds(vault_path)) == 2


class TestCheckThreshold:
    def test_lt_pass(self, vault_path):
        set_threshold(vault_path, "T", "lt", 100.0)
        assert check_threshold(vault_path, "T", 50.0) is True

    def test_lt_fail(self, vault_path):
        set_threshold(vault_path, "T", "lt", 100.0)
        assert check_threshold(vault_path, "T", 150.0) is False

    def test_gte_pass(self, vault_path):
        set_threshold(vault_path, "T2", "gte", 10.0)
        assert check_threshold(vault_path, "T2", 10.0) is True

    def test_eq_pass(self, vault_path):
        set_threshold(vault_path, "T3", "eq", 7.0)
        assert check_threshold(vault_path, "T3", 7.0) is True

    def test_raises_when_no_threshold(self, vault_path):
        with pytest.raises(ThresholdError, match="No threshold defined"):
            check_threshold(vault_path, "UNDEFINED", 1.0)
