"""Tests for envault.cli_scoring."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_scoring import scoring_group
from envault.vault import Vault


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "vault.json"
    v = Vault(p, "secret")
    v.set("STRONG", "C0mpl3x!P@ssw0rd#99")
    v.set("WEAK", "abc")
    return p


def _invoke(runner: CliRunner, *args):
    return runner.invoke(scoring_group, list(args), catch_exceptions=False)


class TestAllCmd:
    def test_exits_zero_on_success(self, runner, vault_path):
        result = _invoke(runner, "all", str(vault_path), "--password", "secret")
        assert result.exit_code == 0

    def test_shows_average_score(self, runner, vault_path):
        result = _invoke(runner, "all", str(vault_path), "--password", "secret")
        assert "Average score:" in result.output

    def test_shows_key_names(self, runner, vault_path):
        result = _invoke(runner, "all", str(vault_path), "--password", "secret")
        assert "STRONG" in result.output
        assert "WEAK" in result.output

    def test_min_grade_passes_when_all_meet_threshold(self, runner, vault_path):
        # All keys should be at least F, so this should pass
        result = _invoke(
            runner, "all", str(vault_path), "--password", "secret", "--min-grade", "F"
        )
        assert result.exit_code == 0

    def test_min_grade_fails_when_key_below_threshold(self, runner, vault_path):
        # WEAK key will fail an A threshold
        result = runner.invoke(
            scoring_group,
            ["all", str(vault_path), "--password", "secret", "--min-grade", "A"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "WEAK" in result.output

    def test_invalid_min_grade_raises(self, runner, vault_path):
        result = runner.invoke(
            scoring_group,
            ["all", str(vault_path), "--password", "secret", "--min-grade", "Z"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0

    def test_empty_vault_no_error(self, runner, tmp_path):
        p = tmp_path / "empty.json"
        Vault(p, "pass")
        result = _invoke(runner, "all", str(p), "--password", "pass")
        assert result.exit_code == 0
        assert "No secrets to score." in result.output


class TestKeyCmd:
    def test_scores_strong_value(self, runner):
        result = _invoke(runner, "key", "MY_KEY", "C0mpl3x!P@ssw0rd#99")
        assert result.exit_code == 0
        assert "MY_KEY" in result.output
        assert "OK" in result.output

    def test_scores_weak_value(self, runner):
        result = _invoke(runner, "key", "MY_KEY", "abc")
        assert result.exit_code == 0
        assert "WEAK" in result.output

    def test_lists_issues(self, runner):
        result = _invoke(runner, "key", "MY_KEY", "abc")
        assert "too short" in result.output
