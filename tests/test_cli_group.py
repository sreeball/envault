import pytest
from click.testing import CliRunner
from envault.cli_group import group_cmd
from envault.group import create_group, add_key_to_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(group_cmd, [*args, "--vault", vault_path])


class TestCreateCmd:
    def test_creates_group(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "backend")
        assert result.exit_code == 0
        assert "created" in result.output

    def test_error_on_duplicate(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        result = _invoke(runner, vault_path, "create", "backend")
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestAddCmd:
    def test_adds_key(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        result = _invoke(runner, vault_path, "add", "backend", "DB_URL")
        assert result.exit_code == 0
        assert "DB_URL" in result.output

    def test_error_missing_group(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "ghost", "KEY")
        assert result.exit_code != 0
        assert "does not exist" in result.output


class TestRemoveCmd:
    def test_removes_key(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        _invoke(runner, vault_path, "add", "backend", "DB_URL")
        result = _invoke(runner, vault_path, "remove", "backend", "DB_URL")
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_error_missing_group(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "ghost", "KEY")
        assert result.exit_code != 0


class TestDeleteCmd:
    def test_deletes_group(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        result = _invoke(runner, vault_path, "delete", "backend")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_error_missing_group(self, runner, vault_path):
        result = _invoke(runner, vault_path, "delete", "ghost")
        assert result.exit_code != 0


class TestListCmd:
    def test_no_groups_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No groups" in result.output

    def test_lists_groups(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        _invoke(runner, vault_path, "add", "backend", "DB_URL")
        result = _invoke(runner, vault_path, "list")
        assert "backend" in result.output
        assert "DB_URL" in result.output

    def test_empty_group_label(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "empty")
        result = _invoke(runner, vault_path, "list")
        assert "(empty)" in result.output


class TestKeysCmd:
    def test_lists_keys(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        _invoke(runner, vault_path, "add", "backend", "SECRET")
        result = _invoke(runner, vault_path, "keys", "backend")
        assert result.exit_code == 0
        assert "SECRET" in result.output

    def test_empty_group_message(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "backend")
        result = _invoke(runner, vault_path, "keys", "backend")
        assert "empty" in result.output

    def test_error_missing_group(self, runner, vault_path):
        result = _invoke(runner, vault_path, "keys", "ghost")
        assert result.exit_code != 0
