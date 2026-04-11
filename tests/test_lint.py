"""Tests for envault.lint."""
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.ttl import set_ttl
from envault.lint import lint_vault, LintIssue, LintResult


PASSWORD = "test-password-123"


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


def seed(vault_path, entries):
    v = Vault(vault_path, PASSWORD)
    for k, val in entries.items():
        v.set(k, val)


class TestLintResult:
    def test_ok_when_no_errors(self):
        r = LintResult(issues=[LintIssue("X", "warning", "w")])
        assert r.ok is True

    def test_not_ok_when_errors(self):
        r = LintResult(issues=[LintIssue("X", "error", "e")])
        assert r.ok is False

    def test_filters_errors_and_warnings(self):
        r = LintResult(issues=[
            LintIssue("A", "error", "e"),
            LintIssue("B", "warning", "w"),
        ])
        assert len(r.errors) == 1
        assert len(r.warnings) == 1


class TestLintVault:
    def test_empty_vault_returns_no_issues(self, vault_path):
        # create vault without any keys
        Vault(vault_path, PASSWORD)
        result = lint_vault(vault_path, PASSWORD)
        assert result.issues == []

    def test_good_key_no_issues(self, vault_path):
        seed(vault_path, {"DATABASE_URL": "postgres://user:supersecret@host/db"})
        result = lint_vault(vault_path, PASSWORD)
        assert result.issues == []

    def test_weak_value_raises_error(self, vault_path):
        seed(vault_path, {"API_KEY": "password"})
        result = lint_vault(vault_path, PASSWORD)
        errors = [i for i in result.issues if i.key == "API_KEY" and i.severity == "error"]
        assert errors, "Expected an error for weak value"

    def test_short_value_raises_warning(self, vault_path):
        seed(vault_path, {"MY_KEY": "abc"})
        result = lint_vault(vault_path, PASSWORD)
        warnings = [i for i in result.issues if i.key == "MY_KEY" and i.severity == "warning"]
        assert warnings, "Expected a warning for short value"

    def test_bad_naming_convention_raises_warning(self, vault_path):
        seed(vault_path, {"myLowercaseKey": "supersecretvalue"})
        result = lint_vault(vault_path, PASSWORD)
        warnings = [i for i in result.issues if "convention" in i.message]
        assert warnings

    def test_expired_ttl_raises_error(self, vault_path):
        seed(vault_path, {"TOKEN": "supersecrettoken"})
        set_ttl(vault_path, "TOKEN", -1)  # already expired
        result = lint_vault(vault_path, PASSWORD)
        errors = [i for i in result.issues if i.key == "TOKEN" and "expired" in i.message]
        assert errors

    def test_multiple_keys_aggregated(self, vault_path):
        seed(vault_path, {
            "GOOD_KEY": "averylongsecretvalue",
            "bad-key": "short",
        })
        result = lint_vault(vault_path, PASSWORD)
        keys_with_issues = {i.key for i in result.issues}
        assert "bad-key" in keys_with_issues
        assert "GOOD_KEY" not in keys_with_issues
