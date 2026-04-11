"""Tests for envault.watch."""

import time
import threading
from pathlib import Path

import pytest

from envault.watch import WatchError, watch, watch_once


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.json"
    p.write_text('{"v": 1}')
    return p


def _touch_after(path: Path, delay: float):
    """Touch *path* after *delay* seconds in a background thread."""
    def _run():
        time.sleep(delay)
        path.write_text('{"v": 2}')
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


class TestWatchOnce:
    def test_detects_change(self, vault_path):
        _touch_after(vault_path, 0.3)
        detected = []
        result = watch_once(vault_path, lambda p: detected.append(p), interval=0.1, timeout=2.0)
        assert result is True
        assert detected == [vault_path]

    def test_returns_false_on_timeout(self, vault_path):
        result = watch_once(vault_path, lambda p: None, interval=0.1, timeout=0.3)
        assert result is False

    def test_raises_if_vault_missing(self, tmp_path):
        missing = tmp_path / "missing.json"
        with pytest.raises(WatchError, match="not found"):
            watch_once(missing, lambda p: None)

    def test_callback_receives_path(self, vault_path):
        received = []
        _touch_after(vault_path, 0.2)
        watch_once(vault_path, lambda p: received.append(str(p)), interval=0.1, timeout=2.0)
        assert str(vault_path) in received


class TestWatch:
    def test_raises_if_vault_missing(self, tmp_path):
        missing = tmp_path / "no.json"
        with pytest.raises(WatchError):
            watch(missing, lambda p: None, interval=0.1, timeout=0.2)

    def test_returns_zero_when_no_changes(self, vault_path):
        count = watch(vault_path, lambda p: None, interval=0.1, timeout=0.3)
        assert count == 0

    def test_counts_change_events(self, vault_path):
        events = []

        def _mutate():
            for _ in range(2):
                time.sleep(0.2)
                vault_path.write_text('{"v": 99}')

        t = threading.Thread(target=_mutate, daemon=True)
        t.start()
        count = watch(vault_path, lambda p: events.append(1), interval=0.1, timeout=1.0)
        assert count >= 1
        assert len(events) == count
