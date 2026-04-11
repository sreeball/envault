"""Tests for envault.diff."""

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.diff import (
    DiffError,
    DiffEntry,
    diff_vaults,
    diff_vault_dotenv,
    _compute_diff,
)

PASSWORD = "hunter2"


@pytest.fixture()
def vault_a(tmp_path):
    p = tmp_path / "a.vault"
    v = Vault(p, PASSWORD)
    v.set("KEY_ONLY_A", "alpha")
    v.set("SHARED", "original")
    return p


@pytest.fixture()
def vault_b(tmp_path):
    p = tmp_path / "b.vault"
    v = Vault(p, PASSWORD)
    v.set("KEY_ONLY_B", "beta")
    v.set("SHARED", "changed")
    return p


class TestComputeDiff:
    def test_added_key(self):
        entries = _compute_diff({}, {"NEW": "val"})
        assert any(e.key == "NEW" and e.status == "added" for e in entries)

    def test_removed_key(self):
        entries = _compute_diff({"OLD": "val"}, {})
        assert any(e.key == "OLD" and e.status == "removed" for e in entries)

    def test_changed_key(self):
        entries = _compute_diff({"K": "v1"}, {"K": "v2"})
        assert any(e.key == "K" and e.status == "changed" for e in entries)

    def test_unchanged_key(self):
        entries = _compute_diff({"K": "same"}, {"K": "same"})
        assert any(e.key == "K" and e.status == "unchanged" for e in entries)

    def test_returns_sorted_keys(self):
        entries = _compute_diff({"Z": "1", "A": "2"}, {"M": "3"})
        keys = [e.key for e in entries]
        assert keys == sorted(keys)

    def test_empty_both_sides(self):
        assert _compute_diff({}, {}) == []


class TestDiffVaults:
    def test_detects_added_key(self, vault_a, vault_b):
        entries = diff_vaults(vault_a, PASSWORD, vault_b, PASSWORD)
        assert any(e.key == "KEY_ONLY_B" and e.status == "added" for e in entries)

    def test_detects_removed_key(self, vault_a, vault_b):
        entries = diff_vaults(vault_a, PASSWORD, vault_b, PASSWORD)
        assert any(e.key == "KEY_ONLY_A" and e.status == "removed" for e in entries)

    def test_detects_changed_value(self, vault_a, vault_b):
        entries = diff_vaults(vault_a, PASSWORD, vault_b, PASSWORD)
        changed = next(e for e in entries if e.key == "SHARED")
        assert changed.status == "changed"
        assert changed.left_value == "original"
        assert changed.right_value == "changed"

    def test_returns_diff_entry_namedtuples(self, vault_a, vault_b):
        entries = diff_vaults(vault_a, PASSWORD, vault_b, PASSWORD)
        assert all(isinstance(e, DiffEntry) for e in entries)


class TestDiffVaultDotenv:
    def test_detects_missing_key_in_dotenv(self, vault_a, tmp_path):
        dotenv = tmp_path / ".env"
        dotenv.write_text("SHARED=original\n")
        entries = diff_vault_dotenv(vault_a, PASSWORD, dotenv)
        assert any(e.key == "KEY_ONLY_A" and e.status == "removed" for e in entries)

    def test_detects_extra_key_in_dotenv(self, vault_a, tmp_path):
        dotenv = tmp_path / ".env"
        dotenv.write_text("SHARED=original\nEXTRA=foo\n")
        entries = diff_vault_dotenv(vault_a, PASSWORD, dotenv)
        assert any(e.key == "EXTRA" and e.status == "added" for e in entries)

    def test_raises_diff_error_on_missing_file(self, vault_a, tmp_path):
        missing = tmp_path / "nonexistent.env"
        with pytest.raises(DiffError):
            diff_vault_dotenv(vault_a, PASSWORD, missing)
