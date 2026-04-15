"""Tests for envault.lineage."""

import json
import pytest

from envault.lineage import (
    LineageError,
    ancestors,
    get_lineage,
    list_lineage,
    remove_lineage,
    set_lineage,
    _lineage_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


# ---------------------------------------------------------------------------
# set_lineage
# ---------------------------------------------------------------------------

class TestSetLineage:
    def test_creates_lineage_file(self, vault_path):
        set_lineage(vault_path, "DB_URL", source="aws/ssm/prod")
        assert _lineage_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_lineage(vault_path, "DB_URL", source="aws/ssm/prod")
        assert entry["source"] == "aws/ssm/prod"
        assert entry["derived_from"] is None

    def test_stores_derived_from(self, vault_path):
        set_lineage(vault_path, "DB_URL_REPLICA", derived_from="DB_URL")
        data = json.loads(_lineage_path(vault_path).read_text())
        assert data["DB_URL_REPLICA"]["derived_from"] == "DB_URL"

    def test_stores_note(self, vault_path):
        entry = set_lineage(vault_path, "API_KEY", source="vault/kv", note="rotated")
        assert entry["note"] == "rotated"

    def test_raises_when_no_origin_given(self, vault_path):
        with pytest.raises(LineageError):
            set_lineage(vault_path, "ORPHAN")

    def test_overwrites_existing_entry(self, vault_path):
        set_lineage(vault_path, "DB_URL", source="old/source")
        set_lineage(vault_path, "DB_URL", source="new/source")
        entry = get_lineage(vault_path, "DB_URL")
        assert entry["source"] == "new/source"


# ---------------------------------------------------------------------------
# get_lineage
# ---------------------------------------------------------------------------

class TestGetLineage:
    def test_returns_correct_entry(self, vault_path):
        set_lineage(vault_path, "TOKEN", source="github")
        entry = get_lineage(vault_path, "TOKEN")
        assert entry["source"] == "github"

    def test_raises_for_unknown_key(self, vault_path):
        with pytest.raises(LineageError, match="MISSING"):
            get_lineage(vault_path, "MISSING")


# ---------------------------------------------------------------------------
# remove_lineage
# ---------------------------------------------------------------------------

class TestRemoveLineage:
    def test_removes_entry(self, vault_path):
        set_lineage(vault_path, "DB_URL", source="ssm")
        remove_lineage(vault_path, "DB_URL")
        assert "DB_URL" not in list_lineage(vault_path)

    def test_raises_for_unknown_key(self, vault_path):
        with pytest.raises(LineageError):
            remove_lineage(vault_path, "GHOST")


# ---------------------------------------------------------------------------
# list_lineage
# ---------------------------------------------------------------------------

class TestListLineage:
    def test_empty_when_no_file(self, vault_path):
        assert list_lineage(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_lineage(vault_path, "A", source="x")
        set_lineage(vault_path, "B", source="y")
        result = list_lineage(vault_path)
        assert set(result.keys()) == {"A", "B"}


# ---------------------------------------------------------------------------
# ancestors
# ---------------------------------------------------------------------------

class TestAncestors:
    def test_single_ancestor(self, vault_path):
        set_lineage(vault_path, "CHILD", derived_from="PARENT")
        set_lineage(vault_path, "PARENT", source="origin")
        assert ancestors(vault_path, "CHILD") == ["PARENT"]

    def test_chain_of_ancestors(self, vault_path):
        set_lineage(vault_path, "C", derived_from="B")
        set_lineage(vault_path, "B", derived_from="A")
        set_lineage(vault_path, "A", source="root")
        assert ancestors(vault_path, "C") == ["B", "A"]

    def test_no_ancestors_returns_empty(self, vault_path):
        set_lineage(vault_path, "ROOT", source="external")
        assert ancestors(vault_path, "ROOT") == []

    def test_unknown_key_returns_empty(self, vault_path):
        assert ancestors(vault_path, "UNKNOWN") == []
