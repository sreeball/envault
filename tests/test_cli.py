import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli import cli


PASSWORD = "test-password-123"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "test.envault")


def invoke_set(runner, vault_path, key, value):
    return runner.invoke(cli, ["set", key, value, "--vault", vault_path, "--password", PASSWORD])


def invoke_get(runner, vault_path, key):
    return runner.invoke(cli, ["get", key, "--vault", vault_path, "--password", PASSWORD])


class TestCliSet:
    def test_set_creates_vault_file(self, runner, vault_path):
        result = invoke_set(runner, vault_path, "MY_KEY", "my_value")
        assert result.exit_code == 0
        assert Path(vault_path).exists()

    def test_set_outputs_confirmation(self, runner, vault_path):
        result = invoke_set(runner, vault_path, "MY_KEY", "my_value")
        assert "MY_KEY" in result.output
        assert "✔" in result.output


class TestCliGet:
    def test_get_returns_value(self, runner, vault_path):
        invoke_set(runner, vault_path, "DB_URL", "postgres://localhost/db")
        result = invoke_get(runner, vault_path, "DB_URL")
        assert result.exit_code == 0
        assert "postgres://localhost/db" in result.output

    def test_get_missing_key_exits_nonzero(self, runner, vault_path):
        invoke_set(runner, vault_path, "EXISTING", "value")
        result = invoke_get(runner, vault_path, "MISSING_KEY")
        assert result.exit_code != 0


class TestCliList:
    def test_list_shows_keys(self, runner, vault_path):
        invoke_set(runner, vault_path, "KEY_A", "val_a")
        invoke_set(runner, vault_path, "KEY_B", "val_b")
        result = runner.invoke(cli, ["list", "--vault", vault_path, "--password", PASSWORD])
        assert result.exit_code == 0
        assert "KEY_A" in result.output
        assert "KEY_B" in result.output

    def test_list_empty_vault(self, runner, vault_path):
        result = runner.invoke(cli, ["list", "--vault", vault_path, "--password", PASSWORD])
        assert result.exit_code == 0
        assert "No variables" in result.output


class TestCliDelete:
    def test_delete_removes_key(self, runner, vault_path):
        invoke_set(runner, vault_path, "TO_DELETE", "some_val")
        result = runner.invoke(cli, ["delete", "TO_DELETE", "--vault", vault_path, "--password", PASSWORD])
        assert result.exit_code == 0
        get_result = invoke_get(runner, vault_path, "TO_DELETE")
        assert get_result.exit_code != 0

    def test_delete_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(cli, ["delete", "GHOST_KEY", "--vault", vault_path, "--password", PASSWORD])
        assert result.exit_code != 0
