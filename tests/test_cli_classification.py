"""Tests for envault.cli_classification."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_classification import classification_group
from envault.classification import classify


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(
        classification_group, list(args) + ["--vault", vault_path]
    )


class TestSetCmd:
    def test_classifies_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "API_KEY", "confidential")
        assert result.exit_code == 0
        assert "confidential" in result.output

    def test_with_reason(self, runner, vault_path):
        result = _invoke(
            runner, vault_path, "set", "DB_PASS", "restricted", "--reason", "PCI"
        )
        assert result.exit_code == 0

    def test_invalid_level_rejected(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "KEY", "bogus")
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_level(self, runner, vault_path):
        classify(vault_path, "TOKEN", "internal")
        result = _invoke(runner, vault_path, "get", "TOKEN")
        assert result.exit_code == 0
        assert "internal" in result.output

    def test_missing_key_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "get", "GHOST")
        assert result.exit_code == 0
        assert "No classification" in result.output


class TestRemoveCmd:
    def test_removes_existing(self, runner, vault_path):
        classify(vault_path, "X", "public")
        result = _invoke(runner, vault_path, "remove", "X")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_not_found_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "MISSING")
        assert result.exit_code == 0
        assert "No classification" in result.output


class TestListCmd:
    def test_lists_all(self, runner, vault_path):
        classify(vault_path, "A", "public")
        classify(vault_path, "B", "internal")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output

    def test_filters_by_level(self, runner, vault_path):
        classify(vault_path, "A", "public")
        classify(vault_path, "B", "restricted")
        result = _invoke(runner, vault_path, "list", "--level", "public")
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" not in result.output

    def test_empty_message_when_none(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No classifications" in result.output
