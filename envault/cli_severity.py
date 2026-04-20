"""CLI commands for managing secret severity levels."""

import click

from envault.cli import get_vault
from envault.severity import (
    SeverityError,
    VALID_LEVELS,
    set_severity,
    get_severity,
    remove_severity,
    list_severity,
)


@click.group("severity")
def severity_group():
    """Manage severity levels for secrets."""


@severity_group.command("set")
@click.argument("key")
@click.argument("level", type=click.Choice(VALID_LEVELS))
@click.option("--note", default="", help="Optional note about the severity.")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def set_cmd(key, level, note, vault_path):
    """Set the severity level for KEY."""
    try:
        entry = set_severity(vault_path, key, level, note)
        click.echo(f"Severity for '{key}' set to '{entry['level']}'.")
    except SeverityError as exc:
        raise click.ClickException(str(exc))


@severity_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def get_cmd(key, vault_path):
    """Get the severity level for KEY."""
    entry = get_severity(vault_path, key)
    if entry is None:
        click.echo(f"No severity set for '{key}'.")
    else:
        note_part = f" ({entry['note']})" if entry["note"] else ""
        click.echo(f"{key}: {entry['level']}{note_part}")


@severity_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(key, vault_path):
    """Remove the severity entry for KEY."""
    removed = remove_severity(vault_path, key)
    if removed:
        click.echo(f"Severity for '{key}' removed.")
    else:
        click.echo(f"No severity entry found for '{key}'.")


@severity_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path):
    """List all severity entries."""
    entries = list_severity(vault_path)
    if not entries:
        click.echo("No severity entries found.")
        return
    for key, entry in sorted(entries.items()):
        note_part = f" — {entry['note']}" if entry["note"] else ""
        click.echo(f"{key}: {entry['level']}{note_part}")
