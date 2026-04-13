"""Tests for envault.cascade."""

from __future__ import annotations

import pytest

from envault.cascade import CascadeError, resolve, sources
from envault.vault import Vault


@pytest.fixture()
def make_vault(tmp_path):
    """Factory: create a vault at a temp path seeded with *secrets*."""

    def _factory(name: str, secrets: dict, password: str = "pass") -> object:
        path = tmp_path / name
        vault = Vault(path, password)
        for k, v in secrets.items():
            vault.set(k, v)
        return path

    return _factory


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------


class TestResolve:
    def test_single_vault_returns_all_keys(self, make_vault):
        path = make_vault("v1.vault", {"A": "1", "B": "2"})
        result = resolve([path], "pass")
        assert result == {"A": "1", "B": "2"}

    def test_first_vault_wins_on_conflict(self, make_vault):
        high = make_vault("high.vault", {"KEY": "high_value"})
        low = make_vault("low.vault", {"KEY": "low_value"})
        result = resolve([high, low], "pass")
        assert result["KEY"] == "high_value"

    def test_missing_keys_filled_from_lower_priority(self, make_vault):
        high = make_vault("high.vault", {"A": "from_high"})
        low = make_vault("low.vault", {"A": "from_low", "B": "only_low"})
        result = resolve([high, low], "pass")
        assert result["A"] == "from_high"
        assert result["B"] == "only_low"

    def test_keys_filter_limits_output(self, make_vault):
        path = make_vault("v.vault", {"X": "1", "Y": "2", "Z": "3"})
        result = resolve([path], "pass", keys=["X", "Z"])
        assert set(result.keys()) == {"X", "Z"}

    def test_empty_vault_list_raises(self):
        with pytest.raises(CascadeError, match="At least one"):
            resolve([], "pass")

    def test_missing_vault_file_raises(self, tmp_path):
        with pytest.raises(CascadeError, match="not found"):
            resolve([tmp_path / "ghost.vault"], "pass")

    def test_returns_empty_dict_for_empty_vaults(self, make_vault):
        path = make_vault("empty.vault", {})
        assert resolve([path], "pass") == {}


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------


class TestSources:
    def test_returns_highest_priority_path(self, make_vault):
        high = make_vault("high.vault", {"DB": "h"})
        low = make_vault("low.vault", {"DB": "l"})
        assert sources([high, low], "pass", "DB") == high

    def test_returns_none_when_key_absent(self, make_vault):
        path = make_vault("v.vault", {"A": "1"})
        assert sources([path], "pass", "MISSING") is None

    def test_skips_missing_files(self, tmp_path, make_vault):
        ghost = tmp_path / "ghost.vault"
        real = make_vault("real.vault", {"K": "v"})
        # ghost does not exist; should not raise, just skip
        assert sources([ghost, real], "pass", "K") == real
