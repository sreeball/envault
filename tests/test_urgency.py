import pytest
from pathlib import Path
from envault.urgency import (
    set_urgency,
    get_urgency,
    remove_urgency,
    list_urgency,
    UrgencyError,
    _urgency_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


class TestSetUrgency:
    def test_creates_urgency_file(self, vault_path):
        set_urgency(vault_path, "API_KEY", "high")
        assert _urgency_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = set_urgency(vault_path, "API_KEY", "critical")
        assert result["level"] == "critical"

    def test_stores_level_in_file(self, vault_path):
        set_urgency(vault_path, "API_KEY", "medium")
        data = list_urgency(vault_path)
        assert data["API_KEY"]["level"] == "medium"

    def test_empty_note_allowed(self, vault_path):
        result = set_urgency(vault_path, "API_KEY", "low", note="")
        assert result["note"] == ""

    def test_stores_note(self, vault_path):
        set_urgency(vault_path, "API_KEY", "high", note="Needs rotation")
        data = list_urgency(vault_path)
        assert data["API_KEY"]["note"] == "Needs rotation"

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(UrgencyError, match="Invalid urgency level"):
            set_urgency(vault_path, "API_KEY", "extreme")

    def test_overwrites_existing_entry(self, vault_path):
        set_urgency(vault_path, "API_KEY", "low")
        set_urgency(vault_path, "API_KEY", "critical")
        data = list_urgency(vault_path)
        assert data["API_KEY"]["level"] == "critical"

    def test_multiple_keys(self, vault_path):
        set_urgency(vault_path, "KEY_A", "low")
        set_urgency(vault_path, "KEY_B", "high")
        data = list_urgency(vault_path)
        assert len(data) == 2


class TestGetUrgency:
    def test_returns_entry(self, vault_path):
        set_urgency(vault_path, "DB_PASS", "critical", note="urgent")
        result = get_urgency(vault_path, "DB_PASS")
        assert result["level"] == "critical"
        assert result["note"] == "urgent"

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(UrgencyError, match="No urgency set"):
            get_urgency(vault_path, "MISSING")


class TestRemoveUrgency:
    def test_removes_entry(self, vault_path):
        set_urgency(vault_path, "API_KEY", "low")
        remove_urgency(vault_path, "API_KEY")
        assert "API_KEY" not in list_urgency(vault_path)

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(UrgencyError, match="No urgency set"):
            remove_urgency(vault_path, "GHOST")


class TestListUrgency:
    def test_empty_when_no_file(self, vault_path):
        assert list_urgency(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_urgency(vault_path, "A", "low")
        set_urgency(vault_path, "B", "high")
        data = list_urgency(vault_path)
        assert set(data.keys()) == {"A", "B"}
