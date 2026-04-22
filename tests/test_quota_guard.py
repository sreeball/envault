"""Tests for envault.quota_guard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.quota_guard import (
    QuotaGuardError,
    check_key_quota,
    check_vault_quota,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _quota_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".quota.json")


def _write_quota(vault_path: Path, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data))


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "vault.db"
    p.write_bytes(b"{}")
    return p


# ---------------------------------------------------------------------------
# check_vault_quota
# ---------------------------------------------------------------------------

class TestCheckVaultQuota:
    def test_no_quota_file_passes(self, vault_path: Path) -> None:
        """When no quota file exists, no error is raised."""
        check_vault_quota(vault_path)  # should not raise

    def test_no_max_secrets_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {})
        check_vault_quota(vault_path)  # should not raise

    def test_within_limit_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"max_secrets": 10})
        check_vault_quota(vault_path, adding=1)  # 0 + 1 <= 10

    def test_exactly_at_limit_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"max_secrets": 1})
        check_vault_quota(vault_path, adding=1)  # 0 + 1 <= 1

    def test_exceeds_limit_raises(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"max_secrets": 0})
        with pytest.raises(QuotaGuardError, match="quota exceeded"):
            check_vault_quota(vault_path, adding=1)

    def test_error_message_contains_counts(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"max_secrets": 0})
        with pytest.raises(QuotaGuardError) as exc_info:
            check_vault_quota(vault_path, adding=3)
        assert "max_secrets=0" in str(exc_info.value)
        assert "attempted to add 3" in str(exc_info.value)


# ---------------------------------------------------------------------------
# check_key_quota
# ---------------------------------------------------------------------------

class TestCheckKeyQuota:
    def test_no_quota_file_passes(self, vault_path: Path) -> None:
        check_key_quota(vault_path, "API_KEY")  # should not raise

    def test_key_not_in_quota_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"keys": {}})
        check_key_quota(vault_path, "API_KEY")  # should not raise

    def test_no_max_writes_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"keys": {"API_KEY": {"writes": 5}}})
        check_key_quota(vault_path, "API_KEY")  # should not raise

    def test_within_limit_passes(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"keys": {"API_KEY": {"max_writes": 10, "writes": 3}}})
        check_key_quota(vault_path, "API_KEY", adding=1)

    def test_exceeds_limit_raises(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"keys": {"API_KEY": {"max_writes": 5, "writes": 5}}})
        with pytest.raises(QuotaGuardError, match="Key quota exceeded"):
            check_key_quota(vault_path, "API_KEY", adding=1)

    def test_error_message_contains_key_name(self, vault_path: Path) -> None:
        _write_quota(vault_path, {"keys": {"DB_PASS": {"max_writes": 2, "writes": 2}}})
        with pytest.raises(QuotaGuardError) as exc_info:
            check_key_quota(vault_path, "DB_PASS")
        assert "DB_PASS" in str(exc_info.value)
        assert "max_writes=2" in str(exc_info.value)
