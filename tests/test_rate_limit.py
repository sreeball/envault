"""Tests for envault.rate_limit."""

import time
import pytest
from pathlib import Path

from envault.rate_limit import (
    RateLimitError,
    set_limit,
    check_and_record,
    remove_limit,
    list_limits,
    _rate_limit_path,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return p


class TestSetLimit:
    def test_creates_rate_limit_file(self, vault_path):
        set_limit(vault_path, "get", 10, 60)
        assert _rate_limit_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_limit(vault_path, "get", 10, 60)
        assert entry["operation"] == "get"
        assert entry["max_calls"] == 10
        assert entry["window_seconds"] == 60

    def test_raises_on_invalid_max_calls(self, vault_path):
        with pytest.raises(RateLimitError):
            set_limit(vault_path, "get", 0, 60)

    def test_raises_on_invalid_window(self, vault_path):
        with pytest.raises(RateLimitError):
            set_limit(vault_path, "get", 5, -1)

    def test_overwrites_existing_limit(self, vault_path):
        set_limit(vault_path, "get", 5, 30)
        entry = set_limit(vault_path, "get", 20, 120)
        assert entry["max_calls"] == 20
        assert entry["window_seconds"] == 120


class TestCheckAndRecord:
    def test_allows_call_within_limit(self, vault_path):
        set_limit(vault_path, "set", 5, 60)
        result = check_and_record(vault_path, "set")
        assert result["allowed"] is True

    def test_decrements_remaining(self, vault_path):
        set_limit(vault_path, "set", 3, 60)
        check_and_record(vault_path, "set")
        result = check_and_record(vault_path, "set")
        assert result["remaining"] == 1

    def test_raises_when_limit_exceeded(self, vault_path):
        set_limit(vault_path, "delete", 2, 60)
        check_and_record(vault_path, "delete")
        check_and_record(vault_path, "delete")
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            check_and_record(vault_path, "delete")

    def test_no_limit_configured_allows_freely(self, vault_path):
        result = check_and_record(vault_path, "unknown_op")
        assert result["allowed"] is True
        assert result["remaining"] is None

    def test_calls_outside_window_not_counted(self, vault_path):
        set_limit(vault_path, "get", 1, 1)
        check_and_record(vault_path, "get")
        time.sleep(1.1)
        # Should not raise because the old call is outside the window
        result = check_and_record(vault_path, "get")
        assert result["allowed"] is True


class TestRemoveLimit:
    def test_removes_existing_limit(self, vault_path):
        set_limit(vault_path, "get", 5, 60)
        remove_limit(vault_path, "get")
        limits = list_limits(vault_path)
        assert "get" not in limits

    def test_raises_if_not_configured(self, vault_path):
        with pytest.raises(RateLimitError):
            remove_limit(vault_path, "nonexistent")


class TestListLimits:
    def test_returns_empty_when_no_limits(self, vault_path):
        assert list_limits(vault_path) == {}

    def test_returns_all_configured_limits(self, vault_path):
        set_limit(vault_path, "get", 10, 60)
        set_limit(vault_path, "set", 5, 30)
        limits = list_limits(vault_path)
        assert "get" in limits
        assert "set" in limits

    def test_does_not_expose_call_history(self, vault_path):
        set_limit(vault_path, "get", 10, 60)
        check_and_record(vault_path, "get")
        limits = list_limits(vault_path)
        assert "calls" not in limits["get"]
