"""Tests for envault.quota."""

import pytest

from envault.vault import Vault
from envault.quota import (
    QuotaError,
    set_quota,
    get_quota,
    remove_quota,
    check_quota,
    enforce_quota,
    _quota_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


def _seed(vault_path, password="pw", keys=None):
    v = Vault(vault_path, password)
    for k in (keys or []):
        v.set(k, f"val_{k}")


# ---------------------------------------------------------------------------
# set_quota
# ---------------------------------------------------------------------------

class TestSetQuota:
    def test_creates_quota_file(self, vault_path):
        set_quota(vault_path, 10)
        assert _quota_path(vault_path).exists()

    def test_returns_dict_with_max_secrets(self, vault_path):
        result = set_quota(vault_path, 5)
        assert result == {"max_secrets": 5}

    def test_raises_on_zero(self, vault_path):
        with pytest.raises(QuotaError):
            set_quota(vault_path, 0)

    def test_raises_on_negative(self, vault_path):
        with pytest.raises(QuotaError):
            set_quota(vault_path, -3)

    def test_overwrites_existing_quota(self, vault_path):
        set_quota(vault_path, 10)
        set_quota(vault_path, 20)
        assert get_quota(vault_path) == 20


# ---------------------------------------------------------------------------
# get_quota
# ---------------------------------------------------------------------------

class TestGetQuota:
    def test_returns_none_when_not_set(self, vault_path):
        assert get_quota(vault_path) is None

    def test_returns_configured_value(self, vault_path):
        set_quota(vault_path, 7)
        assert get_quota(vault_path) == 7


# ---------------------------------------------------------------------------
# remove_quota
# ---------------------------------------------------------------------------

class TestRemoveQuota:
    def test_returns_false_when_no_quota(self, vault_path):
        assert remove_quota(vault_path) is False

    def test_returns_true_when_quota_existed(self, vault_path):
        set_quota(vault_path, 5)
        assert remove_quota(vault_path) is True

    def test_quota_is_none_after_removal(self, vault_path):
        set_quota(vault_path, 5)
        remove_quota(vault_path)
        assert get_quota(vault_path) is None


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

class TestCheckQuota:
    def test_no_quota_returns_none_fields(self, vault_path):
        _seed(vault_path, keys=["A", "B"])
        result = check_quota(vault_path, "pw")
        assert result["max_secrets"] is None
        assert result["remaining"] is None
        assert result["exceeded"] is False
        assert result["current"] == 2

    def test_within_quota(self, vault_path):
        _seed(vault_path, keys=["A", "B"])
        set_quota(vault_path, 5)
        result = check_quota(vault_path, "pw")
        assert result["exceeded"] is False
        assert result["remaining"] == 3

    def test_at_limit_not_exceeded(self, vault_path):
        _seed(vault_path, keys=["A", "B", "C"])
        set_quota(vault_path, 3)
        result = check_quota(vault_path, "pw")
        assert result["exceeded"] is False
        assert result["remaining"] == 0

    def test_over_limit_exceeded(self, vault_path):
        _seed(vault_path, keys=["A", "B", "C", "D"])
        set_quota(vault_path, 2)
        result = check_quota(vault_path, "pw")
        assert result["exceeded"] is True
        assert result["remaining"] == 0


# ---------------------------------------------------------------------------
# enforce_quota
# ---------------------------------------------------------------------------

class TestEnforceQuota:
    def test_no_error_within_limit(self, vault_path):
        _seed(vault_path, keys=["X"])
        set_quota(vault_path, 3)
        enforce_quota(vault_path, "pw")  # should not raise

    def test_raises_when_exceeded(self, vault_path):
        _seed(vault_path, keys=["A", "B", "C"])
        set_quota(vault_path, 2)
        with pytest.raises(QuotaError, match="exceeds quota"):
            enforce_quota(vault_path, "pw")

    def test_no_error_when_no_quota_set(self, vault_path):
        _seed(vault_path, keys=["A", "B", "C", "D", "E"])
        enforce_quota(vault_path, "pw")  # no quota → never raises
