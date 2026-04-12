"""Tests for envault.label module."""

import pytest
from pathlib import Path
from envault.label import (
    LabelError,
    add_label,
    remove_label,
    get_labels,
    keys_with_label,
    all_labels,
    _labels_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


class TestAddLabel:
    def test_creates_labels_file(self, vault_path):
        add_label(vault_path, "DB_URL", "database")
        assert _labels_path(vault_path).exists()

    def test_returns_label_list(self, vault_path):
        result = add_label(vault_path, "DB_URL", "database")
        assert isinstance(result, list)
        assert "database" in result

    def test_accumulates_labels(self, vault_path):
        add_label(vault_path, "DB_URL", "database")
        result = add_label(vault_path, "DB_URL", "production")
        assert "database" in result
        assert "production" in result

    def test_no_duplicate_labels(self, vault_path):
        add_label(vault_path, "DB_URL", "database")
        result = add_label(vault_path, "DB_URL", "database")
        assert result.count("database") == 1

    def test_raises_on_empty_label(self, vault_path):
        with pytest.raises(LabelError):
            add_label(vault_path, "DB_URL", "  ")


class TestRemoveLabel:
    def test_removes_existing_label(self, vault_path):
        add_label(vault_path, "DB_URL", "database")
        result = remove_label(vault_path, "DB_URL", "database")
        assert "database" not in result

    def test_raises_on_missing_label(self, vault_path):
        with pytest.raises(LabelError, match="not found"):
            remove_label(vault_path, "DB_URL", "nonexistent")


class TestGetLabels:
    def test_returns_empty_for_unknown_key(self, vault_path):
        assert get_labels(vault_path, "MISSING_KEY") == []

    def test_returns_labels_for_key(self, vault_path):
        add_label(vault_path, "API_KEY", "external")
        add_label(vault_path, "API_KEY", "sensitive")
        labels = get_labels(vault_path, "API_KEY")
        assert "external" in labels
        assert "sensitive" in labels


class TestKeysWithLabel:
    def test_finds_keys_by_label(self, vault_path):
        add_label(vault_path, "DB_URL", "production")
        add_label(vault_path, "API_KEY", "production")
        add_label(vault_path, "SECRET", "staging")
        keys = keys_with_label(vault_path, "production")
        assert "DB_URL" in keys
        assert "API_KEY" in keys
        assert "SECRET" not in keys

    def test_returns_empty_when_no_match(self, vault_path):
        assert keys_with_label(vault_path, "nolabel") == []


class TestAllLabels:
    def test_returns_full_map(self, vault_path):
        add_label(vault_path, "DB_URL", "database")
        add_label(vault_path, "API_KEY", "external")
        result = all_labels(vault_path)
        assert "DB_URL" in result
        assert "API_KEY" in result

    def test_empty_when_no_labels_file(self, vault_path):
        assert all_labels(vault_path) == {}
