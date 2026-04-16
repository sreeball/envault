"""Tests for envault.spotlight."""

import pytest
from pathlib import Path
from envault import spotlight as sp


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestHighlight:
    def test_creates_spotlight_file(self, vault_path):
        sp.highlight(vault_path, "DB_PASSWORD")
        assert sp._spotlight_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = sp.highlight(vault_path, "API_KEY", reason="critical")
        assert entry["key"] == "API_KEY"
        assert entry["reason"] == "critical"
        assert entry["featured"] is True

    def test_empty_reason_allowed(self, vault_path):
        entry = sp.highlight(vault_path, "TOKEN")
        assert entry["reason"] == ""

    def test_accumulates_highlights(self, vault_path):
        sp.highlight(vault_path, "KEY_A")
        sp.highlight(vault_path, "KEY_B")
        data = sp.get_highlighted(vault_path)
        assert "KEY_A" in data
        assert "KEY_B" in data

    def test_overwrites_existing_entry(self, vault_path):
        sp.highlight(vault_path, "X", reason="old")
        sp.highlight(vault_path, "X", reason="new")
        data = sp.get_highlighted(vault_path)
        assert data["X"]["reason"] == "new"


class TestRemoveHighlight:
    def test_removes_key(self, vault_path):
        sp.highlight(vault_path, "MY_KEY")
        sp.remove_highlight(vault_path, "MY_KEY")
        assert not sp.is_highlighted(vault_path, "MY_KEY")

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(sp.SpotlightError):
            sp.remove_highlight(vault_path, "GHOST")


class TestIsHighlighted:
    def test_true_when_present(self, vault_path):
        sp.highlight(vault_path, "PRESENT")
        assert sp.is_highlighted(vault_path, "PRESENT") is True

    def test_false_when_absent(self, vault_path):
        assert sp.is_highlighted(vault_path, "ABSENT") is False

    def test_false_when_no_file(self, vault_path):
        assert sp.is_highlighted(vault_path, "ANY") is False


class TestGetHighlighted:
    def test_empty_when_no_file(self, vault_path):
        assert sp.get_highlighted(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        sp.highlight(vault_path, "A", reason="r1")
        sp.highlight(vault_path, "B", reason="r2")
        data = sp.get_highlighted(vault_path)
        assert len(data) == 2
