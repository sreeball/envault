"""Tests for envault.resolution."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.resolution import (
    ResolutionError,
    get_resolution_order,
    list_resolution,
    remove_resolution,
    resolve_value,
    set_resolution_order,
    _resolution_path,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.touch()
    return str(p)


class TestSetResolutionOrder:
    def test_creates_resolution_file(self, vault_path):
        set_resolution_order(vault_path, "DB_URL", ["/a/vault.db", "/b/vault.db"])
        assert _resolution_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = set_resolution_order(vault_path, "API_KEY", ["/x/vault.db"])
        assert result["key"] == "API_KEY"
        assert result["sources"] == ["/x/vault.db"]

    def test_stores_entry_in_file(self, vault_path):
        set_resolution_order(vault_path, "SECRET", ["/p/v.db", "/q/v.db"])
        data = json.loads(_resolution_path(vault_path).read_text())
        assert "SECRET" in data
        assert data["SECRET"]["sources"] == ["/p/v.db", "/q/v.db"]

    def test_raises_on_empty_sources(self, vault_path):
        with pytest.raises(ResolutionError):
            set_resolution_order(vault_path, "KEY", [])

    def test_overwrites_existing_entry(self, vault_path):
        set_resolution_order(vault_path, "KEY", ["/a/v.db"])
        set_resolution_order(vault_path, "KEY", ["/b/v.db"])
        data = json.loads(_resolution_path(vault_path).read_text())
        assert data["KEY"]["sources"] == ["/b/v.db"]


class TestGetResolutionOrder:
    def test_returns_sources_list(self, vault_path):
        set_resolution_order(vault_path, "X", ["/a.db", "/b.db"])
        result = get_resolution_order(vault_path, "X")
        assert result == ["/a.db", "/b.db"]

    def test_returns_empty_list_for_unknown_key(self, vault_path):
        result = get_resolution_order(vault_path, "MISSING")
        assert result == []

    def test_returns_empty_when_no_file(self, vault_path):
        result = get_resolution_order(vault_path, "ANY")
        assert result == []


class TestRemoveResolution:
    def test_removes_entry(self, vault_path):
        set_resolution_order(vault_path, "K", ["/a.db"])
        removed = remove_resolution(vault_path, "K")
        assert removed is True
        assert get_resolution_order(vault_path, "K") == []

    def test_returns_false_for_missing_key(self, vault_path):
        assert remove_resolution(vault_path, "NOPE") is False


class TestListResolution:
    def test_returns_all_entries(self, vault_path):
        set_resolution_order(vault_path, "A", ["/a.db"])
        set_resolution_order(vault_path, "B", ["/b.db"])
        data = list_resolution(vault_path)
        assert "A" in data
        assert "B" in data

    def test_empty_when_no_file(self, vault_path):
        assert list_resolution(vault_path) == {}


class TestResolveValue:
    def test_resolves_from_first_source(self, vault_path):
        set_resolution_order(vault_path, "DB_URL", ["/first.db", "/second.db"])
        mock_vault = MagicMock()
        mock_vault.get.return_value = "postgres://localhost/db"
        with patch("envault.resolution.Vault", return_value=mock_vault):
            value = resolve_value(vault_path, "DB_URL", "password")
        assert value == "postgres://localhost/db"

    def test_falls_back_to_second_source(self, vault_path):
        set_resolution_order(vault_path, "KEY", ["/first.db", "/second.db"])
        mock_none = MagicMock()
        mock_none.get.return_value = None
        mock_found = MagicMock()
        mock_found.get.return_value = "found_value"
        with patch("envault.resolution.Vault", side_effect=[mock_none, mock_found]):
            value = resolve_value(vault_path, "KEY", "password")
        assert value == "found_value"

    def test_raises_when_not_found_anywhere(self, vault_path):
        set_resolution_order(vault_path, "MISSING", ["/a.db"])
        mock_vault = MagicMock()
        mock_vault.get.return_value = None
        with patch("envault.resolution.Vault", return_value=mock_vault):
            with pytest.raises(ResolutionError, match="could not be resolved"):
                resolve_value(vault_path, "MISSING", "password")
