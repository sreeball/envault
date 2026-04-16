"""Tests for envault.signal module."""
import pytest
from pathlib import Path
from envault.signal import emit_signal, get_signals, clear_signals, list_all, SignalError


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestEmitSignal:
    def test_creates_signals_file(self, vault_path):
        emit_signal(vault_path, "API_KEY", "on_change")
        signals_file = Path(vault_path).parent / ".envault_signals.json"
        assert signals_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = emit_signal(vault_path, "API_KEY", "on_expire", "payload_data")
        assert entry["signal"] == "on_expire"
        assert entry["payload"] == "payload_data"

    def test_empty_payload_defaults_to_empty_string(self, vault_path):
        entry = emit_signal(vault_path, "API_KEY", "on_change")
        assert entry["payload"] == ""

    def test_accumulates_signals(self, vault_path):
        emit_signal(vault_path, "API_KEY", "on_change")
        emit_signal(vault_path, "API_KEY", "on_expire")
        signals = get_signals(vault_path, "API_KEY")
        assert len(signals) == 2

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(SignalError):
            emit_signal(vault_path, "", "on_change")

    def test_raises_on_empty_signal(self, vault_path):
        with pytest.raises(SignalError):
            emit_signal(vault_path, "API_KEY", "")

    def test_multiple_keys_independent(self, vault_path):
        emit_signal(vault_path, "KEY_A", "on_change")
        emit_signal(vault_path, "KEY_B", "on_expire")
        assert len(get_signals(vault_path, "KEY_A")) == 1
        assert len(get_signals(vault_path, "KEY_B")) == 1


class TestGetSignals:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        assert get_signals(vault_path, "MISSING") == []

    def test_returns_signal_list(self, vault_path):
        emit_signal(vault_path, "DB_PASS", "on_rotate", "context")
        result = get_signals(vault_path, "DB_PASS")
        assert result[0]["signal"] == "on_rotate"


class TestClearSignals:
    def test_removes_all_signals_for_key(self, vault_path):
        emit_signal(vault_path, "API_KEY", "on_change")
        emit_signal(vault_path, "API_KEY", "on_expire")
        count = clear_signals(vault_path, "API_KEY")
        assert count == 2
        assert get_signals(vault_path, "API_KEY") == []

    def test_returns_zero_for_unknown_key(self, vault_path):
        assert clear_signals(vault_path, "GHOST") == 0


class TestListAll:
    def test_returns_empty_dict_when_no_signals(self, vault_path):
        assert list_all(vault_path) == {}

    def test_returns_all_keys(self, vault_path):
        emit_signal(vault_path, "A", "on_change")
        emit_signal(vault_path, "B", "on_expire")
        result = list_all(vault_path)
        assert "A" in result
        assert "B" in result
