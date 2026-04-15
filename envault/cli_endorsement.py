"""CLI commands for the endorsement module."""

from __future__ import annotations

import click
from .endorsement import endorse, revoke, get_endorsements, list_endorsed_keys, EndorsementError


@click.group("endorse")
def endorsement_group() -> None:
    """Manage secret endorsements."""


@endorsement_group.command("add")
@click.argument("vault_path")
@click.argument("key")
@click.argument("endorser")
@click.option("--note", default="", help="Optional note from the endorser.")
def add_cmd(vault_path: str, key: str, endorser: str, note: str) -> None:
    """Endorse a secret KEY as verified by ENDORSER."""
    try:
        entry = endorse(vault_path, key, endorser, note=note)
        click.echo(f"Endorsed '{key}' by '{endorser}' at {entry['endorsed_at']}.")
    except EndorsementError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@endorsement_group.command("revoke")
@click.argument("vault_path")
@click.argument("key")
@click.argument("endorser")
def revoke_cmd(vault_path: str, key: str, endorser: str) -> None:
    """Revoke all endorsements of KEY by ENDORSER."""
    try:
        count = revoke(vault_path, key, endorser)
        click.echo(f"Removed {count} endorsement(s) of '{key}' by '{endorser}'.")
    except EndorsementError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@endorsement_group.command("list")
@click.argument("vault_path")
@click.argument("key")
def list_cmd(vault_path: str, key: str) -> None:
    """List all endorsements for KEY."""
    entries = get_endorsements(vault_path, key)
    if not entries:
        click.echo(f"No endorsements found for '{key}'.")
        return
    for e in entries:
        note_part = f" — {e['note']}" if e.get("note") else ""
        click.echo(f"  {e['endorser']} at {e['endorsed_at']}{note_part}")


@endorsement_group.command("keys")
@click.argument("vault_path")
def keys_cmd(vault_path: str) -> None:
    """List all keys that have at least one endorsement."""
    keys = list_endorsed_keys(vault_path)
    if not keys:
        click.echo("No endorsed keys found.")
        return
    for k in keys:
        click.echo(k)
