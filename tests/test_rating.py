"""Tests for envault.rating."""

import pytest
from pathlib import Path
import json

from envault.rating import (
    RatingError,
    rate_key,
    get_rating,
    remove_rating,
    list_ratings,
    _ratings_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.db")


class TestRateKey:
    def test_creates_ratings_file(self, vault_path):
        rate_key(vault_path, "DB_PASS", 4)
        assert _ratings_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = rate_key(vault_path, "API_KEY", 5, "perfect")
        assert entry["key"] == "API_KEY"
        assert entry["stars"] == 5
        assert entry["review"] == "perfect"

    def test_empty_review_allowed(self, vault_path):
        entry = rate_key(vault_path, "TOKEN", 3)
        assert entry["review"] == ""

    def test_raises_on_stars_below_one(self, vault_path):
        with pytest.raises(RatingError):
            rate_key(vault_path, "X", 0)

    def test_raises_on_stars_above_five(self, vault_path):
        with pytest.raises(RatingError):
            rate_key(vault_path, "X", 6)

    def test_overwrites_existing_rating(self, vault_path):
        rate_key(vault_path, "K", 2)
        entry = rate_key(vault_path, "K", 5, "updated")
        assert entry["stars"] == 5
        assert entry["review"] == "updated"

    def test_persists_to_file(self, vault_path):
        rate_key(vault_path, "SEC", 3, "ok")
        raw = json.loads(_ratings_path(vault_path).read_text())
        assert raw["SEC"]["stars"] == 3


class TestGetRating:
    def test_returns_stored_entry(self, vault_path):
        rate_key(vault_path, "A", 4, "nice")
        entry = get_rating(vault_path, "A")
        assert entry["stars"] == 4

    def test_raises_when_key_absent(self, vault_path):
        with pytest.raises(RatingError):
            get_rating(vault_path, "MISSING")


class TestRemoveRating:
    def test_removes_existing_entry(self, vault_path):
        rate_key(vault_path, "B", 2)
        remove_rating(vault_path, "B")
        with pytest.raises(RatingError):
            get_rating(vault_path, "B")

    def test_no_error_when_key_absent(self, vault_path):
        remove_rating(vault_path, "GHOST")  # should not raise


class TestListRatings:
    def test_returns_empty_list_when_no_ratings(self, vault_path):
        assert list_ratings(vault_path) == []

    def test_sorted_by_stars_descending(self, vault_path):
        rate_key(vault_path, "LOW", 1)
        rate_key(vault_path, "HIGH", 5)
        rate_key(vault_path, "MID", 3)
        entries = list_ratings(vault_path)
        assert [e["stars"] for e in entries] == [5, 3, 1]
