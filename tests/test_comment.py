"""Tests for envault.comment module."""

import json
import pytest
from pathlib import Path

from envault.comment import (
    CommentError,
    add_comment,
    get_comments,
    remove_comments,
    list_commented_keys,
    _comments_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


class TestAddComment:
    def test_creates_comments_file(self, vault_path):
        add_comment(vault_path, "DB_PASS", "Production database password")
        assert _comments_path(vault_path).exists()

    def test_returns_comment_list(self, vault_path):
        result = add_comment(vault_path, "API_KEY", "External API key")
        assert isinstance(result, list)
        assert "External API key" in result

    def test_accumulates_comments(self, vault_path):
        add_comment(vault_path, "TOKEN", "First note")
        result = add_comment(vault_path, "TOKEN", "Second note")
        assert len(result) == 2
        assert "First note" in result
        assert "Second note" in result

    def test_strips_whitespace(self, vault_path):
        result = add_comment(vault_path, "KEY", "  trimmed  ")
        assert result[0] == "trimmed"

    def test_raises_on_empty_comment(self, vault_path):
        with pytest.raises(CommentError):
            add_comment(vault_path, "KEY", "   ")

    def test_multiple_keys_independent(self, vault_path):
        add_comment(vault_path, "KEY_A", "Note for A")
        add_comment(vault_path, "KEY_B", "Note for B")
        assert get_comments(vault_path, "KEY_A") == ["Note for A"]
        assert get_comments(vault_path, "KEY_B") == ["Note for B"]


class TestGetComments:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        result = get_comments(vault_path, "MISSING")
        assert result == []

    def test_returns_all_comments(self, vault_path):
        add_comment(vault_path, "X", "alpha")
        add_comment(vault_path, "X", "beta")
        assert get_comments(vault_path, "X") == ["alpha", "beta"]


class TestRemoveComments:
    def test_removes_key_from_file(self, vault_path):
        add_comment(vault_path, "KEY", "some note")
        remove_comments(vault_path, "KEY")
        assert get_comments(vault_path, "KEY") == []

    def test_raises_if_key_not_found(self, vault_path):
        with pytest.raises(CommentError):
            remove_comments(vault_path, "GHOST")


class TestListCommentedKeys:
    def test_returns_empty_dict_when_no_comments(self, vault_path):
        result = list_commented_keys(vault_path)
        assert result == {}

    def test_returns_all_annotated_keys(self, vault_path):
        add_comment(vault_path, "A", "note a")
        add_comment(vault_path, "B", "note b")
        result = list_commented_keys(vault_path)
        assert set(result.keys()) == {"A", "B"}
