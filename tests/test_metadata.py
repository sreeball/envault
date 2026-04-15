"""Tests for envault.metadata."""

import pytest

from envault.metadata import (
    MetadataError,
    get_meta,
    keys_with_field,
    list_meta,
    remove_meta,
    set_meta,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetMeta:
    def test_creates_metadata_file(self, vault_path, tmp_path):
        set_meta(vault_path, "DB_PASS", "owner", "alice")
        assert (tmp_path / ".envault_metadata.json").exists()

    def test_returns_entry_dict(self, vault_path):
        result = set_meta(vault_path, "DB_PASS", "owner", "alice")
        assert result == {"owner": "alice"}

    def test_accumulates_fields(self, vault_path):
        set_meta(vault_path, "DB_PASS", "owner", "alice")
        result = set_meta(vault_path, "DB_PASS", "env", "prod")
        assert result["owner"] == "alice"
        assert result["env"] == "prod"

    def test_overwrites_existing_field(self, vault_path):
        set_meta(vault_path, "DB_PASS", "owner", "alice")
        result = set_meta(vault_path, "DB_PASS", "owner", "bob")
        assert result["owner"] == "bob"

    def test_raises_on_empty_field(self, vault_path):
        with pytest.raises(MetadataError):
            set_meta(vault_path, "DB_PASS", "  ", "value")

    def test_multiple_keys_independent(self, vault_path):
        set_meta(vault_path, "KEY_A", "owner", "alice")
        set_meta(vault_path, "KEY_B", "owner", "bob")
        assert get_meta(vault_path, "KEY_A")["owner"] == "alice"
        assert get_meta(vault_path, "KEY_B")["owner"] == "bob"


class TestGetMeta:
    def test_returns_empty_dict_when_no_metadata(self, vault_path):
        assert get_meta(vault_path, "MISSING") == {}

    def test_returns_stored_fields(self, vault_path):
        set_meta(vault_path, "API_KEY", "team", "backend")
        assert get_meta(vault_path, "API_KEY") == {"team": "backend"}


class TestRemoveMeta:
    def test_removes_field(self, vault_path):
        set_meta(vault_path, "DB_PASS", "owner", "alice")
        set_meta(vault_path, "DB_PASS", "env", "prod")
        remaining = remove_meta(vault_path, "DB_PASS", "env")
        assert "env" not in remaining
        assert remaining["owner"] == "alice"

    def test_raises_when_field_missing(self, vault_path):
        with pytest.raises(MetadataError):
            remove_meta(vault_path, "DB_PASS", "nonexistent")

    def test_cleans_up_empty_key_entry(self, vault_path, tmp_path):
        import json
        set_meta(vault_path, "DB_PASS", "owner", "alice")
        remove_meta(vault_path, "DB_PASS", "owner")
        data = json.loads((tmp_path / ".envault_metadata.json").read_text())
        assert "DB_PASS" not in data


class TestListMeta:
    def test_returns_empty_dict_when_no_file(self, vault_path):
        assert list_meta(vault_path) == {}

    def test_returns_all_keys_and_fields(self, vault_path):
        set_meta(vault_path, "KEY_A", "env", "prod")
        set_meta(vault_path, "KEY_B", "owner", "bob")
        result = list_meta(vault_path)
        assert "KEY_A" in result
        assert "KEY_B" in result


class TestKeysWithField:
    def test_returns_matching_keys(self, vault_path):
        set_meta(vault_path, "KEY_A", "owner", "alice")
        set_meta(vault_path, "KEY_B", "owner", "bob")
        set_meta(vault_path, "KEY_C", "env", "prod")
        assert set(keys_with_field(vault_path, "owner")) == {"KEY_A", "KEY_B"}

    def test_returns_empty_when_no_match(self, vault_path):
        assert keys_with_field(vault_path, "missing_field") == []
