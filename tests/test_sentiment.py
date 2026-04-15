"""Tests for envault.sentiment."""
import json
import pytest

from envault.sentiment import (
    SentimentError,
    _sentiment_path,
    set_sentiment,
    get_sentiment,
    remove_sentiment,
    list_sentiment,
    summary,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetSentiment:
    def test_creates_sentiment_file(self, vault_path):
        set_sentiment(vault_path, "API_KEY", "positive")
        assert _sentiment_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_sentiment(vault_path, "API_KEY", "positive", note="looks good")
        assert entry["key"] == "API_KEY"
        assert entry["level"] == "positive"
        assert entry["note"] == "looks good"

    def test_empty_note_allowed(self, vault_path):
        entry = set_sentiment(vault_path, "DB_PASS", "neutral")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(SentimentError, match="Invalid sentiment level"):
            set_sentiment(vault_path, "API_KEY", "unknown")

    def test_raises_on_invalid_key(self, vault_path):
        with pytest.raises(SentimentError, match="Invalid key name"):
            set_sentiment(vault_path, "bad key!", "neutral")

    def test_overwrites_existing_entry(self, vault_path):
        set_sentiment(vault_path, "API_KEY", "positive")
        entry = set_sentiment(vault_path, "API_KEY", "negative", note="changed")
        assert entry["level"] == "negative"
        assert entry["note"] == "changed"

    def test_stores_entry_in_file(self, vault_path):
        set_sentiment(vault_path, "TOKEN", "negative", note="risky")
        raw = json.loads(_sentiment_path(vault_path).read_text())
        assert raw["TOKEN"]["level"] == "negative"


class TestGetSentiment:
    def test_returns_entry(self, vault_path):
        set_sentiment(vault_path, "MY_KEY", "neutral")
        entry = get_sentiment(vault_path, "MY_KEY")
        assert entry is not None
        assert entry["level"] == "neutral"

    def test_returns_none_for_missing_key(self, vault_path):
        assert get_sentiment(vault_path, "MISSING") is None


class TestRemoveSentiment:
    def test_removes_entry(self, vault_path):
        set_sentiment(vault_path, "API_KEY", "positive")
        assert remove_sentiment(vault_path, "API_KEY") is True
        assert get_sentiment(vault_path, "API_KEY") is None

    def test_returns_false_for_missing_key(self, vault_path):
        assert remove_sentiment(vault_path, "GHOST") is False


class TestListSentiment:
    def test_returns_all_entries_sorted(self, vault_path):
        set_sentiment(vault_path, "Z_KEY", "positive")
        set_sentiment(vault_path, "A_KEY", "negative")
        entries = list_sentiment(vault_path)
        assert [e["key"] for e in entries] == ["A_KEY", "Z_KEY"]

    def test_empty_when_no_file(self, vault_path):
        assert list_sentiment(vault_path) == []


class TestSummary:
    def test_counts_levels(self, vault_path):
        set_sentiment(vault_path, "A", "positive")
        set_sentiment(vault_path, "B", "positive")
        set_sentiment(vault_path, "C", "negative")
        result = summary(vault_path)
        assert result["positive"] == 2
        assert result["negative"] == 1
        assert result["neutral"] == 0

    def test_all_zero_when_empty(self, vault_path):
        result = summary(vault_path)
        assert all(v == 0 for v in result.values())
