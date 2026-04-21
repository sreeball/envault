"""Tests for envault.suppression."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.suppression import (
    SuppressionError,
    suppress_key,
    is_suppressed,
    remove_suppression,
    list_suppressions,
    _suppression_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


class TestSuppressKey:
    def test_creates_suppression_file(self, vault_path):
        suppress_key(vault_path, "API_KEY", 60)
        assert _suppression_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = suppress_key(vault_path, "API_KEY", 60)
        assert "suppressed_at" in entry
        assert "expires_at" in entry
        assert entry["duration_seconds"] == 60

    def test_stores_reason(self, vault_path):
        entry = suppress_key(vault_path, "API_KEY", 30, reason="maintenance")
        assert entry["reason"] == "maintenance"

    def test_empty_reason_allowed(self, vault_path):
        entry = suppress_key(vault_path, "API_KEY", 30)
        assert entry["reason"] == ""

    def test_raises_on_non_positive_duration(self, vault_path):
        with pytest.raises(SuppressionError):
            suppress_key(vault_path, "API_KEY", 0)

    def test_raises_on_negative_duration(self, vault_path):
        with pytest.raises(SuppressionError):
            suppress_key(vault_path, "API_KEY", -10)

    def test_overwrites_existing_suppression(self, vault_path):
        suppress_key(vault_path, "API_KEY", 60)
        entry = suppress_key(vault_path, "API_KEY", 120)
        assert entry["duration_seconds"] == 120


class TestIsSuppressed:
    def test_active_suppression_returns_true(self, vault_path):
        suppress_key(vault_path, "API_KEY", 3600)
        assert is_suppressed(vault_path, "API_KEY") is True

    def test_missing_key_returns_false(self, vault_path):
        assert is_suppressed(vault_path, "MISSING") is False

    def test_expired_suppression_returns_false(self, vault_path):
        suppress_key(vault_path, "API_KEY", 1)
        time.sleep(1.1)
        assert is_suppressed(vault_path, "API_KEY") is False


class TestRemoveSuppression:
    def test_removes_existing_entry(self, vault_path):
        suppress_key(vault_path, "API_KEY", 60)
        remove_suppression(vault_path, "API_KEY")
        assert "API_KEY" not in list_suppressions(vault_path)

    def test_no_error_on_missing_key(self, vault_path):
        remove_suppression(vault_path, "NONEXISTENT")  # should not raise


class TestListSuppressions:
    def test_returns_all_entries(self, vault_path):
        suppress_key(vault_path, "KEY_A", 60)
        suppress_key(vault_path, "KEY_B", 120)
        result = list_suppressions(vault_path)
        assert "KEY_A" in result
        assert "KEY_B" in result

    def test_empty_when_no_file(self, vault_path):
        result = list_suppressions(vault_path)
        assert result == {}
