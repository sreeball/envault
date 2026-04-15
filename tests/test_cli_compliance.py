"""Tests for envault.cli_compliance."""
import pytest
from click.testing import CliRunner

from envault.cli_compliance import compliance_group
from envault.compliance import tag_compliant


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(
        compliance_group,
        [*args, "--vault", vault_path],
        catch_exceptions=False,
    )


class TestTagCmd:
    def test_tags_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "tag", "DB_PASS", "SOC2", "CC6.1")
        assert result.exit_code == 0
        assert "DB_PASS" in result.output
        assert "SOC2" in result.output

    def test_tag_with_note(self, runner, vault_path):
        result = _invoke(runner, vault_path, "tag", "DB_PASS", "SOC2", "CC6.1", "--note", "encrypted")
        assert result.exit_code == 0

    def test_empty_standard_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            compliance_group,
            ["tag", "DB_PASS", "", "CC6.1", "--vault", vault_path],
        )
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_removes_standard(self, runner, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        result = _invoke(runner, vault_path, "remove", "DB_PASS", "SOC2")
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            compliance_group,
            ["remove", "MISSING", "SOC2", "--vault", vault_path],
        )
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_entries(self, runner, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        result = _invoke(runner, vault_path, "get", "DB_PASS")
        assert result.exit_code == 0
        assert "SOC2" in result.output
        assert "CC6.1" in result.output

    def test_no_entries_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "get", "UNKNOWN")
        assert result.exit_code == 0
        assert "No compliance entries" in result.output


class TestListCmd:
    def test_lists_all_keys(self, runner, vault_path):
        tag_compliant(vault_path, "DB_PASS", "SOC2", "CC6.1")
        tag_compliant(vault_path, "API_KEY", "PCI-DSS", "3.4")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "DB_PASS" in result.output
        assert "API_KEY" in result.output

    def test_empty_vault_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No compliance tags" in result.output
