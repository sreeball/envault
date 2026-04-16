import pytest
from pathlib import Path
from envault.confidence import (
    set_confidence,
    get_confidence,
    remove_confidence,
    list_confidence,
    ConfidenceError,
    _confidence_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetConfidence:
    def test_creates_confidence_file(self, vault_path):
        set_confidence(vault_path, "MY_KEY", "high")
        assert _confidence_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_confidence(vault_path, "MY_KEY", "medium", note="seems ok")
        assert entry["level"] == "medium"
        assert entry["note"] == "seems ok"

    def test_stores_level_in_file(self, vault_path):
        set_confidence(vault_path, "API_KEY", "low")
        data = list_confidence(vault_path)
        assert data["API_KEY"]["level"] == "low"

    def test_empty_note_allowed(self, vault_path):
        entry = set_confidence(vault_path, "X", "high")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(ConfidenceError, match="Invalid level"):
            set_confidence(vault_path, "X", "extreme")

    def test_overwrites_existing_entry(self, vault_path):
        set_confidence(vault_path, "KEY", "low")
        set_confidence(vault_path, "KEY", "high", note="updated")
        entry = get_confidence(vault_path, "KEY")
        assert entry["level"] == "high"
        assert entry["note"] == "updated"


class TestGetConfidence:
    def test_returns_none_when_missing(self, vault_path):
        assert get_confidence(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_confidence(vault_path, "DB_PASS", "medium")
        result = get_confidence(vault_path, "DB_PASS")
        assert result is not None
        assert result["level"] == "medium"


class TestRemoveConfidence:
    def test_removes_existing_key(self, vault_path):
        set_confidence(vault_path, "TO_REMOVE", "low")
        removed = remove_confidence(vault_path, "TO_REMOVE")
        assert removed is True
        assert get_confidence(vault_path, "TO_REMOVE") is None

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_confidence(vault_path, "GHOST") is False


class TestListConfidence:
    def test_empty_when_no_file(self, vault_path):
        assert list_confidence(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_confidence(vault_path, "A", "high")
        set_confidence(vault_path, "B", "low")
        data = list_confidence(vault_path)
        assert len(data) == 2
        assert "A" in data
        assert "B" in data
