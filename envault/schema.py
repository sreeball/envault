"""Schema validation for vault secrets."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class SchemaError(Exception):
    """Raised when schema operations fail."""


VALID_TYPES = {"string", "integer", "float", "boolean", "email", "url", "regex"}


def _schema_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".schema.json")


def _load_schema(vault_path: str) -> dict:
    p = _schema_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_schema(vault_path: str, schema: dict) -> None:
    _schema_path(vault_path).write_text(json.dumps(schema, indent=2))


def add_rule(vault_path: str, key: str, type_: str, pattern: str | None = None, required: bool = False) -> dict:
    """Add or update a validation rule for a key."""
    if type_ not in VALID_TYPES:
        raise SchemaError(f"Unknown type '{type_}'. Valid types: {', '.join(sorted(VALID_TYPES))}")
    if type_ == "regex" and not pattern:
        raise SchemaError("A 'pattern' is required when type is 'regex'.")
    schema = _load_schema(vault_path)
    rule = {"type": type_, "required": required}
    if pattern:
        rule["pattern"] = pattern
    schema[key] = rule
    _save_schema(vault_path, schema)
    return {"key": key, **rule}


def remove_rule(vault_path: str, key: str) -> None:
    """Remove the validation rule for a key."""
    schema = _load_schema(vault_path)
    if key not in schema:
        raise SchemaError(f"No rule found for key '{key}'.")
    del schema[key]
    _save_schema(vault_path, schema)


def get_rules(vault_path: str) -> dict:
    """Return all validation rules."""
    return _load_schema(vault_path)


def validate_value(key: str, value: str, rule: dict) -> list[str]:
    """Validate a single value against a rule. Returns list of error messages."""
    errors: list[str] = []
    t = rule.get("type", "string")
    if t == "integer":
        try:
            int(value)
        except ValueError:
            errors.append(f"'{key}' must be an integer, got '{value}'.")
    elif t == "float":
        try:
            float(value)
        except ValueError:
            errors.append(f"'{key}' must be a float, got '{value}'.")
    elif t == "boolean":
        if value.lower() not in {"true", "false", "1", "0"}:
            errors.append(f"'{key}' must be a boolean (true/false), got '{value}'.")
    elif t == "email":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            errors.append(f"'{key}' must be a valid email address.")
    elif t == "url":
        if not re.match(r"^https?://", value):
            errors.append(f"'{key}' must be a valid URL starting with http:// or https://.")
    elif t == "regex":
        pattern = rule.get("pattern", "")
        if not re.match(pattern, value):
            errors.append(f"'{key}' does not match required pattern '{pattern}'.")
    return errors


def validate_vault(vault_path: str, secrets: dict[str, str]) -> dict[str, list[str]]:
    """Validate all secrets against schema rules. Returns dict of key -> errors."""
    schema = _load_schema(vault_path)
    results: dict[str, list[str]] = {}
    for key, rule in schema.items():
        if key not in secrets:
            if rule.get("required"):
                results[key] = [f"'{key}' is required but not present in vault."]
        else:
            errs = validate_value(key, secrets[key], rule)
            if errs:
                results[key] = errs
    return results
