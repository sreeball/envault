"""Tests for envault.export module."""

import json
import pytest

from envault.export import export_dotenv, export_shell, export_json, export_secrets

SAMPLE = {"DB_URL": "postgres://localhost/db", "API_KEY": "s3cr3t", "DEBUG": "true"}


class TestExportDotenv:
    def test_produces_key_value_pairs(self):
        result = export_dotenv(SAMPLE)
        assert 'DB_URL="postgres://localhost/db"' in result
        assert 'API_KEY="s3cr3t"' in result

    def test_ends_with_newline(self):
        assert export_dotenv(SAMPLE).endswith("\n")

    def test_empty_dict_returns_empty_string(self):
        assert export_dotenv({}) == ""

    def test_escapes_double_quotes_in_value(self):
        result = export_dotenv({"MSG": 'say "hello"'})
        assert 'MSG="say \\"hello\\""' in result

    def test_keys_are_sorted(self):
        lines = export_dotenv(SAMPLE).strip().splitlines()
        keys = [line.split("=")[0] for line in lines]
        assert keys == sorted(keys)


class TestExportShell:
    def test_produces_export_statements(self):
        result = export_shell(SAMPLE)
        assert 'export API_KEY="s3cr3t"' in result
        assert 'export DEBUG="true"' in result

    def test_ends_with_newline(self):
        assert export_shell(SAMPLE).endswith("\n")

    def test_empty_dict_returns_empty_string(self):
        assert export_shell({}) == ""

    def test_keys_are_sorted(self):
        lines = export_shell(SAMPLE).strip().splitlines()
        keys = [line.split("=")[0].replace("export ", "") for line in lines]
        assert keys == sorted(keys)


class TestExportJson:
    def test_valid_json(self):
        result = export_json(SAMPLE)
        parsed = json.loads(result)
        assert parsed == SAMPLE

    def test_ends_with_newline(self):
        assert export_json(SAMPLE).endswith("\n")

    def test_keys_sorted(self):
        result = export_json(SAMPLE)
        parsed = json.loads(result)
        assert list(parsed.keys()) == sorted(parsed.keys())


class TestExportSecrets:
    def test_dispatches_dotenv(self):
        result = export_secrets(SAMPLE, fmt="dotenv")
        assert "=" in result
        assert "export" not in result

    def test_dispatches_shell(self):
        result = export_secrets(SAMPLE, fmt="shell")
        assert result.startswith("export ")

    def test_dispatches_json(self):
        result = export_secrets(SAMPLE, fmt="json")
        json.loads(result)  # should not raise

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown export format"):
            export_secrets(SAMPLE, fmt="xml")  # type: ignore[arg-type]
