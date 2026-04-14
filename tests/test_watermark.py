"""Tests for envault.watermark."""

from __future__ import annotations

import json
import pathlib

import pytest

from envault.watermark import (
    WatermarkError,
    embed,
    get_watermark,
    list_watermarks,
    remove,
    verify,
    _watermark_path,
)


@pytest.fixture()
def vault_path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "vault.json")


class TestEmbed:
    def test_creates_watermark_file(self, vault_path: str) -> None:
        embed(vault_path, "DB_PASS", "secret", "alice")
        assert _watermark_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: str) -> None:
        entry = embed(vault_path, "DB_PASS", "secret", "alice")
        assert entry["key"] == "DB_PASS"
        assert entry["owner"] == "alice"
        assert "fingerprint" in entry

    def test_fingerprint_is_hex_string(self, vault_path: str) -> None:
        entry = embed(vault_path, "API_KEY", "abc123", "bob")
        fp = entry["fingerprint"]
        assert isinstance(fp, str)
        int(fp, 16)  # must be valid hex

    def test_raises_on_empty_key(self, vault_path: str) -> None:
        with pytest.raises(WatermarkError):
            embed(vault_path, "", "val", "alice")

    def test_raises_on_empty_owner(self, vault_path: str) -> None:
        with pytest.raises(WatermarkError):
            embed(vault_path, "KEY", "val", "")

    def test_overwrites_existing_entry(self, vault_path: str) -> None:
        embed(vault_path, "KEY", "old", "alice")
        embed(vault_path, "KEY", "new", "alice")
        data = json.loads(_watermark_path(vault_path).read_text())
        assert len(data) == 1


class TestVerify:
    def test_correct_value_returns_true(self, vault_path: str) -> None:
        embed(vault_path, "KEY", "myvalue", "alice")
        assert verify(vault_path, "KEY", "myvalue") is True

    def test_wrong_value_returns_false(self, vault_path: str) -> None:
        embed(vault_path, "KEY", "myvalue", "alice")
        assert verify(vault_path, "KEY", "wrongvalue") is False

    def test_raises_when_no_watermark(self, vault_path: str) -> None:
        with pytest.raises(WatermarkError, match="no watermark"):
            verify(vault_path, "MISSING", "val")


class TestGetWatermark:
    def test_returns_entry(self, vault_path: str) -> None:
        embed(vault_path, "KEY", "val", "carol")
        entry = get_watermark(vault_path, "KEY")
        assert entry["owner"] == "carol"

    def test_raises_on_missing_key(self, vault_path: str) -> None:
        with pytest.raises(WatermarkError):
            get_watermark(vault_path, "GHOST")


class TestRemove:
    def test_removes_entry(self, vault_path: str) -> None:
        embed(vault_path, "KEY", "val", "alice")
        remove(vault_path, "KEY")
        assert list_watermarks(vault_path) == []

    def test_noop_when_missing(self, vault_path: str) -> None:
        remove(vault_path, "NONEXISTENT")  # should not raise


class TestListWatermarks:
    def test_empty_when_no_file(self, vault_path: str) -> None:
        assert list_watermarks(vault_path) == []

    def test_returns_all_entries(self, vault_path: str) -> None:
        embed(vault_path, "A", "v1", "alice")
        embed(vault_path, "B", "v2", "bob")
        entries = list_watermarks(vault_path)
        keys = {e["key"] for e in entries}
        assert keys == {"A", "B"}
