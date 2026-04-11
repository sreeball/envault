"""Tests for envault.env_check."""

import os
import pytest

from envault.vault import Vault
from envault.env_check import CheckResult, check_env


PASSWORD = "test-password"


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "vault.json")
    v = Vault(path, PASSWORD)
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key")
    return path


# ---------------------------------------------------------------------------
# CheckResult unit tests
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_ok_when_no_issues(self):
        r = CheckResult(present=["A", "B"])
        assert r.ok is True

    def test_not_ok_when_missing(self):
        r = CheckResult(missing=["A"])
        assert r.ok is False

    def test_not_ok_when_mismatched(self):
        r = CheckResult(mismatched=["B"])
        assert r.ok is False

    def test_summary_contains_key(self):
        r = CheckResult(present=["X"], missing=["Y"], mismatched=["Z"])
        summary = r.summary()
        assert "X" in summary
        assert "Y" in summary
        assert "Z" in summary

    def test_summary_labels(self):
        r = CheckResult(present=["A"], missing=["B"], mismatched=["C"])
        summary = r.summary()
        assert "[ok]" in summary
        assert "[missing]" in summary
        assert "[mismatch]" in summary


# ---------------------------------------------------------------------------
# check_env integration tests
# ---------------------------------------------------------------------------

class TestCheckEnv:
    def test_all_missing_when_env_empty(self, vault_path, monkeypatch):
        for key in ("DB_HOST", "DB_PORT", "API_KEY"):
            monkeypatch.delenv(key, raising=False)
        result = check_env(vault_path, PASSWORD)
        assert set(result.missing) == {"DB_HOST", "DB_PORT", "API_KEY"}
        assert result.present == []
        assert result.ok is False

    def test_all_present_when_env_set(self, vault_path, monkeypatch):
        monkeypatch.setenv("DB_HOST", "anything")
        monkeypatch.setenv("DB_PORT", "anything")
        monkeypatch.setenv("API_KEY", "anything")
        result = check_env(vault_path, PASSWORD)
        assert result.missing == []
        assert set(result.present) == {"DB_HOST", "DB_PORT", "API_KEY"}
        assert result.ok is True

    def test_partial_missing(self, vault_path, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("API_KEY", raising=False)
        result = check_env(vault_path, PASSWORD)
        assert "DB_PORT" in result.missing
        assert "API_KEY" in result.missing
        assert "DB_HOST" in result.present

    def test_value_match_detected(self, vault_path, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("API_KEY", "secret-key")
        result = check_env(vault_path, PASSWORD, compare_values=True)
        assert result.mismatched == []
        assert result.ok is True

    def test_value_mismatch_detected(self, vault_path, monkeypatch):
        monkeypatch.setenv("DB_HOST", "remotehost")  # wrong value
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("API_KEY", "secret-key")
        result = check_env(vault_path, PASSWORD, compare_values=True)
        assert "DB_HOST" in result.mismatched
        assert result.ok is False

    def test_empty_vault_returns_empty_result(self, tmp_path):
        path = str(tmp_path / "empty.json")
        Vault(path, PASSWORD)  # create empty vault
        result = check_env(path, PASSWORD)
        assert result.ok is True
        assert result.missing == []
        assert result.present == []
