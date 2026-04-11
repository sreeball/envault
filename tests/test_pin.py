"""Tests for envault.pin and envault.cli_pin."""

from __future__ import annotations

import json
import pytest
from click.testing import CliRunner

from envault.pin import (
    PinError,
    assert_not_pinned,
    is_pinned,
    list_pins,
    pin_key,
    unpin_key,
)
from envault.cli_pin import pin_group


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


# ---------------------------------------------------------------------------
# TestPinKey
# ---------------------------------------------------------------------------

class TestPinKey:
    def test_creates_pins_file(self, vault_path, tmp_path):
        pin_key(vault_path, "SECRET")
        assert (tmp_path / ".envault_pins.json").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = pin_key(vault_path, "API_KEY", reason="do not rotate")
        assert entry == {"key": "API_KEY", "reason": "do not rotate"}

    def test_empty_reason_allowed(self, vault_path):
        entry = pin_key(vault_path, "TOKEN")
        assert entry["reason"] == ""

    def test_is_pinned_true_after_pin(self, vault_path):
        pin_key(vault_path, "DB_PASS")
        assert is_pinned(vault_path, "DB_PASS") is True

    def test_is_pinned_false_for_unknown(self, vault_path):
        assert is_pinned(vault_path, "GHOST") is False


# ---------------------------------------------------------------------------
# TestUnpinKey
# ---------------------------------------------------------------------------

class TestUnpinKey:
    def test_removes_pin(self, vault_path):
        pin_key(vault_path, "X")
        unpin_key(vault_path, "X")
        assert is_pinned(vault_path, "X") is False

    def test_raises_if_not_pinned(self, vault_path):
        with pytest.raises(PinError, match="not pinned"):
            unpin_key(vault_path, "MISSING")


# ---------------------------------------------------------------------------
# TestListPins
# ---------------------------------------------------------------------------

class TestListPins:
    def test_empty_when_no_pins(self, vault_path):
        assert list_pins(vault_path) == []

    def test_returns_all_pins(self, vault_path):
        pin_key(vault_path, "A", "reason A")
        pin_key(vault_path, "B", "reason B")
        keys = {e["key"] for e in list_pins(vault_path)}
        assert keys == {"A", "B"}


# ---------------------------------------------------------------------------
# TestAssertNotPinned
# ---------------------------------------------------------------------------

class TestAssertNotPinned:
    def test_passes_when_not_pinned(self, vault_path):
        assert_not_pinned(vault_path, "FREE")  # should not raise

    def test_raises_when_pinned(self, vault_path):
        pin_key(vault_path, "LOCKED", "safety")
        with pytest.raises(PinError, match="LOCKED"):
            assert_not_pinned(vault_path, "LOCKED")

    def test_error_includes_reason(self, vault_path):
        pin_key(vault_path, "K", reason="critical")
        with pytest.raises(PinError, match="critical"):
            assert_not_pinned(vault_path, "K")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_path, *args):
    return runner.invoke(pin_group, [*args, "--vault", vault_path])


class TestCliPinAdd:
    def test_pins_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "MY_KEY")
        assert result.exit_code == 0
        assert "MY_KEY" in result.output

    def test_shows_reason(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "MY_KEY", "--reason", "locked")
        assert "locked" in result.output


class TestCliPinRemove:
    def test_unpins_key(self, runner, vault_path):
        pin_key(vault_path, "R")
        result = _invoke(runner, vault_path, "remove", "R")
        assert result.exit_code == 0
        assert "Unpinned" in result.output

    def test_error_if_not_pinned(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "GHOST")
        assert result.exit_code != 0


class TestCliPinList:
    def test_no_pins_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert "No pinned" in result.output

    def test_lists_pins(self, runner, vault_path):
        pin_key(vault_path, "FOO", "bar")
        result = _invoke(runner, vault_path, "list")
        assert "FOO" in result.output
