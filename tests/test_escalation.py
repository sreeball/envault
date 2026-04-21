"""Tests for envault.escalation."""
from __future__ import annotations

import json

import pytest

from envault.escalation import (
    EscalationError,
    get_escalation,
    list_escalations,
    remove_escalation,
    set_escalation,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetEscalation:
    def test_creates_escalation_file(self, vault_path, tmp_path):
        set_escalation(vault_path, "DB_PASS", "warning", "ops@example.com")
        assert (tmp_path / ".envault_escalation.json").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_escalation(vault_path, "DB_PASS", "critical", "alice")
        assert entry["level"] == "critical"
        assert entry["contact"] == "alice"
        assert entry["threshold"] == 1

    def test_stores_entry_in_file(self, vault_path, tmp_path):
        set_escalation(vault_path, "API_KEY", "emergency", "pagerduty", threshold=3)
        data = json.loads((tmp_path / ".envault_escalation.json").read_text())
        assert data["API_KEY"]["threshold"] == 3

    def test_custom_threshold(self, vault_path):
        entry = set_escalation(vault_path, "TOKEN", "info", "team", threshold=5)
        assert entry["threshold"] == 5

    def test_note_stored(self, vault_path):
        entry = set_escalation(vault_path, "X", "warning", "bob", note="review soon")
        assert entry["note"] == "review soon"

    def test_empty_note_allowed(self, vault_path):
        entry = set_escalation(vault_path, "X", "warning", "bob")
        assert entry["note"] == ""

    def test_overwrites_existing_rule(self, vault_path):
        set_escalation(vault_path, "K", "info", "alice")
        entry = set_escalation(vault_path, "K", "critical", "bob")
        assert entry["level"] == "critical"
        assert entry["contact"] == "bob"

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(EscalationError, match="Invalid level"):
            set_escalation(vault_path, "K", "extreme", "ops")

    def test_raises_on_zero_threshold(self, vault_path):
        with pytest.raises(EscalationError, match="threshold"):
            set_escalation(vault_path, "K", "warning", "ops", threshold=0)

    def test_raises_on_empty_contact(self, vault_path):
        with pytest.raises(EscalationError, match="contact"):
            set_escalation(vault_path, "K", "warning", "   ")


class TestGetEscalation:
    def test_returns_none_when_missing(self, vault_path):
        assert get_escalation(vault_path, "MISSING") is None

    def test_returns_entry_after_set(self, vault_path):
        set_escalation(vault_path, "DB", "critical", "dba")
        entry = get_escalation(vault_path, "DB")
        assert entry is not None
        assert entry["contact"] == "dba"


class TestRemoveEscalation:
    def test_removes_entry(self, vault_path):
        set_escalation(vault_path, "K", "warning", "ops")
        remove_escalation(vault_path, "K")
        assert get_escalation(vault_path, "K") is None

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(EscalationError, match="No escalation rule"):
            remove_escalation(vault_path, "GHOST")


class TestListEscalations:
    def test_empty_when_no_file(self, vault_path):
        assert list_escalations(vault_path) == {}

    def test_returns_all_rules(self, vault_path):
        set_escalation(vault_path, "A", "info", "alice")
        set_escalation(vault_path, "B", "critical", "bob")
        rules = list_escalations(vault_path)
        assert set(rules.keys()) == {"A", "B"}
