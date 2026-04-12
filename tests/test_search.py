"""Tests for envault.search."""

import pytest

from envault.search import SearchError, list_keys_matching, search
from envault.vault import Vault

PASSWORD = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"))
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("API_KEY", "secret-token-abc", PASSWORD)
    v.set("API_SECRET", "topsecret", PASSWORD)
    v.set("APP_DEBUG", "true", PASSWORD)
    return v


class TestSearch:
    def test_glob_key_match(self, vault):
        results = search(vault, PASSWORD, "DB_*")
        assert set(results.keys()) == {"DB_HOST", "DB_PORT"}

    def test_exact_key_match(self, vault):
        results = search(vault, PASSWORD, "API_KEY")
        assert list(results.keys()) == ["API_KEY"]
        assert results["API_KEY"] == "secret-token-abc"

    def test_no_match_returns_empty(self, vault):
        results = search(vault, PASSWORD, "NONEXISTENT_*")
        assert results == {}

    def test_value_match(self, vault):
        # 'topsecret' is the value of API_SECRET
        results = search(vault, PASSWORD, "topsecret")
        assert "API_SECRET" in results

    def test_keys_only_skips_value_match(self, vault):
        results = search(vault, PASSWORD, "topsecret", keys_only=True)
        assert results == {}

    def test_regex_key_match(self, vault):
        results = search(vault, PASSWORD, r"^API_", regex=True)
        assert set(results.keys()) == {"API_KEY", "API_SECRET"}

    def test_regex_value_match(self, vault):
        results = search(vault, PASSWORD, r"\d{4}", regex=True)
        assert "DB_PORT" in results

    def test_empty_pattern_raises(self, vault):
        with pytest.raises(SearchError, match="must not be empty"):
            search(vault, PASSWORD, "")

    def test_invalid_regex_raises(self, vault):
        with pytest.raises(SearchError, match="Invalid regular expression"):
            search(vault, PASSWORD, "[unclosed", regex=True)

    def test_glob_wildcard_matches_all(self, vault):
        """A bare '*' glob should return every key in the vault."""
        results = search(vault, PASSWORD, "*")
        assert set(results.keys()) == {"DB_HOST", "DB_PORT", "API_KEY", "API_SECRET", "APP_DEBUG"}

    def test_value_match_returns_correct_value(self, vault):
        """Ensure the returned value is correct when matching by value."""
        results = search(vault, PASSWORD, "localhost")
        assert results.get("DB_HOST") == "localhost"


class TestListKeysMatching:
    def test_glob_returns_matching_keys(self, vault):
        keys = list_keys_matching(vault, "APP_*")
        assert keys == ["APP_DEBUG"]

    def test_regex_returns_matching_keys(self, vault):
        keys = list_keys_matching(vault, r"^DB", regex=True)
        assert set(keys) == {"DB_HOST", "DB_PORT"}

    def test_empty_pattern_raises(self, vault):
        with pytest.raises(SearchError):
            list_keys_matching(vault, "")

    def test_no_match_returns_empty_list(self, vault):
        keys = list_keys_matching(vault, "MISSING_*")
        assert keys == []
