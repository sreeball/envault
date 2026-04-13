"""Tests for envault.correlation."""
from __future__ import annotations

import json
import pytest

from envault.correlation import (
    CorrelationError,
    all_correlations,
    get_related,
    link,
    unlink,
    _correlations_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestLink:
    def test_creates_correlations_file(self, vault_path):
        link(vault_path, "DB_HOST", "DB_PORT")
        assert _correlations_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = link(vault_path, "DB_HOST", "DB_PORT")
        assert result["key"] == "DB_HOST"
        assert result["related_key"] == "DB_PORT"
        assert "DB_PORT" in result["all_related"]

    def test_bidirectional_storage(self, vault_path):
        link(vault_path, "A", "B")
        data = json.loads(_correlations_path(vault_path).read_text())
        assert "B" in data["A"]
        assert "A" in data["B"]

    def test_accumulates_related_keys(self, vault_path):
        link(vault_path, "A", "B")
        link(vault_path, "A", "C")
        related = get_related(vault_path, "A")
        assert "B" in related
        assert "C" in related

    def test_no_duplicate_entries(self, vault_path):
        link(vault_path, "A", "B")
        link(vault_path, "A", "B")
        related = get_related(vault_path, "A")
        assert related.count("B") == 1

    def test_raises_on_self_correlation(self, vault_path):
        with pytest.raises(CorrelationError):
            link(vault_path, "A", "A")


class TestUnlink:
    def test_removes_correlation(self, vault_path):
        link(vault_path, "A", "B")
        remaining = unlink(vault_path, "A", "B")
        assert "B" not in remaining

    def test_removes_bidirectional(self, vault_path):
        link(vault_path, "A", "B")
        unlink(vault_path, "A", "B")
        assert "A" not in get_related(vault_path, "B")

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(CorrelationError):
            unlink(vault_path, "X", "Y")


class TestGetRelated:
    def test_returns_empty_for_unknown_key(self, vault_path):
        assert get_related(vault_path, "MISSING") == []

    def test_returns_related_keys(self, vault_path):
        link(vault_path, "DB_HOST", "DB_PORT")
        assert "DB_PORT" in get_related(vault_path, "DB_HOST")


class TestAllCorrelations:
    def test_returns_empty_when_no_file(self, vault_path):
        assert all_correlations(vault_path) == {}

    def test_returns_full_map(self, vault_path):
        link(vault_path, "A", "B")
        link(vault_path, "C", "D")
        data = all_correlations(vault_path)
        assert "A" in data
        assert "C" in data
