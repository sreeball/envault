"""CLI commands for managing escalation rules."""
from __future__ import annotations

import click

from envault.escalation import (
    EscalationError,
    get_escalation,
    list_escalations,
    remove_escalation,
    set_escalation,
)


@click.group("escalation")
def escalation_group() -> None:
    """Manage escalation rules for secret keys."""


@escalation_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("level")
@click.argument("contact")
@click.option("--threshold", default=1, show_default=True, help="Trigger threshold.")
@click.option("--note", default="", help="Optional note.")
def set_cmd(
    vault_path: str,
    key: str,
    level: str,
    contact: str,
    threshold: int,
    note: str,
) -> None:
    """Set an escalation rule for KEY."""
    try:
        entry = set_escalation(vault_path, key, level, contact, threshold, note)
        click.echo(
            f"Escalation set: {key} -> {entry['level']} / {entry['contact']} "
            f"(threshold={entry['threshold']})"
        )
    except EscalationError as exc:
        raise click.ClickException(str(exc)) from exc


@escalation_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path: str, key: str) -> None:
    """Show the escalation rule for KEY."""
    entry = get_escalation(vault_path, key)
    if entry is None:
        click.echo(f"No escalation rule for '{key}'.")
        return
    for field, value in entry.items():
        click.echo(f"{field}: {value}")


@escalation_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove the escalation rule for KEY."""
    try:
        remove_escalation(vault_path, key)
        click.echo(f"Escalation rule for '{key}' removed.")
    except EscalationError as exc:
        raise click.ClickException(str(exc)) from exc


@escalation_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all escalation rules."""
    rules = list_escalations(vault_path)
    if not rules:
        click.echo("No escalation rules defined.")
        return
    for key, entry in rules.items():
        click.echo(
            f"{key}: level={entry['level']}, contact={entry['contact']}, "
            f"threshold={entry['threshold']}"
        )
