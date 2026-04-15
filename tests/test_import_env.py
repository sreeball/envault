"""Tests for envault.import_env."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envault.import_env import (
    ImportError,
    _parse_dotenv,
    _parse_json,
    import_from_env,
    import_from_file,
    load_into_vault,
)


# ---------------------------------------------------------------------------
# _parse_dotenv
# ---------------------------------------------------------------------------

class TestParseDotenv:
    def test_simple_pair(self):
        assert _parse_dotenv("KEY=value") == {"KEY": "value"}

    def test_double_quoted_value(self):
        assert _parse_dotenv('KEY="hello world"') == {"KEY": "hello world"}

    def test_single_quoted_value(self):
        assert _parse_dotenv("KEY='hello'") == {"KEY": "hello"}

    def test_ignores_comments(self):
        result = _parse_dotenv("# comment\nKEY=val")
        assert result == {"KEY": "val"}

    def test_ignores_blank_lines(self):
        result = _parse_dotenv("\nKEY=val\n")
        assert result == {"KEY": "val"}

    def test_multiple_pairs(self):
        text = "A=1\nB=2\nC=3"
        assert _parse_dotenv(text) == {"A": "1", "B": "2", "C": "3"}

    def test_empty_value(self):
        assert _parse_dotenv("KEY=") == {"KEY": ""}

    def test_inline_comment_ignored(self):
        """Values should not include trailing inline comments."""
        result = _parse_dotenv("KEY=value  # inline comment")
        assert result == {"KEY": "value"}

    def test_value_with_equals_sign(self):
        """Only the first '=' is treated as the key/value separator."""
        result = _parse_dotenv("KEY=val=ue")
        assert result == {"KEY": "val=ue"}


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_simple_object(self):
        assert _parse_json('{"A": "1"}') == {"A": "1"}

    def test_numeric_values_converted_to_str(self):
        result = _parse_json('{"PORT": 8080}')
        assert result == {"PORT": "8080"}

    def test_invalid_json_raises(self):
        with pytest.raises(ImportError, match="Invalid JSON"):
            _parse_json("not json")

    def test_non_object_raises(self):
        with pytest.raises(ImportError, match="object"):
            _parse_json('["a", "b"]')


# ---------------------------------------------------------------------------
# import_from_file
# ---------------------------------------------------------------------------

class TestImportFromFile:
    def test_dotenv_file(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("X=hello\nY=world\n")
        assert import_from_file(f) == {"X": "hello", "Y": "world"}

    def test_json_file(self, tmp_path):
        f = tmp_path / "secrets.json"
        f.write_text(json.dumps({"TOKEN": "abc"}))
        assert import_from_file(f, fmt="json") == {"TOKEN": "abc"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ImportError, match="File not found"):
            import_from_file(tmp_path / "nope.env")

    def test_unknown_format_raises(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("A=1")
        with pytest.raises(ImportError, match="Unknown format"):
            import_from_file(f, fmt="yaml")

    def test_json_file_auto_detected_by_extension(self, tmp_path):
        """A .json file should be parsed as JSON without specifying fmt."""
        f = tmp_path / "config.json"
        f.write_text(json.dumps({"DB_HOST": "localhost"}))
        assert import_from_file(f) == {"DB_HOST": "localhost"}


# --------------------------------------------
