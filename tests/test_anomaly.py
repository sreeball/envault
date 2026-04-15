"""Tests for envault.anomaly module."""
import pytest
from pathlib import Path
import json

from envault.anomaly import (
    record_anomaly,
    list_anomalies,
    clear_anomalies,
    summary,
    AnomalyError,
    _anomaly_path,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestRecordAnomaly:
    def test_creates_anomaly_file(self, vault_path):
        record_anomaly(vault_path, "DB_PASS", "unusual_length")
        assert _anomaly_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = record_anomaly(vault_path, "DB_PASS", "unusual_length", detail="too short")
        assert entry["type"] == "unusual_length"
        assert entry["detail"] == "too short"
        assert entry["severity"] == "medium"

    def test_custom_severity(self, vault_path):
        entry = record_anomaly(vault_path, "API_KEY", "repeated_access", severity="high")
        assert entry["severity"] == "high"

    def test_raises_on_invalid_severity(self, vault_path):
        with pytest.raises(AnomalyError, match="Invalid severity"):
            record_anomaly(vault_path, "KEY", "some_type", severity="extreme")

    def test_accumulates_anomalies(self, vault_path):
        record_anomaly(vault_path, "DB_PASS", "type_a")
        record_anomaly(vault_path, "DB_PASS", "type_b")
        anomalies = list_anomalies(vault_path, "DB_PASS")
        assert len(anomalies) == 2

    def test_multiple_keys_independent(self, vault_path):
        record_anomaly(vault_path, "KEY_A", "type_x")
        record_anomaly(vault_path, "KEY_B", "type_y")
        assert len(list_anomalies(vault_path, "KEY_A")) == 1
        assert len(list_anomalies(vault_path, "KEY_B")) == 1


class TestListAnomalies:
    def test_empty_when_no_file(self, vault_path):
        result = list_anomalies(vault_path, "MISSING_KEY")
        assert result == []

    def test_empty_for_unknown_key(self, vault_path):
        record_anomaly(vault_path, "OTHER", "t")
        assert list_anomalies(vault_path, "UNKNOWN") == []

    def test_returns_list_of_entries(self, vault_path):
        record_anomaly(vault_path, "K", "t1", severity="low")
        entries = list_anomalies(vault_path, "K")
        assert isinstance(entries, list)
        assert entries[0]["type"] == "t1"


class TestClearAnomalies:
    def test_returns_count_removed(self, vault_path):
        record_anomaly(vault_path, "K", "t1")
        record_anomaly(vault_path, "K", "t2")
        removed = clear_anomalies(vault_path, "K")
        assert removed == 2

    def test_key_gone_after_clear(self, vault_path):
        record_anomaly(vault_path, "K", "t1")
        clear_anomalies(vault_path, "K")
        assert list_anomalies(vault_path, "K") == []

    def test_returns_zero_for_unknown_key(self, vault_path):
        assert clear_anomalies(vault_path, "GHOST") == 0


class TestSummary:
    def test_empty_when_no_anomalies(self, vault_path):
        assert summary(vault_path) == {}

    def test_counts_per_key(self, vault_path):
        record_anomaly(vault_path, "A", "t")
        record_anomaly(vault_path, "A", "t")
        record_anomaly(vault_path, "B", "t")
        s = summary(vault_path)
        assert s["A"] == 2
        assert s["B"] == 1

    def test_cleared_key_not_in_summary(self, vault_path):
        record_anomaly(vault_path, "A", "t")
        clear_anomalies(vault_path, "A")
        assert "A" not in summary(vault_path)
