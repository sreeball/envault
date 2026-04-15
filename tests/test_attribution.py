"""Tests for envault.attribution."""

import json
import pytest

from envault.attribution import (
    AttributionError,
    _attribution_path,
    set_attribution,
    get_attribution,
    remove_attribution,
    list_attributions,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestSetAttribution:
    def test_creates_attribution_file(self, vault_path):
        set_attribution(vault_path, "DB_PASS", "alice")
        assert _attribution_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_attribution(vault_path, "DB_PASS", "alice")
        assert entry["actor"] == "alice"

    def test_stores_team(self, vault_path):
        set_attribution(vault_path, "DB_PASS", "alice", team="backend")
        data = json.loads(_attribution_path(vault_path).read_text())
        assert data["DB_PASS"]["team"] == "backend"

    def test_stores_note(self, vault_path):
        set_attribution(vault_path, "DB_PASS", "alice", note="initial setup")
        data = json.loads(_attribution_path(vault_path).read_text())
        assert data["DB_PASS"]["note"] == "initial setup"

    def test_empty_team_allowed(self, vault_path):
        entry = set_attribution(vault_path, "API_KEY", "bob")
        assert entry["team"] == ""

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(AttributionError):
            set_attribution(vault_path, "", "alice")

    def test_raises_on_empty_actor(self, vault_path):
        with pytest.raises(AttributionError):
            set_attribution(vault_path, "DB_PASS", "")

    def test_overwrites_existing_entry(self, vault_path):
        set_attribution(vault_path, "DB_PASS", "alice")
        set_attribution(vault_path, "DB_PASS", "bob", team="ops")
        entry = get_attribution(vault_path, "DB_PASS")
        assert entry["actor"] == "bob"
        assert entry["team"] == "ops"


class TestGetAttribution:
    def test_returns_none_when_missing(self, vault_path):
        assert get_attribution(vault_path, "MISSING") is None

    def test_returns_entry_after_set(self, vault_path):
        set_attribution(vault_path, "SECRET", "carol", team="infra")
        entry = get_attribution(vault_path, "SECRET")
        assert entry["actor"] == "carol"
        assert entry["team"] == "infra"


class TestRemoveAttribution:
    def test_returns_true_when_removed(self, vault_path):
        set_attribution(vault_path, "KEY", "alice")
        assert remove_attribution(vault_path, "KEY") is True

    def test_returns_false_when_absent(self, vault_path):
        assert remove_attribution(vault_path, "NONEXISTENT") is False

    def test_entry_gone_after_removal(self, vault_path):
        set_attribution(vault_path, "KEY", "alice")
        remove_attribution(vault_path, "KEY")
        assert get_attribution(vault_path, "KEY") is None


class TestListAttributions:
    def test_empty_when_no_file(self, vault_path):
        assert list_attributions(vault_path) == []

    def test_includes_key_field(self, vault_path):
        set_attribution(vault_path, "DB_PASS", "alice")
        entries = list_attributions(vault_path)
        assert any(e["key"] == "DB_PASS" for e in entries)

    def test_returns_all_entries(self, vault_path):
        set_attribution(vault_path, "A", "alice")
        set_attribution(vault_path, "B", "bob")
        assert len(list_attributions(vault_path)) == 2
