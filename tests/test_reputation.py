"""Tests for envault.reputation."""

import json
import pytest

from envault.reputation import (
    ReputationError,
    _reputation_path,
    record_reputation,
    get_reputation,
    list_reputation,
    remove_reputation,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.json"
    p.write_text(json.dumps({}))
    return str(p)


# ---------------------------------------------------------------------------
# record_reputation
# ---------------------------------------------------------------------------

class TestRecordReputation:
    def test_creates_reputation_file(self, vault_path):
        record_reputation(vault_path, "API_KEY", {})
        assert _reputation_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = record_reputation(vault_path, "API_KEY", {})
        assert entry["key"] == "API_KEY"
        assert "score" in entry
        assert "factors" in entry

    def test_score_perfect_with_all_good_factors(self, vault_path):
        factors = {
            "has_comment": True,
            "has_label": True,
            "is_expired": False,
            "is_archived": False,
            "has_schema": True,
            "is_readonly": True,
        }
        entry = record_reputation(vault_path, "K", factors)
        assert entry["score"] == 105  # capped at 100
        assert entry["score"] <= 100

    def test_score_penalised_for_expired(self, vault_path):
        entry = record_reputation(vault_path, "K", {"is_expired": True})
        assert entry["score"] <= 60

    def test_score_penalised_for_missing_comment_and_label(self, vault_path):
        entry = record_reputation(vault_path, "K", {})
        assert entry["score"] <= 80

    def test_accumulates_entries(self, vault_path):
        record_reputation(vault_path, "A", {})
        record_reputation(vault_path, "B", {"has_comment": True})
        data = json.loads(_reputation_path(vault_path).read_text())
        assert "A" in data and "B" in data

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(ReputationError):
            record_reputation(vault_path, "", {})

    def test_overwrites_existing_entry(self, vault_path):
        record_reputation(vault_path, "K", {})
        record_reputation(vault_path, "K", {"has_comment": True})
        data = json.loads(_reputation_path(vault_path).read_text())
        assert data["K"]["factors"]["has_comment"] is True


# ---------------------------------------------------------------------------
# get_reputation
# ---------------------------------------------------------------------------

class TestGetReputation:
    def test_returns_stored_entry(self, vault_path):
        record_reputation(vault_path, "MY_KEY", {"has_label": True})
        entry = get_reputation(vault_path, "MY_KEY")
        assert entry["key"] == "MY_KEY"

    def test_raises_for_missing_key(self, vault_path):
        with pytest.raises(ReputationError):
            get_reputation(vault_path, "MISSING")


# ---------------------------------------------------------------------------
# list_reputation
# ---------------------------------------------------------------------------

class TestListReputation:
    def test_returns_list(self, vault_path):
        record_reputation(vault_path, "A", {})
        result = list_reputation(vault_path)
        assert isinstance(result, list)

    def test_sorted_by_score_ascending(self, vault_path):
        record_reputation(vault_path, "GOOD", {"has_comment": True, "has_label": True, "has_schema": True})
        record_reputation(vault_path, "BAD", {"is_expired": True, "is_archived": True})
        result = list_reputation(vault_path)
        assert result[0]["score"] <= result[-1]["score"]

    def test_empty_when_no_records(self, vault_path):
        assert list_reputation(vault_path) == []


# ---------------------------------------------------------------------------
# remove_reputation
# ---------------------------------------------------------------------------

class TestRemoveReputation:
    def test_removes_entry(self, vault_path):
        record_reputation(vault_path, "K", {})
        remove_reputation(vault_path, "K")
        data = json.loads(_reputation_path(vault_path).read_text())
        assert "K" not in data

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(ReputationError):
            remove_reputation(vault_path, "GHOST")
