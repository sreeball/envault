"""Tests for envault.expire."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.expire import (
    ExpireError,
    expiry_info,
    list_expired,
    list_expiring_soon,
    purge_expired,
)
from envault.ttl import _ttl_path


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


def _write_ttl(vault_path, entries: dict):
    path = _ttl_path(vault_path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(entries, fh)


def _iso(delta_seconds: int) -> str:
    dt = datetime.now(tz=timezone.utc) + timedelta(seconds=delta_seconds)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# list_expired
# ---------------------------------------------------------------------------

class TestListExpired:
    def test_no_ttl_file_returns_empty(self, vault_path):
        assert list_expired(vault_path) == []

    def test_returns_expired_keys(self, vault_path):
        _write_ttl(vault_path, {
            "OLD_KEY": {"expires_at": _iso(-100)},
            "FRESH_KEY": {"expires_at": _iso(9999)},
        })
        result = list_expired(vault_path)
        assert result == ["OLD_KEY"]

    def test_ignores_entries_without_expires_at(self, vault_path):
        _write_ttl(vault_path, {"NO_TTL": {}})
        assert list_expired(vault_path) == []


# ---------------------------------------------------------------------------
# list_expiring_soon
# ---------------------------------------------------------------------------

class TestListExpiringSoon:
    def test_returns_keys_within_window(self, vault_path):
        _write_ttl(vault_path, {
            "SOON": {"expires_at": _iso(3600)},
            "LATER": {"expires_at": _iso(172800)},
        })
        result = list_expiring_soon(vault_path, within_seconds=7200)
        assert "SOON" in result
        assert "LATER" not in result

    def test_already_expired_not_included(self, vault_path):
        _write_ttl(vault_path, {"OLD": {"expires_at": _iso(-1)}})
        assert list_expiring_soon(vault_path, within_seconds=86400) == []

    def test_raises_on_negative_window(self, vault_path):
        with pytest.raises(ExpireError):
            list_expiring_soon(vault_path, within_seconds=-1)


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

class TestPurgeExpired:
    def test_removes_expired_from_ttl_file(self, vault_path):
        _write_ttl(vault_path, {
            "DEAD": {"expires_at": _iso(-50)},
            "ALIVE": {"expires_at": _iso(9999)},
        })
        removed = purge_expired(vault_path)
        assert removed == ["DEAD"]
        with open(_ttl_path(vault_path)) as fh:
            data = json.load(fh)
        assert "DEAD" not in data
        assert "ALIVE" in data

    def test_returns_empty_when_nothing_expired(self, vault_path):
        _write_ttl(vault_path, {"ALIVE": {"expires_at": _iso(9999)}})
        assert purge_expired(vault_path) == []

    def test_no_ttl_file_returns_empty(self, vault_path):
        assert purge_expired(vault_path) == []


# ---------------------------------------------------------------------------
# expiry_info
# ---------------------------------------------------------------------------

class TestExpiryInfo:
    def test_returns_entry_for_known_key(self, vault_path):
        _write_ttl(vault_path, {"MY_KEY": {"expires_at": _iso(500)}})
        info = expiry_info(vault_path, "MY_KEY")
        assert info is not None
        assert "expires_at" in info

    def test_returns_none_for_unknown_key(self, vault_path):
        _write_ttl(vault_path, {})
        assert expiry_info(vault_path, "MISSING") is None

    def test_returns_none_when_no_ttl_file(self, vault_path):
        assert expiry_info(vault_path, "ANY") is None
