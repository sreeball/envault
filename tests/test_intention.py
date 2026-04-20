"""Tests for envault.intention."""

import json
import pytest

from envault.intention import (
    IntentionError,
    set_intention,
    get_intention,
    remove_intention,
    list_intentions,
    _intentions_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


class TestSetIntention:
    def test_creates_intentions_file(self, vault_path):
        set_intention(vault_path, "DB_PASS", "Primary database password")
        assert _intentions_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_intention(vault_path, "API_KEY", "Third-party API access")
        assert entry["key"] == "API_KEY"
        assert entry["purpose"] == "Third-party API access"

    def test_stores_owner(self, vault_path):
        entry = set_intention(vault_path, "SECRET", "Auth token", owner="platform-team")
        assert entry["owner"] == "platform-team"

    def test_stores_note(self, vault_path):
        entry = set_intention(vault_path, "TOKEN", "CI token", note="Rotate quarterly")
        assert entry["note"] == "Rotate quarterly"

    def test_empty_owner_defaults_to_empty_string(self, vault_path):
        entry = set_intention(vault_path, "X", "Some purpose")
        assert entry["owner"] == ""

    def test_raises_on_empty_purpose(self, vault_path):
        with pytest.raises(IntentionError):
            set_intention(vault_path, "KEY", "   ")

    def test_overwrites_existing_entry(self, vault_path):
        set_intention(vault_path, "KEY", "Old purpose")
        entry = set_intention(vault_path, "KEY", "New purpose")
        assert entry["purpose"] == "New purpose"

    def test_persists_to_file(self, vault_path):
        set_intention(vault_path, "DB_URL", "Database connection string")
        raw = json.loads(_intentions_path(vault_path).read_text())
        assert "DB_URL" in raw
        assert raw["DB_URL"]["purpose"] == "Database connection string"


class TestGetIntention:
    def test_returns_entry_when_set(self, vault_path):
        set_intention(vault_path, "FOO", "Foo purpose")
        entry = get_intention(vault_path, "FOO")
        assert entry is not None
        assert entry["purpose"] == "Foo purpose"

    def test_returns_none_when_not_set(self, vault_path):
        assert get_intention(vault_path, "MISSING") is None


class TestRemoveIntention:
    def test_removes_existing_key(self, vault_path):
        set_intention(vault_path, "KEY", "purpose")
        result = remove_intention(vault_path, "KEY")
        assert result is True
        assert get_intention(vault_path, "KEY") is None

    def test_returns_false_when_key_absent(self, vault_path):
        assert remove_intention(vault_path, "GHOST") is False


class TestListIntentions:
    def test_returns_empty_dict_when_none(self, vault_path):
        assert list_intentions(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_intention(vault_path, "A", "purpose A")
        set_intention(vault_path, "B", "purpose B")
        entries = list_intentions(vault_path)
        assert set(entries.keys()) == {"A", "B"}
