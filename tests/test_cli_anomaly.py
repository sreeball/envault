"""Tests for envault.cli_anomaly CLI commands."""
import pytest
from click.testing import CliRunner

from envault.cli_anomaly import anomaly_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(anomaly_group, [*args, vault_path] if args[0] == "summary" else [args[0], vault_path, *args[1:]])


class TestRecordCmd:
    def test_records_anomaly(self, runner, vault_path):
        result = runner.invoke(anomaly_group, ["record", vault_path, "DB_PASS", "unusual_length"])
        assert result.exit_code == 0
        assert "Anomaly recorded" in result.output

    def test_shows_severity(self, runner, vault_path):
        result = runner.invoke(
            anomaly_group,
            ["record", vault_path, "API_KEY", "repeated_access", "--severity", "high"],
        )
        assert result.exit_code == 0
        assert "high" in result.output

    def test_shows_detail(self, runner, vault_path):
        result = runner.invoke(
            anomaly_group,
            ["record", vault_path, "KEY", "short_value", "--detail", "only 3 chars"],
        )
        assert result.exit_code == 0
        assert "only 3 chars" in result.output

    def test_invalid_severity_fails(self, runner, vault_path):
        result = runner.invoke(
            anomaly_group,
            ["record", vault_path, "KEY", "t", "--severity", "extreme"],
        )
        assert result.exit_code != 0


class TestListCmd:
    def test_no_anomalies_message(self, runner, vault_path):
        result = runner.invoke(anomaly_group, ["list", vault_path, "UNKNOWN"])
        assert result.exit_code == 0
        assert "No anomalies" in result.output

    def test_lists_recorded_anomalies(self, runner, vault_path):
        runner.invoke(anomaly_group, ["record", vault_path, "K", "type_a"])
        runner.invoke(anomaly_group, ["record", vault_path, "K", "type_b", "--severity", "low"])
        result = runner.invoke(anomaly_group, ["list", vault_path, "K"])
        assert result.exit_code == 0
        assert "type_a" in result.output
        assert "type_b" in result.output


class TestClearCmd:
    def test_clears_anomalies(self, runner, vault_path):
        runner.invoke(anomaly_group, ["record", vault_path, "K", "t"])
        result = runner.invoke(anomaly_group, ["clear", vault_path, "K"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_zero_for_unknown_key(self, runner, vault_path):
        result = runner.invoke(anomaly_group, ["clear", vault_path, "GHOST"])
        assert result.exit_code == 0
        assert "0" in result.output


class TestSummaryCmd:
    def test_no_anomalies_message(self, runner, vault_path):
        result = runner.invoke(anomaly_group, ["summary", vault_path])
        assert result.exit_code == 0
        assert "No anomalies" in result.output

    def test_shows_counts(self, runner, vault_path):
        runner.invoke(anomaly_group, ["record", vault_path, "A", "t"])
        runner.invoke(anomaly_group, ["record", vault_path, "A", "t"])
        runner.invoke(anomaly_group, ["record", vault_path, "B", "t"])
        result = runner.invoke(anomaly_group, ["summary", vault_path])
        assert result.exit_code == 0
        assert "A: 2" in result.output
        assert "B: 1" in result.output
