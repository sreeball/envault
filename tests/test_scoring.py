"""Tests for envault.scoring."""
from pathlib import Path

import pytest

from envault.scoring import (
    ScoringError,
    ScoreResult,
    _grade,
    score_value,
    score_vault,
    summary,
)
from envault.vault import Vault


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "vault.json"
    v = Vault(p, "testpass")
    v.set("STRONG_KEY", "C0mpl3x!P@ssw0rd#99")
    v.set("WEAK_KEY", "abc")
    v.set("MEDIUM_KEY", "abcdefgh12")
    return p


class TestGrade:
    def test_a_grade(self):
        assert _grade(95) == "A"

    def test_b_grade(self):
        assert _grade(80) == "B"

    def test_c_grade(self):
        assert _grade(60) == "C"

    def test_d_grade(self):
        assert _grade(45) == "D"

    def test_f_grade(self):
        assert _grade(30) == "F"


class TestScoreValue:
    def test_strong_value_high_score(self):
        r = score_value("KEY", "C0mpl3x!P@ssw0rd#99")
        assert r.score >= 90
        assert r.grade == "A"
        assert r.issues == []

    def test_too_short_penalised(self):
        r = score_value("KEY", "abc")
        assert "too short (< 8 chars)" in r.issues
        assert r.score <= 60

    def test_no_uppercase_penalised(self):
        r = score_value("KEY", "alllowercase1!")
        assert "no uppercase letters" in r.issues

    def test_no_digits_penalised(self):
        r = score_value("KEY", "NoDigitsHere!")
        assert "no digits" in r.issues

    def test_no_special_chars_penalised(self):
        r = score_value("KEY", "NoSpecialChars1")
        assert "no special characters" in r.issues

    def test_repeated_chars_penalised(self):
        r = score_value("KEY", "aaaaaA1!")
        assert "repeated characters detected" in r.issues

    def test_score_clamped_to_zero(self):
        r = score_value("KEY", "a")
        assert r.score >= 0

    def test_ok_property_true_for_good_score(self):
        r = score_value("KEY", "C0mpl3x!P@ssw0rd#99")
        assert r.ok is True

    def test_ok_property_false_for_bad_score(self):
        r = score_value("KEY", "abc")
        assert r.ok is False


class TestScoreVault:
    def test_returns_dict_of_results(self, vault_path: Path):
        results = score_vault(vault_path, "testpass")
        assert set(results.keys()) == {"STRONG_KEY", "WEAK_KEY", "MEDIUM_KEY"}

    def test_strong_key_grades_well(self, vault_path: Path):
        results = score_vault(vault_path, "testpass")
        assert results["STRONG_KEY"].grade in ("A", "B")

    def test_weak_key_grades_poorly(self, vault_path: Path):
        results = score_vault(vault_path, "testpass")
        assert results["WEAK_KEY"].grade in ("D", "F")

    def test_empty_vault_returns_empty_dict(self, tmp_path: Path):
        p = tmp_path / "empty.json"
        Vault(p, "pass")
        results = score_vault(p, "pass")
        assert results == {}


class TestSummary:
    def test_empty_results_message(self):
        assert summary({}) == "No secrets to score."

    def test_contains_key_names(self, vault_path: Path):
        results = score_vault(vault_path, "testpass")
        out = summary(results)
        assert "STRONG_KEY" in out
        assert "WEAK_KEY" in out

    def test_contains_average(self, vault_path: Path):
        results = score_vault(vault_path, "testpass")
        out = summary(results)
        assert "Average score:" in out
