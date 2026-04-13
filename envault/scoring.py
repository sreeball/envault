"""Secret strength scoring for vault entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class ScoringError(Exception):
    pass


@dataclass
class ScoreResult:
    key: str
    score: int          # 0-100
    grade: str          # A, B, C, D, F
    issues: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.score >= 60


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_value(key: str, value: str) -> ScoreResult:
    """Score a single secret value and return a ScoreResult."""
    issues: List[str] = []
    score = 100

    if len(value) < 8:
        issues.append("too short (< 8 chars)")
        score -= 40
    elif len(value) < 16:
        issues.append("short (< 16 chars)")
        score -= 15

    if value.lower() == value:
        issues.append("no uppercase letters")
        score -= 10

    if not re.search(r"[0-9]", value):
        issues.append("no digits")
        score -= 10

    if not re.search(r"[^A-Za-z0-9]", value):
        issues.append("no special characters")
        score -= 10

    if re.search(r"(.)\1{3,}", value):
        issues.append("repeated characters detected")
        score -= 10

    score = max(0, score)
    return ScoreResult(key=key, score=score, grade=_grade(score), issues=issues)


def score_vault(vault_path: Path, password: str) -> Dict[str, ScoreResult]:
    """Score all secrets in a vault. Returns mapping of key -> ScoreResult."""
    from envault.vault import Vault

    v = Vault(vault_path, password)
    keys = v.list()
    results: Dict[str, ScoreResult] = {}
    for key in keys:
        try:
            value = v.get(key)
        except Exception as exc:
            raise ScoringError(f"Could not read key '{key}': {exc}") from exc
        results[key] = score_value(key, value)
    return results


def summary(results: Dict[str, ScoreResult]) -> str:
    """Return a human-readable summary of scoring results."""
    if not results:
        return "No secrets to score."
    lines = []
    for key, r in sorted(results.items()):
        issue_str = "; ".join(r.issues) if r.issues else "OK"
        lines.append(f"  [{r.grade}] {key} (score={r.score}): {issue_str}")
    avg = sum(r.score for r in results.values()) // len(results)
    lines.append(f"\nAverage score: {avg}/100")
    return "\n".join(lines)
