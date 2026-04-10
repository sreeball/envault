"""Tests for envault.sync module."""

import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.sync import push, pull, status, SyncError


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "local.json"), password="test-password")
    v.set("KEY_A", "alpha")
    v.set("KEY_B", "beta")
    return v


@pytest.fixture()
def remote_path(tmp_path):
    return str(tmp_path / "remote" / "vault.json")


class TestPush:
    def test_creates_remote_file(self, vault, remote_path):
        push(vault, remote_path)
        assert Path(remote_path).exists()

    def test_returns_key_count(self, vault, remote_path):
        count = push(vault, remote_path)
        assert count == 2

    def test_remote_contains_all_keys(self, vault, remote_path):
        push(vault, remote_path)
        with open(remote_path) as fh:
            data = json.load(fh)
        assert set(data.keys()) == {"KEY_A", "KEY_B"}

    def test_creates_parent_directories(self, vault, tmp_path):
        deep = str(tmp_path / "a" / "b" / "c" / "vault.json")
        push(vault, deep)
        assert Path(deep).exists()


class TestPull:
    def test_imports_remote_keys(self, vault, remote_path, tmp_path):
        push(vault, remote_path)
        new_vault = Vault(str(tmp_path / "new.json"), password="test-password")
        count = pull(new_vault, remote_path)
        assert count == 2

    def test_does_not_overwrite_by_default(self, vault, remote_path, tmp_path):
        push(vault, remote_path)
        other = Vault(str(tmp_path / "other.json"), password="test-password")
        other.set("KEY_A", "original")
        pull(other, remote_path)
        assert other.get("KEY_A") == "original"

    def test_overwrite_flag_replaces_local(self, vault, remote_path, tmp_path):
        push(vault, remote_path)
        other = Vault(str(tmp_path / "other.json"), password="test-password")
        other.set("KEY_A", "original")
        pull(other, remote_path, overwrite=True)
        assert other.get("KEY_A") == "alpha"

    def test_raises_when_remote_missing(self, vault, remote_path):
        with pytest.raises(SyncError):
            pull(vault, remote_path)


class TestStatus:
    def test_only_local(self, vault, remote_path):
        result = status(vault, remote_path)
        assert "KEY_A" in result["only_local"]
        assert result["only_remote"] == []

    def test_common_after_push(self, vault, remote_path):
        push(vault, remote_path)
        result = status(vault, remote_path)
        assert set(result["common"]) == {"KEY_A", "KEY_B"}
        assert result["only_local"] == []
        assert result["only_remote"] == []

    def test_only_remote(self, vault, remote_path, tmp_path):
        push(vault, remote_path)
        empty_vault = Vault(str(tmp_path / "empty.json"), password="test-password")
        result = status(empty_vault, remote_path)
        assert set(result["only_remote"]) == {"KEY_A", "KEY_B"}
