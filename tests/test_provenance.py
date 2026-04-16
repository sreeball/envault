"""Tests for envault.provenance."""
import pytest
from pathlib import Path
from envault.provenance import (
    set_provenance,
    get_provenance,
    remove_provenance,
    list_provenance,
    ProvenanceError,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.db")


class TestSetProvenance:
    def test_creates_provenance_file(self, vault_path):
        set_provenance(vault_path, "API_KEY", "aws-secrets-manager")
        p = Path(vault_path).parent / ".envault_provenance.json"
        assert p.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_provenance(vault_path, "API_KEY", "aws-secrets-manager")
        assert entry["source"] == "aws-secrets-manager"

    def test_stores_author(self, vault_path):
        entry = set_provenance(vault_path, "DB_PASS", "vault", author="alice")
        assert entry["author"] == "alice"

    def test_stores_url(self, vault_path):
        entry = set_provenance(vault_path, "TOKEN", "github", url="https://github.com")
        assert entry["url"] == "https://github.com"

    def test_stores_note(self, vault_path):
        entry = set_provenance(vault_path, "SECRET", "manual", note="rotated Q1")
        assert entry["note"] == "rotated Q1"

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(ProvenanceError):
            set_provenance(vault_path, "", "manual")

    def test_raises_on_empty_source(self, vault_path):
        with pytest.raises(ProvenanceError):
            set_provenance(vault_path, "API_KEY", "")

    def test_overwrites_existing_entry(self, vault_path):
        set_provenance(vault_path, "API_KEY", "old-source")
        entry = set_provenance(vault_path, "API_KEY", "new-source")
        assert entry["source"] == "new-source"


class TestGetProvenance:
    def test_returns_stored_entry(self, vault_path):
        set_provenance(vault_path, "API_KEY", "ssm", author="bob")
        entry = get_provenance(vault_path, "API_KEY")
        assert entry["source"] == "ssm"
        assert entry["author"] == "bob"

    def test_raises_when_key_missing(self, vault_path):
        with pytest.raises(ProvenanceError, match="no provenance"):
            get_provenance(vault_path, "MISSING")


class TestRemoveProvenance:
    def test_removes_entry(self, vault_path):
        set_provenance(vault_path, "API_KEY", "ssm")
        remove_provenance(vault_path, "API_KEY")
        with pytest.raises(ProvenanceError):
            get_provenance(vault_path, "API_KEY")

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(ProvenanceError):
            remove_provenance(vault_path, "GHOST")


class TestListProvenance:
    def test_empty_when_no_file(self, vault_path):
        assert list_provenance(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_provenance(vault_path, "A", "src1")
        set_provenance(vault_path, "B", "src2")
        result = list_provenance(vault_path)
        assert set(result.keys()) == {"A", "B"}
