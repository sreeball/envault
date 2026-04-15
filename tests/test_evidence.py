"""Tests for envault.evidence."""

import pytest
from pathlib import Path
from envault.vault import Vault
from envault.evidence import (
    attach,
    detach,
    list_evidence,
    clear_evidence,
    EvidenceError,
    _evidence_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    v = Vault(str(p), password="pw")
    v.set("API_KEY", "secret")
    return str(p)


class TestAttach:
    def test_creates_evidence_file(self, vault_path):
        attach(vault_path, "API_KEY", "Proof of rotation")
        assert _evidence_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = attach(vault_path, "API_KEY", "Proof of rotation")
        assert entry["description"] == "Proof of rotation"
        assert "id" in entry
        assert "attached_at" in entry

    def test_default_type_is_note(self, vault_path):
        entry = attach(vault_path, "API_KEY", "Some note")
        assert entry["type"] == "note"

    def test_custom_type_stored(self, vault_path):
        entry = attach(vault_path, "API_KEY", "Link", evidence_type="link")
        assert entry["type"] == "link"

    def test_source_stored(self, vault_path):
        entry = attach(vault_path, "API_KEY", "Ref", source="https://example.com")
        assert entry["source"] == "https://example.com"

    def test_accumulates_entries(self, vault_path):
        attach(vault_path, "API_KEY", "First")
        attach(vault_path, "API_KEY", "Second")
        entries = list_evidence(vault_path, "API_KEY")
        assert len(entries) == 2

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(EvidenceError, match="key"):
            attach(vault_path, "", "desc")

    def test_raises_on_empty_description(self, vault_path):
        with pytest.raises(EvidenceError, match="description"):
            attach(vault_path, "API_KEY", "")


class TestDetach:
    def test_removes_entry(self, vault_path):
        entry = attach(vault_path, "API_KEY", "To remove")
        removed = detach(vault_path, "API_KEY", entry["id"])
        assert removed is True
        assert list_evidence(vault_path, "API_KEY") == []

    def test_returns_false_when_not_found(self, vault_path):
        attach(vault_path, "API_KEY", "Keep")
        assert detach(vault_path, "API_KEY", "nonexistent-id") is False

    def test_only_removes_target(self, vault_path):
        e1 = attach(vault_path, "API_KEY", "Keep")
        e2 = attach(vault_path, "API_KEY", "Remove")
        detach(vault_path, "API_KEY", e2["id"])
        remaining = list_evidence(vault_path, "API_KEY")
        assert len(remaining) == 1
        assert remaining[0]["id"] == e1["id"]


class TestListEvidence:
    def test_empty_for_unknown_key(self, vault_path):
        assert list_evidence(vault_path, "MISSING") == []

    def test_returns_all_entries(self, vault_path):
        attach(vault_path, "API_KEY", "A")
        attach(vault_path, "API_KEY", "B")
        entries = list_evidence(vault_path, "API_KEY")
        assert len(entries) == 2


class TestClearEvidence:
    def test_removes_all_entries(self, vault_path):
        attach(vault_path, "API_KEY", "A")
        attach(vault_path, "API_KEY", "B")
        count = clear_evidence(vault_path, "API_KEY")
        assert count == 2
        assert list_evidence(vault_path, "API_KEY") == []

    def test_returns_zero_when_none(self, vault_path):
        assert clear_evidence(vault_path, "API_KEY") == 0
