import pytest
from click.testing import CliRunner
from envault.cli_intensity import intensity_group
from envault.intensity import set_intensity


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(intensity_group, [*args, vault_path] if args[0] == "list" else [args[0], vault_path, *args[1:]])


class TestSetCmd:
    def test_sets_intensity(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["set", vault_path, "DB_PASS", "high"])
        assert result.exit_code == 0
        assert "high" in result.output

    def test_invalid_level_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["set", vault_path, "KEY", "extreme"])
        assert result.exit_code != 0

    def test_accepts_note_option(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["set", vault_path, "KEY", "critical", "--note", "top secret"])
        assert result.exit_code == 0


class TestGetCmd:
    def test_prints_level(self, runner, vault_path):
        set_intensity(vault_path, "API_KEY", "medium", note="moderate")
        result = runner.invoke(intensity_group, ["get", vault_path, "API_KEY"])
        assert result.exit_code == 0
        assert "medium" in result.output
        assert "moderate" in result.output

    def test_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["get", vault_path, "GHOST"])
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_removes_key(self, runner, vault_path):
        set_intensity(vault_path, "KEY", "low")
        result = runner.invoke(intensity_group, ["remove", vault_path, "KEY"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["remove", vault_path, "GHOST"])
        assert result.exit_code != 0


class TestListCmd:
    def test_no_entries_message(self, runner, vault_path):
        result = runner.invoke(intensity_group, ["list", vault_path])
        assert result.exit_code == 0
        assert "No intensity" in result.output

    def test_lists_all_entries(self, runner, vault_path):
        set_intensity(vault_path, "A", "low")
        set_intensity(vault_path, "B", "critical")
        result = runner.invoke(intensity_group, ["list", vault_path])
        assert "A" in result.output
        assert "B" in result.output
