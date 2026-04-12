"""Tests for envault.policy."""

import pytest
from pathlib import Path
from envault.policy import (
    add_policy,
    remove_policy,
    list_policies,
    enforce,
    PolicyError,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


class TestAddPolicy:
    def test_creates_policy_file(self, vault_path):
        add_policy(vault_path, "API_KEY", required=True)
        policy_file = Path(vault_path).parent / ".envault_policies.json"
        assert policy_file.exists()

    def test_returns_entry_dict(self, vault_path):
        result = add_policy(vault_path, "API_KEY", required=True)
        assert result["key"] == "API_KEY"
        assert result["required"] is True

    def test_stores_pattern(self, vault_path):
        result = add_policy(vault_path, "PORT", pattern=r"\d+")
        assert result["pattern"] == r"\d+"

    def test_raises_on_invalid_pattern(self, vault_path):
        with pytest.raises(PolicyError, match="Invalid regex"):
            add_policy(vault_path, "KEY", pattern="[invalid")

    def test_accumulates_policies(self, vault_path):
        add_policy(vault_path, "KEY_A", required=True)
        add_policy(vault_path, "KEY_B", pattern=r".+")
        policies = list_policies(vault_path)
        assert "KEY_A" in policies
        assert "KEY_B" in policies


class TestRemovePolicy:
    def test_removes_existing_policy(self, vault_path):
        add_policy(vault_path, "API_KEY", required=True)
        remove_policy(vault_path, "API_KEY")
        assert "API_KEY" not in list_policies(vault_path)

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(PolicyError, match="No policy found"):
            remove_policy(vault_path, "NONEXISTENT")


class TestEnforce:
    def test_no_violations_when_all_present(self, vault_path):
        add_policy(vault_path, "API_KEY", required=True)
        violations = enforce(vault_path, {"API_KEY": "secret"})
        assert violations == []

    def test_violation_when_required_key_missing(self, vault_path):
        add_policy(vault_path, "API_KEY", required=True)
        violations = enforce(vault_path, {})
        assert any("API_KEY" in v for v in violations)

    def test_violation_when_pattern_not_matched(self, vault_path):
        add_policy(vault_path, "PORT", pattern=r"\d+")
        violations = enforce(vault_path, {"PORT": "not-a-number"})
        assert any("PORT" in v for v in violations)

    def test_no_violation_when_pattern_matched(self, vault_path):
        add_policy(vault_path, "PORT", pattern=r"\d+")
        violations = enforce(vault_path, {"PORT": "8080"})
        assert violations == []

    def test_optional_missing_key_not_a_violation(self, vault_path):
        add_policy(vault_path, "OPTIONAL_KEY", required=False, pattern=r".+")
        violations = enforce(vault_path, {})
        assert violations == []
