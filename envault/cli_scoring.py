"""CLI commands for secret strength scoring."""
from __future__ import annotations

from pathlib import Path

import click

from envault.scoring import ScoringError, score_vault, score_value, summary


@click.group("score")
def scoring_group() -> None:
    """Score the strength of vault secrets."""


@scoring_group.command("all")
@click.argument("vault_path", type=click.Path())
@click.password_option("--password", "-p", prompt="Vault password")
@click.option("--min-grade", default=None, help="Fail if any key is below this grade (A-F).")
def all_cmd(vault_path: str, password: str, min_grade: str | None) -> None:
    """Score every secret in VAULT_PATH."""
    grades_order = ["A", "B", "C", "D", "F"]
    try:
        results = score_vault(Path(vault_path), password)
    except ScoringError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(summary(results))

    if min_grade:
        min_grade = min_grade.upper()
        if min_grade not in grades_order:
            raise click.ClickException(f"Invalid grade '{min_grade}'. Use A-F.")
        threshold = grades_order.index(min_grade)
        failing = [
            k for k, r in results.items()
            if grades_order.index(r.grade) > threshold
        ]
        if failing:
            raise click.ClickException(
                f"Keys below minimum grade {min_grade}: {', '.join(failing)}"
            )


@scoring_group.command("key")
@click.argument("key")
@click.argument("value")
def key_cmd(key: str, value: str) -> None:
    """Score a single KEY / VALUE pair (value passed directly)."""
    result = score_value(key, value)
    status = "OK" if result.ok else "WEAK"
    click.echo(f"[{result.grade}] {key} — score={result.score}/100 ({status})")
    for issue in result.issues:
        click.echo(f"  - {issue}")
