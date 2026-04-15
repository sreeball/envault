"""Tests for envault.lifecycle."""

import pytest
from pathlib import Path
from envault.lifecycle import (
    set_state, get_state, remove_state, list_states, LifecycleError,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


class TestSetState:
    def test_creates_lifecycle_file(self, vault_path):
        set_state(vault_path, "DB_PASS", "active")
        lc_file = Path(vault_path).parent / ".envault_lifecycle.json"
        assert lc_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_state(vault_path, "DB_PASS", "active")
        assert entry["state"] == "active"

    def test_stores_note(self, vault_path):
        entry = set_state(vault_path, "API_KEY", "draft", note="initial")
        assert entry["note"] == "initial"

    def test_empty_note_allowed(self, vault_path):
        entry = set_state(vault_path, "API_KEY", "draft")
        assert entry["note"] == ""

    def test_raises_on_invalid_state(self, vault_path):
        with pytest.raises(LifecycleError, match="Invalid state"):
            set_state(vault_path, "KEY", "zombie")

    def test_raises_on_invalid_transition(self, vault_path):
        set_state(vault_path, "KEY", "active")
        with pytest.raises(LifecycleError, match="Cannot transition"):
            set_state(vault_path, "KEY", "draft")

    def test_valid_transition_draft_to_active(self, vault_path):
        set_state(vault_path, "KEY", "draft")
        entry = set_state(vault_path, "KEY", "active")
        assert entry["state"] == "active"

    def test_valid_transition_active_to_deprecated(self, vault_path):
        set_state(vault_path, "KEY", "active")
        entry = set_state(vault_path, "KEY", "deprecated")
        assert entry["state"] == "deprecated"

    def test_archived_has_no_transitions(self, vault_path):
        set_state(vault_path, "KEY", "active")
        set_state(vault_path, "KEY", "archived")
        with pytest.raises(LifecycleError):
            set_state(vault_path, "KEY", "deprecated")


class TestGetState:
    def test_defaults_to_draft(self, vault_path):
        entry = get_state(vault_path, "UNKNOWN_KEY")
        assert entry["state"] == "draft"

    def test_returns_set_state(self, vault_path):
        set_state(vault_path, "MY_KEY", "active")
        entry = get_state(vault_path, "MY_KEY")
        assert entry["state"] == "active"


class TestRemoveState:
    def test_returns_true_when_removed(self, vault_path):
        set_state(vault_path, "KEY", "draft")
        assert remove_state(vault_path, "KEY") is True

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_state(vault_path, "MISSING") is False

    def test_key_gone_after_removal(self, vault_path):
        set_state(vault_path, "KEY", "draft")
        remove_state(vault_path, "KEY")
        states = list_states(vault_path)
        assert "KEY" not in states


class TestListStates:
    def test_empty_when_no_file(self, vault_path):
        assert list_states(vault_path) == {}

    def test_returns_all_tracked_keys(self, vault_path):
        set_state(vault_path, "A", "draft")
        set_state(vault_path, "B", "active")
        states = list_states(vault_path)
        assert set(states.keys()) == {"A", "B"}
