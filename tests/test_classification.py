"""Tests for envault.classification."""

import pytest
from pathlib import Path
from envault.classification import (
    ClassificationError,
    classify,
    get_classification,
    remove_classification,
    list_by_level,
    all_classifications,
    CLASSIFICATION_LEVELS,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestClassify:
    def test_creates_classification_file(self, vault_path):
        classify(vault_path, "API_KEY", "confidential")
        cf = Path(vault_path).parent / ".envault_classification.json"
        assert cf.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = classify(vault_path, "API_KEY", "confidential")
        assert entry["level"] == "confidential"

    def test_stores_reason(self, vault_path):
        entry = classify(vault_path, "API_KEY", "restricted", reason="PCI data")
        assert entry["reason"] == "PCI data"

    def test_empty_reason_allowed(self, vault_path):
        entry = classify(vault_path, "API_KEY", "public")
        assert entry["reason"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(ClassificationError, match="Invalid level"):
            classify(vault_path, "API_KEY", "ultra-secret")

    def test_overwrites_existing(self, vault_path):
        classify(vault_path, "API_KEY", "public")
        entry = classify(vault_path, "API_KEY", "restricted")
        assert entry["level"] == "restricted"

    def test_all_levels_accepted(self, vault_path):
        for level in CLASSIFICATION_LEVELS:
            entry = classify(vault_path, f"KEY_{level}", level)
            assert entry["level"] == level


class TestGetClassification:
    def test_returns_entry(self, vault_path):
        classify(vault_path, "DB_PASS", "top-secret")
        entry = get_classification(vault_path, "DB_PASS")
        assert entry is not None
        assert entry["level"] == "top-secret"

    def test_returns_none_for_missing_key(self, vault_path):
        assert get_classification(vault_path, "MISSING") is None


class TestRemoveClassification:
    def test_removes_key(self, vault_path):
        classify(vault_path, "TOKEN", "internal")
        removed = remove_classification(vault_path, "TOKEN")
        assert removed is True
        assert get_classification(vault_path, "TOKEN") is None

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_classification(vault_path, "GHOST") is False


class TestListByLevel:
    def test_returns_matching_keys(self, vault_path):
        classify(vault_path, "A", "confidential")
        classify(vault_path, "B", "confidential")
        classify(vault_path, "C", "public")
        keys = list_by_level(vault_path, "confidential")
        assert set(keys) == {"A", "B"}

    def test_empty_when_no_match(self, vault_path):
        classify(vault_path, "A", "public")
        assert list_by_level(vault_path, "restricted") == []

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(ClassificationError):
            list_by_level(vault_path, "bogus")


class TestAllClassifications:
    def test_returns_full_map(self, vault_path):
        classify(vault_path, "X", "internal")
        classify(vault_path, "Y", "public")
        data = all_classifications(vault_path)
        assert "X" in data and "Y" in data

    def test_empty_when_no_file(self, vault_path):
        assert all_classifications(vault_path) == {}
