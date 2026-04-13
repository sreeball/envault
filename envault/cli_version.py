"""CLI commands for secret version history."""
from __future__ import annotations

import click

from envault.cli import get_vault
from envault.version import VersionError, get_versions, purge_versions, rollback


@click.group("version")
def version_group() -> None:
    """Manage secret version history."""


@version_group.command("list")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def list_cmd(key: str, vault_path: str) -> None:
    """List all recorded versions for KEY."""
    entries = get_versions(vault_path, key)
    if not entries:
        click.echo(f"No version history found for '{key}'.")
        return
    for e in entries:
        click.echo(f"  v{e['version']}  {e['recorded_at']}  actor={e['actor']}")


@version_group.command("show")
@click.argument("key")
@click.argument("version", type=int)
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def show_cmd(key: str, version: int, vault_path: str) -> None:
    """Show the value stored at a specific VERSION number for KEY."""
    try:
        entry = rollback(vault_path, key, version)
    except VersionError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(entry["value"])


@version_group.command("record")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
@click.option("--actor", default="user", show_default=True)
@click.password_option("--password", prompt="Vault password")
def record_cmd(key: str, vault_path: str, actor: str, password: str) -> None:
    """Record the current value of KEY as a new version."""
    vault = get_vault(vault_path, password)
    try:
        value = vault.get(key)
    except KeyError:
        raise click.ClickException(f"Key '{key}' not found in vault.")
    from envault.version import record_version
    entry = record_version(vault_path, key, value, actor=actor)
    click.echo(f"Recorded version {entry['version']} for '{key}'.")


@version_group.command("purge")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
@click.confirmation_option(prompt="Delete all version history for this key?")
def purge_cmd(key: str, vault_path: str) -> None:
    """Delete all version history for KEY."""
    count = purge_versions(vault_path, key)
    click.echo(f"Removed {count} version(s) for '{key}'.")
