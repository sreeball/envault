"""Tests for envault.cli_forecast."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_forecast import forecast_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    vp = tmp_path / "vault.enc"
    vp.write_bytes(b"")
    return str(vp)


def _iso_future(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _seed_ttl(vault_path: str, key: str, days: int):
    p = Path(vault_path).parent / ".envault_ttl.json"
    data = {}
    if p.exists():
        data = json.loads(p.read_text())
    data[key] = {"expires_at": _iso_future(days), "note": ""}
    p.write_text(json.dumps(data))


def _invoke(runner, vault_path, *args):
    return runner.invoke(forecast_group, ["--vault", vault_path, *args])


class TestShowCmd:
    def test_no_events_message(self, runner, vault_path):
        result = runner.invoke(forecast_group, ["show", "--vault", vault_path])
        assert result.exit_code == 0
        assert "No upcoming events" in result.output

    def test_shows_expiry_entry(self, runner, vault_path):
        _seed_ttl(vault_path, "API_KEY", 5)
        result = runner.invoke(forecast_group, ["show", "--vault", vault_path])
        assert result.exit_code == 0
        assert "API_KEY" in result.output
        assert "EXPIRY" in result.output

    def test_filters_by_event_type(self, runner, vault_path):
        _seed_ttl(vault_path, "API_KEY", 5)
        result = runner.invoke(
            forecast_group, ["show", "--vault", vault_path, "--event", "reminder"]
        )
        assert result.exit_code == 0
        assert "No upcoming events" in result.output

    def test_horizon_option_excludes_far_future(self, runner, vault_path):
        _seed_ttl(vault_path, "FAR_KEY", 90)
        result = runner.invoke(
            forecast_group, ["show", "--vault", vault_path, "--horizon", "30"]
        )
        assert result.exit_code == 0
        assert "No upcoming events" in result.output


class TestSummaryCmd:
    def test_zero_total_when_empty(self, runner, vault_path):
        result = runner.invoke(forecast_group, ["summary", "--vault", vault_path])
        assert result.exit_code == 0
        assert "Total upcoming events: 0" in result.output

    def test_counts_shown(self, runner, vault_path):
        _seed_ttl(vault_path, "KEY1", 3)
        _seed_ttl(vault_path, "KEY2", 7)
        result = runner.invoke(forecast_group, ["summary", "--vault", vault_path])
        assert result.exit_code == 0
        assert "Total upcoming events: 2" in result.output
        assert "expiry: 2" in result.output
