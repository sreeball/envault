"""Tests for envault.risk module."""
import pytest
from pathlib import Path
from envault.risk import set_risk, get_risk, remove_risk, list_risk, RiskError


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.env")


class TestSetRisk:
    def test_creates_risk_file(self, vault_path):
        set_risk(vault_path, "DB_PASSWORD", "high")
        risk_file = Path(vault_path).parent / ".envault_risk.json"
        assert risk_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_risk(vault_path, "API_KEY", "critical", reason="exposed externally")
        assert entry["level"] == "critical"
        assert entry["reason"] == "exposed externally"

    def test_stores_level_in_file(self, vault_path):
        set_risk(vault_path, "TOKEN", "medium")
        data = list_risk(vault_path)
        assert data["TOKEN"]["level"] == "medium"

    def test_empty_reason_allowed(self, vault_path):
        entry = set_risk(vault_path, "KEY", "low")
        assert entry["reason"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(RiskError, match="Invalid risk level"):
            set_risk(vault_path, "KEY", "extreme")

    def test_overwrites_existing_entry(self, vault_path):
        set_risk(vault_path, "KEY", "low")
        set_risk(vault_path, "KEY", "high", reason="updated")
        entry = get_risk(vault_path, "KEY")
        assert entry["level"] == "high"
        assert entry["reason"] == "updated"


class TestGetRisk:
    def test_returns_none_when_missing(self, vault_path):
        assert get_risk(vault_path, "MISSING") is None

    def test_returns_entry_for_existing_key(self, vault_path):
        set_risk(vault_path, "DB_PASS", "high", reason="db creds")
        entry = get_risk(vault_path, "DB_PASS")
        assert entry is not None
        assert entry["level"] == "high"


class TestRemoveRisk:
    def test_returns_true_when_removed(self, vault_path):
        set_risk(vault_path, "KEY", "low")
        assert remove_risk(vault_path, "KEY") is True

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_risk(vault_path, "NONEXISTENT") is False

    def test_entry_gone_after_removal(self, vault_path):
        set_risk(vault_path, "KEY", "medium")
        remove_risk(vault_path, "KEY")
        assert get_risk(vault_path, "KEY") is None


class TestListRisk:
    def test_empty_when_no_file(self, vault_path):
        assert list_risk(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_risk(vault_path, "A", "low")
        set_risk(vault_path, "B", "critical")
        data = list_risk(vault_path)
        assert len(data) == 2
        assert data["A"]["level"] == "low"
        assert data["B"]["level"] == "critical"
