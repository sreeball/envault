"""CLI commands for pinning / unpinning secrets."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.pin import PinError, list_pins, pin_key, unpin_key, is_pinned


@click.group("pin")
def pin_group() -> None:
    """Pin secrets to prevent accidental modification."""


@pin_group.command("add")
@click.argument("key")
@click.option("--reason", "-r", default="", help="Human-readable reason for pinning.")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", default="vault.db")
def add_cmd(key: str, reason: str, vault_path: str) -> None:
    """Pin KEY so it cannot be overwritten."""
    try:
        entry = pin_key(vault_path, key, reason)
        msg = f"Pinned '{entry['key']}'"
        if entry["reason"]:
            msg += f" — {entry['reason']}"
        click.echo(msg)
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc


@pin_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", default="vault.db")
def remove_cmd(key: str, vault_path: str) -> None:
    """Unpin KEY, allowing it to be modified again."""
    try:
        unpin_key(vault_path, key)
        click.echo(f"Unpinned '{key}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_group.command("check")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", default="vault.db")
def check_cmd(key: str, vault_path: str) -> None:
    """Check whether KEY is currently pinned."""
    if is_pinned(vault_path, key):
        click.echo(f"'{key}' is pinned.")
    else:
        click.echo(f"'{key}' is not pinned.")


@pin_group.command("list")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", default="vault.db")
def list_cmd(vault_path: str) -> None:
    """List all pinned keys."""
    pins = list_pins(vault_path)
    if not pins:
        click.echo("No pinned keys.")
        return
    for entry in pins:
        line = entry["key"]
        if entry["reason"]:
            line += f"  ({entry['reason']})"
        click.echo(line)
