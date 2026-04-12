"""Tests for envault.schema."""
import json
import pytest
from pathlib import Path
from envault.schema import (
    SchemaError,
    add_rule,
    remove_rule,
    get_rules,
    validate_value,
    validate_vault,
    _schema_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestAddRule:
    def test_creates_schema_file(self, vault_path):
        add_rule(vault_path, "PORT", "integer")
        assert _schema_path(vault_path).exists()

    def test_returns_rule_dict(self, vault_path):
        result = add_rule(vault_path, "PORT", "integer", required=True)
        assert result["key"] == "PORT"
        assert result["type"] == "integer"
        assert result["required"] is True

    def test_stores_rule(self, vault_path):
        add_rule(vault_path, "EMAIL", "email")
        rules = get_rules(vault_path)
        assert "EMAIL" in rules
        assert rules["EMAIL"]["type"] == "email"

    def test_stores_pattern_for_regex(self, vault_path):
        add_rule(vault_path, "CODE", "regex", pattern=r"^[A-Z]{3}$")
        rules = get_rules(vault_path)
        assert rules["CODE"]["pattern"] == r"^[A-Z]{3}$"

    def test_raises_on_invalid_type(self, vault_path):
        with pytest.raises(SchemaError, match="Unknown type"):
            add_rule(vault_path, "X", "uuid")

    def test_raises_on_regex_without_pattern(self, vault_path):
        with pytest.raises(SchemaError, match="pattern"):
            add_rule(vault_path, "X", "regex")

    def test_overwrites_existing_rule(self, vault_path):
        add_rule(vault_path, "PORT", "integer")
        add_rule(vault_path, "PORT", "float")
        rules = get_rules(vault_path)
        assert rules["PORT"]["type"] == "float"


class TestRemoveRule:
    def test_removes_rule(self, vault_path):
        add_rule(vault_path, "PORT", "integer")
        remove_rule(vault_path, "PORT")
        assert "PORT" not in get_rules(vault_path)

    def test_raises_when_key_missing(self, vault_path):
        with pytest.raises(SchemaError, match="No rule found"):
            remove_rule(vault_path, "NONEXISTENT")


class TestValidateValue:
    def test_valid_integer(self):
        assert validate_value("PORT", "8080", {"type": "integer"}) == []

    def test_invalid_integer(self):
        errs = validate_value("PORT", "abc", {"type": "integer"})
        assert len(errs) == 1
        assert "integer" in errs[0]

    def test_valid_float(self):
        assert validate_value("RATIO", "3.14", {"type": "float"}) == []

    def test_invalid_float(self):
        errs = validate_value("RATIO", "not-a-float", {"type": "float"})
        assert errs

    def test_valid_boolean(self):
        for v in ("true", "false", "1", "0", "True", "FALSE"):
            assert validate_value("FLAG", v, {"type": "boolean"}) == []

    def test_invalid_boolean(self):
        errs = validate_value("FLAG", "yes", {"type": "boolean"})
        assert errs

    def test_valid_email(self):
        assert validate_value("EMAIL", "user@example.com", {"type": "email"}) == []

    def test_invalid_email(self):
        errs = validate_value("EMAIL", "not-an-email", {"type": "email"})
        assert errs

    def test_valid_url(self):
        assert validate_value("URL", "https://example.com", {"type": "url"}) == []

    def test_invalid_url(self):
        errs = validate_value("URL", "ftp://example.com", {"type": "url"})
        assert errs

    def test_valid_regex(self):
        assert validate_value("CODE", "ABC", {"type": "regex", "pattern": r"^[A-Z]{3}$"}) == []

    def test_invalid_regex(self):
        errs = validate_value("CODE", "abc", {"type": "regex", "pattern": r"^[A-Z]{3}$"})
        assert errs


class TestValidateVault:
    def test_no_issues_when_valid(self, vault_path):
        add_rule(vault_path, "PORT", "integer")
        result = validate_vault(vault_path, {"PORT": "3000"})
        assert result == {}

    def test_reports_type_error(self, vault_path):
        add_rule(vault_path, "PORT", "integer")
        result = validate_vault(vault_path, {"PORT": "not-a-number"})
        assert "PORT" in result

    def test_required_key_missing(self, vault_path):
        add_rule(vault_path, "SECRET", "string", required=True)
        result = validate_vault(vault_path, {})
        assert "SECRET" in result
        assert "required" in result["SECRET"][0]

    def test_optional_missing_key_ignored(self, vault_path):
        add_rule(vault_path, "OPTIONAL", "string", required=False)
        result = validate_vault(vault_path, {})
        assert "OPTIONAL" not in result

    def test_empty_schema_always_passes(self, vault_path):
        result = validate_vault(vault_path, {"ANY": "value"})
        assert result == {}
