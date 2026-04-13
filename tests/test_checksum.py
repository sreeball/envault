"""Tests for envault.checksum."""

import pytest

from envault.checksum import (
    ChecksumError,
    get_checksum,
    list_checksums,
    record_checksum,
    remove_checksum,
    verify_checksum,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


class TestRecordChecksum:
    def test_creates_checksum_file(self, vault_path, tmp_path):
        record_checksum(vault_path, "KEY", "secret")
        assert (tmp_path / "vault.checksums.json").exists()

    def test_returns_hex_digest(self, vault_path):
        digest = record_checksum(vault_path, "KEY", "secret")
        assert isinstance(digest, str)
        assert len(digest) == 64  # SHA-256 hex

    def test_same_value_same_digest(self, vault_path):
        d1 = record_checksum(vault_path, "A", "value")
        d2 = record_checksum(vault_path, "B", "value")
        assert d1 == d2

    def test_different_values_different_digests(self, vault_path):
        d1 = record_checksum(vault_path, "A", "foo")
        d2 = record_checksum(vault_path, "A", "bar")
        assert d1 != d2

    def test_accumulates_keys(self, vault_path):
        record_checksum(vault_path, "X", "1")
        record_checksum(vault_path, "Y", "2")
        data = list_checksums(vault_path)
        assert "X" in data and "Y" in data


class TestVerifyChecksum:
    def test_returns_true_for_matching_value(self, vault_path):
        record_checksum(vault_path, "K", "correct")
        assert verify_checksum(vault_path, "K", "correct") is True

    def test_returns_false_for_wrong_value(self, vault_path):
        record_checksum(vault_path, "K", "correct")
        assert verify_checksum(vault_path, "K", "wrong") is False

    def test_raises_when_key_not_tracked(self, vault_path):
        with pytest.raises(ChecksumError, match="No checksum recorded"):
            verify_checksum(vault_path, "MISSING", "value")


class TestRemoveChecksum:
    def test_removes_existing_key(self, vault_path):
        record_checksum(vault_path, "K", "v")
        remove_checksum(vault_path, "K")
        assert get_checksum(vault_path, "K") is None

    def test_noop_for_absent_key(self, vault_path):
        remove_checksum(vault_path, "GHOST")  # should not raise


class TestGetChecksum:
    def test_returns_digest_for_known_key(self, vault_path):
        digest = record_checksum(vault_path, "K", "v")
        assert get_checksum(vault_path, "K") == digest

    def test_returns_none_for_unknown_key(self, vault_path):
        assert get_checksum(vault_path, "NOPE") is None


class TestListChecksums:
    def test_empty_when_no_file(self, vault_path):
        assert list_checksums(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        record_checksum(vault_path, "A", "1")
        record_checksum(vault_path, "B", "2")
        result = list_checksums(vault_path)
        assert set(result.keys()) == {"A", "B"}
