"""Tests for envault.compliance."""
import json
import pytest
from pathlib import Path

from envault.compliance import (
    ComplianceError,
    tag_compliant,
    remove_compliance,
    get_compliance,
    list_compliance,
    _compliance_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestTagCompliant:
    def test_creates_compliance_file(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        assert _compliance_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1", note="encrypted at rest")
        assert entry["standard"] == "SOC2"
        assert entry["control_id"] == "CC6.1"
        assert entry["note"] == "encrypted at rest"

    def test_accumulates_entries(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        tag_compliant(vault_path, "DB_PASS", "PCI-DSS", "3.4")
        entries = get_compliance(vault_path, "DB_PASS")
        assert len(entries) == 2

    def test_multiple_keys(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        tag_compliant(vault_path, "API_KEY", "ISO27001", "A.9.4")
        data = list_compliance(vault_path)
        assert "DB_PASS" in data
        assert "API_KEY" in data

    def test_raises_on_empty_standard(self, vault_path):
        with pytest.raises(ComplianceError, match="standard"):
            tag_compliant(vault_path, "DB_PASS", "", "CC6.1")

    def test_raises_on_empty_control_id(self, vault_path):
        with pytest.raises(ComplianceError, match="control_id"):
            tag_compliant(vault_path, "DB_PASS", "SOC2", "")

    def test_empty_note_allowed(self, vault_path):
        entry = tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        assert entry["note"] == ""

    def test_persists_to_file(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        raw = json.loads(_compliance_path(vault_path).read_text())
        assert "DB_PASS" in raw
        assert raw["DB_PASS"][0]["standard"] == "SOC2"


class TestRemoveCompliance:
    def test_removes_matching_standard(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        tag_compliant(vault_path, "DB_PASS", "PCI-DSS", "3.4")
        remaining = remove_compliance(vault_path, "DB_PASS", "SOC2")
        assert all(e["standard"] != "SOC2" for e in remaining)

    def test_raises_when_key_missing(self, vault_path):
        with pytest.raises(ComplianceError, match="no compliance entries"):
            remove_compliance(vault_path, "MISSING", "SOC2")


class TestGetCompliance:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        assert get_compliance(vault_path, "UNKNOWN") == []

    def test_returns_entries_for_known_key(self, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        entries = get_compliance(vault_path, "DB_PASS")
        assert len(entries) == 1
        assert entries[0]["control_id"] == "CC6.1"
