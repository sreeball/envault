"""Tests for envault.trust."""
from __future__ import annotations

import json
import pytest

from envault.trust import (
    TrustError,
    evaluate_trust,
    get_trust,
    list_trust,
    remove_trust,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestEvaluateTrust:
    def test_creates_trust_file(self, vault_path, tmp_path):
        evaluate_trust(vault_path, "API_KEY")
        assert (tmp_path / ".envault_trust.json").exists()

    def test_returns_entry_dict(self, vault_path):
        result = evaluate_trust(vault_path, "API_KEY")
        assert "score" in result
        assert "level" in result
        assert "factors" in result

    def test_zero_score_when_no_factors(self, vault_path):
        result = evaluate_trust(vault_path, "API_KEY")
        assert result["score"] == 0
        assert result["level"] == "untrusted"

    def test_perfect_score_all_factors(self, vault_path):
        result = evaluate_trust(
            vault_path,
            "API_KEY",
            has_comment=True,
            has_label=True,
            has_schema=True,
            has_owner=True,
            has_ttl=True,
        )
        assert result["score"] == 100
        assert result["level"] == "verified"

    def test_partial_score_medium(self, vault_path):
        result = evaluate_trust(
            vault_path, "DB_PASS", has_schema=True, has_owner=True
        )
        assert result["score"] == 55
        assert result["level"] == "medium"

    def test_factors_stored_correctly(self, vault_path):
        result = evaluate_trust(vault_path, "TOKEN", has_comment=True)
        assert result["factors"]["has_comment"] is True
        assert result["factors"]["has_schema"] is False

    def test_overwrites_existing_entry(self, vault_path):
        evaluate_trust(vault_path, "KEY", has_label=True)
        result = evaluate_trust(vault_path, "KEY", has_schema=True)
        assert result["factors"]["has_label"] is False
        assert result["factors"]["has_schema"] is True

    def test_persists_to_file(self, vault_path, tmp_path):
        evaluate_trust(vault_path, "SECRET", has_owner=True)
        raw = json.loads((tmp_path / ".envault_trust.json").read_text())
        assert "SECRET" in raw


class TestGetTrust:
    def test_returns_stored_entry(self, vault_path):
        evaluate_trust(vault_path, "API_KEY", has_label=True)
        entry = get_trust(vault_path, "API_KEY")
        assert entry["factors"]["has_label"] is True

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(TrustError, match="No trust record"):
            get_trust(vault_path, "NONEXISTENT")


class TestListTrust:
    def test_empty_when_no_records(self, vault_path):
        assert list_trust(vault_path) == {}

    def test_returns_all_records(self, vault_path):
        evaluate_trust(vault_path, "A")
        evaluate_trust(vault_path, "B", has_schema=True)
        records = list_trust(vault_path)
        assert set(records.keys()) == {"A", "B"}


class TestRemoveTrust:
    def test_removes_entry(self, vault_path):
        evaluate_trust(vault_path, "KEY")
        remove_trust(vault_path, "KEY")
        assert "KEY" not in list_trust(vault_path)

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(TrustError, match="No trust record"):
            remove_trust(vault_path, "GHOST")
